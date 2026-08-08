# labs/base_lab.py
"""
Abstract base class for all DSP labs
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import numpy as np


class BaseLab(ABC):
    """Abstract base class for DSP laboratory experiments"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize lab
        
        Args:
            name: Lab name
            description: Lab description
        """
        self.name = name
        self.description = description
        self.parameters = {}  # Store lab-specific parameters
        self.results = {}      # Store computation results
    
    @abstractmethod
    def setup(self) -> Dict[str, Any]:
        """
        Setup lab with default parameters
        
        Returns:
            Dictionary of parameter names and their default values/ranges
        """
        pass
    
    @abstractmethod
    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """
        Process signal based on lab parameters
        
        Args:
            **kwargs: Processing parameters
            
        Returns:
            Tuple of (time_array, signal_array) for time domain plot
        """
        pass
    
    @abstractmethod
    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get frequency domain representation
        
        Args:
            signal: Time domain signal
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Tuple of (frequencies, magnitude_spectrum)
        """
        pass
    
    def update_parameter(self, name: str, value: Any):
        """
        Update a lab parameter
        
        Args:
            name: Parameter name
            value: New parameter value
        """
        if name in self.parameters:
            self.parameters[name]['value'] = value
    
    def get_parameter(self, name: str) -> Any:
        """
        Get current parameter value
        
        Args:
            name: Parameter name
            
        Returns:
            Current parameter value
        """
        return self.parameters.get(name, {}).get('value', None)
    
    def validate_parameters(self) -> bool:
        """
        Validate current parameters
        
        Returns:
            True if parameters are valid
        """
        # Override in child classes if needed
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get lab information
        
        Returns:
            Dictionary with lab info
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }