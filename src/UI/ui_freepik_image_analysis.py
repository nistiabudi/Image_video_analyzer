from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QProgressBar,
                            QTextEdit, QMessageBox, QDialog, QLineEdit,
                            QDialogButtonBox, QCheckBox, QStyleFactory, QTabWidget, QSlider, QListWidget,
                            QGroupBox, QApplication, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from freepik_image_analzyer import FreepikImageAnalyzer

class FreepikImageAnalysisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Input folder selection
        input_layout = QHBoxLayout()
        input_label = QLabel("Input Folder:")
        self.input_path = QLabel("Not selected")
        input_button = QPushButton("Browse")
        input_button.setObjectName("browseButton")
        input_button.clicked.connect(self.select_input_folder)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_button)
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
        
        # Model source selection
        model_source = [
            "Adobe Firefly", "Dall-e 1", "Dall-e 2", "Dall-e 3", "Freepik Classic", "Freepik Classic Fast", "Freepik Flux",
            "Freepik Flux Fast", "Freepik Flux Realism", "Freepik Mystic 1.0", "Freepik Mystic 2.5", "Freepik Mystic 2.5 Flexible", "Freepik Pikaso",
            "Ideogram 1.0","Leonardo","Midjourney 1","Midjourney 2","Midjourney 4","Midjourney 5","Midjourney 5.1", "Midjourney 5.2", "Midjourney 6",
            "niji", "Stable Diffusion 1.4", "Stable Diffusion 1.5", "Stable Diffusion 2.0", "Stable Diffusion 2.1", "Stable Diffusion XL", "Wepik"]
        self.combo_box = QComboBox()
        layout.addWidget(QLabel("Select Model Source:"))
        self.combo_box.addItems(model_source)
        layout.addWidget(self.combo_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton("Start Image Analysis")
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
        pass

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_path.setText(folder)
            self.check_start_button()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)
            self.check_start_button()

    def check_start_button(self):
        if (self.input_path.text() != "Not selected" and 
            self.output_path.text() != "Not selected"):
            self.start_button.setEnabled(True)
        else:
            self.start_button.setEnabled(False)

    def start_analysis(self):
        if not self.parent.api_key:
            QMessageBox.warning(self, "Warning", "Please set your API key first!")
            self.parent.show_settings_dialog()
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_text.clear()
        self.progress_bar.setValue(0)

        self.analyzer = FreepikImageAnalyzer(
            input_folder=self.input_path.text(),
            output_folder=self.output_path.text(),
            model_source=self.combo_box.currentText(),
            api_key=self.parent.api_key,
            settings=self.parent.settings
        )
        self.analyzer.progress_updated.connect(self.update_progress)
        self.analyzer.analysis_complete.connect(self.analysis_completed)
        self.analyzer.error_occurred.connect(self.handle_error)
        self.analyzer.start()

    def stop_analysis(self):
        reply = QMessageBox.question(
            self,
            'Confirm Stop',
            'Are you sure you want to stop the analysis?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'analyzer') and self.analyzer.isRunning():
                self.analyzer.stop_requested = True
                self.status_text.append("\nStopping analysis... Please wait...")
                self.stop_button.setEnabled(False)
                self.stop_button.setText("Stopping...")

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_text.append(message)

    def analysis_completed(self, df):
        self.status_text.append("\nAnalysis completed successfully!")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stop")
        QMessageBox.information(
            self,
            "Success",
            f"Analysis completed! CSV file saved in:\n{self.output_path.text()}"
        )

    def handle_error(self, error_message):
        self.status_text.append(f"Error: {error_message}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stop")
        QMessageBox.warning(self, "Error", error_message)
  