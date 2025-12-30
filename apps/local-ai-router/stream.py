"""
SSE streaming utilities for chat completions with status events.

Provides real-time feedback during request lifecycle:
- routing: Backend selection in progress
- loading: Model warming up (cold start)
- generating: Inference started
- streaming: Content chunks arriving
- done: Request complete
- error: Request failed
"""
import json
import time
import logging
from typing import AsyncGenerator, Optional, Dict, Any

import httpx

from models import StreamEvent, StreamStatus
from providers import ProviderSelection

logger = logging.getLogger(__name__)


def format_sse(data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


def format_sse_done() -> str:
    """Format SSE termination signal."""
    return "data: [DONE]\n\n"


def create_stream_event(
    status: StreamStatus,
    message: Optional[str] = None,
    **kwargs
) -> StreamEvent:
    """Create a StreamEvent with current timestamp."""
    return StreamEvent(
        status=status,
        message=message,
        timestamp=time.time(),
        **kwargs
    )


async def stream_chat_completion(
    selection: ProviderSelection,
    body: dict,
    timeout: float = 300.0,
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion with status events.
    
    Yields SSE-formatted events:
    1. routing - Backend selected
    2. loading - If model needs warmup (detected via slow response)
    3. streaming - Content chunks from backend
    4. done - Final completion with metadata
    
    Args:
        selection: Provider and model selection from router
        body: Request body for chat completions
        timeout: Request timeout in seconds
        
    Yields:
        SSE-formatted strings (data: {...}\n\n)
    """
    endpoint_url = f"{selection.provider.endpoint.rstrip('/')}/v1/chat/completions"
    
    yield format_sse(create_stream_event(
        status=StreamStatus.ROUTING,
        message=f"Routing to {selection.provider.name}",
        backend=selection.provider.id,
        provider_name=selection.provider.name,
        model=selection.model.id,
    ).model_dump())
    
    full_content = ""
    metadata: Dict[str, Any] = {}
    error_occurred = False
    error_message = None
    
    request_start = time.time()
    first_chunk_received = False
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            yield format_sse(create_stream_event(
                status=StreamStatus.LOADING,
                message=f"Connecting to {selection.provider.name}...",
                backend=selection.provider.id,
                provider_name=selection.provider.name,
                model=selection.model.id,
            ).model_dump())
            
            async with client.stream(
                "POST",
                endpoint_url,
                json=body,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_message = f"Backend error: {response.status_code} - {error_text.decode()}"
                    logger.error(error_message)
                    yield format_sse(create_stream_event(
                        status=StreamStatus.ERROR,
                        message="Backend request failed",
                        error_detail=error_message,
                        backend=selection.provider.id,
                    ).model_dump())
                    yield format_sse_done()
                    return
                
                async for chunk in response.aiter_bytes():
                    if not first_chunk_received:
                        first_chunk_received = True
                        time_to_first = time.time() - request_start
                        
                        if time_to_first > 5.0:
                            yield format_sse(create_stream_event(
                                status=StreamStatus.LOADING,
                                message=f"Model warming up on {selection.provider.name} (cold start)",
                                backend=selection.provider.id,
                                provider_name=selection.provider.name,
                                estimated_time=int(30 - time_to_first) if time_to_first < 30 else None,
                            ).model_dump())
                        
                        yield format_sse(create_stream_event(
                            status=StreamStatus.GENERATING,
                            message="Generating response...",
                            backend=selection.provider.id,
                            provider_name=selection.provider.name,
                            model=selection.model.id,
                        ).model_dump())
                    
                    chunk_str = chunk.decode('utf-8')
                    
                    for line in chunk_str.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                continue
                            
                            try:
                                chunk_data = json.loads(data_str)
                                
                                if chunk_data.get('id'):
                                    metadata['id'] = chunk_data['id']
                                if chunk_data.get('model'):
                                    metadata['model'] = chunk_data['model']
                                if chunk_data.get('usage'):
                                    metadata['usage'] = chunk_data['usage']
                                
                                choices = chunk_data.get('choices', [])
                                if choices:
                                    delta = choices[0].get('delta', {})
                                    content = delta.get('content', '')
                                    finish_reason = choices[0].get('finish_reason')
                                    
                                    if content:
                                        full_content += content
                                        yield format_sse(create_stream_event(
                                            status=StreamStatus.STREAMING,
                                            delta=content,
                                            backend=selection.provider.id,
                                        ).model_dump())
                                    
                                    if finish_reason:
                                        metadata['finish_reason'] = finish_reason
                                        
                            except json.JSONDecodeError:
                                logger.debug(f"Skipping non-JSON SSE data: {data_str[:100]}")
                                
    except httpx.TimeoutException:
        error_occurred = True
        error_message = "Request timed out"
        logger.error(f"Timeout calling {endpoint_url}")
        yield format_sse(create_stream_event(
            status=StreamStatus.ERROR,
            message="Request timed out",
            error_detail=f"Timeout after {timeout}s",
            backend=selection.provider.id,
        ).model_dump())
        
    except httpx.ConnectError as e:
        error_occurred = True
        error_message = f"Connection failed: {e}"
        logger.error(f"Connection error to {endpoint_url}: {e}")
        yield format_sse(create_stream_event(
            status=StreamStatus.ERROR,
            message="Failed to connect to backend",
            error_detail=str(e),
            backend=selection.provider.id,
        ).model_dump())
        
    except Exception as e:
        error_occurred = True
        error_message = str(e)
        logger.error(f"Stream error: {e}")
        yield format_sse(create_stream_event(
            status=StreamStatus.ERROR,
            message="Streaming error",
            error_detail=str(e),
            backend=selection.provider.id,
        ).model_dump())
    
    if not error_occurred and full_content:
        yield format_sse(create_stream_event(
            status=StreamStatus.DONE,
            message="Complete",
            content=full_content,
            model=metadata.get('model', selection.model.id),
            backend=selection.provider.id,
            provider_name=selection.provider.name,
            usage=metadata.get('usage'),
            finish_reason=metadata.get('finish_reason', 'stop'),
        ).model_dump())
    
    yield format_sse_done()


async def stream_chat_completion_passthrough(
    selection: ProviderSelection,
    body: dict,
    timeout: float = 300.0,
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion with direct passthrough (OpenAI SDK compatible).
    
    Forwards SSE events from backend directly without wrapping in status events.
    This maintains full OpenAI SDK compatibility.
    
    Args:
        selection: Provider and model selection from router
        body: Request body for chat completions
        timeout: Request timeout in seconds
        
    Yields:
        SSE-formatted strings exactly as received from backend
    """
    endpoint_url = f"{selection.provider.endpoint.rstrip('/')}/v1/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                endpoint_url,
                json=body,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_data = {
                        "error": {
                            "message": f"Backend error: {error_text.decode()}",
                            "type": "backend_error",
                            "code": response.status_code,
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                
                async for chunk in response.aiter_bytes():
                    yield chunk.decode('utf-8')
                    
    except httpx.TimeoutException:
        error_data = {
            "error": {
                "message": f"Request timed out after {timeout}s",
                "type": "timeout_error",
                "code": 504,
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"
        
    except httpx.ConnectError as e:
        error_data = {
            "error": {
                "message": f"Failed to connect to backend: {e}",
                "type": "connection_error", 
                "code": 503,
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Passthrough stream error: {e}")
        error_data = {
            "error": {
                "message": f"Streaming error: {e}",
                "type": "stream_error",
                "code": 500,
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"


class StreamAccumulator:
    """Accumulates stream data for post-processing (memory logging, metrics)."""
    
    def __init__(self):
        self.full_content = ""
        self.metadata: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.chunks: list = []
        
    def add_chunk(self, event: dict):
        """Process a stream event and accumulate data."""
        status = event.get('status')
        
        if status == 'streaming':
            delta = event.get('delta', '')
            if delta:
                self.full_content += delta
                self.chunks.append(delta)
                
        elif status == 'done':
            if event.get('content'):
                self.full_content = event['content']
            if event.get('model'):
                self.metadata['model'] = event['model']
            if event.get('usage'):
                self.metadata['usage'] = event['usage']
            if event.get('finish_reason'):
                self.metadata['finish_reason'] = event['finish_reason']
            if event.get('backend'):
                self.metadata['backend'] = event['backend']
                
        elif status == 'error':
            self.error = event.get('error_detail') or event.get('message')
            
    def to_response_data(self, request_body: dict) -> dict:
        """Convert accumulated data to a response dict for logging."""
        return {
            'id': self.metadata.get('id', 'stream-unknown'),
            'object': 'chat.completion',
            'model': self.metadata.get('model', request_body.get('model', 'auto')),
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': self.full_content,
                },
                'finish_reason': self.metadata.get('finish_reason', 'stop'),
            }],
            'usage': self.metadata.get('usage', {}),
            'provider': self.metadata.get('backend'),
        }
