import PyInstaller.__main__
import os
import sys

def build_exe():
    # Konfigurasi build
    print("Building client executable...")
    
    PyInstaller.__main__.run([
        'client.py',
        '--onefile',  # Single executable
        '--windowed',  # No console window
        '--name=WindowsUpdate',  # Nama file output
        '--icon=icon.ico',  # Optional: icon file
        '--add-data=config.json;.',  # Optional: include config file
        '--clean',
        '--noconfirm'
    ])
    
    print("Build complete! Check dist/ folder.")

if __name__ == "__main__":
    build_exe()