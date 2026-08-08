# ui/main_window.py
"""
Main application window with modern UI design
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QScrollArea, QFrame, QPushButton, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap

from ui.custom_title_bar import CustomTitleBar
from ui.lab_container import LabContainer
from ui.home_page import HomePage
from ui.loading_screen import LoadingScreen
from ui.widgets.animated_logo_widget import AnimatedSoundBars
from controller.app_controller import AppController


class MainWindow(QMainWindow):
    """Main application window following 30/60 layout rule"""

    def __init__(self):
        super().__init__()

        # ─── FRAMELESS WINDOW ───
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1200, 800)

        # Setup UI
        self.setup_ui()

        # Initialize controller
        self.controller = AppController()

        # Loading overlay support
        self.loading_overlay = None

        # Connect lab selection
        self.lab_list.currentItemChanged.connect(self.on_lab_selected)

        # Connect home page lab selection
        self.home_page.lab_selected.connect(self.on_home_lab_selected)

    def on_home_lab_selected(self, lab_id: str):
        """Called when a lab card is clicked on the home page."""
        # Show the lab view
        self.content_stack.setCurrentWidget(self.lab_container)

        # Show home button when entering a lab
        if hasattr(self, 'top_home_btn'):
            self.top_home_btn.setVisible(True)

        # Find the matching item in the lab list and select it
        for i in range(self.lab_list.count()):
            item = self.lab_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == lab_id:
                self.lab_list.setCurrentItem(item)
                self.lab_title.setText(item.text())
                self.lab_container.load_lab(lab_id, self.controller)
                break

    def setup_ui(self):
        """Setup the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main vertical layout: Title bar + horizontal content
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ─── CUSTOM TITLE BAR ───
        self._title_bar = CustomTitleBar(self, "DSP Analysis System")
        self._title_bar.minimizeRequested.connect(self.showMinimized)
        self._title_bar.closeRequested.connect(self.close)
        self._title_bar.maximizeRequested.connect(
            lambda: self._title_bar.set_maximized(self.isMaximized())
        )
        root_layout.addWidget(self._title_bar)

        # Thin separator under title bar
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #1e293b;")
        root_layout.addWidget(separator)

        # ─── MAIN CONTENT (30/70 split) ───
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left panel (30%) - Navigation and controls
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 30)

        # Right panel (70%) - Stacked widget holding [HomePage, LabContainer]
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 70)

        root_layout.addWidget(content_widget, stretch=1)

        # Apply styling
        self.apply_styling()

    def create_left_panel(self) -> QWidget:
        """Create the left navigation panel"""
        panel = QWidget()
        panel.setObjectName("leftPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(10)

        # Animated sound bar logo above title
        logo_container = QWidget()
        logo_container.setStyleSheet("background: transparent;")
        logo_container_layout = QHBoxLayout(logo_container)
        logo_container_layout.setContentsMargins(0, 0, 0, 0)
        logo_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._animated_logo = AnimatedSoundBars(bar_count=6, bar_color="#00bfff")
        logo_container_layout.addWidget(self._animated_logo)
        layout.addWidget(logo_container)

        # Logo / Title (clickable to go home)
        title = QLabel("DSP Analysis System")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setCursor(Qt.CursorShape.PointingHandCursor)
        title.mousePressEvent = lambda event: self.go_home()
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Digital Signal Processing")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)

        # Lab selection list
        labs_label = QLabel("Experiments")
        labs_label.setObjectName("sectionLabel")
        layout.addWidget(labs_label)

        self.lab_list = QListWidget()
        self.lab_list.setObjectName("labList")
        self.lab_list.setFixedHeight(350)
        self.lab_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Add labs
        labs = [
            ("SignalSampler: Sampling & Aliasing", "sampling"),
            ("PhotOperator: Convolution & Image Processing", "quantization"),
            ("AliasFree: Convolution & Digital Filters", "convolution"),
            ("SpectrumAnalyzer: DFT & FFT Spectral Analysis", "fft"),
            ("Taper: Windowing & Spectral Leakage", "filtering"),
            ("PoleZero: Z-Transform & Pole-Zero", "ztransform"),
        ]

        for lab_name, lab_id in labs:
            item = QListWidgetItem(lab_name)
            item.setData(Qt.ItemDataRole.UserRole, lab_id)
            self.lab_list.addItem(item)

        layout.addWidget(self.lab_list)

        # Version info
        layout.addStretch()
        version = QLabel(
            "<div style='text-align:center; color:#475569; font-size:10px; line-height:1.5;'>"
            "DSP Analysis System v1.0.0<br>"
            "© 2026 SeanScript Development"
            "</div>"
        )
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("versionInfo")
        layout.addWidget(version)

        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right workspace with stacked widget (HomePage / LabContainer)."""
        panel = QWidget()
        panel.setObjectName("rightPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar (lab title area) - visible only when lab is active
        self.top_bar = QWidget()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.lab_title = QLabel("Select a Lab")
        self.lab_title.setObjectName("labTitle")
        top_layout.addWidget(self.lab_title)
        top_layout.addStretch()

        # Home button in upper-right corner (hidden when on home page)
        self.top_home_btn = QPushButton("Home")
        self.top_home_btn.setObjectName("topHomeBtn")
        self.top_home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.top_home_btn.clicked.connect(self.go_home)
        self.top_home_btn.setStyleSheet("""
            QPushButton#topHomeBtn {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#topHomeBtn:hover {
                background-color: #1e3a8a;
                color: #ffffff;
                border: 1px solid #60a5fa;
            }
        """)
        self.top_home_btn.setVisible(False)  # Hidden by default (on home page)
        top_layout.addWidget(self.top_home_btn)

        layout.addWidget(self.top_bar)

        # Stacked widget: [0] HomePage, [1] LabContainer
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #020617;")

        # Create home page
        self.home_page = HomePage()
        self.content_stack.addWidget(self.home_page)  # index 0

        # Create lab container
        try:
            self.lab_container = LabContainer()
        except Exception:
            from ui.lab_container import LabContainer as _LabContainer
            self.lab_container = _LabContainer()
        self.content_stack.addWidget(self.lab_container)  # index 1

        layout.addWidget(self.content_stack)

        # Start on home page
        self.content_stack.setCurrentIndex(0)

        return panel

    def go_home(self):
        """Return to the home dashboard."""
        self.content_stack.setCurrentWidget(self.home_page)
        self.lab_title.setText("Home")
        self.lab_list.clearSelection()
        # Hide home button when on home page
        if hasattr(self, 'top_home_btn'):
            self.top_home_btn.setVisible(False)
        # Hide lab container content
        if hasattr(self, 'lab_container') and self.lab_container.isVisible():
            self.lab_container.setVisible(False)
        self.home_page.setVisible(True)

    def start_loading(self, logo_path: str = "icons/logoo.png", duration_ms: int = 5000) -> None:
        """Display a loading overlay on top of this main window."""
        if self.loading_overlay is not None:
            self.loading_overlay.close()

        self.loading_overlay = LoadingScreen(
            parent=self,
            logo_path=logo_path,
            duration_ms=duration_ms,
        )
        # When loading finishes, show the home page
        self.loading_overlay.finished.connect(self._on_loading_finished)
        self.loading_overlay.setGeometry(self.geometry())
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        self.loading_overlay.activateWindow()

    def _on_loading_finished(self):
        """Called when loading screen finishes - show home page."""
        # Ensure home page is shown
        self.content_stack.setCurrentWidget(self.home_page)
        self.lab_title.setText("Home")
        self.lab_list.clearSelection()

        # Hide loading overlay
        if self.loading_overlay:
            self.loading_overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.loading_overlay is not None:
            self.loading_overlay.setGeometry(self.rect())

    def changeEvent(self, event):
        """Detect maximize/restore from OS or shortcuts."""
        if event.type() == event.Type.WindowStateChange:
            self._title_bar.set_maximized(self.isMaximized())
        super().changeEvent(event)

    def apply_styling(self):
        """Apply professional dark theme styling"""
        self.setStyleSheet("""
            /* Main background */
            QMainWindow, QWidget#leftPanel, QWidget#rightPanel {
                background-color: #020617;
            }

            /* Custom title bar */
            QWidget#CustomTitleBar {
                background-color: #0f172a;
            }

            /* Left panel styling */
            QWidget#leftPanel {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }

            /* Titles */
            QLabel#appTitle {
                font-size: 30px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px;
            }

            QLabel#appSubtitle {
                font-size: 12px;
                color: #94a3b8;
                padding-bottom: 10px;
            }

            QLabel#sectionLabel {
                font-size: 14px;
                font-weight: bold;
                color: #e2e8f0;
                margin-top: 10px;
                margin-bottom: 5px;
            }

            QLabel#labTitle {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
            }

            /* Separator */
            QFrame#separator {
                background-color: #1e293b;
                max-height: 1px;
                margin: 10px 0;
            }

            /* Lab list */
            QListWidget#labList {
                background-color: #1e293b;
                border: none;
                border-radius: 8px;
                color: #cbd5e1;
                font-size: 13px;
                padding: 5px;
                outline: none;
            }

            QListWidget#labList::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px;
            }

            QListWidget#labList::item:selected {
                background-color: #1e3a8a;
                color: #ffffff;
            }

            QListWidget#labList::item:hover {
                background-color: #2563eb;
                color: #ffffff;
            }

            /* Top bar */
            QWidget#topBar {
                background-color: #0f172a;
                border-bottom: 1px solid #1e293b;
            }

            /* Version info */
            QLabel#versionInfo {
                color: #64748b;
                font-size: 10px;
                margin-top: 20px;
            }

            /* Scroll areas */
            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                background-color: #1e293b;
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #3b82f6;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #2563eb;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def on_lab_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle lab selection"""
        if current:
            lab_id = current.data(Qt.ItemDataRole.UserRole)
            lab_name = current.text()
            self.lab_title.setText(lab_name)

            # Switch to lab container view
            self.content_stack.setCurrentWidget(self.lab_container)

            # Show home button when entering a lab
            if hasattr(self, 'top_home_btn'):
                self.top_home_btn.setVisible(True)

            # Load lab in container
            self.lab_container.load_lab(lab_id, self.controller)

