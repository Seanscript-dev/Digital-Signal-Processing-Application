from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class TextPreviewWidget(QWidget):
    """Simple widget for displaying formatted text in LabContainer.

    Lab 6 uses this (X(z) expression + ROC) instead of time/frequency plots.
    """

    def __init__(self, title: str = ""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.title_label.setStyleSheet(
            "color:#60a5fa; font-weight:bold; font-size:14px;"
        )
        layout.addWidget(self.title_label)

        self.body_label = QLabel("")
        self.body_label.setWordWrap(True)
        self.body_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.body_label.setStyleSheet(
            "color:#e2e8f0; font-size:12px; line-height:1.6;"
        )
        layout.addWidget(self.body_label)

        layout.addStretch(1)

    def set_text(self, title: str, body_html: str):
        self.title_label.setText(title)
        self.body_label.setText(body_html)

