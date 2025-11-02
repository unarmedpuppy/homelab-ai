# Middleware package

from .metrics_middleware import MetricsMiddleware

# Import from parent middleware.py file using direct import
# We need to import it as src.api.middleware to make relative imports work
try:
    # Import as if it were part of the package structure
    import sys
    from pathlib import Path
    import importlib.util
    
    # Get the parent directory (src/api)
    _parent_dir = Path(__file__).parent.parent
    _middleware_file = _parent_dir / "middleware.py"
    
    if _middleware_file.exists():
        # Load the module with the correct package structure
        spec = importlib.util.spec_from_file_location("src.api.middleware_module", _middleware_file)
        if spec and spec.loader:
            # Add src to path temporarily to make relative imports work
            _src_path = str(_parent_dir.parent.parent)
            if _src_path not in sys.path:
                sys.path.insert(0, _src_path)
            try:
                middleware_module = importlib.util.module_from_spec(spec)
                sys.modules['src.api.middleware_module'] = middleware_module
                spec.loader.exec_module(middleware_module)
                LoggingMiddleware = middleware_module.LoggingMiddleware
                RateLimitMiddleware = middleware_module.RateLimitMiddleware
            finally:
                if _src_path in sys.path:
                    sys.path.remove(_src_path)
        else:
            LoggingMiddleware = None
            RateLimitMiddleware = None
    else:
        LoggingMiddleware = None
        RateLimitMiddleware = None
except Exception as e:
    # Fallback: try direct import (won't work with relative imports in middleware.py)
    LoggingMiddleware = None
    RateLimitMiddleware = None

__all__ = ["MetricsMiddleware", "LoggingMiddleware", "RateLimitMiddleware"]

