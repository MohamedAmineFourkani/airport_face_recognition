#!/usr/bin/env python3
"""
Run Script - Starts the app using the venv inside the project folder
"""

import subprocess
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "win32":
    python_path = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")
else:
    python_path = os.path.join(PROJECT_DIR, "venv", "bin", "python")

if not os.path.exists(python_path):
    print("[ERROR] Virtual environment not found. Run: python setup.py")
    sys.exit(1)

print("[INFO] Starting Airport Face Recognition System...")
subprocess.run([python_path, "app.py"], cwd=PROJECT_DIR)
