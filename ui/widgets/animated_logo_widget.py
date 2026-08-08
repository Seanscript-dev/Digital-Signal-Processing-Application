"""
Animated sound-bar logo widget for DSP Analysis System.
Renders an animated equalizer/voice bar using QPainter and QTimer.
Matches the dark cyan theme of the application.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QBrush


class AnimatedSoundBars(QWidget):
    """Custom animated widget that draws animated voice/sound bars."""

    def __init__(self, parent=None, bar_count: int = 6, bar_color: str = "#00bfff"):
        super().__init__(parent)
        self.setFixedSize(60, 50)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bar_count = bar_count
        self._bar_color = QColor(bar_color)
        self._bar_heights = [0.3, 0.5, 0.7, 0.4, 0.6, 0.8]
        self._target_heights = list(self._bar_heights)
        self._phase = 0

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(80)  # ~12 fps for smooth animation
        self._timer.start()

    def _animate(self):
        """Update bar heights with a smooth eased motion."""
        import math
        self._phase += 0.15

        for i in range(self._bar_count):
            # Create a smooth oscillating wave pattern
            t = self._phase + (i * 0.9)
            # Mix sine waves for organic look
            val = (
                0.35
                + 0.35 * math.sin(t * 1.3)
                + 0.2 * math.sin(t * 2.7 + 1.2)
                + 0.1 * math.sin(t * 4.1 + 0.5)
            )
            # Clamp between 0.2 and 1.0
            self._bar_heights[i] = max(0.2, min(1.0, val))

        self.update()

    def paintEvent(self, event):
        """Draw the animated bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Bar dimensions
        bar_count = self._bar_count
        bar_width = 6
        gap = (w - (bar_count * bar_width)) / (bar_count + 1)
        total_height = h - 4  # small padding

        # Draw rounded bars with gradient
        for i in range(bar_count):
            bar_h = total_height * self._bar_heights[i]
            x = gap + i * (bar_width + gap)
            y = h - 2 - bar_h

            # Gradient from bright top to softer bottom
            gradient = QLinearGradient(x, y, x, h - 2)
            gradient.setColorAt(0.0, QColor("#60a5fa"))  # Lighter blue at peak
            gradient.setColorAt(0.5, QColor(self._bar_color))
            gradient.setColorAt(1.0, QColor("#1e3a8a"))  # Darker blue at base

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)

            # Draw rounded rect bar
            rect = QRectF(x, y, bar_width, bar_h)
            painter.drawRoundedRect(rect, 3, 3)

        painter.end()

    def stop(self):
        """Stop the animation timer."""
        if self._timer and self._timer.isActive():
            self._timer.stop()

    def start(self):
        """Start/resume the animation timer."""
        if self._timer and not self._timer.isActive():
            self._timer.start()

