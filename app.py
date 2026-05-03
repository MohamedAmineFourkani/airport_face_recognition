"""
Airport Face Recognition System
Advanced Computer Vision for Automated Passenger Verification
"""

from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, flash
import os
import cv2
import numpy as np
import sqlite3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.face_recognizer import FaceRecognizer
from utils.camera import Camera

app = Flask(__name__)
app.secret_key = "airport_security_secret_key_2025"
app.config["UPLOAD_FOLDER"] = "static/uploads/authorized_faces"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max

# Initialize components
face_recognizer = FaceRecognizer()
camera = Camera()

# Database setup
def init_db():
    conn = sqlite3.connect("airport_security.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS travelers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            passport_id TEXT UNIQUE NOT NULL,
            nationality TEXT,
            flight_number TEXT,
            gate TEXT,
            image_path TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT "active"
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS recognition_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traveler_id TEXT,
            name TEXT,
            passport_id TEXT,
            checkpoint TEXT DEFAULT "A1",
            confidence REAL,
            authorized BOOLEAN,
            image_path TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            status TEXT DEFAULT "active",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default checkpoint if not exists
    c.execute("SELECT * FROM checkpoints WHERE id = 'CP-A1'")
    if not c.fetchone():
        c.execute("INSERT INTO checkpoints (id, name, location) VALUES (?, ?, ?)",
                 ("CP-A1", "Main Security Gate A1", "Terminal 1 - Departures"))
        c.execute("INSERT INTO checkpoints (id, name, location) VALUES (?, ?, ?)",
                 ("CP-A2", "Secondary Gate A2", "Terminal 1 - International"))
        c.execute("INSERT INTO checkpoints (id, name, location) VALUES (?, ?, ?)",
                 ("CP-B1", "Boarding Gate B1", "Terminal 2 - Domestic"))

    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("airport_security.db")
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route("/")
def index():
    """Dashboard"""
    conn = get_db()
    c = conn.cursor()

    stats = {
        "total_travelers": c.execute("SELECT COUNT(*) FROM travelers").fetchone()[0],
        "active_checkpoints": c.execute("SELECT COUNT(*) FROM checkpoints WHERE status = 'active'").fetchone()[0],
        "today_logs": c.execute(
            "SELECT COUNT(*) FROM recognition_logs WHERE date(timestamp) = date('now')"
        ).fetchone()[0],
        "unauthorized_attempts": c.execute(
            "SELECT COUNT(*) FROM recognition_logs WHERE authorized = 0 AND date(timestamp) = date('now')"
        ).fetchone()[0]
    }

    recent_logs = c.execute("""
        SELECT * FROM recognition_logs 
        ORDER BY timestamp DESC LIMIT 10
    """).fetchall()

    checkpoints = c.execute("SELECT * FROM checkpoints WHERE status = 'active'").fetchall()

    engine_stats = face_recognizer.get_stats()

    conn.close()
    return render_template("index.html", stats=stats, logs=recent_logs, 
                         checkpoints=checkpoints, engine=engine_stats)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new authorized traveler"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        passport_id = request.form.get("passport_id", "").strip()
        nationality = request.form.get("nationality", "").strip()
        flight_number = request.form.get("flight_number", "").strip()
        gate = request.form.get("gate", "").strip()

        if not name or not passport_id:
            flash("Name and Passport ID are required", "error")
            return redirect(url_for("register"))

        if "image" not in request.files:
            flash("No image uploaded", "error")
            return redirect(url_for("register"))

        file = request.files["image"]
        if file.filename == "":
            flash("No image selected", "error")
            return redirect(url_for("register"))

        # Save image
        traveler_id = str(uuid.uuid4())[:8].upper()
        filename = secure_filename(f"{traveler_id}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Register face
        success, msg = face_recognizer.register_face(
            filepath, name, passport_id, traveler_id
        )

        if not success:
            os.remove(filepath)
            flash(msg, "error")
            return redirect(url_for("register"))

        # Save to database
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO travelers (id, name, passport_id, nationality, flight_number, gate, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (traveler_id, name, passport_id, nationality, flight_number, gate, filename))
            conn.commit()
            flash(f"Traveler {name} registered successfully! ID: {traveler_id}", "success")
        except sqlite3.IntegrityError:
            flash("Passport ID already exists", "error")
            return redirect(url_for("register"))
        finally:
            conn.close()

        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/checkpoint")
def checkpoint():
    """Live checkpoint monitoring"""
    conn = get_db()
    c = conn.cursor()
    checkpoints = c.execute("SELECT * FROM checkpoints WHERE status = 'active'").fetchall()
    conn.close()
    return render_template("checkpoint.html", checkpoints=checkpoints)

@app.route("/logs")
def logs():
    """Recognition logs"""
    conn = get_db()
    c = conn.cursor()

    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    all_logs = c.execute("""
        SELECT * FROM recognition_logs 
        ORDER BY timestamp DESC LIMIT ? OFFSET ?
    """, (per_page, offset)).fetchall()

    total = c.execute("SELECT COUNT(*) FROM recognition_logs").fetchone()[0]

    conn.close()
    return render_template("logs.html", logs=all_logs, page=page, total=total, per_page=per_page)

@app.route("/travelers")
def travelers():
    """List all registered travelers"""
    conn = get_db()
    c = conn.cursor()
    all_travelers = c.execute("SELECT * FROM travelers ORDER BY registered_at DESC").fetchall()
    conn.close()
    return render_template("travelers.html", travelers=all_travelers)

# API Endpoints
@app.route("/api/recognize", methods=["POST"])
def api_recognize():
    """API endpoint for face recognition from uploaded image"""
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        image_bytes = file.read()
        if len(image_bytes) == 0:
            return jsonify({"error": "Empty file"}), 400

        # Process image
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid image format"}), 400

        # Run face recognition
        try:
            results = face_recognizer.recognize_faces(frame)
        except Exception as rec_err:
            return jsonify({"error": f"Recognition failed: {str(rec_err)}"}), 500

        checkpoint_id = request.form.get("checkpoint", "CP-A1")
        response_results = []

        # Log results to database
        try:
            conn = get_db()
            c = conn.cursor()

            for result in results:
                try:
                    # Save log image
                    log_id = str(uuid.uuid4())
                    display_frame = face_recognizer.draw_results(frame.copy(), [result])
                    log_filename = f"log_{log_id}.jpg"
                    log_path = os.path.join("static/uploads", log_filename)
                    cv2.imwrite(log_path, display_frame)
                except Exception as img_err:
                    log_filename = None

                try:
                    c.execute("""
                        INSERT INTO recognition_logs (traveler_id, name, passport_id, checkpoint, confidence, authorized, image_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.get("traveler_id"),
                        result["name"],
                        result.get("passport_id"),
                        checkpoint_id,
                        result["confidence"],
                        result["authorized"],
                        log_filename
                    ))
                except Exception as db_err:
                    print(f"[DB ERROR] {db_err}")

            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"[DB ERROR] {db_err}")

        # Build response
        for result in results:
            response_results.append({
                "name": result["name"],
                "passport_id": result.get("passport_id"),
                "confidence": result["confidence"],
                "authorized": result["authorized"],
                "location": result["location"]
            })

        return jsonify({
            "success": True,
            "faces_detected": len(results),
            "results": response_results,
            "checkpoint": checkpoint_id,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        import traceback
        print(f"[API ERROR] {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/stats")
def api_stats():
    """Get system statistics"""
    conn = get_db()
    c = conn.cursor()

    stats = {
        "total_travelers": c.execute("SELECT COUNT(*) FROM travelers").fetchone()[0],
        "today_recognitions": c.execute(
            "SELECT COUNT(*) FROM recognition_logs WHERE date(timestamp) = date('now')"
        ).fetchone()[0],
        "unauthorized_today": c.execute(
            "SELECT COUNT(*) FROM recognition_logs WHERE authorized = 0 AND date(timestamp) = date('now')"
        ).fetchone()[0],
        "engine": face_recognizer.get_stats()
    }

    conn.close()
    return jsonify(stats)

@app.route("/api/traveler/<traveler_id>")
def api_traveler(traveler_id):
    """Get traveler details"""
    conn = get_db()
    c = conn.cursor()
    traveler = c.execute("SELECT * FROM travelers WHERE id = ?", (traveler_id,)).fetchone()
    conn.close()

    if traveler is None:
        return jsonify({"error": "Traveler not found"}), 404

    return jsonify(dict(traveler))

@app.route("/video_feed")
def video_feed():
    """Live video streaming endpoint"""
    def generate():
        camera.start()
        while True:
            frame_bytes, results = camera.get_frame()
            if frame_bytes is None:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/camera/start")
def api_camera_start():
    """Start camera"""
    success = camera.start()
    return jsonify({"success": success, "message": "Camera started" if success else "Failed to start camera"})

@app.route("/api/camera/stop")
def api_camera_stop():
    """Stop camera"""
    camera.stop()
    return jsonify({"success": True, "message": "Camera stopped"})

if __name__ == "__main__":
    print("=" * 60)
    print("AIRPORT FACE RECOGNITION SYSTEM")
    print("=" * 60)
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
