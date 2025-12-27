# Plan: Multimodal Inference Support

**Status**: Planning
**Beads Task**: `home-server-6lb`

## Goal
Add support for image generation/editing models alongside existing text generation models in the local AI system.

## Current State

### What Works
- **Text generation models** via vLLM:
  - `llama3-8b` - Text generation
  - `qwen2.5-14b-awq` - Text generation  
  - `deepseek-coder` - Text generation
- **Architecture**: Windows PC runs vLLM containers, server proxy forwards requests
- **UI**: Terminal-style text chat interface

### What Doesn't Work
- **Image models** (e.g., `qwen-image-edit`):
  - vLLM doesn't support image generation/editing models
  - Error: `ValueError: No supported config format found`
  - Different architecture required (diffusion/vision transformers)

## Architecture Options

### Option 1: Separate Inference Engine for Image Models (Recommended)

**Approach**: Run image models in separate containers using a different inference engine (e.g., Diffusers, custom inference server)

**Pros**:
- Clean separation of concerns
- Can use best tool for each task (vLLM for text, Diffusers for images)
- Easier to maintain and debug
- Can scale independently

**Cons**:
- More complex setup
- Need to manage two different inference engines
- More containers to manage

**Implementation**:
1. Create new container type for image models (not vLLM)
2. Use HuggingFace Diffusers or custom inference server
3. Extend manager to handle both vLLM and image model containers
4. Route requests based on model type

### Option 2: Unified Multimodal Manager

**Approach**: Create a unified manager that can handle both text and image models

**Pros**:
- Single interface for all models
- Consistent API

**Cons**:
- More complex manager code
- Harder to maintain
- Still need different inference engines under the hood

## Recommended Approach: Option 1

### Phase 1: Research & Setup Image Inference Engine

**Tasks**:
1. **Research inference engines**:
   - HuggingFace Diffusers (for diffusion models)
   - Custom FastAPI server with transformers
   - Check if Qwen Image Edit has official inference server
   - Evaluate performance and GPU requirements

2. **Choose inference engine**:
   - Document decision and rationale
   - Test with Qwen Image Edit model
   - Verify GPU compatibility

3. **Create image model container setup**:
   - New setup script or extend existing `setup.sh`
   - Dockerfile for image inference engine
   - Test container creation and model loading

**Deliverables**:
- Research document comparing inference engines
- Working image model container (proof of concept)
- Updated setup documentation

### Phase 2: Extend Manager to Support Both Types

**Tasks**:
1. **Update manager architecture**:
   - Add model type detection (text vs image)
   - Extend `models.json` to include model type
   - Update manager to handle both container types

2. **Update models.json format**:
   ```json
   {
       "llama3-8b": {
           "container": "vllm-llama3-8b",
           "port": 8001,
           "type": "text"
       },
       "qwen-image-edit": {
           "container": "qwen-image-server",
           "port": 8005,
           "type": "image"
       }
   }
   ```

3. **Update manager.py**:
   - Add model type checking
   - Route text requests to vLLM containers
   - Route image requests to image inference containers
   - Handle different health check endpoints

4. **Update container management**:
   - Different start/stop logic for image models
   - Different readiness checks
   - Unified interface for both types

**Deliverables**:
- Updated `models.json` with type field
- Updated `manager/manager.py` with dual-type support
- Tests for both model types

### Phase 3: Update Server Proxy

**Tasks**:
1. **Add image generation endpoint**:
   - Ensure `/v1/images/generations` properly routes to image models
   - Handle image model-specific request formats
   - Process image responses (base64, URLs, etc.)

2. **Update error handling**:
   - Better error messages for unsupported operations
   - Model type validation

3. **Add model type detection**:
   - Check model type before routing
   - Validate requests match model capabilities

**Deliverables**:
- Updated `app/main.py` with image model routing
- Image generation endpoint working
- Error handling improvements

### Phase 4: Update UI for Image Support

**Tasks**:
1. **Add image display capability**:
   - Extend terminal UI to display images
   - Support base64 image data
   - Support image URLs
   - Retro-styled image display (fits terminal aesthetic)

2. **Update request handling**:
   - Detect when using image model
   - Use `/v1/images/generations` endpoint for image models
   - Use `/v1/chat/completions` for text models
   - Handle both text and image responses

3. **Add image input support** (optional, future):
   - Image upload capability
   - Multimodal prompts (text + image)
   - Image editing workflow

**Deliverables**:
- Updated `app/static/index.html` with image display
- Image generation working in UI
- Image responses displayed in terminal

### Phase 5: Testing & Documentation

**Tasks**:
1. **End-to-end testing**:
   - Test text models still work
   - Test image model loading and generation
   - Test error cases
   - Test model switching

2. **Update documentation**:
   - Update `local-ai/README.md`
   - Update `apps/local-ai-app/README.md`
   - Update `local-ai-agent.md` persona
   - Add troubleshooting for image models

3. **Performance testing**:
   - Measure image generation latency
   - Test GPU memory usage
   - Optimize if needed

**Deliverables**:
- Test suite
- Updated documentation
- Performance benchmarks

## Technical Considerations

### Inference Engine Options

1. **HuggingFace Diffusers**:
   - Pros: Well-supported, many models, good documentation
   - Cons: May need custom API wrapper
   - Best for: Diffusion-based image models

2. **Custom FastAPI Server**:
   - Pros: Full control, can match vLLM API format
   - Cons: More development work
   - Best for: Custom requirements

3. **Model-Specific Inference Servers**:
   - Pros: Optimized for specific models
   - Cons: May not exist for all models
   - Best for: Official model support

### Model Container Architecture

```
Image Model Container:
- Base: Python + PyTorch + Diffusers (or custom)
- FastAPI server with OpenAI-compatible endpoints
- Model loading and inference logic
- GPU support (CUDA)
- Health check endpoint
- Port: 8005+ (separate from vLLM ports)
```

### Manager Updates

```python
# Pseudo-code for manager updates
def get_model_type(model_name):
    return model_states[model_name]["config"]["type"]

async def start_model_container(model_name):
    model_type = get_model_type(model_name)
    if model_type == "text":
        # Use existing vLLM logic
    elif model_type == "image":
        # Use image model logic
        # Different readiness check
        # Different container management
```

### API Compatibility

**Goal**: Maintain OpenAI-compatible API for both types

**Text Models**:
- `/v1/chat/completions` - Chat completions
- `/v1/completions` - Text completions

**Image Models**:
- `/v1/images/generations` - Image generation
- `/v1/images/edits` - Image editing (if supported)

**Unified Endpoints** (via proxy):
- All endpoints available
- Proxy routes to appropriate backend based on model type

## Implementation Steps

### Step 1: Proof of Concept (Week 1)
- [ ] Research and choose inference engine for Qwen Image Edit
- [ ] Create working image model container
- [ ] Test image generation locally
- [ ] Document findings

### Step 2: Manager Extension (Week 2)
- [ ] Update `models.json` format with type field
- [ ] Extend manager to detect and route by type
- [ ] Add image model container management
- [ ] Test with both text and image models

### Step 3: Server Proxy Updates (Week 2-3)
- [ ] Update proxy to handle image endpoints
- [ ] Add model type validation
- [ ] Test routing logic

### Step 4: UI Updates (Week 3-4)
- [ ] Add image display to terminal UI
- [ ] Update request handling for image models
- [ ] Test image generation in UI
- [ ] Polish image display styling

### Step 5: Testing & Documentation (Week 4)
- [ ] End-to-end testing
- [ ] Update all documentation
- [ ] Performance testing
- [ ] User acceptance testing

## Risks & Mitigations

### Risk 1: Image inference engine doesn't work well
**Mitigation**: Research multiple options, test thoroughly before committing

### Risk 2: GPU memory constraints
**Mitigation**: Test memory usage, consider model quantization, implement smart loading

### Risk 3: API incompatibilities
**Mitigation**: Create abstraction layer, maintain OpenAI compatibility

### Risk 4: UI complexity
**Mitigation**: Keep terminal aesthetic, simple image display, optional advanced features

## Success Criteria

1. ✅ Image models can be loaded and run alongside text models
2. ✅ Manager can handle both model types seamlessly
3. ✅ UI can display generated images
4. ✅ Text models continue to work without issues
5. ✅ Documentation is complete and accurate
6. ✅ Performance is acceptable (< 30s for image generation)

## Future Enhancements

- Image editing (upload + edit)
- Multimodal chat (text + image input)
- Image-to-text (vision understanding)
- Batch image generation
- Image model fine-tuning support

## References

- vLLM documentation: https://docs.vllm.ai/
- HuggingFace Diffusers: https://huggingface.co/docs/diffusers/
- Qwen Image models: https://qwenlm.github.io/blog/qwen-imagen/
- OpenAI API compatibility: https://platform.openai.com/docs/api-reference

---

**Status**: Planning
**Created**: 2025-01-17
**Owner**: local-ai-agent

