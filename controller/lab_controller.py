# controllers/lab_controller.py
"""
Controller for managing lab operations
"""
from typing import Dict, Any, Tuple
import numpy as np
import importlib
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from labs.base_lab import BaseLab


class LabController:
    """Controller for lab experiments"""
    
    def __init__(self, lab_id: str, app_controller):
        """
        Initialize lab controller
        
        Args:
            lab_id: Identifier for the lab (sampling, quantization, etc.)
            app_controller: Reference to main app controller
        """
        self.lab_id = lab_id
        self.app_controller = app_controller
        self.lab_instance = self._load_lab(lab_id)
        self.custom_signal = None
        self.custom_time = None
        self.results = {}
    
    def _load_lab(self, lab_id: str) -> BaseLab:
        """Dynamically load the appropriate lab module"""
        lab_modules = {
            'sampling': ('labs.lab1_sampling', 'Lab1Sampling'),
            'quantization': ('labs.lab2_quantization', 'Lab2Quantization'),
            'convolution': ('labs.lab3_filtering', 'Lab3Filtering'),

            'fft': ('labs.lab4_fft', 'Lab4FFT'),
            'filtering': ('labs.lab5_convulution', 'Lab5Convolution'),


            'ztransform': ('labs.lab6_ztransform', 'Lab6ZTransform'),

            'dft': ('labs.lab7_dft', 'Lab7DFT'),
            'applications': ('labs.lab8_applications', 'Lab8Applications')
        }
        
        if lab_id not in lab_modules:
            raise ValueError(f"Unknown lab ID: {lab_id}")
        
        module_name, class_name = lab_modules[lab_id]
        
        # Import module dynamically
        module = importlib.import_module(module_name)
        lab_class = getattr(module, class_name)
        
        return lab_class()
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get lab parameters"""
        return self.lab_instance.setup()
    
    def get_lab_info(self) -> Dict[str, Any]:
        """Get lab information"""
        return self.lab_instance.get_info()
    
    def update_parameter(self, param_name: str, value: Any):
        """Update a parameter value"""
        self.lab_instance.update_parameter(param_name, value)
    
    def set_custom_signal(self, time_data: np.ndarray, signal_data: np.ndarray, sampling_rate: float | None = None):
        """Set custom signal for processing."""
        self.custom_time = time_data
        self.custom_signal = signal_data
        self.custom_sampling_rate = sampling_rate
        self._custom_signal_source = "file_or_sample"

    def clear_custom_signal(self):
        """Clear any uploaded/sample input so the lab uses its default generation."""
        self.custom_time = None
        self.custom_signal = None
        self.custom_sampling_rate = None
        self._custom_signal_source = None


    
    def process(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process the lab with current parameters
        
        Args:
            params: Optional parameters to override
            
        Returns:
            Dictionary with processing results
        """
        if params:
            for key, value in params.items():
                self.update_parameter(key, value)
        
        # Process using custom signal if available, otherwise lab's default
        # Special case: FileLoader image uploads emit:
        #   time_data = np.array([<file_path>], dtype=object)
        #   signal_data = None
        if self.custom_time is not None and hasattr(self.lab_instance, 'set_signal'):
            sr = getattr(self, 'custom_sampling_rate', None)

            # Detect image-path payload
            if self.custom_signal is None and isinstance(self.custom_time, np.ndarray):
                arr = self.custom_time
                if arr.size == 1 and isinstance(arr.flat[0], str):
                    # Image upload payload: time_data carries the image path.
                    # Lab2Quantization expects signal_data to be an image-like array or a path-aware signal.
                    # We keep time_data empty and pass the image path through signal_data as a 0-d object array.
                    img_path = arr.flat[0]
                    # Send the path in time_data; Lab2Quantization will load the image from it.
                    self.lab_instance.set_signal(
                        np.array([img_path], dtype=object),
                        np.array(['__IMAGE__'], dtype=object),
                        sampling_rate=sr,
                    )

                    result = self.lab_instance.process(**self._get_current_parameters())
                else:
                    # Fallback to whatever the lab expects
                    if self.custom_signal is not None:
                        self.lab_instance.set_signal(self.custom_time, self.custom_signal, sampling_rate=sr)
                    result = self.lab_instance.process(**self._get_current_parameters())
            else:
                if self.custom_signal is not None:
                    self.lab_instance.set_signal(self.custom_time, self.custom_signal, sampling_rate=sr)
                result = self.lab_instance.process(**self._get_current_parameters())
        elif self.custom_signal is not None and self.custom_time is not None:
            # Use uploaded/custom signal as input (must set signal *before* processing)
            if hasattr(self.lab_instance, 'set_signal'):
                sr = getattr(self, 'custom_sampling_rate', None)
                self.lab_instance.set_signal(self.custom_time, self.custom_signal, sampling_rate=sr)
                result = self.lab_instance.process(**self._get_current_parameters())
            else:
                # Fallback: labs that don't support external signals
                result = (self.custom_time, self.custom_signal)
        else:
            # Process with lab's default signal generation
            result = self.lab_instance.process(**self._get_current_parameters())


        
        # Get frequency domain representation
        if len(result) == 2:
            time_data, signal_data = result
            sampling_rate = self._get_sampling_rate()
            freq_data = self.lab_instance.get_frequency_domain(signal_data, sampling_rate)
        else:
            time_data, signal_data = np.array([]), np.array([])
            freq_data = (np.array([]), np.array([]))
        
        return {
            'time_domain': (time_data, signal_data),
            'freq_domain': freq_data,
            'results': self.lab_instance.results
        }
    
    def _get_current_parameters(self) -> Dict[str, Any]:
        """Get current parameter values"""
        params = {}
        for param_name, param_info in self.lab_instance.parameters.items():
            params[param_name] = param_info.get('value', param_info.get('default'))
        return params
    
    def _get_sampling_rate(self) -> float:
        """Get current sampling rate from parameters (ensures minimum of 1.0 to avoid div by zero)"""
        params = self._get_current_parameters()
        sr = params.get('sampling_rate', 1000.0)
        # Guard against division by zero in FFT computation
        if sr is None or float(sr) <= 0:
            return 1000.0
        return float(sr)
    
    def set_results(self, results: Dict[str, Any]):
        """Store processing results"""
        self.results = results
    
    def get_results(self) -> Dict[str, Any]:
        """Get stored results"""
        return self.results