from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QProgressBar,
                            QTextEdit, QMessageBox, QDialog, QLineEdit,
                            QDialogButtonBox, QCheckBox, QStyleFactory, QTabWidget, QSlider, QListWidget,
                            QGroupBox, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from video_analyzer import VideoBatchAnalyzer

import os     
          
class VideoAnalysisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.video_files = []  # List untuk menyimpan file video
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Input video selection (Multiple files)
        input_group = QLabel("Input Videos:")
        input_layout = QHBoxLayout()
        
        self.video_list = QListWidget()  # Mengganti QLabel dengan QListWidget
        self.video_list.setMinimumHeight(100)
        
        # Button layout untuk video input
        video_button_layout = QVBoxLayout()
        add_button = QPushButton("Add Videos")
        add_button.setObjectName("browseButton")
        add_button.clicked.connect(self.select_input_videos)
        
        clear_button = QPushButton("Clear List")
        clear_button.setObjectName("clearButton")
        clear_button.clicked.connect(self.clear_video_list)
        
        video_button_layout.addWidget(add_button)
        video_button_layout.addWidget(clear_button)
        
        input_layout.addWidget(input_group)
        input_layout.addWidget(self.video_list)
        input_layout.addLayout(video_button_layout)
        layout.addLayout(input_layout)

        # Output folder selection
        output_layout = QHBoxLayout()
        output_label = QLabel("Output Folder:")
        self.output_path = QLabel("Not selected")
        output_button = QPushButton("Browse")
        output_button.setObjectName("browseButton")
        output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        # Frame position settings
        frame_group = QGroupBox("Frame Settings")
        frame_layout = QVBoxLayout()

        # Frame position slider
        slider_layout = QHBoxLayout()
        slider_label = QLabel("Frame Position:")
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(100)
        self.frame_slider.setValue(50)
        self.frame_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.frame_position_label = QLabel("50%")
        self.frame_slider.valueChanged.connect(self.update_frame_position)
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.frame_slider)
        slider_layout.addWidget(self.frame_position_label)
        frame_layout.addLayout(slider_layout)

        frame_group.setLayout(frame_layout)
        layout.addWidget(frame_group)

        # Progress information
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        # Overall progress
        overall_layout = QHBoxLayout()
        overall_label = QLabel("Overall Progress:")
        self.overall_progress = QProgressBar()
        overall_layout.addWidget(overall_label)
        overall_layout.addWidget(self.overall_progress)
        progress_layout.addLayout(overall_layout)

        # Current video progress
        current_layout = QHBoxLayout()
        current_label = QLabel("Current Video:")
        self.current_progress = QProgressBar()
        current_layout.addWidget(current_label)
        current_layout.addWidget(self.current_progress)
        progress_layout.addLayout(current_layout)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton("Start Video Analysis")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
    def select_output_folder(self):
        """Method untuk memilih output folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_path.setText(folder)
            self.check_start_button()

    def select_input_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )
        if files:
            self.video_files.extend(files)
            self.update_video_list()
            self.check_start_button()

    def clear_video_list(self):
        self.video_files.clear()
        self.video_list.clear()
        self.check_start_button()

    def update_video_list(self):
        self.video_list.clear()
        for file in self.video_files:
            self.video_list.addItem(os.path.basename(file))

    def check_start_button(self):
        if self.video_files and self.output_path.text() != "Not selected":
            self.start_button.setEnabled(True)
        else:
            self.start_button.setEnabled(False)
            
    def update_frame_position(self):
        """Method untuk update label posisi frame"""
        value = self.frame_slider.value()
        self.frame_position_label.setText(f"{value}%")


    def start_analysis(self):
        if not self.parent.api_key:
            QMessageBox.warning(self, "Warning", "Please set your API key first!")
            self.parent.show_settings_dialog()
            return

        settings = {
            'frame_position': self.frame_slider.value() / 100,
            'request_delay': 2,
            'max_retries': 3
        }

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_text.clear()
        self.overall_progress.setValue(0)
        self.current_progress.setValue(0)

        self.batch_analyzer = VideoBatchAnalyzer(
            video_files=self.video_files,
            output_folder=self.output_path.text(),
            api_key=self.parent.api_key,
            settings=settings
        )

        self.batch_analyzer.overall_progress_updated.connect(self.update_overall_progress)
        self.batch_analyzer.current_progress_updated.connect(self.update_current_progress)
        self.batch_analyzer.status_updated.connect(self.update_status)
        self.batch_analyzer.analysis_complete.connect(self.analysis_completed)
        self.batch_analyzer.error_occurred.connect(self.handle_error)
        self.batch_analyzer.start()

    def stop_analysis(self):
        reply = QMessageBox.question(
            self,
            'Confirm Stop',
            'Are you sure you want to stop the analysis?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'batch_analyzer') and self.batch_analyzer.isRunning():
                self.batch_analyzer.stop_requested = True
                self.status_text.append("\nStopping analysis... Please wait...")
                self.stop_button.setEnabled(False)
                self.stop_button.setText("Stopping...")

    def update_overall_progress(self, value):
        self.overall_progress.setValue(value)

    def update_current_progress(self, value):
        self.current_progress.setValue(value)

    def update_status(self, message):
        self.status_text.append(message)

    def analysis_completed(self, results):
        self.status_text.append("\nAll videos analyzed successfully!")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stop")
        
        # Tampilkan summary
        summary = f"\nAnalysis Summary:\n"
        summary += f"Total videos processed: {len(results)}\n"
        summary += f"Results saved in: {self.output_path.text()}\n"
        
        self.status_text.append(summary)
        
        QMessageBox.information(
            self,
            "Success",
            f"Video analysis completed!\nResults saved in:\n{self.output_path.text()}"
        )

    def handle_error(self, error_message):
        self.status_text.append(f"Error: {error_message}")
        if not hasattr(self, 'batch_analyzer') or not self.batch_analyzer.isRunning():
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.stop_button.setText("Stop")
        QMessageBox.warning(self, "Error", error_message)
