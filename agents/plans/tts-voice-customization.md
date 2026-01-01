# TTS Voice Customization Plan

## Overview

Enable permanent voice customization for Chatterbox Turbo TTS running on the Gaming PC. Currently the system only supports the built-in default voice or per-request voice cloning. This plan adds:

1. Infrastructure for storing custom voice files
2. Ability to set a permanent default voice
3. Documentation for voice cloning workflow

## Current State

- TTS server runs in `chatterbox-tts` container on Gaming PC
- Voice files mount point: `local-ai/voices:/app/voices`
- Server supports `DEFAULT_VOICE_PATH` env var (not currently used)
- No voices directory exists yet

## Implementation Phases

### Phase 1: Infrastructure Setup

**Tasks:**
- [ ] Create `local-ai/voices/` directory with .gitkeep
- [ ] Add voices/ to .gitignore (voice files are personal/large)
- [ ] Update `setup-tts-container.sh` to support `DEFAULT_VOICE_PATH` env var

### Phase 2: Documentation

**Tasks:**
- [ ] Update `agents/skills/test-tts/SKILL.md` with permanent voice customization section
- [ ] Add voice cloning tips to TTS README

### Phase 3: Testing (Manual - on Gaming PC)

**Tasks:**
- [ ] Test adding a custom voice file
- [ ] Test setting DEFAULT_VOICE_PATH
- [ ] Verify voice persists across container restarts

## Technical Details

### Environment Variable

```bash
# In setup-tts-container.sh or docker create command
-e DEFAULT_VOICE_PATH="/app/voices/my-voice.wav"
```

### Voice File Requirements

- Format: WAV (16-bit PCM recommended)
- Duration: 10-15 seconds of clear speech
- Quality: High quality, minimal background noise
- Content: Natural conversational speech

### Directory Structure

```
local-ai/
├── voices/           # Custom voice files (gitignored)
│   ├── .gitkeep      # Ensure directory exists
│   └── *.wav         # User's voice samples
├── setup-tts-container.sh  # Updated with DEFAULT_VOICE_PATH support
└── ...
```

## Success Criteria

1. `local-ai/voices/` directory exists and is gitignored
2. `setup-tts-container.sh` supports optional `DEFAULT_VOICE_PATH`
3. Documentation updated with permanent voice setup instructions
4. User can add a voice file and have it used as default

## Estimated Effort

- Phase 1: 15 minutes
- Phase 2: 15 minutes
- Phase 3: Manual testing by user

Total: ~30 minutes implementation + user testing
