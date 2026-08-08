from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QSplitter,  QTabWidget,
    QGridLayout
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont
import numpy as np
import time
from ui.widgets.plot_widget import PlotWidget
from ui.widgets.control_panel import ControlPanel
from ui.widgets.file_loader import FileLoader
from ui.widgets.audio_player import AudioPlayer
from ui.widgets.image_preview_widget import ImagePreviewWidget
from controller.lab_controller import LabController


class ProcessingThread(QThread):
    """Thread for heavy DSP computations to prevent UI freezing"""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, lab_controller, params):
        super().__init__()
        self.lab_controller = lab_controller
        self.params = params

    def run(self):
        try:
            # No artificial delay to keep UI responsive on startup
            if self.isInterruptionRequested():
                return

            result = self.lab_controller.process(self.params)

            if self.isInterruptionRequested():
                return

            self.finished.emit(result)
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error.emit(str(e))


class LabContainer(QWidget):
    """Container for lab visualization and controls"""

    def __init__(self):
        super().__init__()
        self.current_lab_controller = None
        self.current_lab_id = None
        self.processing_thread = None
        self.audio_players = []  # Store audio player widgets for Lab 3
        self._lab4_scroll = None  # Track Lab 4 scroll area
        self.setup_ui()

    def setup_ui(self):
        """Setup the lab container UI with dark blue theme"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Set container background
        self.setStyleSheet("""
            QWidget {
                background-color: #020617;
            }
        """)

        # Main splitter for plots and controls
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e3a8a;
                width: 2px;
            }
        """)

        # Plot area (right side, wider)
        self.plot_area = self.create_plot_area()
        self.main_splitter.addWidget(self.plot_area)

        # Control panel area (left side, narrower)
        self.control_area = self.create_control_area()
        self.main_splitter.addWidget(self.control_area)

        # Set initial splitter sizes (70% plot, 30% controls)
        self.main_splitter.setSizes([700, 300])

        layout.addWidget(self.main_splitter)

        # Hide initially
        self.setVisible(False)

    def create_plot_area(self) -> QWidget:
        """Create the plotting area with tabs"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #020617;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)


        # Tab widget for different views with dark blue theme
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background-color: #020617;
                border: 1px solid #1e3a8a;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 4px 18px; /* compact header */
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }

            QTabBar::tab:selected {
                background-color: #1e3a8a;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #1e293b;
                color: #e2e8f0;
            }
        """)

        # Time domain plot
        self.time_plot = PlotWidget("Time Domain", "Time (s)", "Amplitude")
        self.time_plot.set_background_color('#020617')
        self.tab_widget.addTab(self.time_plot,QIcon("icons/pending.png"),
            "Time Domain"
        )

        # Frequency domain plot
        self.freq_plot = PlotWidget("Frequency Domain", "Frequency (Hz)", "Magnitude")
        self.freq_plot.set_background_color('#020617')
        self.freq_plot.enable_log_scale()

        self.tab_widget.addTab(
            self.freq_plot,
            QIcon("icons/stats (1).png"),
            "Frequency Domain"
        )

        # Additional info tab (includes Lab 1 result panel)
        self.info_tab = QWidget()
        self.info_tab.setStyleSheet("background-color: #020617;")
        info_layout = QVBoxLayout(self.info_tab)
        info_layout.setContentsMargins(20, 6, 20, 16)
        info_layout.setSpacing(6)

        self.info_label = QLabel("Lab information will appear here")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 12px;
                line-height: 1.2;
            }
        """)
        info_layout.addWidget(self.info_label)

        # Result box — added DIRECTLY (no scroll wrapper here)
        # Scroll is applied conditionally in load_lab() for Lab 4 only
        self.result_box = QLabel("")
        self.result_box.setWordWrap(True)
        self.result_box.setStyleSheet("""
            QLabel {
                background-color: #0b1220;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 14px;
                margin-top: 10px;
                color: #e2e8f0;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self.result_box.setVisible(False)
        info_layout.addWidget(self.result_box)

        # Replace QLabel-based result area with a real 2x2 grid container layout for Lab outputs.
        self.info_content_layout = QGridLayout()


        self.info_content_layout.setContentsMargins(0, 0, 0, 0)
        self.info_content_layout.setHorizontalSpacing(15)
        self.info_content_layout.setVerticalSpacing(10)

        info_layout.addLayout(self.info_content_layout)

        # Forces top alignment by absorbing remaining vertical space.
        info_layout.addStretch(1)

        # No additional spacer items; keeps info area tight (prevents empty containers around Lab2 image preview)
        # Align the Information tab header text to the top (fixes visual misalignment).
        self.tab_widget.tabBar().setStyleSheet("QTabBar::tab { qproperty-alignment: AlignTop; }")

        self.tab_widget.addTab(self.info_tab, "Information")


        # Ensure grid doesn't reserve space before content is added
        self.info_content_layout.setRowStretch(0, 0)
        self.info_content_layout.setRowStretch(1, 0)


        layout.addWidget(self.tab_widget)

        return widget

    def _ensure_lab4_scroll(self):
        """Lab 4 only: wrap result_box in a scroll area with generous spacing."""
        # If already set up, just ensure visibility and sizing
        if self._lab4_scroll is not None and self._lab4_scroll.parent() is not None:
            self._lab4_scroll.setVisible(True)
            self._lab4_scroll.setMinimumHeight(450)
            return

        # Remove result_box from its current parent/layout first
        if self.result_box.parent():
            self.result_box.setParent(None)

        # Create fresh scroll area for Lab 4
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e293b;
                width: 12px;
                border-radius: 6px;
                margin: 6px 4px 6px 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #1e3a8a;
                border-radius: 6px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3b82f6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # More breathing room for Lab 4 content
        self.result_box.setStyleSheet("""
            QLabel {
                background-color: #0b1220;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 24px 28px 24px 24px;   /* MORE padding: top right bottom left */
                margin: 16px 8px 16px 8px;      /* margin around the box */
                color: #e2e8f0;
                font-size: 13px;
                line-height: 1.6;
            }
        """)

        scroll.setWidget(self.result_box)
        self._lab4_scroll = scroll

        # Insert scroll into info_layout at position 1 (after info_label, before grid)
        self.info_tab.layout().insertWidget(1, scroll)
        scroll.setMinimumHeight(450)

    def _restore_normal_result_box(self):
        """Remove scroll wrapper and put result_box back directly in info_layout."""
        layout = self.info_tab.layout()

        # Find and remove any QScrollArea that contains result_box
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, QScrollArea) and widget.widget() is self.result_box:
                widget.takeWidget()  # Detach result_box from scroll
                widget.setVisible(False)
                widget.setParent(None)
                layout.removeItem(item)
                break
            elif isinstance(widget, QScrollArea):
                # Clean up any orphaned scroll areas too
                widget.setVisible(False)
                widget.setParent(None)
                layout.removeItem(item)

        self._lab4_scroll = None

        # Reset to tighter style for non-lab4 labs
        self.result_box.setStyleSheet("""
            QLabel {
                background-color: #0b1220;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 14px;
                margin-top: 10px;
                color: #e2e8f0;
                font-size: 13px;
                line-height: 1.6;
            }
        """)

        # Re-add result_box directly if not already in layout
        found = False
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == self.result_box:
                found = True
                break
        if not found:
            layout.insertWidget(1, self.result_box)
        self.result_box.setVisible(False)

    def create_control_area(self) -> QWidget:
        """Create the control panel area with dark blue theme"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #0f172a;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Title for control area
        title_label = QLabel("CONTROLS")
        title_label.setStyleSheet("""
            QLabel {
                color: #60a5fa;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 1px;
                padding-bottom: 5px;
            }
        """)
        layout.addWidget(title_label)

        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0f172a;
            }
            QScrollBar:vertical {
                background-color: #1e293b;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #1e3a8a;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3b82f6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Control panel widget
        self.control_panel = ControlPanel()

        scroll.setWidget(self.control_panel)
        layout.addWidget(scroll)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #1e3a8a; max-height: 1px; margin: 10px 0;")
        layout.addWidget(separator)

        # File loader with dark blue theme
        self.file_loader = FileLoader()
        self.file_loader.file_loaded.connect(self.on_file_loaded)
        layout.addWidget(self.file_loader)


        # Process button with dark blue theme
        self.process_btn = QPushButton()
        self.process_btn.setText("PROCESS SIGNAL")
        self.process_btn.setIcon(QIcon("icons/play.png"))
        self.process_btn.setIconSize(QSize(16, 16))
        self.process_btn.setObjectName("processBtn")
        self.process_btn.clicked.connect(self.on_process_clicked)

        # Style the process button
        self.process_btn.setStyleSheet("""
            QPushButton#processBtn {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3a8a, stop:1 #1e40af);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
                margin-top: 10px;
            }
            QPushButton#processBtn:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #1e3a8a);
            }
            QPushButton#processBtn:pressed {
                background-color: #1e3a8a;
            }
            QPushButton#processBtn:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)

        layout.addWidget(self.process_btn)

        return widget

    def load_lab(self, lab_id: str, app_controller):
        """Load a lab into the container"""
        # Store current lab ID
        self.current_lab_id = lab_id

        # Fully reset lab-specific UI areas so switching labs never leaves empty/stale widgets
        # Clear the 2x2 information grid
        if hasattr(self, "info_content_layout"):
            grid = self.info_content_layout
            for i in reversed(range(grid.count())):
                item = grid.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                grid.removeItem(item)

        # Clear lab result/notes label (hide box if there's no content)
        if hasattr(self, "result_box"):
            self.result_box.setText("")
            self.result_box.setVisible(False)


        # Clear any cached audio player widgets (Lab 3)
        for item in getattr(self, "audio_players", []):
            if isinstance(item, tuple) and len(item) >= 2:
                pw = item[1]
                fw = item[2] if len(item) >= 3 else None
                if pw is not None:
                    pw.deleteLater()
                if fw is not None:
                    fw.deleteLater()
        self.audio_players = []


        # Create lab controller
        self.current_lab_controller = LabController(lab_id, app_controller)

        # Get lab parameters for control panel
        parameters = self.current_lab_controller.get_parameters()
        self.control_panel.set_parameters(parameters)

        # Disconnect old signal to prevent duplicate connections
        try:
            self.control_panel.parameter_changed.disconnect(self.on_parameter_changed)
        except (TypeError, RuntimeError):
            pass
        self.control_panel.parameter_changed.connect(self.on_parameter_changed)

        # Update info tab with better formatting
        # NOTE: QLabel does NOT support <style> CSS class selectors — use ONLY inline styles.
        lab_info = self.current_lab_controller.get_lab_info()
        info_text = f"""
<div style="color:#60a5fa; font-size:18px; font-weight:bold; margin-bottom:8px;">{lab_info['name'].replace('&', '&amp;')}</div>
<div style="color:#cbd5e1; font-size:13px; margin-bottom:10px; line-height:1.3;">{lab_info['description'].replace('&', '&amp;')}</div>
<div style="color:#3b82f6; font-size:20px; font-weight:bold; margin-top:8px; margin-bottom:6px;">Parameters</div>
        """
        for param_name, param_info in lab_info['parameters'].items():
            label = param_info.get("label", param_name)
            value = param_info.get("value", "N/A")
            info_text += f'<div style="color:#94a3b8; font-size:12px; margin-left:10px;">• <span style="color:#e2e8f0; font-weight:bold;">{label}</span>: {value}</div>'

        # Append lab-specific educational/theory content to the info tab
        # ALL styles must be INLINE — QLabel does NOT support CSS class selectors!
        if lab_id == 'sampling':
            info_text += """
        <br>
<div style="color:#3b82f6; font-size:20px; font-weight:bold; margin-top:8px; margin-bottom:6px;">Nyquist Sampling Theorem</div>
<div style="color:#cbd5e1; font-size:13px; margin-bottom:10px; line-height:1.3;">
        The Nyquist-Shannon sampling theorem states that to perfectly reconstruct a continuous signal from its samples, 
        the sampling frequency <b>f<sub>s</sub></b> must be at least twice the highest frequency component <b>f<sub>max</sub></b> of the signal:
        <br><br>
        <b>f<sub>s</sub> ≥ 2 · f<sub>max</sub></b>
        <br><br>
        The Nyquist frequency (folding frequency) is defined as:
        <br><br>
        <b>f<sub>Nyquist</sub> = f<sub>s</sub> / 2</b>
        <br><br>
        If a signal contains frequencies above the Nyquist limit, aliasing occurs — higher frequencies 
        fold back into the baseband, creating false lower-frequency components that cannot be distinguished 
        from genuine signals. The continuous signal used is <b>x(t) = A · cos(2π f t)</b> and its sampled 
        version is <b>x[n] = A · cos(2π f n / f<sub>s</sub>)</b>.
</div>
        """
        elif lab_id == 'convolution':
            info_text += """
        <br>
<div style="color:#3b82f6; font-size:20px; font-weight:bold; margin-top:8px; margin-bottom:6px;">Butterworth Filter Theory</div>
<div style="color:#cbd5e1; font-size:13px; margin-bottom:10px; line-height:1.3;">
        Butterworth filters are designed to have a maximally flat frequency response in the passband, 
        with no ripples. The magnitude response of an n-th order low-pass Butterworth filter is:
        <br><br>
        <b>|H(jω)|<sup>2</sup> = 1 / (1 + (ω/ω<sub>c</sub>)<sup>2n</sup>)</b>
        <br><br>
        Where <b>ω<sub>c</sub></b> is the cutoff frequency and <b>n</b> is the filter order.
        <br><br>
        <b>Filter Types Available:</b><br>
        • <b>Low-pass</b>: Passes frequencies below cutoff, attenuates above<br>
        • <b>High-pass</b>: Passes frequencies above cutoff, attenuates below<br>
        • <b>Band-pass</b>: Passes frequencies within a specified range<br>
        • <b>Band-stop</b>: Attenuates frequencies within a specified range (notch)<br><br>
        Higher filter orders result in steeper roll-off (20n dB/decade) but introduce more phase delay. 
        The default order of 4 provides a roll-off of 80 dB/decade.
</div>
        """
        elif lab_id in {'fft', 'lab4_fft'}:
            info_text += """
        <br>
<div style="color:#3b82f6; font-size:20px; font-weight:bold; margin-top:8px; margin-bottom:6px;">DFT &amp; FFT Theory</div>
<div style="color:#cbd5e1; font-size:13px; margin-bottom:10px; line-height:1.3;">
        The <b>Discrete Fourier Transform (DFT)</b> converts a finite sequence of time-domain samples 
        into a frequency-domain representation. The DFT is defined as:
        <br><br>
        <b>X[k] = Σ<sub>n=0</sub><sup>N-1</sup> x[n] · e<sup>-j·2π·k·n/N</sup></b>
        <br><br>
        Where <b>k = 0, 1, ..., N-1</b> are the frequency bins, <b>N</b> is the number of samples, 
        and <b>x[n]</b> is the input sequence.
        <br><br>
        The <b>Fast Fourier Transform (FFT)</b> is an optimized algorithm that computes the same result 
        as the DFT but in O(N log N) time instead of O(N²), making it dramatically faster for large N.
        <br><br>
        The <b>frequency resolution</b> (spacing between bins) is:
        <br><br>
        <b>Δf = f<sub>s</sub> / N</b>
        <br><br>
        Where <b>f<sub>s</sub></b> is the sampling rate. A smaller Δf means better frequency resolution.
</div>
        """
        elif lab_id == 'filtering':
            info_text += """
        <br>
<div style="color:#3b82f6; font-size:20px; font-weight:bold; margin-top:8px; margin-bottom:6px;">Windowing &amp; Spectral Leakage</div>
<div style="color:#cbd5e1; font-size:13px; margin-bottom:10px; line-height:1.3;">
        When a signal is analyzed via the DFT/FFT, it is implicitly multiplied by a rectangular window 
        that truncates the signal to a finite length. This truncation causes <b>spectral leakage</b> — 
        energy from a frequency component spreads into adjacent frequency bins.
        <br><br>
        Windowing multiplies the signal by a window function that tapers smoothly to zero at the edges, 
        reducing discontinuity and minimizing leakage:
        <br><br>
        <b>w<sub>Rect</sub>[n] = 1</b> (best resolution, highest sidelobes -13 dB)<br>
        <b>w<sub>Hann</sub>[n] = 0.5 - 0.5·cos(2πn/N)</b> (wider main lobe, -31 dB sidelobes)<br>
        <b>w<sub>Hamm</sub>[n] = 0.54 - 0.46·cos(2πn/N)</b> (good sidelobe suppression -43 dB)<br>
        <b>w<sub>Black</sub>[n] = 0.42 - 0.5·cos(2πn/N) + 0.08·cos(4πn/N)</b> (lowest sidelobes -58 dB)<br><br>
        Trade-off: <b>Main lobe width</b> (frequency resolution) vs <b>sidelobe suppression</b> (leakage reduction).
        The windowed signal is <b>x<sub>w</sub>[n] = x[n] · w[n]</b>.
</div>
        """

        # CRITICAL: Actually set the text on info_label!
        self.info_label.setText(info_text)

        # Lab2 (quantization) should not show time/frequency domain plots
        # Reset domain tabs visibility for every lab load
        self.tab_widget.setTabVisible(0, True)
        self.tab_widget.setTabVisible(1, True)

        # Hide time/frequency domain tabs for labs that render only Information text/widgets.
        if self.current_lab_id in {'quantization'}:
            # Hide both domain tabs for Lab2 image processing.
            self.tab_widget.setTabVisible(0, False)
            self.tab_widget.setTabVisible(1, False)
        else:
            # Ensure other labs restore plots visibility
            self.tab_widget.setTabVisible(0, True)
            self.tab_widget.setTabVisible(1, True)

        # Run initial processing
        self.on_process_clicked()

        # Scroll area: ONLY for Lab 4 (FFT). Other labs use direct layout.
        if self.current_lab_id in {'fft', 'lab4_fft'}:
            self._ensure_lab4_scroll()
        else:
            self._restore_normal_result_box()

        # Show container
        self.setVisible(True)

    def on_parameter_changed(self, param_name: str, value):
        """Handle parameter change in control panel"""
        if self.current_lab_controller:
            self.current_lab_controller.update_parameter(param_name, value)

    def on_file_loaded(self, time_data, signal_data, sampling_rate=None):
        """Handle file loading (or clear inputs)."""
        if not self.current_lab_controller:
            return

        # Clear inputs when loader emits (None, None)
        if time_data is None and signal_data is None:
            self.current_lab_controller.clear_custom_signal()
            self.on_process_clicked()
            return

        # Otherwise, set custom input and process
        self.current_lab_controller.set_custom_signal(time_data, signal_data, sampling_rate)
        self.on_process_clicked()

    def on_process_clicked(self):
        """Start processing in a separate thread"""
        if not self.current_lab_controller:
            return

        # Disable button during processing
        self.process_btn.setEnabled(False)
        self.process_btn.setText("PROCESSING...")
        self.process_btn.setIcon(QIcon("icons/loading.png"))

        # Get current parameters
        params = self.control_panel.get_all_values()

        # If a previous thread is still running, request it to finish first.
        # Prevents: "QThread: Destroyed while thread '' is still running"
        if self.processing_thread is not None:
            try:
                self.processing_thread.requestInterruption()
                self.processing_thread.wait(2000)
            except Exception:
                pass

        # Start processing thread
        self.processing_thread = ProcessingThread(self.current_lab_controller, params)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.finished.connect(self.processing_thread.deleteLater)
        self.processing_thread.start()

    def _reset_info_tab_content(self):
        """Fully reset the Information tab content area for a fresh state."""
        # Clear info_content_layout grid
        if hasattr(self, "info_content_layout"):
            grid = self.info_content_layout
            for i in reversed(range(grid.count())):
                item = grid.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                grid.removeItem(item)

        # Clear result_box
        if hasattr(self, "result_box"):
            self.result_box.setText("")
            self.result_box.setVisible(False)

        # Reset scroll area (remove Lab 4 scroll wrapper)
        self._restore_normal_result_box()

    def on_processing_finished(self, result):
        """Handle successful processing"""
        # Re-enable button
        self.process_btn.setEnabled(True)
        self.process_btn.setText("PROCESS SIGNAL")
        self.process_btn.setIcon(QIcon("icons/play.png"))
        self.process_btn.setIconSize(QSize(16, 16))

        # Update plots
        time_domain = result.get('time_domain')
        if time_domain and len(time_domain) == 2:
            self.time_plot.plot(time_domain[0], time_domain[1], clear=True, color='#3b82f6')

        # Skip generic freq_domain plot for Lab 4 (it uses discrete FFT bins)
        if self.current_lab_id not in {'fft', 'lab4_fft'}:
            freq_domain = result.get('freq_domain')
            if freq_domain and len(freq_domain) == 2:
                self.freq_plot.plot(freq_domain[0], freq_domain[1], clear=True, color='#60a5fa')

        # For Lab 4: plot FFT magnitude spectrum with stem-like appearance
        if self.current_lab_id in {'fft', 'lab4_fft'}:
            # Disable log scale for discrete FFT visualization
            self.freq_plot.setLogMode(False, False)
            
            lab_results = result.get('results', {})
            fft_data = lab_results.get('fft', {})
            dft_data = lab_results.get('dft', {})

            if fft_data.get('frequencies') and fft_data.get('magnitude'):
                freqs = np.array(fft_data['frequencies'])
                mag_fft = np.array(fft_data['magnitude'])
                
                # Plot FFT as stem plot (primary visualization)
                self.freq_plot.stem_plot(freqs, mag_fft, clear=True, color='#60a5fa')
                
                # Plot DFT magnitude as overlay for comparison (lighter color)
                if dft_data.get('magnitude'):
                    mag_dft = np.array(dft_data['magnitude'])
                    # Use scatter points for DFT to distinguish from FFT stems
                    if len(freqs) == len(mag_dft) and len(freqs) > 0:
                        # Plot DFT as circles with different color (faded)
                        self.freq_plot.add_scatter(freqs, mag_dft, color='#34d399', size=6)
        else:
            # Re-enable log scale for other labs that might use it
            self.freq_plot.setLogMode(False, True)

        # Store additional results
        self.current_lab_controller.set_results(result)

        # Result box: update if Lab 1 produced Nyquist/aliasing values
        lab_results = (result.get('results') or {})

        # Handle Lab 3 (Filtering) - Display filtered signals
        if self.current_lab_id == 'convolution':  # Lab 3 is mapped as 'convolution'
            self.display_lab3_results(lab_results)
            # Ensure the Information tab refreshes for Lab 3 so players appear.
            self.update_info_tab_with_players()

        elif self.current_lab_id in {'fft', 'lab4_fft'}:
            display = (lab_results or {}).get('display') if isinstance(lab_results, dict) else None

            if isinstance(display, dict):
                dft_res = display.get('dft_result', '').replace(chr(10), '<br>')
                fft_res = display.get('fft_result', '').replace(chr(10), '<br>')
                dom = display.get('dominant', '').replace(chr(10), '<br>')
                expl = display.get('explanation', '').replace(chr(10), '<br>')
                xz = display.get('xz', '')
                final_ans = display.get('final_answer', '').replace(chr(10), '<br>')

                body_html = (
                    "<table width='100%' cellpadding='0' cellspacing='0' border='0'>"
                    # Title
                    "<tr><td colspan='2' style='color:#60a5fa;font-weight:bold;font-size:16px;padding-bottom:12px;'>" + display.get('title', '') + "</td></tr>"

                    # X(z) / Final Answer - highlighted box
                    "<tr><td colspan='2' style='padding-bottom:12px;'>"
                    "  <div style='color:#e2e8f0;font-size:14px;font-weight:bold;line-height:1.8;padding:12px;background:#0b1220;border-radius:8px;border:2px solid #3b82f6;'>"
                    "    <div style='color:#60a5fa;font-size:12px;margin-bottom:4px;'>X(z) / Final Answer</div>"
                    "    <div style='font-family:monospace;'>" + xz + "</div>"
                    "  </div>"
                    "</td></tr>"

                    # Side-by-side DFT and FFT
                    "<tr>"
                    "  <td width='50%' valign='top' style='padding-right:8px;'>"
                    "    <div style='color:#3b82f6;font-size:13px;font-weight:bold;padding:8px;background:#0b1220;border-radius:6px 6px 0 0;text-align:left;'>DFT Result</div>"
                    "    <div style='color:#94a3b8;font-size:11px;line-height:1.6;font-family:monospace;background:#0b1220;padding:10px;border-radius:0 0 6px 6px;border:1px solid #1e293b;overflow-x:auto;white-space:pre-wrap;word-break:break-all;text-align:left;'>" + dft_res + "</div>"
                    "  </td>"
                    "  <td width='50%' valign='top' style='padding-left:8px;'>"
                    "    <div style='color:#3b82f6;font-size:13px;font-weight:bold;padding:8px;background:#0b1220;border-radius:6px 6px 0 0;text-align:left;'>FFT Result</div>"
                    "    <div style='color:#94a3b8;font-size:11px;line-height:1.6;font-family:monospace;background:#0b1220;padding:10px;border-radius:0 0 6px 6px;border:1px solid #1e293b;overflow-x:auto;white-space:pre-wrap;word-break:break-all;text-align:left;'>" + fft_res + "</div>"
                    "  </td>"
                    "</tr>"
                    "<tr><td colspan='2' style='height:12px;'></td></tr>"

                    # Formula
                    "<tr><td colspan='2' style='color:#3b82f6;font-size:13px;font-weight:bold;padding-bottom:6px;'>Formula</td></tr>"
                    "<tr><td colspan='2' style='color:#94a3b8;font-size:12px;line-height:1.7;padding:10px;background:#0b1220;border-radius:6px;border:1px solid #1e293b;'>X[k] = Σₙ₌₀^(N-1) x[n] · e^(-j·2π·k·n/N)</td></tr>"
                    "<tr><td colspan='2' style='height:12px;'></td></tr>"

                    # Dominant Frequencies
                    "<tr><td colspan='2' style='color:#3b82f6;font-size:13px;font-weight:bold;padding-bottom:6px;'>Dominant Frequencies</td></tr>"
                    "<tr><td colspan='2' style='color:#94a3b8;font-size:12px;line-height:1.7;font-family:monospace;background:#0b1220;padding:10px;border-radius:6px;border:1px solid #1e293b;overflow-x:auto;'>" + dom + "</td></tr>"
                    "<tr><td colspan='2' style='height:12px;'></td></tr>"

                    # Efficiency
                    "<tr><td colspan='2' style='color:#3b82f6;font-size:13px;font-weight:bold;padding-bottom:6px;'>Efficiency Comparison</td></tr>"
                    "<tr><td colspan='2' style='color:#94a3b8;font-size:12px;line-height:1.7;padding:10px;background:#0b1220;border-radius:6px;border:1px solid #1e293b;'>" + display.get('efficiency', '') + "</td></tr>"
                    "<tr><td colspan='2' style='height:12px;'></td></tr>"

                    # Explanation
                    "<tr><td colspan='2' style='color:#3b82f6;font-size:13px;font-weight:bold;padding-bottom:6px;'>Explanation</td></tr>"
                    "<tr><td colspan='2' style='color:#94a3b8;font-size:12px;line-height:1.7;font-family:monospace;background:#0b1220;padding:10px;border-radius:6px;border:1px solid #1e293b;overflow-x:auto;white-space:pre-wrap;word-break:break-all;'>" + expl + "</td></tr>"
                    "</table>"
                )
            else:
                body_html = lab_results.get('final_answer', '') if isinstance(lab_results, dict) else ''

            self.result_box.setText(body_html)
            self.result_box.setVisible(True)

            # Ensure Lab 4 scroll area has proper height
            if self._lab4_scroll is not None:
                self._lab4_scroll.setMinimumHeight(450)

        # Handle Lab 6 (Z-Transform) - Display formatted X(z) + ROC in the Information tab
        elif self.current_lab_id in {'ztransform', 'lab6_ztransform'}:
            display = (lab_results or {}).get('display') if isinstance(lab_results, dict) else None
            final_answer = (lab_results or {}).get('final_answer') if isinstance(lab_results, dict) else None

            if isinstance(display, dict):
                xz = display.get('xz', '')
                roc = display.get('roc', '')
                title = display.get('title', 'Z-transform')
                formula = display.get('formula', '')
                alternative = display.get('alternative', '')
                explanation = display.get('explanation', '')

                # Escape HTML in explanation to preserve formatting
                explanation_escaped = explanation.replace('&', '&amp;').replace('<', '<').replace('>', '>')

                body_html = (
                    f"<div style='color:#60a5fa;font-weight:bold;font-size:15px;margin-bottom:10px;'>{title}</div>"
                    f"<div style='color:#e2e8f0;font-size:13px;line-height:1.8;margin-bottom:8px;'>{xz}</div>"
                    f"<div style='color:#3b82f6;font-size:13px;font-weight:bold;margin-top:14px;margin-bottom:6px;'> Formula</div>"
                    f"<div style='color:#94a3b8;font-size:12px;line-height:1.7;margin-bottom:10px;'>{formula}</div>"
                    f"<div style='color:#3b82f6;font-size:13px;font-weight:bold;margin-top:14px;margin-bottom:6px;'> Alternative Form (Positive Powers)</div>"
                    f"<div style='color:#94a3b8;font-size:12px;line-height:1.7;margin-bottom:10px;'>{alternative}</div>"
                    f"<div style='color:#3b82f6;font-size:13px;font-weight:bold;margin-top:14px;margin-bottom:6px;'> Step-by-Step Explanation</div>"
                    f"<pre style='color:#94a3b8;font-size:12px;line-height:1.7;margin-bottom:10px;font-family:monospace;background:#0b1220;padding:10px;border-radius:6px;border:1px solid #1e293b;'>{explanation_escaped}</pre>"
                    f"<div style='color:#3b82f6;font-size:13px;font-weight:bold;margin-top:14px;margin-bottom:6px;'> Region of Convergence</div>"
                    f"<div style='color:#94a3b8;font-size:12px;line-height:1.7;'>{roc}</div>"
                )
            else:
                body_html = final_answer or ''

            # Clear any widgets in the grid (keep Information tab clean)
            if hasattr(self, 'info_content_layout'):
                grid = self.info_content_layout
                for i in reversed(range(grid.count())):
                    item = grid.itemAt(i)
                    if item is None:
                        continue
                    w = item.widget()
                    if w is not None:
                        w.deleteLater()
                    grid.removeItem(item)

            self.result_box.setText(body_html)
            self.result_box.setVisible(True)

        # Handle Lab 2 (Quantization) - Display image preview
        elif self.current_lab_id == 'quantization':
            self.display_lab2_image_results(lab_results)
        # Handle Lab 1 (Sampling) - Display Nyquist/aliasing info
        elif (

            lab_results
            and 'nyquist_frequency' in lab_results
            and 'signal_frequency' in lab_results
            and 'sampling_rate' in lab_results
        ):
            f = float(lab_results.get('signal_frequency', 0.0))
            fs = float(lab_results.get('sampling_rate', 0.0))
            nyq = float(lab_results.get('nyquist_frequency', fs / 2.0))
            f_alias = float(lab_results.get('aliased_frequency', 0.0))
            is_aliased = bool(lab_results.get('is_aliased', False))

            if is_aliased:
                header = "<b style='color:#ef4444;'>ALIASING DETECTED</b>"
                body = (
                    f"<div style='margin-top:6px;'>Original frequency f = <b>{f:.6g}</b> Hz</div>"
                    f"<div>Sampling frequency fs = <b>{fs:.6g}</b> Hz</div>"
                    f"<div>Nyquist limit fs/2 = <b>{nyq:.6g}</b> Hz</div>"
                    f"<div>Apparent (aliased) frequency = <b>{f_alias:.6g}</b> Hz</div>"
                )
            else:
                header = "<b style='color:#22c55e;'>Nyquist condition satisfied</b>"
                body = (
                    f"<div style='margin-top:6px;'>No aliasing detected</div>"
                    f"<div>f = <b>{f:.6g}</b> Hz</div>"
                    f"<div>fs/2 = <b>{nyq:.6g}</b> Hz</div>"
                )

            self.result_box.setText(header + body)
            self.result_box.setVisible(True)
        else:
            # Default handling for labs that provide a textual "final_answer" or "display".
            if isinstance(lab_results, dict):
                # Prefer a structured display dict if present
                display = lab_results.get('display')
                if isinstance(display, dict) and display.get('explanation'):
                    # Keep formatting close to other labs (HTML breaks)
                    expl = str(display.get('explanation', '')).replace(chr(10), '<br>')
                    self.result_box.setText(
                        f"<div style='color:#60a5fa;font-weight:bold;font-size:14px;margin-bottom:8px;'>Explanation</div>"
                        f"<div style='color:#94a3b8;font-size:12px;line-height:1.7;font-family:monospace;background:#0b1220;padding:10px;border-radius:6px;border:1px solid #1e293b;overflow-x:auto;white-space:pre-wrap;word-break:break-all;'>{expl}</div>"
                    )
                    self.result_box.setVisible(True)
                    return

                # Fall back to final_answer string
                final_answer = lab_results.get('final_answer')
                if final_answer:
                    body_html = str(final_answer).replace(chr(10), '<br>')
                    self.result_box.setText(body_html)
                    self.result_box.setVisible(True)
                    return

            # No renderable info
            self.result_box.setText("")
            self.result_box.setVisible(False)


    def display_lab2_image_results(self, lab_results: dict):
        """Display Lab2 (Image Processing) results using a single preview + selectable view."""
        # Clear all lab-specific widgets from the 2x2 grid so nothing leaks between labs
        if hasattr(self, "info_content_layout"):
            grid = self.info_content_layout
            for i in reversed(range(grid.count())):
                item = grid.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                grid.removeItem(item)

        # Ensure Lab3 players area doesn't keep stale widgets/text
        self.result_box.setText("")

        images_meta = (lab_results or {}).get("images", {})
        default_view_key = (lab_results or {}).get("default_view_key", "")

        preview = ImagePreviewWidget()
        preview.set_images(images_meta, default_view_key)
        preview.setMaximumWidth(780)  # Prevent grid from wiggling during processing
        preview.setMinimumWidth(600)  # Maintain consistent width
        self.info_content_layout.addWidget(preview, 0, 0)

    def display_lab3_results(self, lab_results: dict):
        """Display Lab 3 filtered signal results with audio players"""
        from ui.widgets.audio_player import AudioPlayer

        # Clear previous audio players
        for item in self.audio_players:
            # item = (filter_name, player_widget, filter_widget)
            if isinstance(item, tuple) and len(item) >= 2:
                player_widget = item[1]
                filter_widget = item[2] if len(item) >= 3 else None
                if player_widget is not None:
                    player_widget.deleteLater()
                if filter_widget is not None:
                    filter_widget.deleteLater()
        self.audio_players = []

        # Get filtered files info
        filtered_files = lab_results.get('filtered_files', {})

        if not filtered_files:
            self.result_box.setText("<b>No filtered signals available</b>")
            return

        # Get sampling rate for info
        fs = lab_results.get('fs', 44100)
        cutoffs = lab_results.get('cutoffs', {})

        # Build result HTML
        result_html = "<b style='color:#60a5fa; font-size:14px;'>Filtered Audio Signals</b>"
        result_html += f"<div style='color:#94a3b8; font-size:11px; margin-top:6px;'>Sampling Rate: <b>{fs:.0f}</b> Hz</div>"

        # Add info about each filter
        filter_info = {}
        for fname in ['lowpass', 'highpass']:
            val = cutoffs.get(fname)
            if val is None:
                filter_info[fname] = f"{fname.capitalize()}-pass (cutoff: N/A Hz)"
            else:
                filter_info[fname] = f"{fname.capitalize()}-pass (cutoff: {float(val):.0f} Hz)"
        for fname in ['bandpass', 'bandstop']:
            pair = cutoffs.get(fname)
            if pair is None or not isinstance(pair, (list, tuple)) or len(pair) < 2:
                filter_info[fname] = f"{fname.capitalize()} (range: N/A Hz)"
            else:
                lo, hi = float(pair[0]), float(pair[1])
                filter_info[fname] = f"{fname.capitalize()} (range: {lo:.0f} - {hi:.0f} Hz)"

        result_html += "<div style='margin-top:12px;'>"
        for filter_name in ['lowpass', 'highpass', 'bandpass', 'bandstop']:
            if filter_name in filtered_files:
                result_html += f"<div style='color:#cbd5e1; font-size:12px; margin-top:8px;'>> {filter_info[filter_name]}</div>"
        result_html += "</div>"

        # Keep HTML note minimal; audio widget includes only play + download in lab 3 grid.
        result_html += "<div style='margin-top:12px; color:#94a3b8; font-size:11px;'>Play or download each filtered signal.</div>"

        # IMPORTANT: self.result_box is a QLabel, so it cannot host Qt widgets.
        # Only set text here; the actual AudioPlayer/Quick Play buttons are added below.
        self.result_box.setText(result_html)

        # Clear any previous widgets from the info content layout
        if hasattr(self, "info_content_layout"):
            grid = self.info_content_layout
            for i in reversed(range(grid.count())):
                item = grid.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                grid.removeItem(item)

        # Create audio player widgets for each filter in a 2x2 grid
        filter_order = ['lowpass', 'highpass', 'bandpass', 'bandstop']
        placed_idx = 0
        for filter_name in filter_order:
            if filter_name not in filtered_files:
                continue

            file_info = filtered_files[filter_name]
            file_path = file_info.get('path', '')

            # Create a container for the player
            filter_widget = QWidget()
            filter_layout = QVBoxLayout(filter_widget)
            filter_layout.setContentsMargins(0, 0, 0, 0)
            filter_layout.setSpacing(5)

            # Label
            label = QLabel(filter_info[filter_name])
            label.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 12px;")
            filter_layout.addWidget(label)

            # Audio player
            player = AudioPlayer()
            if player.set_file(file_path):
                filter_layout.addWidget(player)
                self.audio_players.append((filter_name, player, filter_widget))

            else:
                error_label = QLabel(f"Error: Could not load {filter_name} audio file")
                error_label.setStyleSheet("color: #ef4444; font-size: 11px;")
                filter_layout.addWidget(error_label)

            # Add widget into 2x2 grid: row 0-1, col 0-1
            if hasattr(self, "info_content_layout"):
                row = placed_idx // 2
                col = placed_idx % 2
                self.info_content_layout.addWidget(filter_widget, row, col)

            placed_idx += 1

        # Update info tab to show players are available
        if self.audio_players:
            self.update_info_tab_with_players()

    def update_info_tab_with_players(self):
        """Update the info tab to display audio players"""
        current_text = self.result_box.text()
        if "Filtered Audio Signals" in current_text:
            # Add a note that players are displayed
            self.result_box.setText(
                current_text + 
                "<div style='margin-top:16px; padding-top:12px; border-top:1px solid #1e293b; color:#22c55e; font-size:11px;'>"
                "Audio players ready in the Information tab</div>"
            )

    def on_processing_error(self, error_msg):
        """Handle processing error - preserve existing info text, just show error"""
        self.process_btn.setEnabled(True)
        self.process_btn.setText("PROCESS SIGNAL")
        self.process_btn.setIcon(QIcon("icons/play.png"))
        self.process_btn.setIconSize(QSize(16, 16))
        # Append error message to existing info text instead of replacing it
        current_text = self.info_label.text()
        if "Lab information will appear here" in current_text:
            self.info_label.setText(f"<font color='#ef4444'>Error: {error_msg}</font>")
        else:
            self.info_label.setText(
                current_text +
                f"<br><br><div style='color:#ef4444; font-weight:bold; border:1px solid #ef4444; "
                f"border-radius:6px; padding:8px; background:#0b1220;'>"
                f"⚠ Processing Error: {error_msg}</div>"
            )

