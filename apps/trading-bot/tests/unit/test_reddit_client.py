"""
Unit Tests for Reddit Client
=============================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Note: These tests require mocking the praw library
# Full integration tests require real Reddit API credentials


class TestRedditClient:
    """Test suite for RedditClient (with mocks)"""
    
    @patch('src.data.providers.sentiment.reddit.praw')
    def test_client_initialization_with_credentials(self, mock_praw):
        """Test client initialization with valid credentials"""
        from src.data.providers.sentiment.reddit import RedditClient
        from src.config.settings import settings
        
        # Mock praw.Reddit
        mock_reddit = Mock()
        mock_praw.Reddit = Mock(return_value=mock_reddit)
        
        # Mock settings
        with patch.object(settings.reddit, 'client_id', 'test_id'):
            with patch.object(settings.reddit, 'client_secret', 'test_secret'):
                with patch.object(settings.reddit, 'user_agent', 'test_agent'):
                    client = RedditClient()
                    
                    assert client.config is not None
                    # Client should be initialized if credentials are provided
                    # (actual initialization depends on praw availability)
    
    @patch('src.data.providers.sentiment.reddit.praw', None)
    def test_client_initialization_without_praw(self):
        """Test that ImportError is raised when praw is not available"""
        from src.data.providers.sentiment.reddit import RedditClient
        
        with pytest.raises(ImportError):
            RedditClient()
    
    def test_is_available_without_credentials(self):
        """Test availability check when credentials are missing"""
        from src.data.providers.sentiment.reddit import RedditClient
        from src.config.settings import settings
        
        with patch.object(settings.reddit, 'client_id', None):
            client = RedditClient()
            assert client.is_available() == False
    
    def test_extract_symbols_from_text(self):
        """Test symbol extraction from text"""
        from src.data.providers.sentiment.reddit import RedditClient
        from src.config.settings import settings
        
        with patch.object(settings.reddit, 'client_id', 'test'):
            client = RedditClient()
            
            # Test various symbol patterns
            text1 = "$AAPL is going up!"
            symbols1 = client._extract_symbols(text1)
            assert "AAPL" in symbols1 or "AAPL" in [s.upper() for s in symbols1]
            
            text2 = "I'm buying TSLA and NVDA shares"
            symbols2 = client._extract_symbols(text2)
            assert len(symbols2) > 0
    
    def test_build_symbol_query(self):
        """Test Reddit search query building"""
        from src.data.providers.sentiment.reddit import RedditClient
        from src.config.settings import settings
        
        with patch.object(settings.reddit, 'client_id', 'test'):
            client = RedditClient()
            
            query = client.build_symbol_query("AAPL")
            assert "AAPL" in query
            assert "$" in query or "stock" in query.lower()

