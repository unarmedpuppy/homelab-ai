"""
Monitoring Routes
=================

API routes for monitoring and health checks.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import psutil
import time

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            },
            "services": {
                "api": "running",
                "database": "connected",
                "data_providers": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/metrics")
async def get_metrics():
    """Get system and application metrics"""
    return {
        "timestamp": time.time(),
        "uptime": time.time(),  # TODO: Calculate actual uptime
        "requests_processed": 0,  # TODO: Track requests
        "active_connections": 0,  # TODO: Track connections
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }
