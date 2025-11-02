"""
Unit Tests for Twitter Client
==============================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Note: These tests require mocking the tweepy library
# Full integration tests require real Twitter API credentials


class TestTwitterClient:
    """Test suite for TwitterClient (with mocks)"""
    
    @patch('src.data.providers.sentiment.twitter.tweepy')
    @patch('src.data.providers.sentiment.twitter.Client')
    def test_client_initialization_with_credentials(self, mock_client, mock_tweepy):
        """Test client initialization with valid credentials"""
        from src.data.providers.sentiment.twitter import TwitterClient
        from src.config.settings import settings
        
        # Mock settings
        with patch.object(settings.twitter, 'bearer_token', 'test_token'):
            with patch.object(settings.twitter, 'api_key', 'test_key'):
                client = TwitterClient()
                
                assert client.config is not None
                # Client should be initialized if credentials are provided
                # (actual initialization depends on tweepy availability)
    
    @patch('src.data.providers.sentiment.twitter.tweepy', None)
    def test_client_initialization_without_tweepy(self):
        """Test that ImportError is raised when tweepy is not available"""
        from src.data.providers.sentiment.twitter import TwitterClient
        
        with pytest.raises(ImportError):
            TwitterClient()
    
    def test_is_available_without_credentials(self):
        """Test availability check when credentials are missing"""
        from src.data.providers.sentiment.twitter import TwitterClient
        from src.config.settings import settings
        
        with patch.object(settings.twitter, 'bearer_token', None):
            client = TwitterClient()
            assert client.is_available() == False
    
    @patch('src.data.providers.sentiment.twitter.tweepy')
    @patch('src.data.providers.sentiment.twitter.Client')
    def test_rate_limit_check(self, mock_client, mock_tweepy):
        """Test rate limiting is enabled"""
        from src.data.providers.sentiment.twitter import TwitterClient
        from src.config.settings import settings
        
        with patch.object(settings.twitter, 'bearer_token', 'test_token'):
            with patch.object(settings.twitter, 'rate_limit_enabled', True):
                client = TwitterClient()
                # Rate limiting should be configured
                # (actual check depends on tweepy implementation)
                assert client.config.rate_limit_enabled == True

