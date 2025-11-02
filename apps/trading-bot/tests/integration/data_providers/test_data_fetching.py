"""
Data Provider Data Fetching Integration Tests
=============================================

Tests data fetching integration with caching and error handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.data.providers.market_data import MarketDataProvider
from src.utils.cache import get_cache_manager


class TestDataFetching:
    """Test data fetching integration"""
    
    @pytest.mark.asyncio
    async def test_quote_fetching_with_cache(self):
        """Test quote fetching with cache integration"""
        provider = MarketDataProvider()
        cache = get_cache_manager()
        
        # Clear cache first
        await cache.delete('quote:AAPL')
        
        # Mock provider to return data
        with patch.object(provider, '_get_quote_from_providers', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'symbol': 'AAPL',
                'price': 150.0,
                'timestamp': datetime.now()
            }
            
            # First call - should fetch
            result1 = await provider.get_quote('AAPL')
            assert result1 is not None
            assert mock_get.call_count == 1
            
            # Second call - should use cache
            result2 = await provider.get_quote('AAPL')
            assert result2 is not None
            assert mock_get.call_count == 1  # Still 1, cache used
    
    @pytest.mark.asyncio
    async def test_historical_data_fetching(self):
        """Test historical data fetching"""
        provider = MarketDataProvider()
        
        # Mock historical data
        with patch.object(provider, '_get_historical_data_from_providers', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [
                {'date': '2024-01-01', 'open': 150.0, 'high': 155.0, 'low': 148.0, 'close': 152.0, 'volume': 1000000}
            ]
            
            result = await provider.get_historical_data('AAPL', days=30)
            
            assert result is not None
            assert len(result) > 0
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_data_fetch(self):
        """Test error handling during data fetch"""
        provider = MarketDataProvider()
        
        # Mock provider to raise error
        with patch.object(provider, '_get_quote_from_providers', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Provider error")
            
            with pytest.raises(Exception):
                await provider.get_quote('AAPL')
            
            mock_get.assert_called_once()

