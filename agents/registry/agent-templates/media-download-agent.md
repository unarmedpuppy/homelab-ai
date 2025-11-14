# Agent Template: Media Download Specialist

Template for creating media download specialized agents.

## Specialization

Sonarr, Radarr, and download client management (NZBGet, qBittorrent).

## Capabilities

### Skills
- `troubleshoot-stuck-downloads` - Download queue diagnostics and fixes

### MCP Tools
- All Sonarr tools (5 tools)
- All Radarr tools (6 tools)
- Download client tools (2 tools)

### Domain Knowledge
- Sonarr configuration and troubleshooting
- Radarr configuration and troubleshooting
- NZBGet download client
- qBittorrent download client
- Media organization and file management
- Download queue management
- Root folder configuration

## Typical Tasks

- Fix stuck downloads in Sonarr/Radarr
- Configure download clients
- Manage root folders
- Troubleshoot media import issues
- Clear download queues
- Diagnose download client connectivity

## Prompt

**Use**: `agents/prompts/base.md` (general agent prompt)

The base prompt provides:
- Discovery workflow
- Universal systems (memory, monitoring, communication, task coordination)
- How to work (principles, best practices)

**Note**: If a media-download-specific prompt is created in the future (`agents/prompts/media-download.md`), use that instead.

## Usage

Copy this template when creating a media download specialized agent.

When creating the agent definition, reference:
- **Template**: `media-download-agent.md` (this file)
- **Prompt**: `agents/prompts/base.md`

---

**Template Version**: 1.1
**Last Updated**: 2025-01-13

