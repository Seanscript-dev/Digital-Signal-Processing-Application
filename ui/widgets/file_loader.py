# ui/widgets/file_loader.py
"""File loader widget for importing signals from audio/CSV files and images."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QSizePolicy,
)

from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Signal, Qt


import numpy as np
import os


class FileLoader(QWidget):
    """Widget for loading signal data from files."""

    file_loaded = Signal(object, object)  # (time_data, signal_data)

    def __init__(self):
        super().__init__()
        self.current_file = None
        self._has_input = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("Import Signal")
        title.setStyleSheet(
            """
            QLabel {
                color: #e2e8f0;
                font-weight: bold;
                font-size: 13px;
                margin-top: 10px;
                background-color: transparent;
            }
            """
        )
        layout.addWidget(title)

        self.load_btn = QPushButton()
        self.load_btn.setText("Upload MP3/WAV or Image")
        self.load_btn.setIcon(QIcon("icons/upload.png"))
        self.load_btn.setIconSize(QSize(20, 20))
        self.load_btn.clicked.connect(self.load_file)
        self.load_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                padding: 8px 8px 8px 40px;
                padding-left: 57px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1e3a8a;
                color: white;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
            """
        )
        layout.addWidget(self.load_btn)

        # Row: [filename] x (place X next to filename, not at the far right)
        self.filename_row = QWidget()

        row_layout = QHBoxLayout(self.filename_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(False)
        # Keep X right after the filename (avoid pushing it to the far right).
        # Use size policies that exist across supported PySide6 versions.
        self.file_label.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred))

        self.file_label.setStyleSheet("color: #64748b; font-size: 11px;")

        row_layout.addWidget(self.file_label)

        self.x_btn = QPushButton("x")
        self.x_btn.setFixedWidth(20)
        self.x_btn.setFixedHeight(20)
        self.x_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #e2e8f0;
            }
            QPushButton:disabled {
                color: #64748b;
            }
            """
        )
        self.x_btn.clicked.connect(self.clear_inputs)
        row_layout.addWidget(self.x_btn)

        layout.addWidget(self.filename_row)


        self.sample_btn = QPushButton()
        self.sample_btn.setText("Generate Sample Signal")
        self.sample_btn.setIcon(QIcon("icons/music.png"))
        self.sample_btn.setIconSize(QSize(20, 20))
        self.sample_btn.clicked.connect(self.generate_sample)
        self.sample_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                padding: 8px 8px 8px 40px;
                padding-left: 60px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1e3a8a;
                color: white;
            }
            """
        )
        layout.addWidget(self.sample_btn)

        self._render_label()

    def _render_label(self):
        if not self._has_input:
            self.file_label.setText("No file loaded")
            self.file_label.setStyleSheet("color: #64748b; font-size: 11px;")
            self.x_btn.setVisible(False)
            return

        fname = self.current_file if self.current_file else "Sample"
        fname = os.path.basename(str(fname))
        self.file_label.setText(fname)
        self.file_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        self.x_btn.setVisible(True)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Signal Data",
            "",
            "All Supported Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.csv *.txt);;"
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;"
            "Image Files (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp);;"
            "CSV Files (*.csv);;"
            "Text Files (*.txt);;"
            "All Files (*.*)",
        )

        if not file_path:
            return

        try:
            ext = os.path.splitext(file_path)[1].lower()

            if ext in {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}:
                from core.signal import SignalProcessor

                t, signal, fs = SignalProcessor.load_from_audio(file_path)
                self.current_file = file_path
                self._has_input = True
                self._render_label()
                self.file_loaded.emit(t, signal)
                return

            if ext in {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}:
                self.current_file = file_path
                self._has_input = True
                self._render_label()
                self.file_loaded.emit(
                    np.array([file_path], dtype=object),
                    np.array(['__IMAGE__'], dtype=object),
                )
                return

            data = np.loadtxt(file_path, delimiter=',')

            if data.ndim == 1:
                t = np.arange(len(data), dtype=float)
                signal = data.astype(float)
            else:
                t = data[:, 0].astype(float)
                signal = data[:, 1].astype(float)

            self.current_file = file_path
            self._has_input = True
            self._render_label()
            self.file_loaded.emit(t, signal)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def clear_inputs(self):
        self.current_file = None
        self._has_input = False
        self._render_label()
        self.file_loaded.emit(None, None)

    def generate_sample(self):
        duration = 1.0
        sampling_rate = 1000
        t = np.arange(0, duration, 1 / sampling_rate)

        freq1, amp1 = 10, 1.0
        freq2, amp2 = 30, 0.5
        signal = amp1 * np.sin(2 * np.pi * freq1 * t) + amp2 * np.sin(2 * np.pi * freq2 * t)

        self.current_file = "Sample"
        self._has_input = True
        self._render_label()
        self.file_loaded.emit(t, signal)
