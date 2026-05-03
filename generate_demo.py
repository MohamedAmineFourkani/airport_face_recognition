#!/usr/bin/env python3
"""
Demo Data Generator for Airport Face Recognition System
Generates sample travelers and recognition logs for testing
"""

import sqlite3
import random
from datetime import datetime, timedelta
import uuid

DB_PATH = "airport_security.db"

def generate_demo_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Sample data
    names = [
        "John Smith", "Emma Johnson", "Michael Brown", "Sarah Davis",
        "James Wilson", "Olivia Martinez", "William Anderson", "Sophia Taylor",
        "Benjamin Thomas", "Isabella Jackson", "Daniel White", "Mia Harris",
        "Matthew Martin", "Charlotte Thompson", "David Garcia", "Amelia Robinson",
        "Joseph Clark", "Harper Rodriguez", "Andrew Lewis", "Evelyn Lee"
    ]

    nationalities = ["USA", "UK", "Canada", "Germany", "France", "Japan", "Australia", "UAE", "Morocco", "Spain"]
    flights = ["AA101", "BA205", "DL340", "LH780", "AF520", "JL090", "EK420", "AT800", "IB330", "QR900"]
    gates = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D1"]
    checkpoints = ["CP-A1", "CP-A2", "CP-B1"]

    print("[INFO] Generating demo travelers...")

    # Generate travelers
    for i, name in enumerate(names):
        traveler_id = f"TRV-{str(i+1).zfill(4)}"
        passport = f"P{random.randint(10000000, 99999999)}"
        nationality = random.choice(nationalities)
        flight = random.choice(flights)
        gate = random.choice(gates)

        try:
            c.execute("""
                INSERT INTO travelers (id, name, passport_id, nationality, flight_number, gate, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (traveler_id, name, passport, nationality, flight, gate, None))
        except sqlite3.IntegrityError:
            pass

    print(f"[INFO] Generated {len(names)} travelers")

    # Generate recognition logs
    print("[INFO] Generating demo recognition logs...")

    for _ in range(50):
        # 80% authorized, 20% unauthorized
        is_authorized = random.random() < 0.8

        if is_authorized:
            c.execute("SELECT id, name, passport_id FROM travelers ORDER BY RANDOM() LIMIT 1")
            traveler = c.fetchone()
            if traveler:
                traveler_id, name, passport_id = traveler
                confidence = random.uniform(85.0, 99.5)
            else:
                continue
        else:
            traveler_id = None
            name = "Unknown"
            passport_id = None
            confidence = random.uniform(30.0, 65.0)

        checkpoint = random.choice(checkpoints)

        # Random timestamp within last 7 days
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        c.execute("""
            INSERT INTO recognition_logs (traveler_id, name, passport_id, checkpoint, confidence, authorized, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (traveler_id, name, passport_id, checkpoint, confidence, is_authorized, None))

    conn.commit()
    conn.close()

    print("[INFO] Demo data generated successfully!")
    print("[INFO] You can now run: python app.py")

if __name__ == "__main__":
    generate_demo_data()
