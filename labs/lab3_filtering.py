"""labs.lab3_filtering

This file is used by the Qt-based DSP app (see controller/lab_controller.py).
The app expects a class named `Lab3Filtering` implementing the `BaseLab` API.

The original project also contained a standalone Tkinter app. That code is
preserved below (as ButterworthAudioFilterApp), but the DSP app integration is
provided by the `Lab3Filtering` wrapper class.
"""

from __future__ import annotations

import numpy as np
import os
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from scipy.signal import butter, filtfilt

from labs.base_lab import BaseLab


def _normalize_audio_for_wav(x: np.ndarray) -> np.ndarray:
    """Convert arbitrary float signal to int16-safe range for WAV export."""
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return x.astype(np.int16)

    peak = float(np.max(np.abs(x)))
    if peak <= 0:
        return np.zeros_like(x, dtype=np.int16)

    # Scale to full int16 range
    y = x / peak
    y = np.clip(y, -1.0, 1.0)
    return (y * np.iinfo(np.int16).max).astype(np.int16)


def _write_wav_int16(path: str, audio_int16: np.ndarray, fs: float) -> None:
    """Write int16 mono audio to WAV using scipy."""
    from scipy.io import wavfile

    fs_i = int(round(float(fs)))
    wavfile.write(path, fs_i, audio_int16)



class FilterType(Enum):
    ORIGINAL = "Original"
    LOWPASS = "Low-pass"
    HIGHPASS = "High-pass"
    BANDPASS = "Band-pass"
    BANDSTOP = "Band-stop"


@dataclass
class FilterParameters:
    filter_type: str = "Original"
    filter_order: int = 4
    lowpass_cutoff: float = 3000.0
    highpass_cutoff: float = 300.0
    band_low_cutoff: float = 500.0
    band_high_cutoff: float = 5000.0


def butter_filter(data: np.ndarray, cutoff, fs: float, filter_type: str, order: int = 4) -> np.ndarray:
    nyquist = 0.5 * fs

    if isinstance(cutoff, (list, tuple)):
        normal_cutoff = [c / nyquist for c in cutoff]
    else:
        normal_cutoff = cutoff / nyquist

    if isinstance(normal_cutoff, list):
        normal_cutoff = [max(0.001, min(0.999, c)) for c in normal_cutoff]
    else:
        normal_cutoff = max(0.001, min(0.999, float(normal_cutoff)))

    b, a = butter(order, normal_cutoff, btype=filter_type)
    return filtfilt(b, a, data)


def get_filter_cutoffs(params: FilterParameters, fs: float) -> Dict[str, Any]:
    nyquist = fs / 2.0

    lowpass_cutoff = min(params.lowpass_cutoff, nyquist * 0.99)
    highpass_cutoff = min(params.highpass_cutoff, nyquist * 0.99)
    band_low = min(params.band_low_cutoff, nyquist * 0.99)
    band_high = min(params.band_high_cutoff, nyquist * 0.99)

    if band_low >= band_high:
        band_low = band_high * 0.5

    return {
        "lowpass": lowpass_cutoff,
        "highpass": highpass_cutoff,
        "bandpass": (band_low, band_high),
        "bandstop": (band_low, band_high),
    }


class Lab3Filtering(BaseLab):
    """Butterworth audio filtering lab integrated with the Qt app."""


    def __init__(self):
        super().__init__(
            name="Convolution & System Response (Butterworth Filtering)",
            description=(
                "Applies Butterworth low-pass/high-pass/band-pass/band-stop filters "
                "to an input signal and displays time/frequency results. "
                "(Integrated wrapper for the standalone Lab 3 filtering code.)"
            ),
        )

        self._params = FilterParameters()
        self._fs: float = 44100.0
        self.results: Dict[str, Any] = {}

        # UI expects a dict of parameter metadata, including at least:
        # - type: float/int/bool/choice/list
        # - min/max/step/default for sliders/spinboxes
        # - choices for choice
        self.parameters = {
            "filter_type": {
                "type": "choice",
                "choices": ["Original", "Low-pass", "High-pass", "Band-pass", "Band-stop"],
                "default": "Original",
                "value": self._params.filter_type,
                "label": "Select Filter",
            },
            "filter_order": {
                "type": "int",
                "min": 2,
                "max": 8,
                "step": 1,
                "default": 2,
                "value": 2,
                "label": "Filter Order",
            },
            "lowpass_cutoff": {
                "type": "float",
                "min": 20,
                "max": 20000,
                "step": 100,
                "default": 20.0,
                "value": 20.0,
                "label": "Low-pass Cutoff (Hz)",
            },
            "highpass_cutoff": {
                "type": "float",
                "min": 20,
                "max": 20000,
                "step": 100,
                "default": 20.0,
                "value": 20.0,
                "label": "High-pass Cutoff (Hz)",
            },
            "band_low_cutoff": {
                "type": "float",
                "min": 20,
                "max": 20000,
                "step": 100,
                "default": 20.0,
                "value": 20.0,
                "label": "Band-pass/stop Low Cutoff (Hz)",
            },
            "band_high_cutoff": {
                "type": "float",
                "min": 20,
                "max": 20000,
                "step": 100,
                "default": 20.0,
                "value": 20.0,
                "label": "Band-pass/stop High Cutoff (Hz)",
            },
        }

    def setup(self) -> Dict[str, Any]:
        # Sync values from self.parameters into the dataclass
        self._params.filter_type = self.parameters["filter_type"]["value"]
        self._params.filter_order = int(self.parameters["filter_order"]["value"])
        self._params.lowpass_cutoff = float(self.parameters["lowpass_cutoff"]["value"])
        self._params.highpass_cutoff = float(self.parameters["highpass_cutoff"]["value"])
        self._params.band_low_cutoff = float(self.parameters["band_low_cutoff"]["value"])
        self._params.band_high_cutoff = float(self.parameters["band_high_cutoff"]["value"])
        return self.parameters

    def update_parameter(self, name: str, value: Any):
        super().update_parameter(name, value)
        if name == "filter_type":
            self._params.filter_type = str(value)
        elif name == "filter_order":
            self._params.filter_order = int(value)
        elif name == "lowpass_cutoff":
            self._params.lowpass_cutoff = float(value)
        elif name == "highpass_cutoff":
            self._params.highpass_cutoff = float(value)
        elif name == "band_low_cutoff":
            self._params.band_low_cutoff = float(value)
        elif name == "band_high_cutoff":
            self._params.band_high_cutoff = float(value)

    def set_signal(self, time_data: np.ndarray, signal_data: np.ndarray, sampling_rate: Optional[float] = None):
        # Called by LabController when a file is loaded
        if sampling_rate is not None:
            self._fs = float(sampling_rate)
        self._time = np.asarray(time_data)
        # mono
        sig = np.asarray(signal_data)
        if sig.ndim > 1:
            sig = np.mean(sig, axis=1)
        self._signal = sig

    def _get_current_signal_and_time(self) -> Tuple[np.ndarray, np.ndarray]:
        # If set_signal not used, synthesize a simple test tone so lab can run.
        if hasattr(self, "_signal") and hasattr(self, "_time"):
            return self._time, self._signal

        self._fs = 44100.0
        t = np.linspace(0, 1.0, int(self._fs), endpoint=False)
        # Two-tone mixture
        x = 0.6 * np.sin(2 * np.pi * 200 * t) + 0.4 * np.sin(2 * np.pi * 3000 * t)
        return t, x

    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        # Apply any parameter overrides from LabController
        for k, v in kwargs.items():
            if k in self.parameters:
                self.update_parameter(k, v)

        time_data, signal = self._get_current_signal_and_time()

        fs = float(self._fs)
        cutoffs = get_filter_cutoffs(self._params, fs)
        order = int(self._params.filter_order)

        filtered = {
            "original": signal.copy(),
            "lowpass": butter_filter(signal, cutoffs["lowpass"], fs, "low", order=order),
            "highpass": butter_filter(signal, cutoffs["highpass"], fs, "high", order=order),
            "bandpass": butter_filter(signal, cutoffs["bandpass"], fs, "band", order=order),
            "bandstop": butter_filter(signal, cutoffs["bandstop"], fs, "bandstop", order=order),
        }

        selected = self._params.filter_type
        key_map = {
            "Original": "original",
            "Low-pass": "lowpass",
            "High-pass": "highpass",
            "Band-pass": "bandpass",
            "Band-stop": "bandstop",
        }
        out_key = key_map.get(selected, "original")

        # Export all filtered signals as WAV so the UI can play/download them.
        # AudioPlayer calls a download() method that copies the file to a user-chosen location.
        out_dir = os.path.join(os.path.dirname(__file__), "..", "filtered_audio")
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir, exist_ok=True)

        def build_path(filter_key: str) -> str:
            return os.path.join(out_dir, f"lab3_{filter_key}_{int(fs)}Hz.wav")

        filtered_files = {}
        for filter_key, sig in filtered.items():
            # sig is float; convert to int16 and write wav
            audio_int16 = _normalize_audio_for_wav(sig)
            out_path = build_path(filter_key)
            try:
                # Ensure the output directory exists even if relative paths change
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                _write_wav_int16(out_path, audio_int16, fs)
                filtered_files[filter_key] = {"path": out_path}
            except Exception as e:
                warnings.warn(f"Failed to write WAV for {filter_key}: {e}")


        # Store results in the shape LabContainer expects for Lab 3
        self.results = {
            "fs": fs,
            "cutoffs": {
                "lowpass": cutoffs["lowpass"],
                "highpass": cutoffs["highpass"],
                "bandpass": cutoffs["bandpass"],
                "bandstop": cutoffs["bandstop"],
            },
            "filtered_files": filtered_files,
        }

        return time_data, filtered[out_key]


    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        x = np.asarray(signal)
        x = x if x.ndim == 1 else np.mean(x, axis=1)
        n = len(x)
        yf = np.fft.fft(x)
        xf = np.fft.fftfreq(n, d=1.0 / float(sampling_rate))

        pos = xf >= 0
        xf = xf[pos]
        mag = np.abs(yf[pos]) / n
        if len(mag) > 2:
            mag[1:-1] *= 2
        return xf, mag

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


# -----------------------------------------------------------------------------
# Original standalone Tkinter app code (optional). Left out intentionally to
# avoid mixing Tkinter/Qt implementations inside the lab module.
# If you still need it, it can be restored into a separate file.
# -----------------------------------------------------------------------------

