# core/fft.py
"""
FFT and frequency domain analysis utilities
"""
import numpy as np
from typing import Tuple, Optional


class FFTProcessor:
    """FFT computation and analysis class"""
    
    @staticmethod
    def compute_fft(
        signal: np.ndarray,
        sampling_rate: float,
        window: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute FFT of a signal
        
        Args:
            signal: Input signal array
            sampling_rate: Sampling rate in Hz
            window: Window type ('hann', 'hamming', 'blackman', None)
            
        Returns:
            Tuple of (frequencies, magnitude_spectrum)
        """
        n = len(signal)
        
        # Apply window if specified
        if window == 'hann':
            w = np.hanning(n)
        elif window == 'hamming':
            w = np.hamming(n)
        elif window == 'blackman':
            w = np.blackman(n)
        else:
            w = np.ones(n)
        
        windowed_signal = signal * w
        
        # Compute FFT
        fft_result = np.fft.fft(windowed_signal)
        
        # Get magnitude spectrum (normalized)
        magnitude = np.abs(fft_result) / n
        
        # Single-sided spectrum
        magnitude = magnitude[:n // 2]
        magnitude[1:] *= 2  # Double except DC component
        
        # Frequency axis - guard against division by zero
        safe_sampling_rate = max(float(sampling_rate), 1.0)
        frequencies = np.fft.fftfreq(n, 1/safe_sampling_rate)[:n // 2]
        
        return frequencies, magnitude
    
    @staticmethod
    def compute_phase_spectrum(
        signal: np.ndarray,
        sampling_rate: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute phase spectrum of a signal
        
        Args:
            signal: Input signal array
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Tuple of (frequencies, phase_spectrum)
        """
        n = len(signal)
        fft_result = np.fft.fft(signal)
        phase = np.angle(fft_result)
        
        # Single-sided phase spectrum
        phase = phase[:n // 2]
        frequencies = np.fft.fftfreq(n, 1/sampling_rate)[:n // 2]
        
        return frequencies, phase
    
    @staticmethod
    def compute_power_spectral_density(
        signal: np.ndarray,
        sampling_rate: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Power Spectral Density using Welch's method
        
        Args:
            signal: Input signal array
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Tuple of (frequencies, psd)
        """
        from scipy import signal as scipy_signal
        
        frequencies, psd = scipy_signal.welch(
            signal,
            fs=sampling_rate,
            nperseg=min(256, len(signal)),
            noverlap=None
        )
        
        return frequencies, psd
    
    @staticmethod
    def compute_stft(
        signal: np.ndarray,
        sampling_rate: float,
        nperseg: int = 256
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute Short-Time Fourier Transform
        
        Args:
            signal: Input signal array
            sampling_rate: Sampling rate in Hz
            nperseg: Length of each segment
            
        Returns:
            Tuple of (frequencies, times, spectrogram)
        """
        from scipy import signal as scipy_signal
        
        frequencies, times, spectrogram = scipy_signal.spectrogram(
            signal,
            fs=sampling_rate,
            nperseg=nperseg,
            noverlap=nperseg // 2,
            mode='magnitude'
        )
        
        return frequencies, times, spectrogram
    
    @staticmethod
    def ifft_from_spectrum(
        magnitude: np.ndarray,
        phase: np.ndarray,
        n_original: Optional[int] = None
    ) -> np.ndarray:
        """
        Reconstruct signal from magnitude and phase spectra
        
        Args:
            magnitude: Magnitude spectrum
            phase: Phase spectrum in radians
            n_original: Original signal length (for proper reconstruction)
            
        Returns:
            Reconstructed time-domain signal
        """
        n = n_original if n_original else 2 * (len(magnitude) - 1)
        
        # Create symmetric spectrum
        complex_spectrum = magnitude * np.exp(1j * phase)
        
        # Full spectrum with symmetry
        full_spectrum = np.zeros(n, dtype=complex)
        full_spectrum[:len(magnitude)] = complex_spectrum
        full_spectrum[-(len(magnitude)-1):] = np.conj(complex_spectrum[1:][::-1])
        
        # Inverse FFT
        signal = np.fft.ifft(full_spectrum)
        
        return np.real(signal)