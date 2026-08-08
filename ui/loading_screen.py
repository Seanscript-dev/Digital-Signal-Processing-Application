"""ui.loading_screen

Minimalist full-screen loading screen for DSP Analysis System.
Designed for formal, clean aesthetic matching the application theme.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
)
from pathlib import Path

from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)


class LoadingScreen(QWidget):
    """Formal, minimalistic 5-second full-screen loading screen.

    Emits `finished` signal when loading completes.
    Integrates into existing PySide6 DSP application.
    """

    finished = Signal()

    def __init__(
        self,
        logo_path: str = "icons/logoo.png",
        duration_ms: int = 5000,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self._duration_ms = duration_ms
        self._logo_path = logo_path
        self._status_messages = [
            "Initializing",
            "Loading Modules",
            "Configuring Signal Paths",
            "Calibrating FFT Engine",
            "Ready",
        ]

        self._setup_window()
        self._setup_styles()
        self._build_ui()
        self._start_sequence()

    def _setup_window(self) -> None:
        """Configure window properties for top-level or overlay mode."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_StyledBackground, True)

        if self.parent() is None:
            self.setWindowState(Qt.WindowFullScreen)
            screen = QApplication.primaryScreen().geometry()
            self.setGeometry(screen)
        else:
            parent = self.parent()
            rect = parent.frameGeometry() if hasattr(parent, 'frameGeometry') else parent.geometry()
            self.setGeometry(rect)

    def _setup_styles(self) -> None:
        """Configure fonts and palette."""
        self._bg_color = QColor(10, 14, 26)          # #0a0e1a
        self._text_color = QColor(224, 230, 240)      # #e0e6f0
        self._accent_cyan = QColor(100, 180, 255)     # #64b4ff
        self._accent_purple = QColor(168, 85, 247)    # #a855f7

        # Responsive font sizing based on screen height
        screen_height = QApplication.primaryScreen().geometry().height()
        base_size = max(screen_height // 60, 10)

        self._font_light = QFont("Segoe UI", base_size * 2, QFont.Light)
        self._font_regular = QFont("Segoe UI", base_size, QFont.Normal)
        self._font_small = QFont("Segoe UI", int(base_size * 0.8), QFont.Normal)
        self._font_tiny = QFont("Segoe UI", int(base_size * 0.65), QFont.Normal)

    def _build_ui(self) -> None:
        """Construct the loading screen layout."""
        self.setStyleSheet(
            f"background-color: {self._bg_color.name()};"
            " QLabel { background: transparent; border: none; }"
        )
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(14)

        # Responsive margins based on screen size
        screen = QApplication.primaryScreen().geometry()
        margin_h = screen.width() // 8
        margin_v = screen.height() // 10
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)

        layout.addStretch(2)

        # Logo — larger circular container with steady glow
        logo_size = int(min(QApplication.primaryScreen().geometry().height() // 6, 540) * 2.5)

        self._logo_container = QWidget()
        self._logo_container.setFixedSize(logo_size + 48, logo_size + 48)
        self._logo_container.setAttribute(Qt.WA_TranslucentBackground)
        self._logo_container.setStyleSheet(
            "background: qradialgradient(cx:0.5, cy:0.45, fx:0.5, fy:0.45, "
            "stop:0 rgba(100,180,255,36), stop:0.6 rgba(168,85,247,18), stop:1 rgba(10,14,26,0)); "
            "border-radius: %dpx;" % ((logo_size + 48) // 2)
        )

        # inner layout to center the logo label
        from PySide6.QtWidgets import QHBoxLayout

        _inner = QHBoxLayout(self._logo_container)
        _inner.setContentsMargins(8, 8, 8, 8)
        _inner.setAlignment(Qt.AlignCenter)

        self._logo_label = QLabel(self._logo_container)
        self._logo_label.setAlignment(Qt.AlignCenter)
        self._logo_label.setAttribute(Qt.WA_TranslucentBackground)
        self._logo_label.setStyleSheet("background: transparent; border: none; text-align: center;")
        self._logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._logo_label.setFixedSize(logo_size, logo_size)
        _inner.addWidget(self._logo_label)
        self._load_logo()

        # subtle ring border
        self._logo_container.setStyleSheet(self._logo_container.styleSheet() + (
            "border: 4px solid rgba(255,255,255,0.04);"
        ))

        layout.addWidget(self._logo_container, alignment=Qt.AlignCenter)

        layout.addSpacing(28)

        # Title
        self._title = QLabel("DSP ANALYSIS")
        self._title.setFont(self._font_light)
        self._title.setStyleSheet(
            f"color: #ffffff; letter-spacing: 12px; text-transform: uppercase; background: transparent; text-align: center;"
        )
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        layout.addSpacing(16)

        # Subtitle
        self._subtitle = QLabel("Digital Signal Processing Laboratory")
        self._subtitle.setFont(self._font_small)
        self._subtitle.setStyleSheet(
            f"color: {self._accent_cyan.name()}; letter-spacing: 6px; text-transform: uppercase; background: transparent; text-align: center;"
        )
        self._subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._subtitle)

        layout.addSpacing(50)

        # Progress bar — responsive width
        screen_width = QApplication.primaryScreen().geometry().width()
        bar_width = min(screen_width // 2, 520)

        self._progress = QProgressBar()
        self._progress.setFixedSize(bar_width, 4)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(100, 180, 255, 0.1);
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #64b4ff,
                    stop: 1 #a855f7
                );
                border-radius: 1px;
            }
        """)
        layout.addWidget(self._progress, alignment=Qt.AlignCenter)

        layout.addSpacing(40)

        # Status text
        self._status = QLabel("Initializing")
        self._status.setFont(self._font_tiny)
        self._status.setStyleSheet(
            f"color: rgba(224, 230, 240, 0.7); letter-spacing: 4px; text-transform: uppercase; background: transparent; text-align: center;"
        )
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

        layout.addStretch(2)

        # Version — bottom aligned
        self._version = QLabel("v1.0.0")
        self._version.setFont(self._font_tiny)
        self._version.setStyleSheet(
            f"color: rgba(224, 230, 240, 0.35); letter-spacing: 3px; text-transform: uppercase; background: transparent; text-align: center;"
        )
        self._version.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._version)

        # Fade in animation
        self._fade_in()

        # start logo pulse glow
        self._start_logo_pulse()

    def _load_logo(self) -> None:
        """Load and scale the splash logo from icons/logoo.png."""
        logo_size = int(min(QApplication.primaryScreen().geometry().height() // 6, 540) * 2.5)
        logo_path = Path(self._logo_path)
        if not logo_path.is_absolute():
            logo_path = Path(__file__).resolve().parents[1] / logo_path

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled = pixmap.scaled(
                logo_size,
                logo_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            if not scaled.isNull():
                self._logo_label.setPixmap(scaled)
                return

        self._logo_label.setText("DSP")
        self._logo_label.setStyleSheet(
            f"color: #64b4ff; font-size: {logo_size // 3}px; font-weight: 700; background: transparent;"
        )

    def _add_glow_effect(self, widget: QWidget) -> QGraphicsDropShadowEffect:
        """Add subtle drop shadow glow to widget."""
        glow = QGraphicsDropShadowEffect(widget)
        glow.setBlurRadius(60)
        glow.setColor(QColor(100, 180, 255, 100))
        glow.setOffset(0, 0)
        widget.setGraphicsEffect(glow)
        return glow

    def _fade_in(self) -> None:
        """Animate opacity from 0 to 1."""
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(800)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

    def _start_logo_pulse(self) -> None:
        """Apply a steady glow around the logo container and prevent shaking."""
        glow_effect = self._add_glow_effect(self._logo_container)
        glow_effect.setBlurRadius(80)
        glow_effect.setColor(QColor(100, 180, 255, 120))

    def _start_sequence(self) -> None:
        """Begin the 5-second loading sequence."""
        self._elapsed = 0
        self._update_interval = 50  # 50ms refresh

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(self._update_interval)

    def _on_tick(self) -> None:
        """Update progress and status."""
        self._elapsed += self._update_interval
        progress = min((self._elapsed / self._duration_ms) * 100, 100)

        self._progress.setValue(int(progress))

        status_index = min(
            int((progress / 100) * len(self._status_messages)),
            len(self._status_messages) - 1,
        )
        self._status.setText(self._status_messages[status_index])

        if progress >= 100:
            self._timer.stop()
            self._status.setText("Launching...")
            self._finish()

    def _finish(self) -> None:
        """Close the loading screen and emit finished signal immediately."""
        self.close()
        self.finished.emit()

    def _on_fade_out_complete(self) -> None:
        """Close loading screen and notify main app."""
        self.close()
        self.finished.emit()

    def paintEvent(self, event) -> None:
        """Draw ambient radial glow behind logo."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Multiple ambient glow layers
        center_x = self.width() // 2
        center_y = self.height() // 2 - 80

        # Large subtle glow
        gradient1 = QRadialGradient(center_x, center_y, self.height() // 2)
        gradient1.setColorAt(0, QColor(100, 180, 255, 15))
        gradient1.setColorAt(1, QColor(10, 14, 26, 0))
        painter.fillRect(self.rect(), gradient1)

        # Tighter glow around logo area
        gradient2 = QRadialGradient(center_x, center_y, 250)
        gradient2.setColorAt(0, QColor(168, 85, 247, 12))
        gradient2.setColorAt(1, QColor(10, 14, 26, 0))
        painter.fillRect(self.rect(), gradient2)

        painter.end()

    def resizeEvent(self, event) -> None:
        """Handle resize to maintain full-screen coverage."""
        super().resizeEvent(event)
        if hasattr(self, '_container'):
            self._container.setGeometry(self.rect())

    def keyPressEvent(self, event) -> None:
        """Allow Escape key to skip loading (for development)."""
        if event.key() == Qt.Key_Escape:
            self._timer.stop()
            self._finish()
        else:
            super().keyPressEvent(event)


# ─── Standalone Test ───

if __name__ == "__main__":
    app = QApplication(sys.argv)

    loading = LoadingScreen(
        logo_path="icons/logoo.png",
        duration_ms=5000,
    )
    loading.show()

    loading.finished.connect(lambda: print("Loading complete — app would launch here"))

    sys.exit(app.exec())