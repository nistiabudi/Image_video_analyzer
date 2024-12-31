import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QStyleFactory
from PyQt6.QtCore import Qt
from ui import MainWindow
from video_analyzer import VideoAnalyzer

def setup_exception_handler():
    def exception_hook(exctype, value, traceback_obj):
        error_msg = ''.join(traceback.format_exception(exctype, value, traceback_obj))
        QMessageBox.critical(None, "Error",
                           "An unexpected error occurred:\n\n" + error_msg)
    
    sys.excepthook = exception_hook

def load_stylesheet(app):
    try:
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            application_path = os.path.dirname(current_dir)
        
        style_path = os.path.join(application_path, 'assets', 'style.qss')
        
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
                print(f"Stylesheet loaded from: {style_path}")
        else:
            print(f"Style file not found at: {style_path}")
    except Exception as e:
        print(f"Error loading stylesheet: {str(e)}")

def main():
    # Initialize application
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistency
    app.setStyle(QStyleFactory.create('Fusion'))
    
    # Setup exception handler
    setup_exception_handler()
    
    # Load stylesheet
    load_stylesheet(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()