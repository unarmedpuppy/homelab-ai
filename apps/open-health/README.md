# OpenHealth

**AI Health Assistant | Powered by Your Data**

OpenHealth helps you take charge of your health data. By leveraging AI and your personal health information, OpenHealth provides a private assistant that helps you better understand and manage your health.

## Features

- 📊 **Centralized Health Data Input:** Easily consolidate all your health data in one place
- 🛠️ **Smart Parsing:** Automatically parses your health data and generates structured data files
- 🤝 **Contextual Conversations:** Use the structured data as context for personalized interactions with GPT-powered AI
- 🔒 **Privacy-First:** Run completely locally for maximum privacy

## Supported Data Sources

- Blood Test Results
- Health Checkup Data
- Personal Physical Information
- Family History
- Symptoms

## Supported Language Models

- LLaMA (via Ollama)
- DeepSeek-V3
- GPT (OpenAI)
- Claude (Anthropic)
- Gemini (Google)

## Quick Start

### 1. Clone the Repository

```bash
cd apps/open-health
git clone https://github.com/OpenHealthForAll/open-health.git open-health-repo
```

### 2. Setup Environment

```bash
cp env.template .env
```

### 3. Generate Encryption Key

```bash
# Generate encryption key and add to .env
echo "ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)" >> .env
```

Or manually edit `.env` and add:
```
ENCRYPTION_KEY=<generated-key>
```

### 4. Configure Ollama (Optional)

If using Ollama for local LLM, edit `.env`:
- Mac: `OLLAMA_API_URL=http://docker.for.mac.localhost:11434`
- Windows/Linux: `OLLAMA_API_URL=http://host.docker.internal:11434`

### 5. Start the Application

```bash
docker compose up -d --build
```

### 6. Access OpenHealth

- **Local**: http://localhost:8095
- **HTTPS**: https://open-health.server.unarmedpuppy.com
- **Homepage**: Listed under "Health & Wellness" group

## Updating OpenHealth

To update to the latest version:

```bash
cd apps/open-health
cd open-health-repo
git pull origin main
cd ..
docker compose up -d --build
```

## Configuration

### Environment Variables

See `env.template` for all available configuration options.

**Required:**
- `ENCRYPTION_KEY` - Encryption key for data security (generate with `head -c 32 /dev/urandom | base64`)

**Optional:**
- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `OLLAMA_API_URL` - Ollama API endpoint for local LLM
- `NEXT_PUBLIC_APP_URL` - Public URL for the application
- `OPENAI_API_KEY` - OpenAI API key (if using GPT)
- `ANTHROPIC_API_KEY` - Anthropic API key (if using Claude)
- `GOOGLE_API_KEY` - Google API key (if using Gemini)

## Data Persistence

Data is stored in:
- `./data/` - Application data and database
- `./uploads/` - User uploaded files

## Architecture

OpenHealth consists of:
1. **Next.js Frontend** - Web interface (TypeScript)
2. **Data Parser** - Python server for parsing health documents (planned migration to TypeScript)
3. **LLM Integration** - Supports multiple AI models (local and cloud)

## Troubleshooting

### Port Already in Use

If port 8095 is already in use, change it in `docker-compose.yml`:
```yaml
ports:
  - "8096:3000"  # Change 8095 to your preferred port
```

### Ollama Connection Issues

If using Ollama in Docker:
- Ensure Ollama container is running
- Use `host.docker.internal` for Docker-to-Docker communication
- Check firewall settings

### Database Issues

If using SQLite (default):
- Ensure `./data` directory is writable
- Check disk space

## Resources

- **GitHub**: https://github.com/OpenHealthForAll/open-health
- **Website**: https://www.open-health.me
- **Documentation**: See repository README

## License

AGPL-3.0

