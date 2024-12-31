from PyQt6.QtWidgets import (QVBoxLayout, 
                            QPushButton, QLabel, QMessageBox, QDialog,
                            QDialogButtonBox, QListWidget,
                            QGroupBox, QApplication)
import google.generativeai as genai


class ModelSelectionDialog(QDialog):
    def __init__(self, parent=None, available_models=None):
        super().__init__(parent)
        self.parent = parent
        self.available_models = available_models or []
        self.selected_model = parent.selected_model
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Select Model")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Model list
        model_group = QGroupBox("Available Models")
        model_layout = QVBoxLayout()

        self.model_list = QListWidget()
        if self.available_models:
            self.model_list.addItems(self.available_models)
            # Select current model
            for i in range(self.model_list.count()):
                if self.model_list.item(i).text() == self.selected_model:
                    self.model_list.setCurrentRow(i)
                    break
        else:
            self.model_list.addItem("No models available")
        
        model_layout.addWidget(self.model_list)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Status and info
        self.status_label = QLabel()
        self.status_label.setText(f"Current model: {self.selected_model}")
        layout.addWidget(self.status_label)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Refresh button
        refresh_button = QPushButton("Refresh Models")
        refresh_button.clicked.connect(self.refresh_models)
        layout.addWidget(refresh_button)

    def refresh_models(self):
        try:
            if not self.parent.api_key:
                QMessageBox.warning(self, "Warning", "Please set API key first.")
                return

            genai.configure(api_key=self.parent.api_key)
            self.available_models = []
            
            # Show loading indicator
            self.status_label.setText("Loading models...")
            QApplication.processEvents()

            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    self.available_models.append(m.name)

            # Update list widget
            self.model_list.clear()
            self.model_list.addItems(self.available_models)

            # Select current model
            for i in range(self.model_list.count()):
                if self.model_list.item(i).text() == self.selected_model:
                    self.model_list.setCurrentRow(i)
                    break

            self.status_label.setText(f"Found {len(self.available_models)} models")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh models: {str(e)}")
            self.status_label.setText("Error loading models")

    def get_selected_model(self):
        if self.model_list.currentItem():
            return self.model_list.currentItem().text()
        return self.selected_model

    def accept(self):
        if self.model_list.currentItem():
            self.selected_model = self.model_list.currentItem().text()
        super().accept()
        
