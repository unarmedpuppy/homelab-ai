# Testing Guide for Multimodal Inference Support

## Overview

This document outlines testing procedures for the multimodal inference support system, which handles both text generation (vLLM) and image generation (Diffusers) models.

## Test Environment Setup

### Prerequisites
- Windows PC with Docker Desktop and GPU support
- Server with `local-ai-app` proxy service running
- Access to `https://local-ai.server.unarmedpuppy.com`

### Initial Setup
1. **Windows PC**: Ensure manager service is running
   ```powershell
   cd local-ai
   docker compose up -d
   ```

2. **Server**: Ensure proxy service is running
   ```bash
   cd apps/local-ai-app
   docker compose up -d
   ```

## Test Cases

### Phase 1: Text Models (Existing Functionality)

#### Test 1.1: Text Model Loading
- **Action**: Select a text model (e.g., `qwen2.5-14b-awq`)
- **Expected**: Model container starts, becomes ready
- **Verify**: 
  - Manager health check shows model as running
  - First request triggers container start
  - Response time acceptable (< 30s for first request)

#### Test 1.2: Text Generation
- **Action**: Send text prompt to text model
- **Expected**: Text response generated
- **Verify**:
  - Response is coherent and relevant
  - No errors in logs
  - Conversation history maintained

#### Test 1.3: Model Switching
- **Action**: Switch between different text models
- **Expected**: Previous model stops, new model starts
- **Verify**:
  - Old model container stops after idle timeout
  - New model starts correctly
  - No conflicts or errors

### Phase 2: Image Models (New Functionality)

#### Test 2.1: Image Model Detection
- **Action**: Select image model (`qwen-image-edit`)
- **Expected**: UI shows note that it's an image model
- **Verify**:
  - `/model qwen-image-edit` command works
  - System message indicates image model selected

#### Test 2.2: Image Model Loading
- **Action**: Send image generation request
- **Expected**: Image model container starts
- **Verify**:
  - Container `qwen-image-server` starts
  - Health check endpoint responds
  - Loading progress shown in UI

#### Test 2.3: Image Generation
- **Action**: Generate image with prompt (e.g., "a duck jumping over a puddle")
- **Expected**: Image generated and displayed
- **Verify**:
  - Image appears in terminal UI
  - Image is properly formatted (base64 or URL)
  - Image quality acceptable
  - No errors in response

#### Test 2.4: Image Model Endpoint Routing
- **Action**: Use `/v1/images/generations` endpoint
- **Expected**: Request routed to image model
- **Verify**:
  - Proxy correctly routes to image endpoint
  - Manager routes to image container
  - Response format is correct

### Phase 3: Error Handling

#### Test 3.1: Wrong Endpoint Usage
- **Action**: Try text chat with image model
- **Expected**: Error message indicating wrong endpoint
- **Verify**: Clear error message, no crashes

#### Test 3.2: Wrong Endpoint Usage (Reverse)
- **Action**: Try image generation with text model
- **Expected**: Error message indicating wrong endpoint
- **Verify**: Clear error message, no crashes

#### Test 3.3: Model Loading Timeout
- **Action**: Request model that takes too long to load
- **Expected**: Timeout error with helpful message
- **Verify**: Error message indicates model is loading

#### Test 3.4: Container Not Found
- **Action**: Request model with missing container
- **Expected**: 404 error with clear message
- **Verify**: Error indicates container not found

### Phase 4: Integration Tests

#### Test 4.1: Mixed Usage
- **Action**: Switch between text and image models
- **Expected**: Both work correctly
- **Verify**:
  - Text model generates text
  - Image model generates images
  - No conflicts or errors

#### Test 4.2: Concurrent Requests
- **Action**: Send multiple requests to different models
- **Expected**: All requests handled correctly
- **Verify**: No race conditions, proper locking

#### Test 4.3: Idle Timeout
- **Action**: Wait 10+ minutes without using model
- **Expected**: Model container stops
- **Verify**: Container stops, restarts on next request

### Phase 5: UI Tests

#### Test 5.1: Image Display
- **Action**: Generate image
- **Expected**: Image displayed in terminal UI
- **Verify**:
  - Image visible and properly sized
  - Retro terminal styling applied
  - Image doesn't break layout

#### Test 5.2: Model Selection UI
- **Action**: Use `/model` and `/models` commands
- **Expected**: Commands work correctly
- **Verify**:
  - Image models listed separately
  - Model selection works
  - Notes shown for image models

#### Test 5.3: Error Display
- **Action**: Trigger various errors
- **Expected**: Errors displayed clearly
- **Verify**: Error messages are helpful and visible

## Performance Benchmarks

### Text Models
- **First request**: < 60s (includes model loading)
- **Subsequent requests**: < 5s
- **Model switching**: < 30s

### Image Models
- **First request**: < 120s (includes model loading)
- **Subsequent requests**: < 30s
- **Image generation**: < 60s per image

## Known Issues

### Current Limitations
1. **Image input support**: Not yet implemented (optional task)
2. **Image editing**: Basic support only
3. **Model progress**: Estimated, not exact

### Future Enhancements
- Exact model loading progress
- Image upload capability
- Multimodal prompts (text + image)
- Batch image generation

## Troubleshooting

### Image Model Not Loading
1. Check container exists: `docker ps -a | grep qwen-image`
2. Check container logs: `docker logs qwen-image-server`
3. Verify GPU available: `nvidia-smi`
4. Check manager logs: `docker logs vllm-manager`

### Image Not Displaying
1. Check browser console for errors
2. Verify response format (base64 or URL)
3. Check network tab for API response
4. Verify image data is valid base64

### Wrong Endpoint Errors
1. Verify model type in `models.json`
2. Check manager routing logic
3. Verify proxy endpoint detection

## Test Results Template

```
Date: [DATE]
Tester: [NAME]
Environment: [Windows/Server versions]

Phase 1 - Text Models:
- [ ] Test 1.1: Pass/Fail
- [ ] Test 1.2: Pass/Fail
- [ ] Test 1.3: Pass/Fail

Phase 2 - Image Models:
- [ ] Test 2.1: Pass/Fail
- [ ] Test 2.2: Pass/Fail
- [ ] Test 2.3: Pass/Fail
- [ ] Test 2.4: Pass/Fail

Phase 3 - Error Handling:
- [ ] Test 3.1: Pass/Fail
- [ ] Test 3.2: Pass/Fail
- [ ] Test 3.3: Pass/Fail
- [ ] Test 3.4: Pass/Fail

Phase 4 - Integration:
- [ ] Test 4.1: Pass/Fail
- [ ] Test 4.2: Pass/Fail
- [ ] Test 4.3: Pass/Fail

Phase 5 - UI:
- [ ] Test 5.1: Pass/Fail
- [ ] Test 5.2: Pass/Fail
- [ ] Test 5.3: Pass/Fail

Issues Found:
- [List any issues]

Notes:
[Additional notes]
```

