---
name: deploy-polymarket-bot
description: Safe deployment of Polymarket trading bot with active trade protection
when_to_use: When deploying changes to the polymarket-bot application
script: scripts/deploy-polymarket-bot.sh
---

# Deploy Polymarket Bot

Safe deployment workflow for the Polymarket arbitrage trading bot that prevents interrupting active trades.

## Why This Matters

The bot executes real-money arbitrage trades on Polymarket. If the container is restarted while a trade is active (awaiting market resolution), we could:

1. Lose visibility into pending trades
2. Miss resolution events
3. Leave positions unmonitored

The pre-deployment check ensures we only deploy when it's safe.

## Quick Deploy

```bash
# Safe deploy (checks for active trades first)
./scripts/deploy-polymarket-bot.sh

# Force deploy (DANGEROUS - skips safety check)
./scripts/deploy-polymarket-bot.sh --force
```

## What the Script Does

1. **Pre-check**: Runs `check_active_trades.py` in the container
   - Queries the database for unresolved real trades
   - Checks if markets have ended (safe to deploy)
   - Blocks deployment if active trades exist

2. **Deploy**: Standard git pull + docker compose rebuild

3. **Verify**: Shows startup logs to confirm success

## Manual Pre-Check

You can run the active trade check independently:

```bash
# Via SSH
scripts/connect-server.sh "docker exec polymarket-bot python3 /app/scripts/check_active_trades.py"

# Exit codes:
#   0 = Safe to deploy (no active trades)
#   1 = NOT safe (active trades exist)
#   2 = Error checking
```

## When to Force Deploy

Only use `--force` when:

- The bot is crashed/hung and needs restart
- You're certain any active trades are already lost
- Emergency security fix is needed
- User explicitly approves the risk

## Trade Lifecycle

```
Trade Executed → status='pending' → Market Resolves → status='won'/'lost'
                     ↑                                      ↓
              ⚠️ DANGER ZONE                          Safe to deploy
```

## Troubleshooting

### "Container may not be running"

The pre-check failed because the bot isn't running. This is safe to deploy:

```bash
./scripts/deploy-polymarket-bot.sh  # Will proceed automatically
```

### Stuck in "not safe" state

If trades are stuck as pending after market resolution:

```bash
# Check database state
scripts/connect-server.sh "docker exec polymarket-bot python3 -c \"
import asyncio
import aiosqlite
async def check():
    async with aiosqlite.connect('/app/data/gabagool.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT id, asset, status, market_end_time FROM trades WHERE dry_run=0 ORDER BY created_at DESC LIMIT 5') as cur:
            for row in await cur.fetchall():
                print(dict(row))
asyncio.run(check())
\""
```

### Emergency restart

If you must restart regardless:

```bash
./scripts/deploy-polymarket-bot.sh --force
```

## Related Files

- `apps/polymarket-bot/scripts/check_active_trades.py` - Pre-deployment check script
- `apps/polymarket-bot/src/persistence.py` - Database schema
- `apps/polymarket-bot/src/strategies/gabagool.py` - Trading logic
