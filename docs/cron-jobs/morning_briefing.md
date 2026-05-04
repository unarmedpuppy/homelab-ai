# Morning Briefing

**Job ID:** `b2f59efd652d`

## Description

Daily morning market briefing that fetches real-time market data from TradingView via MCP protocol and posts a formatted briefing to the Mattermost Coins channel. Runs every weekday at 8:30 AM CST.

## Schedule

Runs at 8:30 AM CST (13:30 UTC) Monday through Friday.

## What It Does

1. Connects to the running TradingView Desktop instance via Chrome DevTools Protocol (CDP) on port 9222
2. Uses the tradingview-mcp-oak MCP server to fetch real-time data:
   - **Indices:** SPY, QQQ, IWM prices
   - **Macro:** VIX, US10Y (10-year Treasury yield), Gold, TLT (20+ year Treasury)
   - **Crypto:** BTC (Bitcoin)
3. Fetches SPY daily technical indicators:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands
   - EMA (Exponential Moving Average)
   - VWAP (Volume Weighted Average Price)
4. Formats the data into a readable briefing with:
   - Timestamp (CST)
   - Price changes with arrows (▲ for up, ▼ for down, ➡ for flat)
   - VIX volatility level classification
   - SPY technical indicators
5. Posts the formatted briefing to Mattermost Coins channel

## Prerequisites

- **TradingView Desktop** must be running with `--remote-debugging-port=9222`
- **tradingview-mcp-oak** server must be accessible at `~/workspace/tradingview-mcp-oak/`
- **Mattermost bot token** configured in `~/.grove/agents/oak/.env`

## Configuration

- **MCP Server:** `~/workspace/tradingview-mcp-oak/src/server.js`
- **Briefing Script:** `~/workspace/tradingview-mcp-oak/scripts/briefing.js`
- **Mattermost Channel:** Coins channel (ID: s9mwic8setrxbbqy9ykjff4gaw)
- **Env File:** `~/.grove/agents/oak/.env`

## Market Data Sources

| Instrument | Symbol | Group |
|------------|--------|-------|
| SPY | AMEX:SPY | Indices |
| QQQ | NASDAQ:QQQ | Indices |
| IWM | AMEX:IWM | Indices |
| VIX | TVC:VIX | Macro |
| US10Y | TVC:US10Y | Macro |
| Gold | CAPITALCOM:GOLD | Macro |
| TLT | NASDAQ:TLT | Macro |
| BTC | COINBASE:BTCUSD | Crypto |

## Output Format

```
📊 **Morning Briefing** — Mon, May 4 2026 8:30 AM CST

**Indices**
- SPY: $523.45 (+1.23%) ▲
- QQQ: $467.89 (+0.87%) ▲
- IWM: $234.56 (-0.45%) ▼

**Macro**
- VIX: 14.5 — calm
- US10Y: 4.32%
- Gold: $2,345.67
- TLT: $92.34
- BTC: $67,890.12

**SPY Technicals** (daily)
- Relative Strength Index: 65.4 — overbought territory
- MACD: -0.23 | Signal: -0.15 | Histogram: -0.08 — bearish crossover
- Bollinger Bands: Upper $530.12 | Middle $523.45 | Lower $516.78
- EMA 20: $521.34 | EMA 50: $518.92 | EMA 200: $510.45
- VWAP: $522.78
```

## Monitoring

- **Last Run:** Check the dashboard for the most recent execution time
- **Status:** Green = success, Red = failure
- **Logs:** Review Mattermost Coins channel for the posted briefing
- **Errors:** If TradingView is not running, the script handles gracefully and sends a fallback briefing

## Troubleshooting

### "Briefing failed" message
- Verify TradingView Desktop is running with CDP enabled
- Check if port 9222 is accessible
- Ensure tradingview-mcp-oak is installed

### Missing data for certain instruments
- Some symbols may not be available on TradingView
- The script gracefully handles null responses
- Technical indicators only populate if CDP connection succeeds

### VIX level classification
- **Calm:** VIX < 15
- **Low:** VIX 15-20
- **Elevated:** VIX 20-30
- **High:** VIX > 30

## Related

- [TradingView MCP Server](https://github.com/unarmedpuppy/tradingview-mcp)
- [Mattermost Integration](../docs/mattermost-integration.md)
- [Morning Briefing Skill](../skills/morning-briefing.md)
