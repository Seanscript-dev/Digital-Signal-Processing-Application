#!/usr/bin/env python3
"""Test Lab 4 plotting to verify stem plot visualization works"""

import sys
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from controller.lab_controller import LabController
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from ui.widgets.plot_widget import PlotWidget

def test_stem_plot():
    """Test stem plot functionality"""
    app = QApplication(sys.argv)
    
    # Create a test window
    window = QWidget()
    window.setWindowTitle("Lab 4 FFT Stem Plot Test")
    layout = QVBoxLayout(window)
    
    # Create plot widget
    plot = PlotWidget("FFT Magnitude Spectrum", "Frequency (Hz)", "Magnitude")
    layout.addWidget(plot)
    
    # Get Lab 4 controller
    class DummyAppController:
        pass
    
    lab_controller = LabController('fft', DummyAppController())
    
    # Process with default sequence
    result = lab_controller.process()
    
    # Extract FFT data
    lab_results = result.get('results', {})
    fft_data = lab_results.get('fft', {})
    freqs = np.array(fft_data.get('frequencies', []))
    mag = np.array(fft_data.get('magnitude', []))
    
    print(f"Frequencies: {freqs}")
    print(f"Magnitudes: {mag}")
    
    # Plot using stem plot
    plot.stem_plot(freqs, mag, clear=True, color='#60a5fa')
    
    # Show window
    window.resize(800, 600)
    window.show()
    
    # Run event loop for a few seconds then close
    from PySide6.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_stem_plot()
