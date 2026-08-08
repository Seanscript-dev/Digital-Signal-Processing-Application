# ui/widgets/control_panel.py
"""
Dynamic control panel for lab parameters - Dark Blue Theme
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QLineEdit,
    QGroupBox, QGridLayout, QHBoxLayout, QMessageBox,
    QDialog, QPushButton
)
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any
import numpy as np


class ControlPanel(QWidget):
    """Dynamic control panel that generates controls based on lab parameters"""
    
    parameter_changed = Signal(str, object)
    
    def __init__(self):
        super().__init__()
        self.controls = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the control panel UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Set panel background to match dark blue theme
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Create controls for the given parameters"""
        # Clear existing controls
        self.clear_controls()
        
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        icon = QLabel()
        icon.setPixmap(QPixmap("icons/user.png").scaled(QSize(20,20), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        header_layout.addWidget(icon)
        header_layout.addStretch()
        
        
        # Keep existing param_group UI but add our header + controls into it
        param_group = QGroupBox("PARAMETERS")
        param_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #1e3a8a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 0px;
                background-color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 50%;
                padding: 0 8px;
                color: #60a5fa;
            }
        """)

        main_layout = QVBoxLayout(param_group)
        main_layout.setContentsMargins(12, 20, 12, 12)
        main_layout.addWidget(header)

        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setColumnStretch(1, 1)

        main_layout.addLayout(layout)
        
        row = 0
        for param_name, param_info in parameters.items():
            # Store param name in info
            param_info['name'] = param_name
            
            label_text = param_info.get('label', param_name)
            label = QLabel(label_text)
            label.setStyleSheet("""
                QLabel {
                    color: #e2e8f0;
                    font-weight: 500;
                    font-size: 12px;
                }
            """)
            label.setWordWrap(True)
            
            param_type = param_info.get('type', 'float')
            raw_value = param_info.get('value', param_info.get('default', 0))
            # Handle None/empty values: use minimum for numeric, empty string for text
            if raw_value is None:
                if param_type in ('float', 'int'):
                    current_value = param_info.get('min', 0)
                elif param_type == 'text':
                    current_value = ""
                else:
                    current_value = 0
            else:
                current_value = raw_value
            
            # Create appropriate control based on parameter type
            if param_type == 'float':
                control = self.create_float_control(param_info, current_value)
            elif param_type == 'int':
                control = self.create_int_control(param_info, current_value)
            elif param_type == 'bool':
                control = self.create_bool_control(param_info, current_value)
            elif param_type == 'choice':
                control = self.create_choice_control(param_info, current_value)
            elif param_type == 'list':
                control = self.create_list_control(param_info, current_value)
            else:
                control = self.create_text_control(param_info, current_value)
            
            # Store control reference
            self.controls[param_name] = control
            
            # Add to layout
            layout.addWidget(label, row, 0)
            layout.addWidget(control, row, 1)
            
            row += 1
        
        self.main_layout.addWidget(param_group)
        self.main_layout.addStretch()
    
    def create_float_control(self, param_info: Dict, current_value: float) -> QWidget:
        """Create a float input control (slider + spinbox) - REMOVED ARROWS"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        min_val = param_info.get('min', 0)
        max_val = param_info.get('max', 100)
        step = param_info.get('step', (max_val - min_val) / 100)
        
        # Slider with dark blue theme
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val / step))
        slider.setMaximum(int(max_val / step))
        slider.setValue(int(current_value / step))
        slider.valueChanged.connect(lambda v: self.on_float_changed(param_info, v * step, spinbox))
        slider.setMinimumHeight(24)
        
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background-color: #1e293b;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background-color: #3b82f6;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background-color: #334155;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #60a5fa;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
                border: 2px solid #1e3a8a;
            }
            QSlider::handle:horizontal:hover {
                background-color: #93c5fd;
                width: 18px;
            }
        """)
        
        # Spinbox with dark blue theme - REMOVED ARROWS
        spinbox = QDoubleSpinBox()
        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setValue(current_value)
        spinbox.setButtonSymbols(QSpinBox.NoButtons)  # This removes the arrows
        spinbox.valueChanged.connect(lambda v: self.on_float_changed(param_info, v, slider))
        
        spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e3a8a;
                border-radius: 4px;
                padding: 4px;
                min-width: 70px;
                font-weight: bold;
            }
            QDoubleSpinBox:hover {
                border: 1px solid #3b82f6;
                background-color: #334155;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #60a5fa;
            }
        """)
        
        layout.addWidget(slider, stretch=2)
        layout.addWidget(spinbox, stretch=1)
        
        return widget
    
    def create_int_control(self, param_info: Dict, current_value: int) -> QWidget:
        """Create an integer input control - REMOVED ARROWS"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        min_val = param_info.get('min', 0)
        max_val = param_info.get('max', 100)
        
        # Slider with dark blue theme
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(current_value)
        slider.valueChanged.connect(lambda v: self.on_int_changed(param_info, v, spinbox))
        
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background-color: #1e293b;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background-color: #3b82f6;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background-color: #334155;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #60a5fa;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
                border: 2px solid #1e3a8a;
            }
            QSlider::handle:horizontal:hover {
                background-color: #93c5fd;
                width: 18px;
            }
        """)
        
        # Spinbox with dark blue theme - REMOVED ARROWS
        spinbox = QSpinBox()
        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setValue(current_value)
        spinbox.setButtonSymbols(QSpinBox.NoButtons)  # This removes the arrows
        spinbox.valueChanged.connect(lambda v: self.on_int_changed(param_info, v, slider))
        
        spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e3a8a;
                border-radius: 4px;
                padding: 4px;
                min-width: 70px;
                font-weight: bold;
            }
            QSpinBox:hover {
                border: 1px solid #3b82f6;
                background-color: #334155;
            }
            QSpinBox:focus {
                border: 2px solid #60a5fa;
            }
        """)
        
        layout.addWidget(slider, stretch=2)
        layout.addWidget(spinbox, stretch=1)
        
        return widget
    
    def create_bool_control(self, param_info: Dict, current_value: bool) -> QWidget:
        """Create a boolean checkbox control"""
        checkbox = QCheckBox()
        checkbox.setChecked(current_value)
        checkbox.toggled.connect(lambda v: self.emit_change(param_info, v))
        
        # Style checkbox with dark blue theme
        checkbox.setStyleSheet("""
            QCheckBox {
                color: #e2e8f0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #1e3a8a;
                background-color: #0f172a;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #3b82f6;
                background-color: #1e293b;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border: 2px solid #60a5fa;
            }
        """)
        
        return checkbox
    
    def create_choice_control(self, param_info: Dict, current_value: str) -> QWidget:
        """Create a combo box for choices - REMOVED DROP ARROW"""
        combo = QComboBox()
        choices = param_info.get('choices', [])
        combo.addItems(choices)
        combo.setCurrentText(current_value)
        combo.currentTextChanged.connect(lambda v: self.emit_change(param_info, v))
        
        # Style combo box with dark blue theme - HIDE DROP ARROW
        combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e3a8a;
                border-radius: 4px;
                padding: 5px;
                font-weight: 500;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox:hover {
                background-color: #334155;
                border: 1px solid #3b82f6;
            }
            QComboBox:focus {
                border: 2px solid #60a5fa;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e3a8a;
                selection-background-color: #1e3a8a;
                selection-color: #ffffff;
            }
        """)
        
        return combo
    
    @staticmethod
    def _show_styled_warning(title: str, message: str):
        """Show a frameless warning dialog styled to match the dark blue theme with no title bar."""
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setFixedSize(380, 200)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        dialog.setObjectName("warningDialog")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Warning icon + title header bar (dark styled, no white)
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background-color: #1e3a8a; border-radius: 8px 8px 0 0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        
        warn_label = QLabel("\u26A0")
        warn_label.setStyleSheet("color: #fbbf24; font-size: 22px; font-weight: bold; background: transparent;")
        header_layout.addWidget(warn_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;")
        header_layout.addWidget(title_label, stretch=1)
        
        layout.addWidget(header)
        
        # Message body
        body = QLabel(message)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setStyleSheet("color: #e2e8f0; font-size: 13px; padding: 20px 24px; background-color: #0f172a;")
        layout.addWidget(body, stretch=1)
        
        # Button area
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: #0f172a; border-radius: 0 0 8px 8px;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(16, 8, 16, 16)
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(100, 34)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3a8a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addWidget(btn_container)
        
        dialog.setStyleSheet("QDialog#warningDialog { border: 2px solid #1e3a8a; border-radius: 8px; background-color: #0f172a; }")
        
        dialog.exec()

    def create_list_control(self, param_info: Dict, current_value: list) -> QWidget:
        """Create a text input for list parameters"""
        line_edit = QLineEdit(str(current_value))
        # Store initial valid value
        line_edit._last_valid_text = str(current_value)
        
        def on_list_text_changed(text: str):
            # Check if text contains alphabetic characters
            import re
            # Strip allowed characters: digits, spaces, minus, comma, decimal point, brackets
            stripped = re.sub(r'[0-9\s\-,\.\[\]\(\)]', '', text)
            if stripped:
                # Alphabetic or other disallowed characters found
                self._show_styled_warning(
                    "Invalid Input",
                    "Only numerals (0-9), spaces, decimal points, commas, and brackets are allowed.\n"
                    "Alphabetic characters are not accepted."
                )
                # Revert to last valid text
                line_edit.blockSignals(True)
                line_edit.setText(line_edit._last_valid_text)
                line_edit.blockSignals(False)
                return
            # Update last valid text
            line_edit._last_valid_text = text
            self.emit_change(param_info, eval(text) if text.strip() else [])
        
        line_edit.textChanged.connect(on_list_text_changed)
        
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e3a8a;
                border-radius: 4px;
                padding: 6px;
                font-family: monospace;
            }
            QLineEdit:hover {
                border: 1px solid #3b82f6;
                background-color: #334155;
            }
            QLineEdit:focus {
                border: 2px solid #60a5fa;
            }
        """)
        
        return line_edit
    
    def create_text_control(self, param_info: Dict, current_value: str) -> QWidget:
        """Create a text input control with validation for numeric-only input"""
        line_edit = QLineEdit(str(current_value))
        # Store initial valid value
        line_edit._last_valid_text = str(current_value)
        
        def on_text_changed(text: str):
            # Check if text contains alphabetic characters
            import re
            # Strip allowed characters: digits, spaces, minus, comma, decimal point
            stripped = re.sub(r'[0-9\s\-,\.]', '', text)
            if stripped:
                # Alphabetic or other disallowed characters found
                self._show_styled_warning(
                    "Invalid Input",
                    "Only numerals (0-9), spaces, decimal points, commas, and minus signs are allowed.\n"
                    "Alphabetic characters are not accepted."
                )
                # Revert to last valid text
                line_edit.blockSignals(True)
                line_edit.setText(line_edit._last_valid_text)
                line_edit.blockSignals(False)
                return
            # Update last valid text
            line_edit._last_valid_text = text
            self.emit_change(param_info, text)
        
        line_edit.textChanged.connect(on_text_changed)
        
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e3a8a;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:hover {
                border: 1px solid #3b82f6;
                background-color: #334155;
            }
            QLineEdit:focus {
                border: 2px solid #60a5fa;
            }
        """)
        
        return line_edit
    
    def on_float_changed(self, param_info: Dict, value: float, other_control):
        """Handle float value change and sync controls"""
        self.emit_change(param_info, value)
        # Sync slider/spinbox
        if hasattr(other_control, 'setValue'):
            other_control.blockSignals(True)
            other_control.setValue(value)
            other_control.blockSignals(False)
    
    def on_int_changed(self, param_info: Dict, value: int, other_control):
        """Handle integer value change and sync controls"""
        self.emit_change(param_info, value)
        # Sync slider/spinbox
        if hasattr(other_control, 'setValue'):
            other_control.blockSignals(True)
            other_control.setValue(value)
            other_control.blockSignals(False)
    
    def emit_change(self, param_info: Dict, value):
        """Emit parameter change signal"""
        param_name = param_info.get('name', '')
        param_info['value'] = value
        self.parameter_changed.emit(param_name, value)
    
    def get_all_values(self) -> Dict[str, Any]:
        """Get current values of all parameters from the created controls.

        Notes:
        - Control widgets are stored in self.controls[param_name]
        - Parameter info with current values is also updated via emit_change()
        - We return the latest values so LabContainer/ProcessingThread can process.
        """
        values: Dict[str, Any] = {}

        for param_name, param_info in getattr(self, "parameters", {}).items():
            # Prefer stored value if available
            if "value" in param_info:
                values[param_name] = param_info["value"]

        # Fallback: read from widget controls if possible
        for param_name, widget in self.controls.items():
            if param_name in values:
                continue

            if hasattr(widget, "value"):
                # QSpinBox/QDoubleSpinBox/QSlider
                values[param_name] = widget.value()
            elif hasattr(widget, "isChecked"):
                values[param_name] = widget.isChecked()
            elif hasattr(widget, "currentText"):
                values[param_name] = widget.currentText()
            elif widget.__class__.__name__ == "QLineEdit":
                text = widget.text()
                # Try to parse list params safely
                try:
                    values[param_name] = eval(text) if text else []
                except Exception:
                    values[param_name] = text
            else:
                # Last resort
                try:
                    values[param_name] = widget.text()
                except Exception:
                    pass

        return values
    
    def clear_controls(self):
        """Clear all controls from the panel"""
        # Clear layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.controls.clear()

