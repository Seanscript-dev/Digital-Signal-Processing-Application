# ui/widgets/audio_player.py
"""Audio player widget for playing and downloading filtered audio files."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QUrl

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os


class AudioPlayer(QWidget):
    """Widget for playing and downloading audio files"""

    def __init__(self):
        super().__init__()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.current_file = None
        self.is_playing = False
        self._duration_ready = False
        self._pending_play = False

        # Connect player signals
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)

        # Timer to force-stop / re-check if duration is still wrong after load
        self._load_timer = QTimer(self)
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._on_load_timeout)

        # Duration validation settings
        self._min_duration_ms = 2000
        self._duration_stability_required = 3  # consecutive samples

        self._duration_candidates = 0
        self._last_duration_ms = -1


        self.setup_ui()

    def setup_ui(self):
        """Setup the audio player UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Control buttons
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)

        # Play button
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play)

        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3a8a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        control_layout.addWidget(self.play_btn)

        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.download)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #065f46;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #059669;
            }
        """)
        control_layout.addWidget(self.download_btn)


        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #1e293b;
                border-radius: 3px;
                background-color: #0f172a;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Time labels
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(5)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)

        layout.addLayout(time_layout)

    def set_file(self, file_path: str):
        """Set the audio file to play"""
        if not os.path.exists(file_path):
            return False

        self.current_file = file_path
        self._duration_ready = False
        self._pending_play = False

        try:
            url = QUrl.fromLocalFile(os.path.abspath(file_path))
            self.media_player.setSource(url)
            # Wait for media to fully load before reporting success
            return True
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False

    def play(self):
        """Play the audio file (plays full duration)"""

        """Play the audio file (plays full duration)"""
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please load an audio file first")
            return

        if self.is_playing:
            # Pause should retain current position (no seek)
            self.media_player.pause()
            self.is_playing = False
            self.play_btn.setText("▶ Play")
            return

        # Resume: keep current position unless we're explicitly starting from 0.
        if not getattr(self, "_starting_over", False):
            # Ensure we don't rewind when toggling pause/play
            self._starting_over = False
        else:
            self.media_player.setPosition(0)
            self._starting_over = False



        # Check if media is fully loaded (duration > 0 and reasonable)
        duration = self.media_player.duration()

        # If duration is not ready or suspiciously short, wait for it
        if duration < self._min_duration_ms or not self._duration_ready:

            self._pending_play = True
            self._load_timer.start(500)  # Wait up to 500ms for duration to settle
            # Still try to play immediately - QMediaPlayer may handle it
            self.media_player.play()
        else:
            self.media_player.play()

        self.is_playing = True
        self.play_btn.setText("⏸ Pause")

    def _on_load_timeout(self):
        """Handle case where duration took time to load"""
        if self._pending_play:
            duration = self.media_player.duration()
            if duration > 2000:
                # Duration is now valid, ensure we're playing from start
                self.media_player.setPosition(0)
                if self.media_player.playbackState() != QMediaPlayer.PlayingState:
                    self.media_player.play()
            self._pending_play = False

    def stop(self):
        """Stop playback"""
        self.media_player.stop()
        self.is_playing = False
        self.play_btn.setText("▶ Play")
        self.progress_bar.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def download(self):
        """Copy the audio file to downloads or user-selected location"""
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please load an audio file first")
            return

        from PySide6.QtWidgets import QFileDialog
        import shutil

        # Get filename
        filename = os.path.basename(self.current_file)
        default_name = os.path.splitext(filename)[0] + "_filtered" + os.path.splitext(filename)[1]

        # Show save dialog
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audio File",
            default_name,
            "WAV Files (*.wav);;All Files (*.*)"
        )

        if save_path:
            try:
                shutil.copy(self.current_file, save_path)
                QMessageBox.information(self, "Success", f"File saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")

    def on_position_changed(self, position: int):
        """Update progress bar and time label"""
        duration = self.media_player.duration()
        if duration > 0:
            self.progress_bar.setValue(int((position / duration) * 100))

        # Update time label
        current_time = self.format_time(position)
        total_time = self.format_time(duration)
        self.time_label.setText(f"{current_time} / {total_time}")

    def on_duration_changed(self, duration: int):
        """Handle duration updates.

        QMediaPlayer may emit an early/incorrect duration (e.g. ~1s) before the
        decoder finishes reading the WAV header/metadata. To fix that, only
        trust the duration after it has remained stable for a few consecutive
        signals and is above a minimum length.
        """
        if duration <= 0:
            return

        # Ignore obviously wrong durations (keep waiting)
        if duration < self._min_duration_ms:
            self._duration_ready = False
            self._duration_candidates = 0
            self._last_duration_ms = duration
            return

        # Stability check
        if self._last_duration_ms == duration:
            self._duration_candidates += 1
        else:
            self._last_duration_ms = duration
            self._duration_candidates = 1

        if self._duration_candidates >= self._duration_stability_required:
            if not self._duration_ready:
                self._duration_ready = True

            # Now that duration is validated, update UI consistently
            self.time_label.setText(f"00:00 / {self.format_time(duration)}")

            # If we were waiting to play, resume now that duration is valid
            if self._pending_play:
                self._pending_play = False
                self._load_timer.stop()
                self.media_player.setPosition(0)
                if self.media_player.playbackState() != QMediaPlayer.PlayingState:
                    self.media_player.play()


    def on_media_status_changed(self, status):
        """Handle media status changes"""
        try:
            dur = self.media_player.duration()
            pos = self.media_player.position()
            print(f"[AudioPlayer] mediaStatusChanged={status} pos={pos}ms dur={dur}ms")
        except Exception:
            pass

        if status == QMediaPlayer.EndOfMedia:
            self.is_playing = False
            self.play_btn.setText("▶ Play")
            self.progress_bar.setValue(0)
        elif status == QMediaPlayer.LoadedMedia:
            # LoadedMedia means the backend is ready; real duration may still update.
            # We still rely on duration stability in on_duration_changed.
            self._duration_ready = True


    def on_playback_state_changed(self, state):
        """Handle playback state changes to detect unexpected stops"""
        if state == QMediaPlayer.StoppedState and self.is_playing:
            # Check if we stopped unexpectedly (not at end of media)
            position = self.media_player.position()
            duration = self.media_player.duration()

            # If stopped before 90% of duration, it might be a premature stop
            if duration > 0 and position < duration * 0.9:
                print(f"Warning: Playback stopped unexpectedly at {position}ms / {duration}ms")
                # Try to resume if duration is valid
                if duration > 2000:
                    self.media_player.setPosition(position)
                    self.media_player.play()
            else:
                # Normal end of playback
                self.is_playing = False
                self.play_btn.setText("▶ Play")
                self.progress_bar.setValue(0)

    @staticmethod
    def format_time(milliseconds: int) -> str:
        """Format time in milliseconds to MM:SS"""
        if milliseconds < 0:
            milliseconds = 0

        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60

        return f"{minutes:02d}:{seconds:02d}"