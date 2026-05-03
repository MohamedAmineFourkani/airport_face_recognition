#!/usr/bin/env python3
"""
Setup Script - Creates venv inside project folder and installs requirements
NO dlib/face_recognition needed - uses pure OpenCV
"""

import subprocess
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, "venv")

def run(cmd, cwd=None):
    print(f"\n[RUN] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or PROJECT_DIR)
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(1)

def main():
    print("=" * 60)
    print("AIRPORT FACE RECOGNITION - SETUP")
    print("=" * 60)

    if os.path.exists(VENV_DIR):
        print(f"\n[INFO] Virtual environment already exists at: {VENV_DIR}")
    else:
        print(f"\n[INFO] Creating virtual environment at: {VENV_DIR}")
        run(f'"{sys.executable}" -m venv venv')

    if sys.platform == "win32":
        pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        python_path = os.path.join(VENV_DIR, "bin", "python")

    print("\n[INFO] Upgrading pip...")
    run(f'"{python_path}" -m pip install --upgrade pip')

    print("\n[INFO] Installing requirements...")
    req_file = os.path.join(PROJECT_DIR, "requirements.txt")
    run(f'"{pip_path}" install -r "{req_file}"')

    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nVirtual environment: {VENV_DIR}")
    print("\nTo run the application:")
    print(f"    python run.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
