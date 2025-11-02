"""
Trends Data Providers
=====================

Providers for tracking trends and search interest data.
"""

try:
    from .google_trends import GoogleTrendsProvider
except ImportError:
    GoogleTrendsProvider = None

__all__ = [
    'GoogleTrendsProvider',
]

