import PyInstaller.__main__
import os
import sys

def build_exe():
    # Get absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    assets_path = os.path.join(current_dir, 'assets')
    
    # Ensure assets folder exists
    if not os.path.exists(assets_path):
        os.makedirs(assets_path)
    
    PyInstaller.__main__.run([
        os.path.join(src_path, 'main.py'),
        '--name=AnalyzerAppUpdated',
        '--onefile',
        '--windowed',
        f'--icon={os.path.join(assets_path, "icon.ico")}',
        '--add-data', f'{assets_path};assets',
        '--hidden-import=PIL._tkinter',
        '--hidden-import=google.generativeai',
        f'--paths={src_path}',
        '--noconfirm',
        '--clean',
        '--add-binary', f'{assets_path};assets',
        '--collect-data=google.generativeai',
        '--collect-all=PIL',
    ])

if __name__ == "__main__":
    build_exe()