"""
Clean all demo/personal data from the project before pushing to GitHub.
"""

import sqlite3
import os
import glob

DB_FILE = "airport_security.db"
ENCODINGS_FILE = "face_encodings.pkl"
UPLOAD_DIR = "static/uploads"

# Clear SQLite database
if os.path.exists(DB_FILE):
    print("[*] Clearing database tables...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM travelers")
    c.execute("DELETE FROM recognition_logs")
    conn.commit()
    conn.close()
    print("[+] Database tables cleared (travelers & recognition_logs)")
else:
    print("[!] Database not found, skipping")

# Clear face encodings pickle
if os.path.exists(ENCODINGS_FILE):
    os.remove(ENCODINGS_FILE)
    print(f"[+] Removed {ENCODINGS_FILE}")
else:
    print("[!] Face encodings file not found, skipping")

# Clear uploaded images
if os.path.exists(UPLOAD_DIR):
    for folder in os.listdir(UPLOAD_DIR):
        folder_path = os.path.join(UPLOAD_DIR, folder)
        if os.path.isdir(folder_path):
            for f in glob.glob(os.path.join(folder_path, "*")):
                os.remove(f)
            print(f"[+] Cleared images from {folder_path}")
else:
    print("[!] Upload directory not found, skipping")

print("\n[+] All personal data cleared. Project is clean for GitHub.")
