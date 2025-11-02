"""
Parameter Space Definition
==========================

Define parameter ranges and generate combinations for strategy optimization.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParameterRange:
    """Define a parameter range for optimization"""
    name: str
    min_val: Union[int, float]
    max_val: Union[int, float]
    step: Optional[Union[int, float]] = None
    log_scale: bool = False
    dtype: type = float
    
    def __post_init__(self):
        """Validate and adjust parameters"""
        if self.step is None:
            # Default step based on range and type
            if self.dtype == int:
                self.step = max(1, int((self.max_val - self.min_val) / 10))
            else:
                self.step = (self.max_val - self.min_val) / 10
        
        # Ensure step is positive
        if self.step <= 0:
            raise ValueError(f"Step must be positive for parameter {self.name}")
        
        # Ensure min < max
        if self.min_val >= self.max_val:
            raise ValueError(f"min_val must be less than max_val for parameter {self.name}")
    
    def generate_values(self) -> List[Any]:
        """
        Generate list of values for this parameter range
        
        Returns:
            List of parameter values
        """
        if self.log_scale:
            # Logarithmic scale
            if self.min_val <= 0 or self.max_val <= 0:
                raise ValueError(f"Log scale requires positive values for parameter {self.name}")
            
            min_log = np.log10(self.min_val)
            max_log = np.log10(self.max_val)
            
            # Generate log-spaced values
            num_steps = int((max_log - min_log) / np.log10(1 + self.step / self.min_val)) + 1
            log_values = np.logspace(min_log, max_log, num=num_steps)
            
            # Round to appropriate precision
            if self.dtype == int:
                values = [int(round(v)) for v in log_values]
            else:
                # Round to step precision
                precision = len(str(self.step).split('.')[-1]) if '.' in str(self.step) else 2
                values = [round(float(v), precision) for v in log_values]
        else:
            # Linear scale
            num_steps = int((self.max_val - self.min_val) / self.step) + 1
            values = np.linspace(self.min_val, self.max_val, num=num_steps)
            
            if self.dtype == int:
                values = [int(round(v)) for v in values]
            else:
                # Round to step precision
                precision = len(str(self.step).split('.')[-1]) if '.' in str(self.step) else 2
                values = [round(float(v), precision) for v in values]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_values = []
        for v in values:
            if v not in seen:
                seen.add(v)
                unique_values.append(v)
        
        # Ensure values are within bounds
        unique_values = [v for v in unique_values if self.min_val <= v <= self.max_val]
        
        logger.debug(f"Generated {len(unique_values)} values for parameter {self.name}")
        
        return unique_values


class ParameterSpace:
    """
    Define a parameter space for optimization
    
    Supports multiple parameter ranges and generates all combinations.
    """
    
    def __init__(self, ranges: Dict[str, ParameterRange]):
        """
        Initialize parameter space
        
        Args:
            ranges: Dictionary mapping parameter names to ParameterRange objects
        """
        self.ranges = ranges
        self._validate_ranges()
    
    def _validate_ranges(self):
        """Validate all parameter ranges"""
        if not self.ranges:
            raise ValueError("ParameterSpace must have at least one parameter range")
        
        for name, param_range in self.ranges.items():
            if not isinstance(param_range, ParameterRange):
                raise TypeError(f"Range for {name} must be a ParameterRange instance")
            if param_range.name != name:
                logger.warning(
                    f"ParameterRange name '{param_range.name}' doesn't match key '{name}'. "
                    f"Using key '{name}' as parameter name."
                )
    
    def generate_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate all parameter combinations
        
        Returns:
            List of dictionaries, each containing one parameter combination
        """
        if not self.ranges:
            return [{}]
        
        # Generate values for each parameter
        param_values = {}
        for name, param_range in self.ranges.items():
            param_values[name] = param_range.generate_values()
        
        # Generate all combinations
        from itertools import product
        
        param_names = list(param_values.keys())
        value_lists = [param_values[name] for name in param_names]
        
        combinations = []
        for combo in product(*value_lists):
            combination = dict(zip(param_names, combo))
            combinations.append(combination)
        
        logger.info(
            f"Generated {len(combinations)} parameter combinations from {len(self.ranges)} parameters"
        )
        
        return combinations
    
    def get_total_combinations(self) -> int:
        """
        Calculate total number of combinations without generating them
        
        Returns:
            Total number of parameter combinations
        """
        if not self.ranges:
            return 1
        
        total = 1
        for param_range in self.ranges.values():
            values = param_range.generate_values()
            total *= len(values)
        
        return total
    
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all parameters
        
        Returns:
            Dictionary with parameter information
        """
        info = {}
        for name, param_range in self.ranges.items():
            values = param_range.generate_values()
            info[name] = {
                "min": param_range.min_val,
                "max": param_range.max_val,
                "step": param_range.step,
                "log_scale": param_range.log_scale,
                "dtype": param_range.dtype.__name__,
                "num_values": len(values),
                "values": values[:10] if len(values) > 10 else values,  # Sample first 10
            }
        
        return info

