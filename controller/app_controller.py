# controllers/app_controller.py
"""
Main application controller
"""
from typing import Dict, Any
import numpy as np


class AppController:
    """Main application controller managing global state"""
    
    def __init__(self):
        """Initialize the application controller"""
        self.global_settings = {
            'theme': 'dark',
            'default_sampling_rate': 1000.0,
            'plot_update_rate': 30,  # Hz
            'auto_range': True
        }
        self.current_lab = None
        self.signal_cache = {}
    
    def get_setting(self, key: str) -> Any:
        """Get a global setting value"""
        return self.global_settings.get(key)
    
    def set_setting(self, key: str, value: Any):
        """Update a global setting"""
        self.global_settings[key] = value
    
    def cache_signal(self, key: str, time_data: np.ndarray, signal_data: np.ndarray):
        """Cache a signal for later use"""
        self.signal_cache[key] = (time_data, signal_data)
    
    def get_cached_signal(self, key: str) -> tuple:
        """Retrieve a cached signal"""
        return self.signal_cache.get(key, (None, None))
    
    def clear_cache(self):
        """Clear all cached signals"""
        self.signal_cache.clear()
    
    def export_results(self, time_data: np.ndarray, signal_data: np.ndarray, 
                      filepath: str):
        """Export processing results to CSV"""
        data = np.column_stack((time_data, signal_data))
        np.savetxt(filepath, data, delimiter=',', 
                  header='Time (s),Amplitude', comments='')