"""labs.lab4_fft

Lab 4: DFT and FFT Spectral Analysis

Rubric Requirements:
1. Compute DFT and FFT
2. Convert time-domain signals to frequency domain
3. Display magnitude spectra
4. Identify dominant frequencies
5. Compare DFT vs FFT outputs and efficiencies
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import time
import numpy as np

from .base_lab import BaseLab


def _compute_dft(x: np.ndarray) -> np.ndarray:
    """Compute Discrete Fourier Transform directly using the DFT formula."""
    N = len(x)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        for n in range(N):
            X[k] += x[n] * np.exp(-2j * np.pi * k * n / N)
    return X


def _compute_fft(x: np.ndarray) -> np.ndarray:
    """Compute Fast Fourier Transform using numpy's optimized FFT."""
    return np.fft.fft(x)


def _get_single_sided_magnitude(X: np.ndarray) -> np.ndarray:
    """Return single-sided magnitude spectrum for a real-valued time signal."""
    N = len(X)
    mag = np.abs(X) / N
    half = N // 2
    mag_single = mag[:half]
    if len(mag_single) > 1:
        mag_single[1:] *= 2
    return mag_single


def _get_single_sided_freqs(N: int, sampling_rate_hz: float) -> np.ndarray:
    """Single-sided frequency bins in Hz matching single-sided spectrum."""
    if sampling_rate_hz <= 0:
        sampling_rate_hz = 1000.0
    if N <= 0:
        return np.array([], dtype=float)
    return np.fft.rfftfreq(N, d=1.0 / sampling_rate_hz)[:-1]  # drop Nyquist to match [:N//2]


def _identify_dominant(freqs: np.ndarray, mag: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
    """Identify top K dominant frequencies."""
    if len(freqs) == 0 or len(mag) == 0:
        return []

    # Exclude DC (0 Hz)
    if len(mag) <= 1:
        return []

    idx = np.argsort(mag[1:])[::-1] + 1
    idx = idx[: min(top_k, len(idx))]

    return [
        {"rank": i + 1, "frequency_hz": float(freqs[j]), "magnitude": float(mag[j])}
        for i, j in enumerate(idx)
    ]


class Lab4FFT(BaseLab):
    """DFT/FFT spectral analysis lab.
    
    Visualizes the frequency domain representation of discrete signals using:
    - Stem plot: Shows FFT magnitude at discrete frequency bins (blue vertical stems)
    - Overlay scatter: Shows DFT magnitude for direct comparison (green points)
    
    Both DFT and FFT compute the same result, but FFT is much faster for large signals.
    Dominant frequencies are identified and ranked by magnitude.
    """

    def __init__(self):
        super().__init__(
            name="DFT & FFT Spectral Analysis",
            description=(
                "Compute DFT and FFT, convert signals to frequency domain, display magnitude spectra, "
                "identify dominant frequencies, and compare DFT vs FFT efficiency."
            ),
        )

        self._sequence_text: str = "1 2 3 4"
        self._sampling_rate_hz: float = 1000.0

        self.parameters = {
            "sequence": {
                "type": "text",
                "default": "",
                "value": "",
                "label": "x(n) sequence (space-separated values)",
            },
            "sampling_rate_hz": {
                "type": "number",
                "default": 1000.0,
                "value": 1000.0,
                "label": "Sampling rate (Hz) [for frequency axis]",
                "min": 0.000001,
                "max": 1e6,
                "step": 0.1,
            },
        }

        self.results: Dict[str, Any] = {}

    def setup(self) -> Dict[str, Any]:
        self._sequence_text = str(self.parameters["sequence"]["value"])
        self._sampling_rate_hz = float(self.parameters["sampling_rate_hz"]["value"])
        return self.parameters

    def update_parameter(self, name: str, value: Any):
        super().update_parameter(name, value)
        if name == "sequence":
            self._sequence_text = str(value)
        elif name == "sampling_rate_hz":
            self._sampling_rate_hz = float(value)

    def _parse_sequence(self) -> np.ndarray:
        try:
            tokens = self._sequence_text.strip().split()
            if not tokens:
                return np.array([0.0], dtype=float)
            return np.array([float(t) for t in tokens], dtype=float)
        except ValueError:
            return np.array([0.0], dtype=float)

    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        for k, v in kwargs.items():
            if k in self.parameters:
                self.update_parameter(k, v)

        x = self._parse_sequence()
        top_k = 3
        N = len(x)

        fs = float(self.parameters.get("sampling_rate_hz", {}).get("value", self._sampling_rate_hz))
        if fs <= 0.0:
            fs = 1000.0

        t = np.arange(N)

        # DFT
        dft_t0 = time.perf_counter()
        X_dft = _compute_dft(x)
        dft_t1 = time.perf_counter()
        dft_time = dft_t1 - dft_t0

        # FFT
        fft_t0 = time.perf_counter()
        X_fft = _compute_fft(x)
        fft_t1 = time.perf_counter()
        fft_time = fft_t1 - fft_t0

        # Single-sided spectra (used by UI)
        freqs = _get_single_sided_freqs(N, fs)
        mag_dft = _get_single_sided_magnitude(X_dft)
        mag_fft = _get_single_sided_magnitude(X_fft)

        # Dominant frequencies
        dom_dft = _identify_dominant(freqs, mag_dft, top_k)
        dom_fft = _identify_dominant(freqs, mag_fft, top_k)

        # Efficiency comparison
        speedup = (dft_time / fft_time) if fft_time > 0 else float("inf")
        mse = float(np.mean((mag_dft - mag_fft) ** 2))

        # Two-sided (for completeness / optional plotting elsewhere)
        N_pad = max(2, N * 8)
        X_dft_pad = np.fft.fft(x, n=N_pad)
        X_fft_pad = np.fft.fft(x, n=N_pad)

        freqs_full = np.fft.fftfreq(N_pad, d=1.0 / fs)
        freqs_shifted = np.fft.fftshift(freqs_full)
        mag_dft_shifted = np.fft.fftshift(np.abs(X_dft_pad) / N_pad)
        mag_fft_shifted = np.fft.fftshift(np.abs(X_fft_pad) / N_pad)

        # Text displays of X[k]
        xn_set = "{" + ", ".join(f"{v:.4g}" for v in x) + "}"

        def _format_complex_list(X: np.ndarray) -> str:
            lines: List[str] = []
            for k in range(min(N, 8)):
                real = X[k].real
                imag = X[k].imag
                if abs(imag) < 1e-10:
                    lines.append(f"X[{k}] = {real:.4g}")
                else:
                    lines.append(f"X[{k}] = {real:.4g} + {imag:.4g}j")
            if N > 8:
                lines.append(f"... ({N - 8} more values)")
            return "\n".join(lines)

        dft_display = _format_complex_list(X_dft)
        fft_display = _format_complex_list(X_fft)

        dom_text = "\n".join(
            f"  #{d['rank']}: f = {d['frequency_hz']:.4g} Hz (mag = {d['magnitude']:.4g})" for d in dom_fft
        )

        explanation_lines = [
            f"Given the discrete sequence x(n) = {xn_set} with N = {N} samples.",
            "",
            "The Discrete Fourier Transform (DFT) is defined as:",
            "    X[k] = Σₙ₌₀^(N-1) x[n] · e^(-j·2π·k·n/N)",
            "",
            "The Fast Fourier Transform (FFT) is an optimized algorithm",
            "that computes the same result as DFT but much faster.",
            "",
            f"DFT Computation Time: {dft_time*1000:.4f} ms",
            f"FFT Computation Time: {fft_time*1000:.4f} ms",
            f"FFT Speedup: {speedup:.2f}x faster",
            "",
            f"Magnitude MSE (DFT vs FFT): {mse:.2e}",
            "",
            f"Frequency Resolution (bin width): Δf = fs/N = {fs/N:.4g} Hz",
            "",
            f"Top {top_k} Dominant Frequencies:",
            dom_text if dom_text else "  No significant frequencies found",
        ]

        explanation = "\n".join(explanation_lines)

        xz_terms = []
        for n, val in enumerate(x):
            xz_terms.append(f"{val:.4g}" if n == 0 else f"{val:.4g}z⁻{n}")
        xz_expr = "X(z) = " + " + ".join(xz_terms)

        self.results = {
            "dft": {
                "values": X_dft.tolist(),
                "magnitude": mag_dft.tolist(),
                "frequencies": freqs.tolist(),
                "computation_time_ms": dft_time * 1000,
            },
            "fft": {
                "values": X_fft.tolist(),
                "magnitude": mag_fft.tolist(),
                "frequencies": freqs.tolist(),
                "computation_time_ms": fft_time * 1000,
            },
            "dominant_frequencies": dom_fft,
            "efficiency": {
                "dft_time_ms": dft_time * 1000,
                "fft_time_ms": fft_time * 1000,
                "speedup": speedup,
                "mse_dft_vs_fft": mse,
            },
            "display": {
                "title": f"DFT & FFT of x(n) = {xn_set}",
                "xz": xz_expr,
                "dft_result": dft_display,
                "fft_result": fft_display,
                "formula": "X[k] = Σₙ₌₀^(N-1) x[n] · e^(-j·2π·k·n/N)",
                "dominant": f"Top {top_k} Dominant Frequencies:\n{dom_text}" if dom_text else "No dominant frequencies",
                "efficiency": f"DFT: {dft_time*1000:.4f} ms | FFT: {fft_time*1000:.4f} ms | Speedup: {speedup:.2f}x",
                "explanation": explanation,
            },
            "final_answer": (
                f"DFT & FFT of x(n) = {xn_set}\n\n"
                f"DFT Result:\n{dft_display}\n\n"
                f"FFT Result:\n{fft_display}\n\n"
                f"Top {top_k} Dominant Frequencies:\n{dom_text}\n\n"
                f"Efficiency Comparison:\n"
                f"  DFT Time: {dft_time*1000:.4f} ms\n"
                f"  FFT Time: {fft_time*1000:.4f} ms\n"
                f"  Speedup: {speedup:.2f}x"
            ),
            "freq_domain_plot": {
                "frequencies": freqs_shifted.tolist(),
                "dft_magnitude": mag_dft_shifted.tolist(),
                "fft_magnitude": mag_fft_shifted.tolist(),
            },
        }

        return t, x

    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """Return FFT magnitude spectrum for generic frequency-domain plotting."""
        if signal is None or len(signal) == 0:
            return np.array([], dtype=float), np.array([], dtype=float)

        X = np.fft.fft(signal)
        N = len(X)
        fs = float(sampling_rate)
        if fs <= 0.0:
            fs = 1000.0

        N_pad = max(2, N * 8)
        X_pad = np.fft.fft(signal, n=N_pad)
        freqs_full = np.fft.fftfreq(N_pad, d=1.0 / fs)
        mag = np.abs(X_pad) / N_pad

        freqs_shifted = np.fft.fftshift(freqs_full)
        mag_shifted = np.fft.fftshift(mag)
        return freqs_shifted, mag_shifted

    def get_info(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description, "parameters": self.parameters}
