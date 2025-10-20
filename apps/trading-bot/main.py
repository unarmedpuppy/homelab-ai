#!/usr/bin/env python3
"""
Trading Bot Main Application
============================

Main entry point for the trading bot application.
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.main import app
from src.config.settings import settings
import logging

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.logging.level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("Starting Trading Bot Application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.api.debug}")
    logger.info(f"API host: {settings.api.host}")
    logger.info(f"API port: {settings.api.port}")
    
    # Start the application
    uvicorn.run(
        "src.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level=settings.logging.level.lower()
    )

if __name__ == "__main__":
    main()
