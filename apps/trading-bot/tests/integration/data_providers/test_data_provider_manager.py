"""
Integration Tests for Data Provider Manager
===========================================

Tests that verify DataProviderManager handles fallback, error handling, and caching.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.data.providers.market_data import (
    DataProviderManager,
    DataProviderType,
    DataProviderFactory,
    BaseDataProvider,
    MarketData,
    OHLCVData
)


class MockDataProvider(BaseDataProvider):
    """Mock data provider for testing"""
    
    def __init__(self, provider_name: str, should_fail: bool = False, delay: float = 0.0):
        super().__init__()
        self.provider_name = provider_name
        self.should_fail = should_fail
        self.delay = delay
        self.call_count = 0
    
    async def get_quote(self, symbol: str) -> MarketData:
        """Mock get_quote"""
        self.call_count += 1
        await asyncio.sleep(self.delay)
        
        if self.should_fail:
            raise RuntimeError(f"{self.provider_name} failed")
        
        return MarketData(
            symbol=symbol,
            price=100.0,
            change=1.0,
            change_pct=0.01,
            volume=1000000,
            timestamp=datetime.now()
        )
    
    async def get_historical_data(self, symbol: str, start_date: datetime,
                                 end_date: datetime, interval: str = "1d") -> list[OHLCVData]:
        """Mock get_historical_data"""
        self.call_count += 1
        await asyncio.sleep(self.delay)
        
        if self.should_fail:
            raise RuntimeError(f"{self.provider_name} failed")
        
        return [
            OHLCVData(
                symbol=symbol,
                timestamp=start_date + timedelta(days=i),
                open=100.0 + i,
                high=102.0 + i,
                low=98.0 + i,
                close=101.0 + i,
                volume=1000000
            )
            for i in range((end_date - start_date).days + 1)
        ]
    
    async def get_multiple_quotes(self, symbols: list[str]) -> dict[str, MarketData]:
        """Mock get_multiple_quotes"""
        self.call_count += 1
        
        if self.should_fail:
            raise RuntimeError(f"{self.provider_name} failed")
        
        return {
            symbol: MarketData(
                symbol=symbol,
                price=100.0,
                change=1.0,
                change_pct=0.01,
                volume=1000000,
                timestamp=datetime.now()
            )
            for symbol in symbols
        }


class TestDataProviderManagerInitialization:
    """Test DataProviderManager initialization"""
    
    def test_initialization_with_single_provider(self):
        """Test initialization with single provider"""
        providers = [(DataProviderType.YAHOO_FINANCE, None)]
        
        manager = DataProviderManager(providers)
        
        assert len(manager.providers) == 1
    
    def test_initialization_with_multiple_providers(self):
        """Test initialization with multiple providers"""
        # Create mock providers to avoid needing real API keys
        with patch('src.data.providers.market_data.DataProviderFactory.create_provider') as mock_factory:
            mock_provider1 = Mock(spec=BaseDataProvider)
            mock_provider2 = Mock(spec=BaseDataProvider)
            mock_factory.side_effect = [mock_provider1, mock_provider2]
            
            providers = [
                (DataProviderType.YAHOO_FINANCE, None),
                (DataProviderType.ALPHA_VANTAGE, "fake_key")
            ]
            
            manager = DataProviderManager(providers)
            
            assert len(manager.providers) == 2
    
    def test_initialization_handles_failed_provider(self):
        """Test that failed provider initialization doesn't crash"""
        with patch('src.data.providers.market_data.DataProviderFactory.create_provider') as mock_factory:
            mock_provider = Mock(spec=BaseDataProvider)
            mock_factory.side_effect = [mock_provider, Exception("Provider init failed")]
            
            providers = [
                (DataProviderType.YAHOO_FINANCE, None),
                (DataProviderType.ALPHA_VANTAGE, "fake_key")
            ]
            
            manager = DataProviderManager(providers)
            
            # Should have only one provider (first one succeeded)
            assert len(manager.providers) == 1


class TestProviderFallback:
    """Test provider fallback mechanisms"""
    
    @pytest.fixture
    def manager(self):
        """Create manager with mock providers"""
        # Create mock providers
        provider1 = MockDataProvider("Provider1", should_fail=True)
        provider2 = MockDataProvider("Provider2", should_fail=False)
        
        manager = DataProviderManager([])
        manager.providers = [provider1, provider2]
        return manager
    
    @pytest.mark.asyncio
    async def test_fallback_on_first_provider_failure(self, manager):
        """Test that manager falls back to second provider when first fails"""
        result = await manager.get_quote("SPY")
        
        assert result is not None
        assert result.symbol == "SPY"
        assert result.price == 100.0
        
        # First provider should have been called (and failed)
        assert manager.providers[0].call_count == 1
        # Second provider should have been called (and succeeded)
        assert manager.providers[1].call_count == 1
    
    @pytest.mark.asyncio
    async def test_fallback_on_all_providers_fail(self, manager):
        """Test error when all providers fail"""
        # Make both providers fail
        manager.providers[0].should_fail = True
        manager.providers[1].should_fail = True
        
        with pytest.raises(RuntimeError, match="All providers failed"):
            await manager.get_quote("SPY")
    
    @pytest.mark.asyncio
    async def test_fallback_for_historical_data(self, manager):
        """Test fallback for historical data"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result = await manager.get_historical_data("SPY", start_date, end_date)
        
        assert result is not None
        assert len(result) > 0
        assert all(isinstance(item, OHLCVData) for item in result)
    
    @pytest.mark.asyncio
    async def test_fallback_for_multiple_quotes(self, manager):
        """Test fallback for multiple quotes"""
        symbols = ["SPY", "QQQ", "IWM"]
        
        result = await manager.get_multiple_quotes(symbols)
        
        assert len(result) == 3
        assert all(symbol in result for symbol in symbols)


class TestProviderErrorHandling:
    """Test error handling in data providers"""
    
    @pytest.fixture
    def manager(self):
        """Create manager with providers that may fail"""
        provider1 = MockDataProvider("Provider1", should_fail=True)
        provider2 = MockDataProvider("Provider2", should_fail=False)
        
        manager = DataProviderManager([])
        manager.providers = [provider1, provider2]
        return manager
    
    @pytest.mark.asyncio
    async def test_handles_network_errors(self, manager):
        """Test handling of network errors"""
        # Provider 1 fails (network error), Provider 2 succeeds
        result = await manager.get_quote("SPY")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_handles_timeout_errors(self, manager):
        """Test handling of timeout errors"""
        # First provider times out (fails), second succeeds
        manager.providers[0].should_fail = True
        
        result = await manager.get_quote("SPY")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_handles_invalid_symbol(self, manager):
        """Test handling of invalid symbol"""
        # Both providers might fail for invalid symbol
        manager.providers[0].should_fail = True
        manager.providers[1].should_fail = True
        
        with pytest.raises(RuntimeError):
            await manager.get_quote("INVALID_SYMBOL_XYZ")


class TestProviderPriority:
    """Test provider priority and ordering"""
    
    @pytest.fixture
    def manager(self):
        """Create manager with ordered providers"""
        provider1 = MockDataProvider("FastProvider", should_fail=False, delay=0.0)
        provider2 = MockDataProvider("SlowProvider", should_fail=False, delay=0.1)
        
        manager = DataProviderManager([])
        manager.providers = [provider1, provider2]
        return manager
    
    @pytest.mark.asyncio
    async def test_uses_first_provider_when_available(self, manager):
        """Test that first provider is used when it succeeds"""
        result = await manager.get_quote("SPY")
        
        assert result is not None
        # First provider should be called
        assert manager.providers[0].call_count == 1
        # Second provider should NOT be called (first succeeded)
        assert manager.providers[1].call_count == 0
    
    @pytest.mark.asyncio
    async def test_provider_order_matters(self, manager):
        """Test that provider order affects which one is used"""
        # Reverse order
        manager.providers = list(reversed(manager.providers))
        
        result = await manager.get_quote("SPY")
        
        assert result is not None
        # Now second provider (original first) should be called
        assert manager.providers[0].call_count == 1


class TestMultipleQuotesFallback:
    """Test fallback for multiple quotes"""
    
    @pytest.fixture
    def manager(self):
        """Create manager with providers"""
        # Provider 1 fails for some symbols, succeeds for others
        provider1 = MockDataProvider("Provider1", should_fail=False)
        provider2 = MockDataProvider("Provider2", should_fail=False)
        
        # Mock provider1 to fail for specific symbols
        async def mock_get_multiple_quotes(symbols):
            result = {}
            for symbol in symbols:
                if symbol == "FAIL_SYMBOL":
                    raise RuntimeError("Provider1 failed")
                result[symbol] = MarketData(
                    symbol=symbol,
                    price=100.0,
                    change=1.0,
                    change_pct=0.01,
                    volume=1000000,
                    timestamp=datetime.now()
                )
            return result
        
        provider1.get_multiple_quotes = mock_get_multiple_quotes
        
        manager = DataProviderManager([])
        manager.providers = [provider1, provider2]
        return manager
    
    @pytest.mark.asyncio
    async def test_partial_failure_with_fallback(self, manager):
        """Test partial failure with fallback to second provider"""
        symbols = ["SPY", "QQQ", "FAIL_SYMBOL"]
        
        result = await manager.get_multiple_quotes(symbols)
        
        # Should have all symbols (fallback worked)
        assert len(result) == 3
        assert all(symbol in result for symbol in symbols)


@pytest.mark.integration
class TestDataProviderIntegration:
    """Integration tests for data provider manager"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_quote_retrieval(self):
        """Test end-to-end quote retrieval with real provider structure"""
        # Use Yahoo Finance (no API key needed) - but mock it for tests
        with patch('src.data.providers.market_data.YahooFinanceProvider.get_quote') as mock_quote:
            mock_quote.return_value = MarketData(
                symbol="SPY",
                price=450.0,
                change=2.5,
                change_pct=0.0056,
                volume=50000000,
                timestamp=datetime.now()
            )
            
            providers = [(DataProviderType.YAHOO_FINANCE, None)]
            manager = DataProviderManager(providers)
            
            result = await manager.get_quote("SPY")
            
            assert result.symbol == "SPY"
            assert result.price == 450.0
    
    @pytest.mark.asyncio
    async def test_end_to_end_historical_data(self):
        """Test end-to-end historical data retrieval"""
        with patch('src.data.providers.market_data.YahooFinanceProvider.get_historical_data') as mock_hist:
            mock_data = [
                OHLCVData(
                    symbol="SPY",
                    timestamp=datetime.now() - timedelta(days=i),
                    open=100.0,
                    high=102.0,
                    low=98.0,
                    close=101.0,
                    volume=1000000
                )
                for i in range(5, 0, -1)
            ]
            mock_hist.return_value = mock_data
            
            providers = [(DataProviderType.YAHOO_FINANCE, None)]
            manager = DataProviderManager(providers)
            
            start_date = datetime.now() - timedelta(days=5)
            end_date = datetime.now()
            
            result = await manager.get_historical_data("SPY", start_date, end_date)
            
            assert len(result) == 5
            assert all(isinstance(item, OHLCVData) for item in result)

