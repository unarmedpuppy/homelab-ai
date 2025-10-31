# TradingAgents (Dockerized)

This app runs the open-source TradingAgents multi-agent LLM trading framework inside Docker on your home server.

- Upstream repo: `https://github.com/TauricResearch/TradingAgents`
- Paper: `https://arxiv.org/abs/2412.20138`

## What it does
TradingAgents coordinates multiple role-based LLM agents (fundamental, sentiment, news, technical researchers; trader; risk/PM) to debate and propose a trading decision for a ticker and date.

## Requirements
- OpenAI API key (for agent LLMs)
- Alpha Vantage API key (for fundamentals and news by default)

## Setup
1) Create env and data dirs, set keys

```bash
mkdir -p env data
cp env.template env/.env
# edit env/.env and set OPENAI_API_KEY, ALPHA_VANTAGE_API_KEY
```

2) Build the image

```bash
docker compose build
```

## Usage

> Compose services use profiles. Running `docker compose up -d` with no profile will select no service. Use a profile or service name as below.

### Interactive CLI (TUI)
Runs the official CLI with an interactive interface.

```bash
# using profile
docker compose --profile cli up
# or one-off
docker compose run --rm --profile cli tradingagents
# or by service name
docker compose up tradingagents
```

### One-off batch run
Runs a single decision for a ticker/date and prints the result. Env values are read from `env/.env` (via env_file).

```bash
# using values from env/.env
docker compose --profile batch run --rm tradingagents-batch

# override inline (takes precedence over env/.env)
TICKER=AAPL DATE=2024-06-15 docker compose --profile batch run --rm tradingagents-batch
```

## Notes
- Env vars are provided to containers via `env_file: ./env/.env`; no need to bind-mount `.env`.
- Data vendor defaults follow upstream: yfinance for price/technical, Alpha Vantage for fundamentals & news. You can customize by wrapping the batch command to modify `DEFAULT_CONFIG`.
- The container mounts `./data` to persist caches under `/workspace/TradingAgents/.cache`.
- The CLI is interactive and requires TTY; compose sets `stdin_open` and `tty` accordingly.

## References
- Upstream repo: `https://github.com/TauricResearch/TradingAgents`
- Paper: `https://arxiv.org/abs/2412.20138`
