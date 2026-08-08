# core/filters.py
"""
Digital filter design and implementation
"""
import numpy as np
from typing import Tuple, Optional, Union
from enum import Enum
from scipy import signal as scipy_signal


class FilterType(Enum):
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"
    BANDSTOP = "bandstop"


class FilterDesign(Enum):
    BUTTERWORTH = "butterworth"
    CHEBYSHEV1 = "chebyshev1"
    CHEBYSHEV2 = "chebyshev2"
    ELLIPTIC = "elliptic"
    BESSEL = "bessel"


class DigitalFilter:
    """Digital filter design and application class"""
    
    @staticmethod
    def design_iir_filter(
        filter_type: FilterType,
        design_type: FilterDesign,
        cutoff_freq: Union[float, Tuple[float, float]],
        sampling_rate: float,
        order: int = 4,
        ripple_db: float = 1.0,
        stop_atten_db: float = 40.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Design IIR filter
        
        Args:
            filter_type: Type of filter
            design_type: Filter design method
            cutoff_freq: Cutoff frequency/ies (single for LP/HP, tuple for BP/BS)
            sampling_rate: Sampling rate in Hz
            order: Filter order
            ripple_db: Passband ripple in dB (Chebyshev/elliptic)
            stop_atten_db: Stopband attenuation in dB (Chebyshev2/elliptic)
            
        Returns:
            Tuple of (b, a) filter coefficients
        """
        nyquist = sampling_rate / 2
        
        # Normalize frequencies
        if isinstance(cutoff_freq, (int, float)):
            normalized_cutoff = cutoff_freq / nyquist
            if filter_type in [FilterType.BANDPASS, FilterType.BANDSTOP]:
                raise ValueError("Bandpass/stop requires two cutoff frequencies")
        else:
            normalized_cutoff = (cutoff_freq[0] / nyquist, cutoff_freq[1] / nyquist)
        
        # Design filter based on type
        if design_type == FilterDesign.BUTTERWORTH:
            b, a = scipy_signal.butter(
                order, normalized_cutoff,
                btype=filter_type.value,
                analog=False
            )
        elif design_type == FilterDesign.CHEBYSHEV1:
            b, a = scipy_signal.cheby1(
                order, ripple_db, normalized_cutoff,
                btype=filter_type.value,
                analog=False
            )
        elif design_type == FilterDesign.CHEBYSHEV2:
            b, a = scipy_signal.cheby2(
                order, stop_atten_db, normalized_cutoff,
                btype=filter_type.value,
                analog=False
            )
        elif design_type == FilterDesign.ELLIPTIC:
            b, a = scipy_signal.ellip(
                order, ripple_db, stop_atten_db, normalized_cutoff,
                btype=filter_type.value,
                analog=False
            )
        elif design_type == FilterDesign.BESSEL:
            b, a = scipy_signal.bessel(
                order, normalized_cutoff,
                btype=filter_type.value,
                analog=False
            )
        else:
            raise ValueError(f"Unknown filter design: {design_type}")
        
        return b, a
    
    @staticmethod
    def apply_filter(
        signal: np.ndarray,
        b: np.ndarray,
        a: np.ndarray
    ) -> np.ndarray:
        """
        Apply filter to signal
        
        Args:
            signal: Input signal array
            b: Numerator coefficients
            a: Denominator coefficients
            
        Returns:
            Filtered signal
        """
        # Use lfilter for zero-phase filtering (forward-backward)
        filtered = scipy_signal.filtfilt(b, a, signal)
        return filtered
    
    @staticmethod
    def design_fir_filter(
        filter_type: FilterType,
        cutoff_freq: Union[float, Tuple[float, float]],
        sampling_rate: float,
        num_taps: int = 51,
        window: str = 'hamming'
    ) -> np.ndarray:
        """
        Design FIR filter using window method
        
        Args:
            filter_type: Type of filter
            cutoff_freq: Cutoff frequency/ies
            sampling_rate: Sampling rate in Hz
            num_taps: Number of filter taps (must be odd)
            window: Window type ('hamming', 'hann', 'blackman')
            
        Returns:
            Filter coefficients
        """
        nyquist = sampling_rate / 2
        
        # Normalize frequencies
        if isinstance(cutoff_freq, (int, float)):
            normalized_cutoff = cutoff_freq / nyquist
        else:
            normalized_cutoff = (cutoff_freq[0] / nyquist, cutoff_freq[1] / nyquist)
        
        # Design filter
        taps = scipy_signal.firwin(
            num_taps, normalized_cutoff,
            window=window,
            pass_zero=(filter_type == FilterType.LOWPASS),
            fs=2.0  # Normalized to Nyquist frequency
        )
        
        return taps
    
    @staticmethod
    def get_frequency_response(
        b: np.ndarray,
        a: np.ndarray,
        sampling_rate: float,
        n_points: int = 512
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get frequency response of a filter
        
        Args:
            b: Numerator coefficients
            a: Denominator coefficients
            sampling_rate: Sampling rate in Hz
            n_points: Number of frequency points
            
        Returns:
            Tuple of (frequencies, magnitude_response)
        """
        w, h = scipy_signal.freqz(b, a, worN=n_points)
        frequencies = w * sampling_rate / (2 * np.pi)
        magnitude = 20 * np.log10(np.abs(h) + 1e-10)
        
        return frequencies, magnitude