from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
import shutil


class ImagePreviewWidget(QWidget):
    # Hard cap the preview area size so pixmaps can't widen the whole UI.
    # Allow more space for the preview, but still cap width to avoid pushing other UI (controls/parameters).
    PREVIEW_MAX_W = 750
    PREVIEW_MAX_H = 500

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.title_label = QLabel("Image Preview")
        self.title_label.setStyleSheet("color:#60a5fa; font-weight:bold; font-size:13px;")
        layout.addWidget(self.title_label)

        self.preview_label = QLabel("No image loaded")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(
            "color:#94a3b8; border:1px solid #1e293b; background-color:#020617; min-height:400px;"
        )

        # Prevent the label from requesting an unbounded width based on the pixmap.
        self.preview_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.preview_label.setMaximumWidth(self.PREVIEW_MAX_W)
        # Keep height somewhat bounded too (helps layout stability).
        self.preview_label.setMaximumHeight(self.PREVIEW_MAX_H)

        layout.addWidget(self.preview_label, stretch=1)

        self.view_selector = QComboBox()
        self.view_selector.currentIndexChanged.connect(self._on_view_changed)
        self.view_selector.setStyleSheet(
            "QComboBox { background-color:#1e293b; color:#e2e8f0; border:1px solid #1e3a8a; border-radius:4px; padding:5px; }"
        )
        layout.addWidget(self.view_selector)

        self.download_btn = QPushButton("Download")
        self.download_btn.setStyleSheet(
            "QPushButton { background-color:#065f46; color:white; border:none; border-radius:6px; padding:8px 12px; font-weight:bold; }"
            "QPushButton:hover { background-color:#047857; }"
        )
        self.download_btn.clicked.connect(self.download)
        layout.addWidget(self.download_btn)

        self._images = {}
        self._current_key = None

        # Cache the raw pixmap so we can re-scale on resize without re-reading file.
        self._current_pixmap = None
        self._last_render_size = None

    def set_images(self, images: dict, default_view_key: str):
        """images: key -> {'path': str, 'label': str}"""
        self._images = images or {}
        self.view_selector.blockSignals(True)
        self.view_selector.clear()
        for key, meta in self._images.items():
            self.view_selector.addItem(meta.get("label", key), key)
        self.view_selector.blockSignals(False)

        default_key = default_view_key if default_view_key in self._images else (next(iter(self._images), None))
        if default_key is None:
            self._current_key = None
            self.preview_label.setText("No image loaded")
            return

        idx = self.view_selector.findData(default_key)
        if idx >= 0:
            self.view_selector.setCurrentIndex(idx)
        else:
            self._current_key = default_key
            self._render_current()

    def _on_view_changed(self, _idx: int):
        self._current_key = self.view_selector.currentData()
        self._render_current()

    def _render_current(self):
        if not self._current_key or self._current_key not in self._images:
            self.preview_label.setText("No image loaded")
            self._current_pixmap = None
            return

        path = self._images[self._current_key].get("path", "")
        if not path or not os.path.exists(path):
            self.preview_label.setText("Missing image file")
            self._current_pixmap = None
            return

        pix = QPixmap(path)
        if pix.isNull():
            self.preview_label.setText("Could not render image")
            self._current_pixmap = None
            return

        self._current_pixmap = pix
        self._apply_scaled_pixmap()

    def _apply_scaled_pixmap(self):
        """Scale current pixmap to the current preview label size (zoom out / fit)."""
        if self._current_pixmap is None or self._current_pixmap.isNull():
            self.preview_label.setText("No image loaded")
            self.preview_label.setPixmap(QPixmap())
            return

        # Subtle: use the label's *current* internal size to avoid layout-driven widening.
        label_size = self.preview_label.size()
        if not label_size.isValid() or label_size.width() <= 0 or label_size.height() <= 0:
            label_size = self.preview_label.sizeHint()

        target_w = max(1, min(label_size.width(), self.PREVIEW_MAX_W))
        target_h = max(1, min(label_size.height(), self.PREVIEW_MAX_H))

        # Avoid re-rendering for the same target size.
        current_key = (target_w, target_h)
        if self._last_render_size == current_key:
            return
        self._last_render_size = current_key

        scaled = self._current_pixmap.scaled(
            target_w,
            target_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):
        # When layout changes (e.g. splitter resize), re-fit the image to the capped label size.
        super().resizeEvent(event)
        if self._current_pixmap is not None:
            self._apply_scaled_pixmap()

    def download(self):
        if not self._current_key or self._current_key not in self._images:
            QMessageBox.warning(self, "No image", "Nothing to download")
            return

        src = self._images[self._current_key].get("path", "")
        if not src or not os.path.exists(src):
            QMessageBox.warning(self, "Missing", "Source image not found")
            return

        filename = os.path.basename(src)
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            filename,
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
        )
        if save_path:
            try:
                shutil.copy(src, save_path)
                QMessageBox.information(self, "Success", f"Saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

