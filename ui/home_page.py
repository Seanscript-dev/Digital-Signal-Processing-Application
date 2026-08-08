"""ui/home_page.py

Modern home/dashboard page for DSP Analysis System.
Displayed after loading screen completes.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon


class LabCard(QFrame):
    """Clickable card widget representing a lab experiment."""

    clicked = Signal(str)  # emits lab_id

    def __init__(self, lab_id: str, title: str, description: str, icon_path: str = ""):
        super().__init__()
        self.lab_id = lab_id
        self.setObjectName("labCard")
        self.setFixedSize(280, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Icon area
        icon_label = QLabel()
        icon_label.setFixedSize(40, 40)
        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setWordWrap(True)
        title_label.setStyleSheet(
            "color: #e2e8f0; font-size: 14px; font-weight: bold; background: transparent; border: none;"
        )
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDesc")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            "color: #94a3b8; font-size: 11px; line-height: 1.3; background: transparent; border: none;"
        )
        layout.addWidget(desc_label)

        layout.addStretch()

        self.setStyleSheet("""
            LabCard#labCard {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
            LabCard#labCard:hover {
                background-color: #1e293b;
                border: 1px solid #3b82f6;
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.lab_id)
        super().mousePressEvent(event)


class HomePage(QWidget):
    """Main dashboard / home page displayed after loading."""

    lab_selected = Signal(str)  # emitted with lab_id when user clicks a lab card

    def __init__(self):
        super().__init__()
        self.setObjectName("homePage")
        self.setStyleSheet("QWidget#homePage { background-color: #020617; }")
        self.setup_ui()

    def setup_ui(self):
        """Build the home page layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                background-color: transparent; width: 0px; border-radius: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: transparent; border-radius: 0px; min-height: 0px;
            }
            QScrollBar::handle:vertical:hover { background-color: transparent; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar:horizontal {
                background-color: transparent; height: 0px; border-radius: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: transparent; border-radius: 0px; min-width: 0px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)

        # ── Welcome Section ──
        welcome = QWidget()
        welcome.setStyleSheet("background-color: transparent;")
        welcome_layout = QVBoxLayout(welcome)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(8)

        title = QLabel("DSP Analysis System")
        title.setStyleSheet(
            "color: #ffffff; font-size: 32px; font-weight: bold; background: transparent;"
        )
        welcome_layout.addWidget(title)

        subtitle = QLabel(
            "Digital Signal Processing Laboratory — Explore sampling, filtering, "
            "FFT analysis, and more through interactive experiments."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "color: #94a3b8; font-size: 14px; line-height: 1.5; background: transparent;"
        )
        welcome_layout.addWidget(subtitle)

        content_layout.addWidget(welcome)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #1e293b; max-height: 1px;")
        content_layout.addWidget(sep)

        # ── Labs Section Title ──
        section_title = QLabel("Experiments")
        section_title.setStyleSheet(
            "color: #60a5fa; font-size: 18px; font-weight: bold; background: transparent; letter-spacing: 1px;"
        )
        content_layout.addWidget(section_title)

        # ── Lab Cards Grid ──
        labs_data = [
            ("sampling", "SignalSampler", "Sampling & Aliasing", "Sample continuous signals and explore the Nyquist theorem with interactive frequency controls.", "icons/wave-sound.png"),
            ("quantization", "PhotOperator", "Convolution & Image Processing", "Apply image operators: blurs, edge detection, sharpening, and more.", "icons/image-editing.png"),
            ("convolution", "AliasFree", "Convolution & Digital Filters", "Butterworth filtering — apply low-pass, high-pass, band-pass, and band-stop filters.", "icons/music.png"),        
              ("fft", "SpectrumAnalyzer", "DFT & FFT Spectral Analysis", "Compute DFT and FFT, compare efficiency, and identify dominant frequencies.", "icons/equalizer.png"),
            ("filtering", "Taper", "Windowing & Spectral Leakage", "Generate signals, apply window functions, and visualize spectral leakage.", "icons/sound-control.png"),
            ("ztransform", "PoleZero", "Z-Transform & Pole-Zero", "Compute the Z-transform of discrete sequences with formatted algebraic output.", "icons/target.png"),
        ]

        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setContentsMargins(0, 0, 0, 0)

        for idx, (lab_id, short_name, full_name, desc, icon_path) in enumerate(labs_data):
            card = LabCard(
                lab_id=lab_id,
                title=f"{short_name}: {full_name}",
                description=desc,
                icon_path=icon_path,
            )
            card.clicked.connect(self._on_card_clicked)
            row = idx // 3
            col = idx % 3
            grid.addWidget(card, row, col)

        content_layout.addLayout(grid)

        # ── Footer ──
        footer = QLabel(
            "<div style='text-align:center; color:#475569; font-size:10px; line-height:1.5;'>"
            "DSP Analysis System v1.0.0 &nbsp;|&nbsp; © 2026 SeanScript Development"
            "</div>"
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("background: transparent; padding: 20px 0;")
        content_layout.addWidget(footer)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _on_card_clicked(self, lab_id: str):
        """Forward card click to the lab_selected signal."""
        self.lab_selected.emit(lab_id)

