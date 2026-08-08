"""ui/custom_title_bar

Custom frameless title bar matching the DSP Analysis System dark theme.
Replaces the native OS title bar with a seamless dark header.
"""

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QFont, QColor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
)


class CustomTitleBar(QWidget):
    """Dark-themed title bar with window controls and drag support."""

    # Signals for external handling
    minimizeRequested = Signal()
    maximizeRequested = Signal()
    closeRequested = Signal()

    def __init__(self, parent: QWidget = None, title: str = "DSP Analysis System"):
        super().__init__(parent)

        self._parent = parent
        self._drag_pos = QPoint()
        self._is_maximized = False

        self._setup_ui(title)
        self._setup_effects()

    def _setup_ui(self, title: str) -> None:
        """Build the title bar layout and widgets."""
        # Use a thinner title bar to match native size
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # Match your app's dark palette
        self.setStyleSheet("""
            QWidget#CustomTitleBar {
                background-color: #0d1220;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
            }
            QLabel#TitleLabel {
                color: #e0e6f0;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 1.5px;
            }
            QLabel#IconLabel {
                color: #64b4ff;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                background: transparent;
                color: #6b7a8f;
                border: none;
                font-family: 'Segoe UI';
                font-size: 16px;
                font-weight: 400;
                padding: 0 18px;
                min-width: 46px;
                max-width: 46px;
            }
            QPushButton:hover {
                background-color: rgba(100, 180, 255, 0.08);
                color: #64b4ff;
            }
            QPushButton#CloseBtn {
                border-top-right-radius: 0px;
            }
            QPushButton#CloseBtn:hover {
                background-color: #e81123;
                color: #ffffff;
            }
        """)

        self.setObjectName("CustomTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(8)

        # Logo icon
        self._logo_label = QLabel()
        self._logo_label.setFixedSize(20, 17)
        logo_pixmap = QPixmap("icons/logos.svg")
        if not logo_pixmap.isNull():
            self._logo_label.setPixmap(
                logo_pixmap.scaled(20, 17, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self._logo_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._logo_label)

        # Window title
        self._title = QLabel(title.upper())
        self._title.setObjectName("TitleLabel")
        layout.addWidget(self._title)

        layout.addStretch()

        # ─── Window Controls ───
        self._btn_min = QPushButton("−")
        self._btn_min.setToolTip("Minimize")
        self._btn_min.clicked.connect(self._on_minimize)
        layout.addWidget(self._btn_min)

        self._btn_max = QPushButton("□")
        self._btn_max.setToolTip("Maximize")
        self._btn_max.setObjectName("MaxBtn")
        self._btn_max.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._btn_max)

        self._btn_close = QPushButton("×")
        self._btn_close.setToolTip("Close")
        self._btn_close.setObjectName("CloseBtn")
        self._btn_close.clicked.connect(self._on_close)
        layout.addWidget(self._btn_close)

    def _setup_effects(self) -> None:
        """Add subtle bottom glow/separator."""
        # Optional: uncomment for a subtle cyan glow under the title bar
        # glow = QGraphicsDropShadowEffect(self)
        # glow.setBlurRadius(20)
        # glow.setColor(QColor(100, 180, 255, 30))
        # glow.setOffset(0, 2)
        # self.setGraphicsEffect(glow)
        pass

    def _window(self):
        """Return the top-level window for this title bar."""
        return self.window() if self.window() is not None else self._parent

    def _on_minimize(self) -> None:
        """Minimize the top-level window and emit the signal."""
        window = self._window()
        if window is not None:
            window.showMinimized()
        self.minimizeRequested.emit()

    def _on_close(self) -> None:
        """Close the top-level window and emit the signal."""
        window = self._window()
        if window is not None:
            window.close()
        self.closeRequested.emit()

    def _toggle_maximize(self) -> None:
        """Toggle between maximized and normal state."""
        window = self._window()
        if window is None:
            return

        if self._is_maximized:
            window.showNormal()
            self._btn_max.setText("□")
            self._is_maximized = False
        else:
            window.showMaximized()
            self._btn_max.setText("❐")
            self._is_maximized = True
        self.maximizeRequested.emit()

    def set_title(self, text: str) -> None:
        """Update the displayed title."""
        self._title.setText(text.upper())

    def set_maximized(self, maximized: bool) -> None:
        """Sync button icon with actual window state."""
        self._is_maximized = maximized
        self._btn_max.setText("❐" if maximized else "□")

    # ─── Drag Support ───
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and not self._is_maximized:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent.move(self._parent.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
