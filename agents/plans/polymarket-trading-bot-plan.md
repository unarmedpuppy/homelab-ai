# Polymarket Trading Bot Implementation Plan

**Created**: 2025-12-07
**Status**: Planning
**Goal**: Build a Polymarket trading bot with copy-trading capability

## Overview

This plan outlines the infrastructure and implementation steps for creating a Polymarket trading bot that can:
1. Connect to Polymarket's CLOB (Central Limit Order Book) API
2. Monitor target wallet positions for copy-trading
3. Execute trades programmatically
4. Track positions and performance

## Architecture

```
apps/polymarket-bot/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Python container
├── requirements.txt            # Dependencies
├── .env.template               # Environment variables template
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration management
│   ├── client/
│   │   ├── __init__.py
│   │   ├── polymarket.py       # Polymarket CLOB client wrapper
│   │   └── gamma.py            # Gamma API for market metadata
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py             # Base strategy class
│   │   └── copy_trading.py     # Copy trading strategy
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── wallet_tracker.py   # Track target wallet positions
│   │   └── position_manager.py # Manage our positions
│   ├── data/
│   │   ├── __init__.py
│   │   └── models.py           # Pydantic models
│   └── utils/
│       ├── __init__.py
│       └── logging.py          # Logging configuration
├── tests/
│   └── ...
└── scripts/
    └── generate_api_keys.py    # API key generation helper
```

## Technical Requirements

### Polymarket API Structure

**API Endpoints**:
- CLOB HTTP URL: `https://clob.polymarket.com/`
- CLOB WebSocket URL: `wss://ws-subscriptions-clob.polymarket.com/ws`
- Gamma API URL: `https://gamma-api.polymarket.com`

**Key Contracts (Polygon Mainnet, Chain ID 137)**:
- USDC Contract: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`
- Conditional Tokens Framework
- Neg Risk Adapter
- Proxy Wallet Factory

### Authentication Levels

| Level | Description | Requirements |
|-------|-------------|--------------|
| L0 | Public endpoints | None |
| L1 | Wallet signer methods | Private key |
| L2 | Trading methods | API credentials (apiKey, secret, passphrase) |

### Python Dependencies

```txt
# Core
py-clob-client>=0.12.0       # Official Polymarket Python client
python-dotenv>=1.0.0         # Environment management
pydantic>=2.0.0              # Data validation
httpx>=0.25.0                # Async HTTP client
websockets>=12.0             # WebSocket support

# Blockchain
web3>=6.0.0                  # Ethereum/Polygon interaction

# Utilities
structlog>=24.0.0            # Structured logging
schedule>=1.2.0              # Task scheduling
tenacity>=8.2.0              # Retry logic

# Database (optional - for tracking)
sqlalchemy>=2.0.0            # ORM
aiosqlite>=0.19.0            # Async SQLite
```

---

## Implementation Phases

### Phase 1: Foundation Setup

**Objective**: Get basic infrastructure working with read-only API access

#### 1.1 Create Project Structure
- Create `apps/polymarket-bot/` directory
- Set up Docker environment
- Create requirements.txt
- Create .env.template with required variables

#### 1.2 Environment Configuration

```bash
# .env.template
POLYGON_PRIVATE_KEY=          # Wallet private key (NEVER commit!)
POLYMARKET_PROXY_WALLET=      # Your Polymarket proxy wallet address
POLYGON_RPC_URL=https://polygon-rpc.com  # or your preferred RPC

# VPN Configuration
VPN_SERVICE_PROVIDER=mullvad  # or nordvpn, expressvpn, etc.
VPN_PRIVATE_KEY=              # WireGuard private key
VPN_ADDRESS=                  # WireGuard address

# API Configuration
CLOB_HTTP_URL=https://clob.polymarket.com/
CLOB_WS_URL=wss://ws-subscriptions-clob.polymarket.com/ws
GAMMA_API_URL=https://gamma-api.polymarket.com

# Copy Trading Configuration
TARGET_WALLET_ADDRESS=        # Wallet to copy trades from
POLL_INTERVAL_SECONDS=4       # How often to check target positions
MAX_POSITION_SIZE_USD=100     # Maximum position size per market

# Risk Management
MAX_TOTAL_EXPOSURE_USD=1000   # Maximum total exposure
MIN_USDC_BALANCE=50           # Minimum USDC to keep available
```

#### 1.3 API Key Generation Script

```python
# scripts/generate_api_keys.py
"""
Generate or derive Polymarket API credentials from private key.
Run once to get your API credentials, then store securely.
"""
import os
from py_clob_client.client import ClobClient
from dotenv import load_dotenv

def main():
    load_dotenv()

    host = "https://clob.polymarket.com"
    key = os.getenv("POLYGON_PRIVATE_KEY")
    chain_id = 137  # Polygon Mainnet

    if not key:
        raise ValueError("POLYGON_PRIVATE_KEY not found in environment")

    # For EOA wallet (direct key)
    client = ClobClient(host, key=key, chain_id=chain_id)

    # For Polymarket proxy wallet (email/browser wallet):
    # proxy_address = os.getenv("POLYMARKET_PROXY_WALLET")
    # client = ClobClient(host, key=key, chain_id=chain_id,
    #                     signature_type=1, funder=proxy_address)

    try:
        api_creds = client.create_or_derive_api_creds()
        print("\n=== API Credentials ===")
        print(f"API Key:     {api_creds.api_key}")
        print(f"Secret:      {api_creds.api_secret}")
        print(f"Passphrase:  {api_creds.api_passphrase}")
        print("\nStore these securely in your .env file!")
        print("Do NOT commit these to git!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

#### 1.4 Basic Client Wrapper

```python
# src/client/polymarket.py
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

class PolymarketClient:
    """Wrapper around py-clob-client with convenience methods."""

    def __init__(self, config):
        self.config = config
        self.client = self._init_client()

    def _init_client(self) -> ClobClient:
        client = ClobClient(
            host=self.config.clob_http_url,
            key=self.config.private_key,
            chain_id=137,  # Polygon
            signature_type=self.config.signature_type,
            funder=self.config.proxy_wallet
        )

        # Set API credentials if available
        if self.config.api_key:
            creds = ApiCreds(
                api_key=self.config.api_key,
                api_secret=self.config.api_secret,
                api_passphrase=self.config.api_passphrase
            )
            client.set_api_creds(creds)

        return client

    # L0 Methods (Public)
    def get_markets(self):
        """Get all available markets."""
        return self.client.get_simplified_markets()

    def get_order_book(self, token_id: str):
        """Get order book for a specific token."""
        return self.client.get_order_book(token_id)

    def get_price(self, token_id: str, side: str = "buy"):
        """Get current price for a token."""
        return self.client.get_price(token_id, side)

    # L2 Methods (Authenticated)
    def create_market_order(self, token_id: str, amount: float, side: str):
        """Execute a market order."""
        return self.client.create_market_order(token_id, amount, side)

    def create_limit_order(self, token_id: str, price: float,
                           size: float, side: str):
        """Place a limit order."""
        return self.client.create_order(token_id, price, size, side)

    def cancel_order(self, order_id: str):
        """Cancel an open order."""
        return self.client.cancel(order_id)

    def get_orders(self):
        """Get all open orders."""
        return self.client.get_orders()

    def get_trades(self):
        """Get trade history."""
        return self.client.get_trades()
```

---

### Phase 2: Wallet Monitoring & Copy Trading

**Objective**: Monitor target wallet and replicate positions

#### 2.1 Wallet Position Tracker

```python
# src/monitoring/wallet_tracker.py
"""
Monitor target wallet positions via Polymarket API.
The Gamma API provides position data for any wallet address.
"""
import httpx
from typing import List, Dict

class WalletTracker:
    def __init__(self, gamma_api_url: str, target_address: str):
        self.gamma_url = gamma_api_url
        self.target_address = target_address
        self.last_positions: Dict[str, float] = {}

    async def get_positions(self) -> List[Dict]:
        """Fetch current positions for target wallet."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.gamma_url}/users/{self.target_address}/positions"
            )
            return response.json()

    async def detect_changes(self) -> Dict:
        """Compare current vs last positions to detect changes."""
        current = await self.get_positions()

        changes = {
            "new_positions": [],
            "closed_positions": [],
            "size_changes": []
        }

        current_map = {p['token_id']: p for p in current}

        # Detect new and changed positions
        for token_id, position in current_map.items():
            if token_id not in self.last_positions:
                changes["new_positions"].append(position)
            elif position['size'] != self.last_positions[token_id]:
                changes["size_changes"].append({
                    "token_id": token_id,
                    "old_size": self.last_positions[token_id],
                    "new_size": position['size']
                })

        # Detect closed positions
        for token_id in self.last_positions:
            if token_id not in current_map:
                changes["closed_positions"].append(token_id)

        # Update last known positions
        self.last_positions = {p['token_id']: p['size'] for p in current}

        return changes
```

#### 2.2 Copy Trading Strategy

```python
# src/strategies/copy_trading.py
"""
Copy trading strategy that replicates target wallet positions.
Configurable position sizing relative to target.
"""
from dataclasses import dataclass
from typing import Optional
import structlog

log = structlog.get_logger()

@dataclass
class CopyTradeConfig:
    target_wallet: str
    size_multiplier: float = 1.0  # 1.0 = same size as target
    max_position_size: float = 100.0  # Max USD per position
    min_position_size: float = 5.0   # Min USD to place order

class CopyTradingStrategy:
    def __init__(self, client, tracker, config: CopyTradeConfig):
        self.client = client
        self.tracker = tracker
        self.config = config

    async def process_position_change(self, change: dict):
        """Process detected position change from target wallet."""

        # Calculate our target size
        target_size = change.get('new_size', 0) * self.config.size_multiplier
        target_size = min(target_size, self.config.max_position_size)

        if target_size < self.config.min_position_size:
            log.info("Position size below minimum, skipping",
                    token_id=change['token_id'], size=target_size)
            return

        # Get current price
        token_id = change['token_id']
        price = await self.client.get_price(token_id, "buy")

        # Execute trade
        log.info("Executing copy trade",
                token_id=token_id, size=target_size, price=price)

        try:
            order = await self.client.create_market_order(
                token_id=token_id,
                amount=target_size,
                side="buy"  # or determine from position change
            )
            log.info("Order placed", order_id=order['id'])
        except Exception as e:
            log.error("Order failed", error=str(e))
```

---

### Phase 3: Risk Management & Safety

**Objective**: Add safety controls and monitoring

#### 3.1 Risk Manager

```python
# src/monitoring/risk_manager.py
"""
Risk management controls to prevent excessive losses.
"""
from dataclasses import dataclass

@dataclass
class RiskLimits:
    max_total_exposure: float = 1000.0  # Max total USD at risk
    max_position_size: float = 100.0     # Max per position
    max_daily_loss: float = 200.0        # Stop trading if exceeded
    min_usdc_balance: float = 50.0       # Keep minimum balance

class RiskManager:
    def __init__(self, client, limits: RiskLimits):
        self.client = client
        self.limits = limits
        self.daily_pnl = 0.0

    async def check_limits(self) -> dict:
        """Check all risk limits before allowing trade."""
        checks = {
            "total_exposure_ok": True,
            "daily_loss_ok": True,
            "balance_ok": True,
            "can_trade": True,
            "reasons": []
        }

        # Check total exposure
        positions = await self.get_total_exposure()
        if positions > self.limits.max_total_exposure:
            checks["total_exposure_ok"] = False
            checks["can_trade"] = False
            checks["reasons"].append(
                f"Total exposure {positions} exceeds {self.limits.max_total_exposure}"
            )

        # Check daily P&L
        if abs(self.daily_pnl) > self.limits.max_daily_loss:
            checks["daily_loss_ok"] = False
            checks["can_trade"] = False
            checks["reasons"].append(
                f"Daily loss {self.daily_pnl} exceeds {self.limits.max_daily_loss}"
            )

        return checks

    async def get_total_exposure(self) -> float:
        """Calculate total USD exposure across all positions."""
        # Implementation depends on position tracking
        pass
```

#### 3.2 Main Application Loop

```python
# src/main.py
"""
Main entry point for the Polymarket copy trading bot.
"""
import asyncio
import structlog
from config import load_config
from client.polymarket import PolymarketClient
from monitoring.wallet_tracker import WalletTracker
from monitoring.risk_manager import RiskManager, RiskLimits
from strategies.copy_trading import CopyTradingStrategy, CopyTradeConfig

log = structlog.get_logger()

async def main():
    config = load_config()

    # Initialize components
    client = PolymarketClient(config)
    tracker = WalletTracker(config.gamma_api_url, config.target_wallet)
    risk_manager = RiskManager(client, RiskLimits(
        max_total_exposure=config.max_total_exposure,
        max_daily_loss=config.max_daily_loss
    ))

    strategy = CopyTradingStrategy(
        client=client,
        tracker=tracker,
        config=CopyTradeConfig(
            target_wallet=config.target_wallet,
            size_multiplier=config.size_multiplier,
            max_position_size=config.max_position_size
        )
    )

    log.info("Starting copy trading bot",
            target=config.target_wallet,
            poll_interval=config.poll_interval)

    while True:
        try:
            # Check risk limits
            risk_check = await risk_manager.check_limits()
            if not risk_check["can_trade"]:
                log.warning("Risk limits exceeded", reasons=risk_check["reasons"])
                await asyncio.sleep(60)  # Wait longer when risk limited
                continue

            # Check for position changes
            changes = await tracker.detect_changes()

            # Process new positions
            for position in changes["new_positions"]:
                await strategy.process_position_change(position)

            # Process size changes
            for change in changes["size_changes"]:
                await strategy.process_position_change(change)

        except Exception as e:
            log.error("Error in main loop", error=str(e))

        await asyncio.sleep(config.poll_interval)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Phase 4: Docker & Deployment

#### 4.1 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY scripts/ ./scripts/

# Run
CMD ["python", "-m", "src.main"]
```

#### 4.2 Docker Compose

```yaml
# docker-compose.yml
version: "3.8"

services:
  polymarket-bot:
    build: .
    container_name: polymarket-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data  # For local database/logs
    networks:
      - traefik
    labels:
      - "homepage.group=Trading"
      - "homepage.name=Polymarket Bot"
      - "homepage.icon=si-polymarket"
      - "homepage.description=Copy trading bot"

networks:
  traefik:
    external: true
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create `apps/polymarket-bot/` directory structure
- [ ] Create `requirements.txt` with dependencies
- [ ] Create `.env.template` with all required variables
- [ ] Create `scripts/generate_api_keys.py`
- [ ] Create basic `PolymarketClient` wrapper
- [ ] Create `config.py` with Pydantic settings
- [ ] Test L0 (read-only) API access
- [ ] Generate and store API credentials

### Phase 2: Copy Trading
- [ ] Create `WalletTracker` class
- [ ] Implement Gamma API position fetching
- [ ] Create `CopyTradingStrategy` class
- [ ] Implement position change detection
- [ ] Test trade execution (paper/small amounts)

### Phase 3: Risk Management
- [ ] Create `RiskManager` class
- [ ] Implement position size limits
- [ ] Implement total exposure limits
- [ ] Implement daily loss limits
- [ ] Add emergency stop functionality

### Phase 4: Deployment
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Add to Traefik network
- [ ] Add Homepage labels
- [ ] Deploy to server

### Phase 5: Monitoring & Improvement
- [ ] Add Prometheus metrics
- [ ] Add Grafana dashboard
- [ ] Add alerting (Discord/Telegram)
- [ ] Add WebSocket support for real-time updates
- [ ] Add position/PnL tracking database

---

## Important Considerations

### Network Configuration

The bot will operate behind a VPN to ensure proper geo-routing. Add VPN configuration to deployment:

```yaml
# docker-compose.yml addition for VPN routing
services:
  polymarket-bot:
    # ... existing config ...
    network_mode: "container:vpn"  # Route through VPN container
    depends_on:
      - vpn

  vpn:
    image: qmcgaw/gluetun:latest
    container_name: polymarket-vpn
    cap_add:
      - NET_ADMIN
    environment:
      - VPN_SERVICE_PROVIDER=your_provider  # mullvad, nordvpn, etc.
      - VPN_TYPE=wireguard
      - WIREGUARD_PRIVATE_KEY=${VPN_PRIVATE_KEY}
      - WIREGUARD_ADDRESSES=${VPN_ADDRESS}
      - SERVER_COUNTRIES=Netherlands  # or other supported country
    volumes:
      - ./vpn:/gluetun
    restart: unless-stopped
```

**Recommended VPN locations** (Polymarket-friendly):
- Netherlands
- Germany
- Singapore
- UK

### Security Best Practices

1. **Never commit private keys** - Use .env files (gitignored)
2. **Use a dedicated wallet** - Don't use your main wallet
3. **Start with small amounts** - Test thoroughly before scaling
4. **Enable 2FA** on all associated accounts
5. **Run in isolated environment** - Docker container recommended

### Wallet Setup Options

| Wallet Type | Signature Type | Notes |
|-------------|----------------|-------|
| EOA (MetaMask export) | 0 | Direct key, requires manual allowances |
| Email/Magic wallet | 1 | Requires proxy address, auto allowances |
| Browser wallet | 2 | Requires proxy address |

For copy trading, you'll likely use **EOA wallet** (export private key from MetaMask).

### Rate Limits

- Basic access: ~1,000 calls/hour for non-trading queries
- Trading endpoints have separate limits
- WebSocket preferred for real-time data

---

## Resources

### Official Documentation
- [Polymarket Docs](https://docs.polymarket.com/)
- [CLOB Clients](https://docs.polymarket.com/developers/CLOB/clients)
- [Authentication](https://docs.polymarket.com/developers/CLOB/authentication)

### Official SDKs
- [py-clob-client (Python)](https://github.com/Polymarket/py-clob-client)
- [clob-client (TypeScript)](https://github.com/Polymarket/clob-client)
- [Polymarket Agents (AI framework)](https://github.com/Polymarket/agents)

### Community Examples
- [polymarket-copy-trading-bot](https://github.com/Trust412/polymarket-copy-trading-bot-v1)
- [Polymarket-spike-bot](https://github.com/Trust412/Polymarket-spike-bot-v1)

### Tutorials
- [Generating API Keys](https://jeremywhittaker.com/index.php/2024/08/28/generating-api-keys-for-polymarket-com/)
- [Accessing Polymarket Data in Python](https://jeremywhittaker.com/index.php/2024/08/20/accessing-polymarket-data-in-python/)

---

## Next Steps

1. **Immediate**: Set up basic project structure (Phase 1.1)
2. **Wallet Setup**: Export private key from your Polymarket wallet
3. **API Keys**: Run key generation script to get API credentials
4. **Test Read-Only**: Verify market data fetching works
5. **Target Wallet**: Identify the wallet address you want to copy
6. **Start Small**: Begin with minimal position sizes for testing
