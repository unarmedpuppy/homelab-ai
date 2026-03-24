# ADR: Remove mirror-llama-cpp CI Job

- **Date:** 2026-03-23
- **Status:** Accepted
- **Repos/Services affected:** `.gitea/workflows/build.yml`

## Context

The `mirror-llama-cpp` job in the build workflow pulled `ghcr.io/ggerganov/llama.cpp:server-cuda`
and pushed it to Harbor so the gaming PC's `llm-manager` could reference it as `LLAMA_IMAGE`.

The job was consistently failing immediately (after ~2s) due to a wrong secret name (`HARBOR_USER`
instead of `HARBOR_USERNAME`) and use of `docker/login-action@v3` (GitHub Marketplace) rather than
the plain `docker login` pattern used by all other jobs. Fix attempts in v1.9.6 and v1.10.83 did
not resolve the issue. The underlying failure was blocking diagnosis of other CI problems.

## Decision

Remove the `mirror-llama-cpp` job from the CI workflow entirely.

The image is only referenced in `docker-compose.gaming.yml` as `LLAMA_IMAGE` for the gaming PC.
It is not used by any server-side service. The llama.cpp runtime was added for GGUF model support
on the gaming PC but is not currently in active use — the gaming PC runs vLLM (AWQ) models.

If llama.cpp mirroring is needed in the future, it should be done as a standalone manual step or
a separate scheduled workflow, not as a gate on every homelab-ai release.

## Consequences

- CI builds and deploys cleanly on every tag push
- `harbor.server.unarmedpuppy.com/library/llama.cpp-server:cuda` will not be auto-updated
- Gaming PC GGUF workflows must mirror the image manually if needed:
  ```bash
  docker pull ghcr.io/ggerganov/llama.cpp:server-cuda
  docker tag ghcr.io/ggerganov/llama.cpp:server-cuda harbor.server.unarmedpuppy.com/library/llama.cpp-server:cuda
  docker push harbor.server.unarmedpuppy.com/library/llama.cpp-server:cuda
  ```
