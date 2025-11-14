"""Evaluation Framework Tools for MCP Server

Provides tools for evaluating agent performance, quality, and effectiveness.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging

# Try to import evaluation modules
try:
    from agents.evaluation.engine import EvaluationEngine
    from agents.evaluation.metrics import AgentMetrics
    EVALUATION_AVAILABLE = True
except ImportError as e:
    EVALUATION_AVAILABLE = False
    print(f"⚠️  Warning: Evaluation Framework modules not available: {e}")


def register_evaluation_tools(server: Server):
    """Register evaluation framework MCP tools."""
    
    if not EVALUATION_AVAILABLE:
        return
    
    engine = EvaluationEngine()
    
    @server.tool()
    @with_automatic_logging()
    async def evaluate_agent_task(
        agent_id: str,
        task_id: str,
        start_time: str,
        end_time: str,
        tool_calls: str,
        success: bool,
        quality_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate an agent task.
        
        Args:
            agent_id: ID of agent that completed task
            task_id: Task ID
            start_time: Task start time (ISO format)
            end_time: Task end time (ISO format)
            tool_calls: JSON string with list of tool calls
            success: Whether task was successful
            quality_score: Optional quality score from Critiquing Agent
        
        Returns:
            Evaluation report with scores and metrics
        """
        try:
            tool_calls_list = json.loads(tool_calls) if isinstance(tool_calls, str) else tool_calls
            
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            
            metrics = engine.evaluate_agent_task(
                agent_id=agent_id,
                task_id=task_id,
                start_time=start,
                end_time=end,
                tool_calls=tool_calls_list,
                output=None,  # Output not needed for basic evaluation
                success=success,
                quality_score=quality_score
            )
            
            report = engine.generate_evaluation_report(metrics)
            
            return {
                "status": "success",
                "report": report
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in tool_calls parameter"
            }
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Invalid datetime format: {e}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def get_agent_performance(
        agent_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Args:
            agent_id: ID of agent
            limit: Maximum number of metrics to return
        
        Returns:
            Agent performance summary
        """
        try:
            # This would query stored metrics
            # For now, return placeholder structure
            return {
                "status": "success",
                "agent_id": agent_id,
                "metrics": [],
                "message": "Metrics storage not yet implemented - use evaluate_agent_task for evaluation"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

