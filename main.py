"""
DSP Analysis System - Main Entry Point
A comprehensive desktop application for digital signal processing education and analysis
"""
import sys
from pathlib import Path


def _verify_python_runtime() -> None:
    """Detect a broken/mismatched Python interpreter early.

    The project itself is fine; this guards against cases where the user runs
    a bundled/broken interpreter (e.g., from GTKWave/iverilog) that cannot
    import the stdlib 'encodings' module.
    """
    try:
        import encodings  # noqa: F401
    except Exception as e:
        msg = (
            "Python runtime validation failed.\n\n"
            f"sys.executable: {sys.executable}\n"
            f"sys.prefix: {sys.prefix}\n\n"
            "Error: "
            f"{type(e).__name__}: {e}\n\n"
            "Fix: ensure VSCode/terminal uses a proper Python installation and/or a venv "
            "created with that Python. Do NOT use an interpreter from unrelated tool bundles."
        )
        raise RuntimeError(msg) from e


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """Application entry point"""
    _verify_python_runtime()

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.showMaximized()
    print('DEBUG: MainWindow visible=', window.isVisible())
    geom = window.geometry()
    print(f'DEBUG: MainWindow geometry={geom.x()},{geom.y()},{geom.width()},{geom.height()}')
    window.start_loading(
        logo_path="icons/logoo.png",
        duration_ms=5000,
    )
    app.processEvents()

    print('DEBUG: entering app.exec()')
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
