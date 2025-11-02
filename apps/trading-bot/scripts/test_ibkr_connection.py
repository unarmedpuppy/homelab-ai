#!/usr/bin/env python3
"""
Interactive Brokers Connection Test
===================================

Script to test the connection to Interactive Brokers TWS/Gateway.
This helps verify that the IBKR connection is properly configured.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

from src.data.brokers.ibkr_client import IBKRClient
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test IBKR connection"""
    logger.info("=" * 60)
    logger.info("Interactive Brokers Connection Test")
    logger.info("=" * 60)
    
    # Display configuration
    logger.info("\n📋 Configuration:")
    logger.info(f"   Host: {settings.ibkr.host}")
    logger.info(f"   Port: {settings.ibkr.port}")
    logger.info(f"   Client ID: {settings.ibkr.client_id}")
    logger.info("")
    
    # Check if ib_insync is installed
    try:
        from ib_insync import IB
        logger.info("✅ ib_insync is installed")
    except ImportError:
        logger.error("❌ ib_insync is not installed")
        logger.error("   Please run: pip install ib-insync")
        return False
    
    # Test connection
    client = None
    try:
        logger.info("🔌 Attempting to connect to IBKR...")
        logger.info("   Make sure TWS or IB Gateway is running!")
        logger.info("")
        
        client = IBKRClient(
            host=settings.ibkr.host,
            port=settings.ibkr.port,
            client_id=settings.ibkr.client_id
        )
        
        connected = await client.connect()
        
        if not connected:
            logger.error("❌ Failed to connect to IBKR")
            logger.error("")
            logger.error("Common issues:")
            logger.error("1. TWS or IB Gateway is not running")
            logger.error("2. API connections are disabled in TWS/Gateway")
            logger.error("3. Wrong port (7497 for paper, 7496 for live)")
            logger.error("4. Firewall blocking the connection")
            logger.error("5. Client ID conflict (another app using same ID)")
            logger.error("")
            logger.error("To enable API connections in TWS:")
            logger.error("  Edit → Global Configuration → API → Settings")
            logger.error("  ✓ Enable ActiveX and Socket Clients")
            logger.error("  ✓ Read-Only API: Unchecked (for trading)")
            logger.error("  ✓ Port: 7497 (paper) or 7496 (live)")
            return False
        
        logger.info("✅ Successfully connected to IBKR!")
        logger.info("")
        
        # Test getting account summary
        logger.info("📊 Testing account access...")
        try:
            account_summary = await client.get_account_summary()
            logger.info(f"✅ Account access successful!")
            logger.info(f"   Retrieved {len(account_summary)} account fields")
            
            # Display some key account info
            if account_summary:
                logger.info("")
                logger.info("💰 Account Summary (sample):")
                for tag, value_info in list(account_summary.items())[:10]:
                    currency = value_info.get("currency", "")
                    value = value_info.get("value", "")
                    logger.info(f"   {tag}: {value} {currency}")
        except Exception as e:
            logger.warning(f"⚠️  Could not get account summary: {e}")
            logger.warning("   This might be normal if you don't have market data subscriptions")
        
        # Test getting market data for a common symbol
        logger.info("")
        logger.info("📈 Testing market data access...")
        try:
            contract = client.create_contract("AAPL")
            market_data = await client.get_market_data(contract)
            
            logger.info(f"✅ Market data access successful!")
            logger.info(f"   AAPL Quote:")
            if market_data.get("last"):
                logger.info(f"      Last: ${market_data['last']:.2f}")
            if market_data.get("bid"):
                logger.info(f"      Bid: ${market_data['bid']:.2f}")
            if market_data.get("ask"):
                logger.info(f"      Ask: ${market_data['ask']:.2f}")
        except Exception as e:
            logger.warning(f"⚠️  Could not get market data: {e}")
            logger.warning("   This might require a market data subscription")
        
        # Test getting positions
        logger.info("")
        logger.info("💼 Testing position access...")
        try:
            positions = await client.get_positions()
            logger.info(f"✅ Position access successful!")
            logger.info(f"   Current positions: {len(positions)}")
            if positions:
                for pos in positions:
                    logger.info(f"   {pos.symbol}: {pos.quantity} @ ${pos.average_price:.2f}")
        except Exception as e:
            logger.warning(f"⚠️  Could not get positions: {e}")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Connection test completed successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Your IBKR connection is properly configured and working.")
        logger.info("You can now use the trading bot with Interactive Brokers.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        logger.error("")
        logger.error("Please check:")
        logger.error("1. TWS or IB Gateway is running")
        logger.error("2. API connections are enabled")
        logger.error("3. Port and client ID are correct")
        logger.error("4. Network connectivity")
        import traceback
        logger.debug(traceback.format_exc())
        return False
        
    finally:
        if client:
            logger.info("")
            logger.info("🔌 Disconnecting...")
            await client.disconnect()
            logger.info("✅ Disconnected")

async def main():
    """Main function"""
    try:
        success = await test_connection()
        return success
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"\n\n❌ Unexpected error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

