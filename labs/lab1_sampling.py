# labs/lab1_sampling.py
"""
Lab 1: Sampling Theory and Aliasing Demonstration
"""
import numpy as np
from typing import Dict, Any, Tuple

from .base_lab import BaseLab


class Lab1Sampling(BaseLab):
    """Sampling Theory and Aliasing (Lab 1)

    Demonstrates:
    - Continuous-time x(t)=cos(2π f t) with user-defined time range.
    - Sampling with user-defined fs (Nyquist satisfied vs undersampled aliasing).
    - Optional discrete-time cosine sequences with stem-style visualization data.
    """

    def __init__(self):
        super().__init__(
            name="Sampling & Aliasing",
            description=(
                "Interactive sampling simulation demonstrating Nyquist theorem, aliasing, and optional discrete-time sequences. "
                "Continuous signal: x(t)=cos(2π f t)."
            ),
        )
        self.setup()

    def setup(self) -> Dict[str, Any]:
        self.parameters = {
            'signal_frequency': {
                'type': 'float',
                'min': 1.0,
                'max': 10000.0,
                'default': 10.0,
                'value': 10.0,
                'label': 'Signal Frequency f (Hz)'
            },
            'sampling_rate': {
                'type': 'float',
                'min': 1.0,
                'max': 10000.0,
                'default': 100.0,
                'value': 100.0,
                'label': 'Sampling Frequency fs (Hz)'
            },
        }
        return self.parameters

    @staticmethod
    def _wrap_alias_frequency(f: float, fs: float) -> float:
        """Fold frequency into [0, fs/2] using aliasing periodicity."""
        if fs <= 0:
            return 0.0
        f_mod = f % fs
        if f_mod > fs / 2:
            f_mod = fs - f_mod
        return float(f_mod)

    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        # Update parameters from kwargs
        for key, value in kwargs.items():
            if key in self.parameters:
                self.update_parameter(key, value)

        f  = float(self.get_parameter('signal_frequency'))
        fs = float(self.get_parameter('sampling_rate'))

        # Clamp to allowed range
        f  = np.clip(f,  0.0, 10000.0)
        fs = np.clip(fs, 1.0, 10000.0)

        A = 1.0

        # ── Log-scaled cycles to show ──────────────────────────────────────
        # Cycles double for every 10× increase in frequency:
        #   10 Hz → 10 cycles, 100 Hz → 20, 1000 Hz → 40, 10000 Hz → 80
        # Formula: NUM_CYCLES = 10 × 2^(log10(f / 10))
        if f >= 1.0:
            NUM_CYCLES = 10.0 * 2.0 ** (np.log10(f / 10.0))
        else:
            NUM_CYCLES = 5.0            # near-zero: just show a few periods

        if f > 0:
            T = NUM_CYCLES / f
        else:
            T = NUM_CYCLES / fs

        # ── Continuous signal ──────────────────────────────────────────────
        # Always use 1 000 000 points spread over T so we get maximum
        # density per cycle regardless of how long or short T is.
        CONT_PTS = 1_000_000
        t_cont = np.linspace(0.0, T, CONT_PTS, endpoint=False)
        x_cont = A * np.cos(2.0 * np.pi * f * t_cont)

        # ── Sampled signal ─────────────────────────────────────────────────
        # Number of samples that fall inside the window T at rate fs.
        n_samp = max(2, round(fs * T))
        ts     = np.linspace(0.0, T, n_samp, endpoint=False)
        x_samp = A * np.cos(2.0 * np.pi * f * ts)

        # ── Nyquist evaluation ─────────────────────────────────────────────
        nyquist    = fs / 2.0
        is_aliased = f > nyquist
        f_alias    = self._wrap_alias_frequency(f, fs)

        # Store full results for UI result panel
        self.results = {
            'continuous':        (t_cont, x_cont),
            'sampled':           (ts, x_samp),
            'sampling_rate':     fs,
            'nyquist_frequency': nyquist,
            'signal_frequency':  f,
            'aliased_frequency': f_alias,
            'is_aliased':        is_aliased,
        }

        return ts.astype(float), x_samp.astype(float)

    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        from core.fft import FFTProcessor
        frequencies, magnitude = FFTProcessor.compute_fft(signal, sampling_rate)
        return frequencies, magnitude
