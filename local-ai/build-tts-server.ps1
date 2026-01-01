# Build TTS Inference Server Docker image
# Run from local-ai directory: .\build-tts-server.ps1

Write-Host "Building TTS Inference Server Docker image..." -ForegroundColor Cyan

# Build the image
docker build -t tts-inference-server:latest ./tts-inference-server

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "`nNext steps:"
    Write-Host "1. Create the container (manager will start it on-demand):"
    Write-Host "   docker create --name chatterbox-tts --gpus all -v `${PWD}/voices:/app/voices -v `${PWD}/cache:/root/.cache/huggingface --network my-network tts-inference-server:latest"
    Write-Host ""
    Write-Host "2. Test manually:"
    Write-Host "   docker start chatterbox-tts"
    Write-Host "   curl http://localhost:8006/health"
    Write-Host ""
    Write-Host "3. Or let the manager handle it - just send a request to:"
    Write-Host "   POST http://localhost:8000/v1/audio/speech"
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
    exit 1
}
