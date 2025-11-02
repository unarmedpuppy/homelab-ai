# IBKR + UnusualWhales + SMA Bot

## Overview
- Live trading via **Interactive Brokers** (`ib_insync`).
- Entries: price within **0.5%** of **SMA20** or **SMA200** _and_ refinement checks.
- Exits: **+20%** take‑profit **or** extension from **SMA20** by **3%**.
- Refinements (optional):
  1. **Volume confirmation** – OBV slope > 0 near the tag.
  2. **Higher timeframe alignment** – (left as extension in API version).
  3. **Options flow delta** – 3‑day MA of call premium rising (placeholder).
  4. **Entry timing** – tag SMA20, hammer/engulfing + **RSI 45–55**, enter on confirmation.
  5. **Stops/Targets** – stop under SMA20 or prior swing; T1 prior high/2R; T2 trail 10‑EMA/ATR(5) (extension hook).

- **Backtesting**: event-driven engine over OHLC CSV.
- **Screener** (defaults per your image): Trailing P/E<25, Forward P/E<15, D/E<35%, EPS>15%, PEG<1.2, MktCap>$5B.
- **Web UI** (FastAPI) + **SQLite** DB for running & storing screeners/backtests.
- **Dockerized** with `docker-compose`.

> **Note:** Unusual Whales API calls are placeholders; add real endpoints if you have access.

## Files
- `ibkr_uw_sma_bot.py` – bot, backtester, screener, and FastAPI app.
- `Dockerfile`, `requirements.txt`, `docker-compose.yml`.
- Data persisted at `./data/bot.db` (SQLite) by default.

## Quickstart (Docker)
```bash
docker compose up --build -d
open http://localhost:8000
```

## Local CLI
```bash
pip install -r requirements.txt

# Screener
python ibkr_uw_sma_bot.py screen --universe "AAPL,MSFT,NVDA"

# Backtest from CSV
python ibkr_uw_sma_bot.py backtest --csv ./AAPL_30m.csv --symbol AAPL   --entry-sma-threshold 0.005 --exit-sma20-extension 0.03 --tp 0.20 --qty 10

# Live loop (requires IB TWS/Gateway + market data perms)
# First, test your IBKR connection:
python scripts/test_ibkr_connection.py

# Then run live trading:
export IBKR_HOST=127.0.0.1 IBKR_PORT=7497 IBKR_CLIENT_ID=9 UW_API_KEY=...
python ibkr_uw_sma_bot.py live --symbol AAPL
```

## Environment
- `BOT_DB_URL` – SQLAlchemy URL (default `sqlite:///./bot.db` in container => `/data/bot.db`).
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID` – IB connection (see [IBKR Connection Guide](docs/IBKR_CONNECTION.md)).
- `UW_API_KEY` – Unusual Whales key (optional).

## IBKR Connection Setup

Before using live trading, you need to set up the Interactive Brokers connection:

1. **Install TWS or IB Gateway** from Interactive Brokers
2. **Enable API connections** in TWS/Gateway settings
3. **Configure environment variables** (see `env.template`)
4. **Test the connection**:
   ```bash
   python scripts/test_ibkr_connection.py
   ```

For detailed setup instructions, see the [IBKR Connection Guide](docs/IBKR_CONNECTION.md).

## Constraints & Logic (as requested)
- **Entry** when price within `entry_sma_threshold` (default **0.5%**) of SMA20/200 AND:
  - OBV slope positive (volume confirmation).
  - RSI within **45–55**.
  - If `require_uw_bull`: `market_tide ≥ 0.15`, `flow_bullish_ratio ≥ 0.1`, and **flow delta MA(3) > 0**.
- **Exit** when:
  - `+20%` from entry (TP), **or**
  - `|price − SMA20| / SMA20 ≥ 3%` (extension), **or**
  - (extensions available) stop under SMA20/prior swing, 10‑EMA/ATR(5) trailing.
- **Screener default filters**: Trailing P/E<25; Forward P/E<15; D/E<0.35; EPS growth>0.15; PEG<1.2; MktCap>5B.
- **Backtest accounting**: bar close fills; equity MTM each bar; final force‑close at last bar.

## Extending
- Wire **UW** real endpoints and symbol‑level flow delta.
- Add **weekly/daily** HTF SMA checks in strategy/backtester.
- Add **slippage/fees**, partial fills, and ATR‑based position sizing.
- Button: “Backtest all passed” in UI; job queue for live trading.

## Safety
This is not investment advice. Paper trade first. Verify data licenses and broker compliance.
