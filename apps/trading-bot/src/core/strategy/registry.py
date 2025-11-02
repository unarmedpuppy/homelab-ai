"""
Strategy Registry
=================

Central registry for managing and instantiating trading strategies.
"""

from typing import Dict, Type, Any, Optional, List
import logging
from .base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry for managing trading strategies"""
    
    _instance = None
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _strategy_metadata: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, name: str, strategy_class: Type[BaseStrategy],
                metadata: Optional[Dict[str, Any]] = None):
        """
        Register a strategy class
        
        Args:
            name: Strategy name/identifier
            strategy_class: Strategy class (must inherit from BaseStrategy)
            metadata: Optional metadata about the strategy
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy class must inherit from BaseStrategy: {strategy_class}")
        
        self._strategies[name] = strategy_class
        
        if metadata:
            self._strategy_metadata[name] = metadata
        else:
            self._strategy_metadata[name] = {
                'name': name,
                'description': strategy_class.__doc__ or f"{name} strategy",
                'class': strategy_class.__name__
            }
        
        logger.info(f"Registered strategy: {name}")
    
    def get_strategy(self, name: str, config: Dict[str, Any]) -> BaseStrategy:
        """
        Create and return a strategy instance
        
        Args:
            name: Strategy name
            config: Strategy configuration dictionary
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy name not found
        """
        if name not in self._strategies:
            available = ', '.join(self._strategies.keys())
            raise ValueError(
                f"Unknown strategy: '{name}'. Available strategies: {available}"
            )
        
        strategy_class = self._strategies[name]
        return strategy_class(config)
    
    def list_strategies(self) -> List[str]:
        """Get list of all registered strategy names"""
        return list(self._strategies.keys())
    
    def get_strategy_info(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a strategy
        
        Args:
            name: Strategy name
            
        Returns:
            Dictionary with strategy metadata
            
        Raises:
            ValueError: If strategy name not found
        """
        if name not in self._strategy_metadata:
            raise ValueError(f"Strategy not found: {name}")
        
        return self._strategy_metadata[name].copy()
    
    def is_registered(self, name: str) -> bool:
        """Check if a strategy is registered"""
        return name in self._strategies
    
    def unregister(self, name: str):
        """Unregister a strategy"""
        if name in self._strategies:
            del self._strategies[name]
            if name in self._strategy_metadata:
                del self._strategy_metadata[name]
            logger.info(f"Unregistered strategy: {name}")


# Global registry instance
_registry = StrategyRegistry()


def register_strategy(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to register a strategy class
    
    Usage:
        @register_strategy('my_strategy', {'description': 'My strategy'})
        class MyStrategy(BaseStrategy):
            ...
    """
    def decorator(strategy_class: Type[BaseStrategy]):
        _registry.register(name, strategy_class, metadata)
        return strategy_class
    return decorator


def get_registry() -> StrategyRegistry:
    """Get the global strategy registry"""
    return _registry

