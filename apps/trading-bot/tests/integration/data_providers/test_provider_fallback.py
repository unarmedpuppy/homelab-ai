"""
Data Provider Fallback Integration Tests
========================================

Tests provider fallback mechanism and error handling when providers fail.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Optional

from src.data.providers.market_data import MarketDataProvider
from src.data.providers.yahoo import YahooFinanceProvider
from src.data.providers.alpha_vantage import AlphaVantageProvider


class TestProviderFallback:
    """Test provider fallback mechanism"""
    
    @pytest.mark.asyncio
    async def test_yahoo_primary_provider_success(self):
        """Test that primary provider (Yahoo) works correctly"""
        provider = MarketDataProvider()
        
        # Mock Yahoo provider to return success
        with patch.object(YahooFinanceProvider, 'get_quote', new_callable=AsyncMock) as mock_get_quote:
            mock_get_quote.return_value = {
                'symbol': 'AAPL',
                'price': 150.0,
                'volume': 1000000
            }
            
            result = await provider.get_quote('AAPL')
            
            assert result is not None
            assert result['symbol'] == 'AAPL'
            assert result['price'] == 150.0
            mock_get_quote.assert_called_once_with('AAPL')
    
    @pytest.mark.asyncio
    async def test_fallback_on_yahoo_failure(self):
        """Test fallback to Alpha Vantage when Yahoo fails"""
        provider = MarketDataProvider()
        
        # Mock Yahoo to fail, Alpha Vantage to succeed
        with patch.object(YahooFinanceProvider, 'get_quote', new_callable=AsyncMock) as mock_yahoo:
            mock_yahoo.side_effect = Exception("Yahoo API error")
            
            with patch.object(AlphaVantageProvider, 'get_quote', new_callable=AsyncMock) as mock_av:
                mock_av.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.0,
                    'volume': 1000000
                }
                
                result = await provider.get_quote('AAPL')
                
                assert result is not None
                assert result['symbol'] == 'AAPL'
                mock_yahoo.assert_called_once()
                mock_av.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test behavior when all providers fail"""
        provider = MarketDataProvider()
        
        # Mock all providers to fail
        with patch.object(YahooFinanceProvider, 'get_quote', new_callable=AsyncMock) as mock_yahoo:
            mock_yahoo.side_effect = Exception("Yahoo API error")
            
            with patch.object(AlphaVantageProvider, 'get_quote', new_callable=AsyncMock) as mock_av:
                mock_av.side_effect = Exception("Alpha Vantage API error")
                
                with pytest.raises(Exception):
                    await provider.get_quote('AAPL')
    
    @pytest.mark.asyncio
    async def test_caching_with_fallback(self):
        """Test that fallback results are cached"""
        provider = MarketDataProvider()
        
        # First call: Yahoo fails, fallback to Alpha Vantage
        with patch.object(YahooFinanceProvider, 'get_quote', new_callable=AsyncMock) as mock_yahoo:
            mock_yahoo.side_effect = Exception("Yahoo API error")
            
            with patch.object(AlphaVantageProvider, 'get_quote', new_callable=AsyncMock) as mock_av:
                mock_av.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.0
                }
                
                # First call - should hit Alpha Vantage
                result1 = await provider.get_quote('AAPL')
                assert result1 is not None
                
                # Second call - should use cache (neither provider called)
                result2 = await provider.get_quote('AAPL')
                assert result2 is not None
                assert result2 == result1
                
                # Verify Alpha Vantage only called once
                assert mock_av.call_count == 1

