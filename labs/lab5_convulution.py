"""labs.lab5_convolution

Lab 5: Signal Generation + Windowing + Spectral Leakage Visualization

Requirements implemented:
- Generate or accept user-defined signals (sine/cosine/noise)
  with adjustable: frequency, amplitude, sampling rate, duration, optional phase.
- Windowing: Rectangular, Hamming, Hann, Blackman.
- Apply selected window to the signal.
- Compare original vs windowed in time domain.
- Demonstrate spectral leakage via FFT magnitude visualization.

UI Integration:
- process() returns (t, x_windowed) for primary time-domain plot
- get_frequency_domain() returns (freqs, mag) for frequency-domain tab
- self.results contains all data for additional UI rendering
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from labs.base_lab import BaseLab
from core.signal import SignalType, SignalProcessor
from core.fft import FFTProcessor


@dataclass
class Lab5Params:
    signal_type: str = SignalType.SINUSOID.value
    frequency_hz: float = 50.0
    amplitude: float = 1.0
    sampling_rate_hz: float = 1000.0
    duration_s: float = 1.0
    phase_rad: float = 0.0
    window_type: str = "Rectangular"


def _make_window(window_type: str, n: int) -> np.ndarray:
    """Return a window vector of length n.

    Supported window types:
    - Rectangular (boxcar)
    - Hamming
    - Hann (Hanning)
    - Blackman
    """
    w_type = str(window_type).strip().lower()

    if w_type in {"rectangular", "boxcar", "rect", "none"}:
        return np.ones(n, dtype=np.float64)

    if w_type in {"hamming"}:
        return np.hamming(n).astype(np.float64)

    if w_type in {"hann", "hanning"}:
        return np.hanning(n).astype(np.float64)

    if w_type in {"blackman"}:
        return np.blackman(n).astype(np.float64)

    # Fallback to rectangular
    return np.ones(n, dtype=np.float64)


def _compute_single_sided_fft(signal: np.ndarray, sampling_rate_hz: float) -> Tuple[np.ndarray, np.ndarray]:
    """Compute single-sided FFT magnitude spectrum.

    Returns:
        freqs: Single-sided frequency bins (0 to Nyquist, excluding Nyquist)
        mag: Single-sided magnitude spectrum with proper scaling
    """
    x = np.asarray(signal, dtype=np.float64)
    N = len(x)

    if N < 2:
        return np.array([0.0]), np.array([0.0])

    # Compute FFT
    X = np.fft.fft(x)

    # Single-sided magnitude
    mag = np.abs(X) / N
    half = N // 2
    mag_single = mag[:half].copy()

    # Double non-DC components (energy preservation)
    if len(mag_single) > 1:
        mag_single[1:] *= 2.0

    # Frequency bins matching single-sided spectrum
    freqs = np.fft.rfftfreq(N, d=1.0 / sampling_rate_hz)[:-1]  # drop Nyquist to match [:N//2]

    return freqs, mag_single


class Lab5Convolution(BaseLab):
    """Lab 5: Signal generation, windowing, and spectral leakage demonstration.

    This lab demonstrates how different window functions affect the frequency
    domain representation of signals, particularly in reducing spectral leakage
    when the signal frequency does not align with FFT bins.
    """

    def __init__(self):
        super().__init__(
            name="Windowing & Spectral Leakage",
            description=(
                "Generate sine, cosine, or noise signals; apply Rectangular/Hamming/Hann/Blackman windows; "
                "compare original vs windowed signals in time and frequency domains; "
                "visualize spectral leakage using FFT magnitude spectra."
            ),
        )

        self._params = Lab5Params()
        self.results: Dict[str, Any] = {}

        self.parameters: Dict[str, Dict[str, Any]] = {
            "signal_type": {
                "type": "choice",
                "choices": [SignalType.SINUSOID.value, SignalType.COSINE.value, SignalType.NOISE.value],
                "default": self._params.signal_type,
                "value": self._params.signal_type,
                "label": "Signal Type",
            },
            "frequency_hz": {
                "type": "float",
                "min": 0.01,
                "max": 5000.0,
                "step": 0.1,
                "default": 0.01,
                "value": 0.01,
                "label": "Frequency (Hz)",
            },
            "amplitude": {
                "type": "float",
                "min": 0.0,
                "max": 5.0,
                "step": 0.01,
                "default": 0.0,
                "value": 0.0,
                "label": "Amplitude",
            },
            "sampling_rate_hz": {
                "type": "float",
                "min": 10.0,
                "max": 48000.0,
                "step": 10.0,
                "default": 10.0,
                "value": 10.0,
                "label": "Sampling Rate (Hz)",
            },
            "duration_s": {
                "type": "float",
                "min": 0.01,
                "max": 10.0,
                "step": 0.01,
                "default": 0.01,
                "value": 0.01,
                "label": "Duration (s)",
            },
            "phase_rad": {
                "type": "float",
                "min": -np.pi,
                "max": np.pi,
                "step": 0.01,
                "default": 0.0,
                "value": 0.0,
                "label": "Phase Shift (rad)",
            },
            "window_type": {
                "type": "choice",
                "choices": ["Rectangular", "Hamming", "Hann", "Blackman"],
                "default": self._params.window_type,
                "value": self._params.window_type,
                "label": "Window Function",
            },
        }

        self._time: Optional[np.ndarray] = None
        self._signal: Optional[np.ndarray] = None
        self._custom_sampling_rate: Optional[float] = None

        # Cached processed data for consistent get_frequency_domain access
        self._cached_fs: Optional[float] = None
        self._cached_windowed_signal: Optional[np.ndarray] = None
        self._cached_original_signal: Optional[np.ndarray] = None
        self._cached_window: Optional[np.ndarray] = None

    def setup(self) -> Dict[str, Any]:
        """Sync parameter values to internal state."""
        self._params.signal_type = str(self.parameters["signal_type"]["value"])
        self._params.frequency_hz = float(self.parameters["frequency_hz"]["value"])
        self._params.amplitude = float(self.parameters["amplitude"]["value"])
        self._params.sampling_rate_hz = float(self.parameters["sampling_rate_hz"]["value"])
        self._params.duration_s = float(self.parameters["duration_s"]["value"])
        self._params.phase_rad = float(self.parameters["phase_rad"]["value"])
        self._params.window_type = str(self.parameters["window_type"]["value"])
        return self.parameters

    def update_parameter(self, name: str, value: Any):
        """Update a parameter and sync internal state."""
        super().update_parameter(name, value)
        if name == "signal_type":
            self._params.signal_type = str(value)
        elif name == "frequency_hz":
            self._params.frequency_hz = float(value)
        elif name == "amplitude":
            self._params.amplitude = float(value)
        elif name == "sampling_rate_hz":
            self._params.sampling_rate_hz = float(value)
        elif name == "duration_s":
            self._params.duration_s = float(value)
        elif name == "phase_rad":
            self._params.phase_rad = float(value)
        elif name == "window_type":
            self._params.window_type = str(value)

    def set_signal(
        self,
        time_data: np.ndarray,
        signal_data: np.ndarray,
        sampling_rate: Optional[float] = None,
    ):
        """Optional hook to accept uploaded/custom signals via LabController."""
        if sampling_rate is not None:
            self._custom_sampling_rate = float(sampling_rate)
        self._time = np.asarray(time_data, dtype=np.float64) if time_data is not None else None
        sig = np.asarray(signal_data, dtype=np.float64)
        if sig.ndim > 1:
            sig = np.mean(sig, axis=1)
        self._signal = sig

    def _get_or_generate_signal(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """Get signal from custom input or generate from parameters."""
        # If custom signal provided via set_signal(), use it
        if self._signal is not None and self._time is not None:
            fs = self._custom_sampling_rate or self._params.sampling_rate_hz
            if len(self._time) != len(self._signal):
                n = len(self._signal)
                t = np.arange(n, dtype=np.float64) / fs
            else:
                t = self._time
            return t, self._signal, float(fs)

        # Generate from parameters
        sig_type = SignalType(self._params.signal_type)
        t, x = SignalProcessor.generate_signal(
            signal_type=sig_type,
            duration=float(self._params.duration_s),
            sampling_rate=float(self._params.sampling_rate_hz),
            frequency=float(self._params.frequency_hz),
            amplitude=float(self._params.amplitude),
            phase=float(self._params.phase_rad),
            noise_amplitude=0.0,
        )
        return t, x.astype(np.float64), float(self._params.sampling_rate_hz)

    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """Main processing: generate signal, apply window, compute spectra, store results.

        Returns:
            t: Time array
            xw: Windowed signal (for primary time-domain plot)
        """
        # Apply parameter overrides
        for k, v in kwargs.items():
            if k in self.parameters:
                self.update_parameter(k, v)

        # Get signal
        t, x, fs = self._get_or_generate_signal()
        n = len(x)

        # Ensure minimum length for stable FFT
        if n < 4:
            x = np.pad(x, (0, 4 - n), mode="constant")
            t = np.arange(len(x), dtype=np.float64) / fs
            n = len(x)

        # Generate window
        window = _make_window(self._params.window_type, n)

        # Apply window to signal
        xw = x * window

        # Cache for get_frequency_domain consistency
        self._cached_fs = float(fs)
        self._cached_original_signal = x.copy()
        self._cached_windowed_signal = xw.copy()
        self._cached_window = window.copy()

        # Coherent gain for amplitude correction
        coherent_gain = float(np.sum(window) / n) if n > 0 else 1.0

        # Compute single-sided FFT magnitudes for both original and windowed signals
        freqs, mag_orig = _compute_single_sided_fft(x, fs)
        _, mag_windowed = _compute_single_sided_fft(xw, fs)

        # Correct windowed magnitude by coherent gain for fair amplitude comparison
        mag_windowed_corrected = mag_windowed / coherent_gain if coherent_gain > 0 else mag_windowed

        # Spectral leakage analysis
        f0 = float(self._params.frequency_hz) if self._params.signal_type != SignalType.NOISE.value else 0.0
        bin_width = fs / n if n > 0 else 1.0
        bin_float = (f0 * n) / fs if fs > 0 else 0.0
        nearest_bin = int(np.round(bin_float))
        f_nearest = nearest_bin * bin_width if n > 0 else 0.0
        bin_offset = f0 - f_nearest

        # Leakage severity assessment
        if self._params.signal_type in {SignalType.SINUSOID.value, SignalType.COSINE.value}:
            if abs(bin_offset) < 0.01 * bin_width:
                leakage_status = "MINIMAL: Frequency aligns nearly with FFT bin. Rectangular window acceptable."
            else:
                leakage_status = "SIGNIFICANT: Frequency offset from nearest bin causes spectral leakage. Windowing reduces sidelobes."
            leakage_hint = (
                "Expected spectral leakage when the sinusoid frequency does not fall exactly on an FFT bin "
                "(i.e., f differs from k·fs/N). Windowing reduces sidelobes but typically widens the main lobe.\n"
                f"Offset: {bin_offset:.4f} Hz ({abs(bin_offset)/bin_width:.2f} bins)."
            )
        else:
            leakage_status = "N/A: Broadband noise energy spread across all frequencies."
            leakage_hint = "Noise has broadband energy, so leakage is inherently spread across frequencies."

        # Identify dominant frequencies for both spectra
        def _find_dominant(freqs_arr: np.ndarray, mag_arr: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
            """Find top K dominant frequencies (excluding DC)."""
            if len(freqs_arr) <= 1 or len(mag_arr) <= 1:
                return []
            idx = np.argsort(mag_arr[1:])[::-1] + 1
            idx = idx[:min(top_k, len(idx))]
            return [
                {"rank": i + 1, "frequency_hz": float(freqs_arr[j]), "magnitude": float(mag_arr[j])}
                for i, j in enumerate(idx)
            ]

        dom_orig = _find_dominant(freqs, mag_orig)
        dom_windowed = _find_dominant(freqs, mag_windowed_corrected)

        # Build display strings
        dom_orig_text = "\n".join(
            f"  #{d['rank']}: f = {d['frequency_hz']:.4g} Hz (mag = {d['magnitude']:.4g})"
            for d in dom_orig
        ) if dom_orig else "  No significant frequencies found"

        dom_windowed_text = "\n".join(
            f"  #{d['rank']}: f = {d['frequency_hz']:.4g} Hz (mag = {d['magnitude']:.4g})"
            for d in dom_windowed
        ) if dom_windowed else "  No significant frequencies found"

        # DFT Computation Info for Information Tab
        # Compute full complex FFT values for display
        X_orig_full = np.fft.fft(x)
        X_win_full = np.fft.fft(xw)

        def _format_fft_values(X: np.ndarray, max_show: int = 8) -> str:
            """Format FFT complex values for display."""
            lines = []
            N = len(X)
            for k in range(min(N, max_show)):
                real = X[k].real
                imag = X[k].imag
                if abs(imag) < 1e-10:
                    lines.append(f"  X[{k}] = {real:.6g}")
                else:
                    sign = "+" if imag >= 0 else "-"
                    lines.append(f"  X[{k}] = {real:.6g} {sign} {abs(imag):.6g}j")
            if N > max_show:
                lines.append(f"  ... ({N - max_show} more values)")
            return "\n".join(lines)

        dft_orig_display = _format_fft_values(X_orig_full)
        dft_win_display = _format_fft_values(X_win_full)

        dft_computation_text = (
            f"DFT Computation using np.fft.fft\n"
            f"{'='*50}\n\n"
            f"Original Signal x[n]:\n"
            f"  N = {n} samples\n"
            f"  x = [{', '.join(f'{v:.4g}' for v in x[:min(n, 8)])}"
            f"{'...' if n > 8 else ''}]\n\n"
            f"Windowed Signal xw[n] = x[n] · w[n]:\n"
            f"  Window: {self._params.window_type}\n"
            f"  w = [{', '.join(f'{v:.4g}' for v in window[:min(n, 8)])}"
            f"{'...' if n > 8 else ''}]\n"
            f"  xw = [{', '.join(f'{v:.4g}' for v in xw[:min(n, 8)])}"
            f"{'...' if n > 8 else ''}]\n\n"
            f"DFT of Original Signal (np.fft.fft(x)):\n"
            f"{dft_orig_display}\n\n"
            f"DFT of Windowed Signal (np.fft.fft(xw)):\n"
            f"{dft_win_display}\n\n"
            f"Single-Sided Magnitude Computation:\n"
            f"  mag = |X[k]| / N  (for k = 0 to N/2 - 1)\n"
            f"  mag[k>0] *= 2  (energy preservation for real signals)\n"
            f"  freqs = np.fft.rfftfreq(N, d=1/fs)[:-1]\n\n"
            f"Frequency Resolution: Δf = fs/N = {bin_width:.6g} Hz"
        )

        # Explanation text
        explanation_lines = [
            f"Signal: {self._params.signal_type}, f₀ = {f0:.4g} Hz, A = {self._params.amplitude:.4g}",
            f"Sampling: fs = {fs:.4g} Hz, duration = {self._params.duration_s:.4g} s, N = {n} samples",
            f"Frequency Resolution: Δf = fs/N = {bin_width:.6g} Hz",
            f"Window: {self._params.window_type} (coherent gain = {coherent_gain:.4f})",
            f"Leakage Status: {leakage_status}",
            "Window Effects:",
            "- Rectangular: No tapering, best frequency resolution, highest sidelobes (-13 dB)",
            "- Hamming: Moderate tapering, good resolution, reduced sidelobes (-43 dB)",
            "- Hann: Stronger tapering, wider main lobe, lower sidelobes (-31 dB)",
            "- Blackman: Strongest tapering, widest main lobe, lowest sidelobes (-58 dB)",
            f"Top Dominant Frequencies (Original):\n{dom_orig_text}",
            f"Top Dominant Frequencies (Windowed):\n{dom_windowed_text}",
        ]
        explanation = "\n".join(explanation_lines)

        # Store comprehensive results
        self.results = {
            "signal": {
                "type": self._params.signal_type,
                "frequency_hz": float(self._params.frequency_hz),
                "amplitude": float(self._params.amplitude),
                "sampling_rate_hz": float(fs),
                "duration_s": float(self._params.duration_s),
                "phase_rad": float(self._params.phase_rad),
                "n_samples": int(n),
            },
            "window": {
                "type": self._params.window_type,
                "coherent_gain": coherent_gain,
                "vector": window.tolist(),
            },
            "time_domain": {
                "time": t.tolist(),
                "original": x.tolist(),
                "windowed": xw.tolist(),
                "window_shape": window.tolist(),
            },
            "spectra": {
                "frequencies_hz": freqs.tolist(),
                "magnitude_original": mag_orig.tolist(),
                "magnitude_windowed": mag_windowed.tolist(),
                "magnitude_windowed_corrected": mag_windowed_corrected.tolist(),
            },
            "dominant_frequencies": {
                "original": dom_orig,
                "windowed": dom_windowed,
            },
            "dft_computation": {
                "original_fft_values": X_orig_full.tolist(),
                "windowed_fft_values": X_win_full.tolist(),
                "original_fft_display": dft_orig_display,
                "windowed_fft_display": dft_win_display,
                "dft_info_text": dft_computation_text,
                "n_samples": n,
                "computation_method": "np.fft.fft",
            },
            "fft_visualization": {
                "frequency_resolution_hz": bin_width,
                "leakage_hint": leakage_hint,
                "leakage_status": leakage_status,
                "nearest_bin": int(nearest_bin),
                "nearest_bin_frequency_hz": float(f_nearest),
                "bin_offset_hz": float(bin_offset),
                "bins_off_center": float(abs(bin_offset) / bin_width) if bin_width > 0 else 0.0,
            },
            "display": {
                "title": f"Windowing: {self._params.window_type} on {self._params.signal_type}",
                "explanation": explanation,
                "formula": "Xw[n] = x[n] · w[n]",
                "leakage_status": leakage_status,
                "efficiency": f"N = {n}, Δf = {bin_width:.6g} Hz",
                "dft_computation": dft_computation_text,
            },
            "final_answer": (
                f"Windowing Analysis: {self._params.window_type}\n\n"
                f"Signal: {self._params.signal_type}, f₀ = {f0:.4g} Hz, A = {self._params.amplitude:.4g}\n"
                f"Sampling: fs = {fs:.4g} Hz, N = {n}, Δf = {bin_width:.6g} Hz\n\n"
                f"Leakage Status: {leakage_status}\n\n"
                f"Top Dominant (Original):\n{dom_orig_text}\n\n"
                f"Top Dominant (Windowed):\n{dom_windowed_text}\n\n"
                f"Window Effects: {self._params.window_type} window applied with coherent gain = {coherent_gain:.4f}"
            ),
            "freq_domain_plot": {
                "frequencies": freqs.tolist(),
                "magnitude_original": mag_orig.tolist(),
                "magnitude_windowed": mag_windowed.tolist(),
                "magnitude_windowed_corrected": mag_windowed_corrected.tolist(),
                "nyquist_hz": fs / 2,
                "bin_width_hz": bin_width,
            },
        }

        # Return windowed signal for primary time-domain plot
        return t, xw

    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """Return windowed spectrum magnitude for frequency-domain tab.

        Uses cached data when available to maintain consistency with process().
        Applies coherent gain correction for accurate amplitude representation.
        """
        # Prefer cached data to maintain consistency
        if (self._cached_windowed_signal is not None and 
            self._cached_fs is not None and 
            abs(float(sampling_rate) - self._cached_fs) < 0.001):
            xw = self._cached_windowed_signal
            fs = self._cached_fs
        else:
            # Fallback: recompute if cache miss
            x = np.asarray(signal, dtype=np.float64)
            n = len(x)
            fs = float(sampling_rate)
            window = _make_window(self._params.window_type, n)
            xw = x * window

        # Compute single-sided spectrum
        freqs, mag = _compute_single_sided_fft(xw, fs)

        # Apply coherent gain correction
        n = len(xw)
        window = _make_window(self._params.window_type, n)
        coherent_gain = float(np.sum(window) / n) if n > 0 else 1.0
        mag_corrected = mag / coherent_gain if coherent_gain > 0 else mag

        return freqs, mag_corrected

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }