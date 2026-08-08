# core/signal.py
"""
Signal generation and processing utilities
"""
import numpy as np
from typing import Tuple, Optional, Callable
from enum import Enum


class SignalType(Enum):
    SINUSOID = "sinusoid"
    COSINE = "cosine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    NOISE = "noise"
    UNIT_STEP = "unit_step"
    IMPULSE = "impulse"
    RAMP = "ramp"
    EXPONENTIAL = "exponential"


class SignalProcessor:
    """Signal generation and processing class"""
    
    @staticmethod
    def generate_signal(
        signal_type: SignalType,
        duration: float = 1.0,
        sampling_rate: float = 1000.0,
        frequency: float = 10.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        offset: float = 0.0,
        noise_amplitude: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate various types of signals
        
        Returns:
            Tuple of (time_array, signal_array)
        """
        t = np.arange(0, duration, 1/sampling_rate)
        
        if signal_type == SignalType.SINUSOID:
            signal = amplitude * np.sin(2 * np.pi * frequency * t + phase) + offset
            
        elif signal_type == SignalType.COSINE:
            signal = amplitude * np.cos(2 * np.pi * frequency * t + phase) + offset
            
        elif signal_type == SignalType.SQUARE:
            signal = amplitude * np.sign(np.sin(2 * np.pi * frequency * t + phase)) + offset
            
        elif signal_type == SignalType.TRIANGLE:
            # Triangle wave generation
            period = 1 / frequency
            t_mod = t % period
            signal = 2 * amplitude * np.abs(2 * (t_mod / period) - 1) - amplitude + offset
            
        elif signal_type == SignalType.SAWTOOTH:
            period = 1 / frequency
            t_mod = t % period
            signal = 2 * amplitude * (t_mod / period) - amplitude + offset
            
        elif signal_type == SignalType.NOISE:
            signal = amplitude * np.random.randn(len(t)) + offset
            
        elif signal_type == SignalType.UNIT_STEP:
            signal = amplitude * (t >= 0).astype(float) + offset
            
        elif signal_type == SignalType.IMPULSE:
            signal = np.zeros(len(t))
            # Place impulse at t=0
            idx = np.argmin(np.abs(t))
            signal[idx] = amplitude
            signal += offset
            
        elif signal_type == SignalType.RAMP:
            signal = amplitude * t + offset
            
        elif signal_type == SignalType.EXPONENTIAL:
            signal = amplitude * np.exp(-frequency * t) + offset
            
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")
        
        # Add noise if specified
        if noise_amplitude > 0:
            signal += noise_amplitude * np.random.randn(len(t))
        
        return t, signal
    
    @staticmethod
    def load_from_audio(filepath: str) -> Tuple[np.ndarray, np.ndarray, float]:
        """Load an audio file (e.g., MP3/WAV) into a time-series.

        Returns:
            (time_array, signal_array, sampling_rate)

        Notes:
            - Uses soundfile for MP3/WAV loading (supports multiple formats)
            - Falls back to scipy.io.wavfile for WAV files
        """
        # Try soundfile first (supports MP3, WAV, FLAC, OGG, etc.)
        try:
            import soundfile as sf
            
            data, fs = sf.read(filepath)
            data = np.asarray(data, dtype=np.float32)
            
            # Convert to mono if stereo
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            
            # Normalize if needed
            max_val = np.max(np.abs(data))
            if max_val > 0:
                data = data / max_val
            
            t = np.arange(len(data), dtype=np.float64) / float(fs)
            return t, data, float(fs)
        except ImportError:
            pass  # Fall through to scipy fallback
        except Exception:
            pass  # Fall through to scipy fallback
        
        # Fallback: Try scipy.io.wavfile for WAV files only
        try:
            from scipy.io import wavfile

            ext = str(filepath).lower()
            if ext.endswith('.wav'):
                fs, data = wavfile.read(filepath)
                data = np.asarray(data)
                # Convert integer PCM to float in [-1, 1]
                if np.issubdtype(data.dtype, np.integer):
                    max_val = np.iinfo(data.dtype).max
                    data = data.astype(np.float32) / float(max_val)

                if data.ndim == 1:
                    signal = data
                else:
                    # average channels to mono
                    signal = data.astype(np.float32)
                    signal = np.mean(signal, axis=1)

                t = np.arange(len(signal), dtype=np.float64) / float(fs)
                return t, signal, float(fs)
        except Exception:
            pass  # Fall through to error

        # If all else fails, raise a clear error
        raise RuntimeError(
            f"Failed to decode audio file: {filepath}. "
            "Install soundfile (pip install soundfile) for MP3/WAV support."
        )



    
    @staticmethod
    def resample_signal(signal: np.ndarray, original_rate: float, target_rate: float) -> np.ndarray:
        """
        Resample signal to a different sampling rate
        
        Args:
            signal: Input signal array
            original_rate: Original sampling rate in Hz
            target_rate: Target sampling rate in Hz
            
        Returns:
            Resampled signal
        """
        from scipy import signal as scipy_signal
        
        # Calculate new length
        original_length = len(signal)
        target_length = int(original_length * target_rate / original_rate)
        
        # Resample using FFT-based method (works well for bandlimited signals)
        resampled = scipy_signal.resample(signal, target_length)
        
        return resampled