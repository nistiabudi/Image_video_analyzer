from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QMessageBox, QDialog, QLineEdit,
                            QDialogButtonBox, QCheckBox, QTabWidget)
from PyQt6.QtGui import QAction
import os
import json
import google.generativeai as genai
from UI.ui_image_analysis import ImageAnalysisTab
from UI.ui_video_analysis import VideoAnalysisTab
from UI.model_selection_dialog import ModelSelectionDialog
from UI.ui_freepik_image_analysis import FreepikImageAnalysisTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = ""
        self.settings = {}
        self.selected_model = "gemini-1.5-flash"
        self.setup_ui()
        self.create_menu_bar()
        self.load_settings()

    def setup_ui(self):
        self.setWindowTitle("Media Analyzer Pro")
        self.setMinimumSize(800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add Image Analysis tab
        self.image_tab = ImageAnalysisTab(self)
        self.tab_widget.addTab(self.image_tab, "Image Analysis")
        
        # Add Video Analysis tab
        self.video_tab = VideoAnalysisTab(self)
        self.tab_widget.addTab(self.video_tab, "Video Analysis")
        
        # Add Image Analysis tab
        self.image_tab = FreepikImageAnalysisTab(self)
        self.tab_widget.addTab(self.image_tab, "Freepik Image Analysis")
        
        main_layout.addWidget(self.tab_widget)

        # Status bar
        self.statusBar().showMessage('Ready')

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        # API Settings action
        api_settings_action = QAction('API Settings', self)
        api_settings_action.setStatusTip('Change API Key settings')
        api_settings_action.triggered.connect(self.api_show_settings_dialog)
        settings_menu.addAction(api_settings_action)
        
        # # Refresh Models action
        # refresh_models_action = QAction('Refresh Models', self)
        # refresh_models_action.setStatusTip('Refresh available Models')
        # refresh_models_action.triggered.connect(self.load_available_dialog)
        # settings_menu.addAction(refresh_models_action) 
        
        # Select Models action
        select_model_action = QAction('Select Models', self)
        select_model_action.setStatusTip('Change Another Models')
        select_model_action.triggered.connect(self.show_model_dialog)
        settings_menu.addAction(select_model_action)
        
    def show_model_dialog(self):
        dialog = ModelSelectionDialog(self)
        dialog.exec()
        
    def load_available_dialog(self):
        try:
            if not self.api_key:
                QMessageBox.warning(self, "Warning", "Please Set API Key first to load Models.")
                return
            
            #Konfigurasi API
            genai.configure(api_key=self.api_key)
            
            #Load Models
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
                    
            # Show model selection dialog with loaded models
            dialog = ModelSelectionDialog(self, available_models)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.selected_model = dialog.get_selected_model()
                self.settings['selected_model'] = self.selected_model
                self.save_settings()
                self.statusBar().showMessage(f"Selected model: {self.selected_model}", 3000)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load models: {str(e)}")
            
    def api_show_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("API Settings")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()

        # Current API Key display
        current_api_layout = QHBoxLayout()
        current_api_label = QLabel("Current API Key:")
        current_api_value = QLabel("Not set" if not self.api_key else 
                                 '*' * (len(self.api_key) - 4) + self.api_key[-4:])
        current_api_layout.addWidget(current_api_label)
        current_api_layout.addWidget(current_api_value)
        layout.addLayout(current_api_layout)

        # New API Key input
        new_api_layout = QHBoxLayout()
        new_api_label = QLabel("New API Key:")
        new_api_input = QLineEdit()
        new_api_input.setPlaceholderText("Enter new API key here")
        new_api_input.setEchoMode(QLineEdit.EchoMode.Password)
        new_api_layout.addWidget(new_api_label)
        new_api_layout.addWidget(new_api_input)
        layout.addLayout(new_api_layout)

        # Show/Hide password checkbox
        show_password = QCheckBox("Show API Key")
        show_password.stateChanged.connect(
            lambda state: new_api_input.setEchoMode(
                QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
            )
        )
        layout.addWidget(show_password)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_api = new_api_input.text().strip()
            if new_api:
                self.api_key = new_api
                self.settings['api_key'] = new_api
                self.save_settings()
                QMessageBox.information(self, "Success", 
                                      "API Key has been updated successfully!")
            else:
                QMessageBox.warning(self, "Warning", 
                                  "API Key cannot be empty!")

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    self.settings = json.load(f)
                    self.api_key = self.settings.get('api_key', '')
                    self.selected_model = self.settings.get('selected_model', 'gemini-1.5-flash')
            else:
                self.settings = {
                    'api_key': '',
                    'selected_model': 'gemini-1.5-flash',
                    'request_delay': 2,
                    'batch_size': 5,
                    'max_retries': 3
                }
                self.save_settings()
        except Exception as e:
            QMessageBox.warning(self, "Warning", 
                              f"Error loading settings: {str(e)}")

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.statusBar().showMessage("Settings saved successfully!", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Warning", 
                              f"Error saving settings: {str(e)}")
        
