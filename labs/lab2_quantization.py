"""labs.lab2_quantization


Lab 2 (Remodeled): CONVOLUTION IMAGE PROCESSING

Implements image filtering operators and provides 3 outputs while allowing
UI to preview/download only one at a time.

The Qt app expects a Lab class named `Lab2Quantization` implementing the
`BaseLab` interface.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple, List

import numpy as np

from labs.base_lab import BaseLab


class ImageOperator(str, Enum):
    ORIGINAL = "Original"
    AVERAGE_BLUR = "Average Blur"
    GAUSSIAN_BLUR = "Gaussian Blur"
    MEDIAN_BLUR = "Median Blur"
    IMAGE_SHARPENING = "Image Sharpening"
    SOBEL_X = "Sobel Operator X direction"
    SOBEL_Y = "Sobel Operator Y direction"
    SOBEL_X_AND_Y = "Combined X AND Y"
    PREWITT = "Prewitt Operator"
    LAPLACIAN = "Laplacian Operator"


@dataclass
class Lab2Params:
    operator: str = ImageOperator.ORIGINAL.value
    kernel_size: int = 3  # used for blurs/filters


def _ensure_uint8(img: np.ndarray) -> np.ndarray:
    img = np.asarray(img)
    if img.dtype == np.uint8:
        return img
    img = img.astype(np.float32)
    img_min = float(np.min(img)) if img.size else 0.0
    img_max = float(np.max(img)) if img.size else 1.0
    if img_max - img_min < 1e-12:
        return np.zeros_like(img, dtype=np.uint8)
    norm = (img - img_min) / (img_max - img_min)
    norm = np.clip(norm, 0.0, 1.0)
    return (norm * 255.0).astype(np.uint8)


def _rgb_to_gray_uint8(img: np.ndarray) -> np.ndarray:
    # OpenCV loads BGR; we handle generic RGB-like arrays.
    img = np.asarray(img)
    if img.ndim == 2:
        return _ensure_uint8(img)
    if img.ndim == 3 and img.shape[2] >= 3:
        r = img[..., 0].astype(np.float32)
        g = img[..., 1].astype(np.float32)
        b = img[..., 2].astype(np.float32)
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        return _ensure_uint8(gray)
    # Fallback
    return _ensure_uint8(img[..., 0])


def _to_float01(img_u8: np.ndarray) -> np.ndarray:
    img_u8 = _ensure_uint8(img_u8)
    return img_u8.astype(np.float32) / 255.0


def _edge_magnitude(dx: np.ndarray, dy: np.ndarray) -> np.ndarray:
    mag = np.sqrt(np.square(dx.astype(np.float32)) + np.square(dy.astype(np.float32)))
    return _ensure_uint8(mag)


def _save_image(path: str, img_u8: np.ndarray) -> None:
    import cv2

    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img_u8)


def _load_image(path: str) -> np.ndarray:
    import cv2

    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to load image: {path}")
    # If image has alpha, drop it.
    if img.ndim == 3 and img.shape[2] > 3:
        img = img[..., :3]
    return img


def _blur_average(img_u8: np.ndarray, k: int) -> np.ndarray:
    import cv2

    kk = max(1, int(k))
    if kk % 2 == 0:
        kk += 1
    return cv2.blur(img_u8, (kk, kk))


def _blur_gaussian(img_u8: np.ndarray, k: int) -> np.ndarray:
    import cv2

    kk = max(1, int(k))
    if kk % 2 == 0:
        kk += 1
    return cv2.GaussianBlur(img_u8, (kk, kk), 0)


def _blur_median(img_u8: np.ndarray, k: int) -> np.ndarray:
    import cv2

    kk = max(1, int(k))
    if kk % 2 == 0:
        kk += 1
    # medianBlur works on 1-channel or 3-channel uint8
    return cv2.medianBlur(img_u8, kk)


def _sharpen(img_u8: np.ndarray) -> np.ndarray:
    # Simple unsharp mask kernel using OpenCV filter2D
    import cv2

    kernel = np.array(
        [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
        dtype=np.float32,
    )
    out = cv2.filter2D(img_u8, ddepth=-1, kernel=kernel)
    return _ensure_uint8(out)


def _sobel(gray_u8: np.ndarray, dx: int, dy: int, ksize: int = 3) -> np.ndarray:
    import cv2

    k = max(1, int(ksize))
    if k % 2 == 0:
        k += 1
    out = cv2.Sobel(gray_u8, ddepth=cv2.CV_32F, dx=dx, dy=dy, ksize=k)
    return out


def _prewitt(gray_u8: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    # Prewitt kernels
    px = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float32)
    py = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float32)

    import cv2

    dx = cv2.filter2D(gray_u8.astype(np.float32), ddepth=-1, kernel=px)
    dy = cv2.filter2D(gray_u8.astype(np.float32), ddepth=-1, kernel=py)
    return dx, dy


def _laplacian(gray_u8: np.ndarray, ksize: int = 3) -> np.ndarray:
    import cv2

    k = max(1, int(ksize))
    if k % 2 == 0:
        k += 1
    out = cv2.Laplacian(gray_u8, ddepth=cv2.CV_32F, ksize=k)
    return out


def _convert_audio_to_spectrogram_image(audio: np.ndarray, fs: float) -> np.ndarray:
    """Convert 1D audio to a spectrogram-like grayscale image (uint8)."""
    # Use numpy FFT (no scipy dependency) and render magnitude to an image array.
    x = np.asarray(audio, dtype=np.float32)
    if x.ndim > 1:
        x = np.mean(x, axis=1)

    x = x - np.mean(x)
    x_abs = np.abs(x)

    # STFT parameters
    n_fft = 512
    hop = 256
    if len(x) < n_fft:
        # pad
        pad = n_fft - len(x)
        x = np.pad(x, (0, pad))

    frames = []
    for start in range(0, len(x) - n_fft + 1, hop):
        frame = x[start : start + n_fft]
        window = np.hanning(n_fft).astype(np.float32)
        spec = np.fft.rfft(frame * window)
        mag = np.abs(spec)
        frames.append(mag)

    if not frames:
        return np.zeros((64, 64), dtype=np.uint8)

    S = np.stack(frames, axis=1)  # (freq, time)
    S_db = 20.0 * np.log10(S + 1e-8)

    # Normalize to uint8
    S_db = S_db - np.min(S_db)
    if np.max(S_db) > 0:
        S_db = S_db / np.max(S_db)
    img = (S_db * 255.0).astype(np.uint8)

    return img


class Lab2Quantization(BaseLab):
    """Lab 2: convolution image processing operators."""

    def __init__(self):
        super().__init__(
            name="Convolution Image Processing",
            description=(
                "Apply image operators (blurs, sharpening, Sobel, Prewitt, Laplacian) "
                "and preview/download the resulting images."
            ),
        )

        self._params = Lab2Params()
        self._gray_input_u8: Optional[np.ndarray] = None
        self._color_input_u8: Optional[np.ndarray] = None
        self._image_source_path: Optional[str] = None
        self._fs: float = 44100.0

        self.results: Dict[str, Any] = {}

        self.parameters = {
            "operator": {
                "type": "choice",
                "choices": [op.value for op in ImageOperator],
                "default": ImageOperator.ORIGINAL.value,
                "value": self._params.operator,
                "label": "Select Image Operator",
            },
            "kernel_size": {
                "type": "int",
                "min": 1,
                "max": 11,
                "step": 2,
                "default": 1,
                "value": 1,
                "label": "Kernel Size (odd preferred)",
            },
        }

    def setup(self) -> Dict[str, Any]:
        self._params.operator = str(self.parameters["operator"]["value"])
        self._params.kernel_size = int(self.parameters["kernel_size"]["value"])
        return self.parameters

    def update_parameter(self, name: str, value: Any):
        super().update_parameter(name, value)
        if name == "operator":
            self._params.operator = str(value)
        elif name == "kernel_size":
            self._params.kernel_size = int(value)

    def set_signal(
        self,
        time_data: np.ndarray,
        signal_data: np.ndarray,
        sampling_rate: Optional[float] = None,
    ):
        """For compatibility with LabController.

        - If FileLoader passes an image, it will pass (time_data=None, signal_data=image_array, fs=None)
          OR can pass the path via time_data (we will also support that in controller changes later).
        - If audio is passed, we convert it to a spectrogram image.
        """
        if sampling_rate is not None:
            self._fs = float(sampling_rate)

        # Handle image uploads from FileLoader/LabController:
        # - signal_data is a tagged marker: ['__IMAGE__']
        # - time_data contains the image path: array([<path>], dtype=object)
        if isinstance(signal_data, np.ndarray) and signal_data.size == 1 and str(signal_data.flat[0]) == '__IMAGE__':
            # time_data should carry the path
            if isinstance(time_data, np.ndarray) and time_data.size == 1 and isinstance(time_data.flat[0], str):
                self._image_source_path = str(time_data.flat[0])
                img = _load_image(self._image_source_path)
                # Keep colored original for preview/download
                self._color_input_u8 = _ensure_uint8(img)
                self._gray_input_u8 = _rgb_to_gray_uint8(img)
                return

        sig = np.asarray(signal_data)

        # If it's already an image-like array
        if sig.ndim in (2, 3):
            self._color_input_u8 = _ensure_uint8(sig) if sig.ndim == 3 else None
            self._gray_input_u8 = _rgb_to_gray_uint8(sig)
            self._image_source_path = None
            return


        # Otherwise treat as audio and convert to spectrogram image
        gray = _convert_audio_to_spectrogram_image(sig, fs=self._fs)
        self._gray_input_u8 = gray
        self._color_input_u8 = None
        self._image_source_path = None

    def _is_color_operator(self, operator: str) -> bool:
        """Return True if operator should process color images when available."""
        return operator in {
            ImageOperator.ORIGINAL.value,
            ImageOperator.AVERAGE_BLUR.value,
            ImageOperator.GAUSSIAN_BLUR.value,
            ImageOperator.MEDIAN_BLUR.value,
            ImageOperator.IMAGE_SHARPENING.value,
        }

    def _apply_operator(self, img_u8: np.ndarray, operator: str, ksize: int) -> np.ndarray:
        op = str(operator)

        if op == ImageOperator.ORIGINAL.value:
            return img_u8
        if op == ImageOperator.AVERAGE_BLUR.value:
            return _blur_average(img_u8, ksize)
        if op == ImageOperator.GAUSSIAN_BLUR.value:
            return _blur_gaussian(img_u8, ksize)
        if op == ImageOperator.MEDIAN_BLUR.value:
            return _blur_median(img_u8, ksize)
        if op == ImageOperator.IMAGE_SHARPENING.value:
            return _sharpen(img_u8)

        # Edge-like operators — always grayscale
        gray = _rgb_to_gray_uint8(img_u8) if img_u8.ndim == 3 else img_u8

        if op == ImageOperator.SOBEL_X.value:
            dy = _sobel(gray, dx=0, dy=1, ksize=ksize)
            return _ensure_uint8(np.abs(dy))
        if op == ImageOperator.SOBEL_Y.value:
            dx = _sobel(gray, dx=1, dy=0, ksize=ksize)
            return _ensure_uint8(np.abs(dx))
        if op == ImageOperator.SOBEL_X_AND_Y.value:
            dx = _sobel(gray, dx=1, dy=0, ksize=ksize)
            dy = _sobel(gray, dx=0, dy=1, ksize=ksize)
            return _edge_magnitude(dx, dy)
        if op == ImageOperator.PREWITT.value:
            dx, dy = _prewitt(gray)
            return _edge_magnitude(dx, dy)
        if op == ImageOperator.LAPLACIAN.value:
            lap = _laplacian(gray, ksize=ksize)
            return _ensure_uint8(np.abs(lap))

        # Default
        return img_u8

    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        # Apply parameter overrides
        for k, v in kwargs.items():
            if k in self.parameters:
                self.update_parameter(k, v)

        if self._gray_input_u8 is None:
            # If no input provided, generate a simple synthetic image.
            # (UI will still work; user can upload for meaningful results.)
            h, w = 256, 256
            yy, xx = np.mgrid[0:h, 0:w]
            synthetic = ((xx - w / 2) ** 2 + (yy - h / 2) ** 2)
            synthetic = (synthetic / np.max(synthetic) * 255.0).astype(np.uint8)
            self._gray_input_u8 = synthetic
            self._color_input_u8 = None

        operator = self._params.operator
        ksize = self._params.kernel_size

        # Determine whether to use color or grayscale input for this operator
        use_color = self._is_color_operator(operator) and self._color_input_u8 is not None
        working_img = self._color_input_u8 if use_color else self._gray_input_u8

        # Output #1: Original (colored if the input was a color image)
        if self._color_input_u8 is not None and operator == ImageOperator.ORIGINAL.value:
            out_original = self._color_input_u8
        elif self._color_input_u8 is not None:
            out_original = self._color_input_u8  # Always preserve original color when available
        else:
            out_original = self._gray_input_u8

        # Output #2: Operator output
        out_operator = self._apply_operator(working_img, operator, ksize)

        # Output #3: secondary enhancement (NOT shown simultaneously; used for selection)
        if operator in {
            ImageOperator.SOBEL_X.value,
            ImageOperator.SOBEL_Y.value,
            ImageOperator.SOBEL_X_AND_Y.value,
            ImageOperator.PREWITT.value,
            ImageOperator.LAPLACIAN.value,
        }:
            # Edge magnitude variant from operator output (if edges)
            # If operator already returns magnitude/abs, normalize further.
            out_third = _ensure_uint8(_to_float01(out_operator) ** 0.8 * 255.0)
        else:
            # Sharpen + contrast for non-edge operators
            out_third = _sharpen(out_operator)
            # Contrast stretch
            f = _to_float01(out_third)
            f = np.clip((f - 0.5) * 1.6 + 0.5, 0.0, 1.0)
            out_third = (f * 255.0).astype(np.uint8)

        # Save images for preview/download
        out_dir = os.path.join(os.path.dirname(__file__), "..", "filtered_images")
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir, exist_ok=True)

        safe_op = operator.replace(" ", "_").replace("/", "_").replace("&", "and")
        base = f"lab2_{safe_op}_k{ksize}"

        p1 = os.path.join(out_dir, f"{base}_out1_original.png")
        p2 = os.path.join(out_dir, f"{base}_out2_operator.png")
        p3 = os.path.join(out_dir, f"{base}_out3_third.png")

        _save_image(p1, out_original)
        _save_image(p2, out_operator)
        _save_image(p3, out_third)

        # Store results: LabContainer will render the selected preview
        self.results = {
            "operator": operator,
            "kernel_size": ksize,
            "images": {
                "out1_original": {"path": p1, "label": "Original"},
                "out2_operator": {"path": p2, "label": f"Operator: {operator}"},
                "out3_third": {"path": p3, "label": "Enhanced view"},
            },
            # default selection
            "default_view_key": "out2_operator",
        }

        # Disable time/frequency domain for Lab2 by returning empties.
        # LabContainer also hides domain tabs for this lab.
        return np.array([]), np.array([])


    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        return np.array([]), np.array([])

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }