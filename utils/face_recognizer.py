"""
Face Recognition Engine for Airport Security System
Pure OpenCV implementation - NO dlib/face_recognition needed
Works on Python 3.10+ without CMake or C++ compiler
"""

import os
import cv2
import numpy as np
import pickle
from datetime import datetime

class FaceRecognizer:
    def __init__(self, encodings_path="face_encodings.pkl"):
        self.encodings_path = encodings_path
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.known_passports = []

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.load_encodings()

    def load_encodings(self):
        if os.path.exists(self.encodings_path):
            try:
                with open(self.encodings_path, "rb") as f:
                    data = pickle.load(f)
                    self.known_encodings = data.get("encodings", [])
                    self.known_names = data.get("names", [])
                    self.known_ids = data.get("ids", [])
                    self.known_passports = data.get("passports", [])
                print(f"[INFO] Loaded {len(self.known_encodings)} face encodings")
            except Exception as e:
                print(f"[ERROR] Loading encodings: {e}")

    def save_encodings(self):
        data = {
            "encodings": self.known_encodings,
            "names": self.known_names,
            "ids": self.known_ids,
            "passports": self.known_passports
        }
        with open(self.encodings_path, "wb") as f:
            pickle.dump(data, f)

    def detect_faces(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        locations = [(y, x+w, y+h, x) for (x, y, w, h) in faces]
        return locations

    def get_face_encoding(self, image, face_location=None):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if face_location:
            top, right, bottom, left = face_location
            face_roi = gray[top:bottom, left:right]
        else:
            face_roi = gray

        if face_roi.size == 0:
            return None

        face_roi = cv2.resize(face_roi, (128, 128))

        hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist)

        lbp = self._local_binary_pattern(face_roi)
        lbp_hist = cv2.calcHist([lbp.astype(np.uint8)], [0], None, [256], [0, 256])
        cv2.normalize(lbp_hist, lbp_hist)

        grid_features = []
        grid_size = 4
        h, w = face_roi.shape
        cell_h, cell_w = h // grid_size, w // grid_size
        for i in range(grid_size):
            for j in range(grid_size):
                cell = face_roi[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                cell_hist = cv2.calcHist([cell], [0], None, [32], [0, 256])
                cv2.normalize(cell_hist, cell_hist)
                grid_features.extend(cell_hist.flatten())

        encoding = np.concatenate([hist.flatten(), lbp_hist.flatten(), np.array(grid_features)])
        norm = np.linalg.norm(encoding)
        if norm > 0:
            encoding = encoding / norm
        return encoding

    def _local_binary_pattern(self, image, P=8, R=1):
        h, w = image.shape
        lbp = np.zeros((h, w), dtype=np.uint8)

        angles = 2 * np.pi * np.arange(P) / P
        dx = R * np.cos(angles)
        dy = -R * np.sin(angles)

        y, x = np.mgrid[R:h-R, R:w-R]

        x_coords = x[:, :, np.newaxis] + dx
        y_coords = y[:, :, np.newaxis] + dy

        x0 = np.floor(x_coords).astype(int)
        y0 = np.floor(y_coords).astype(int)
        x1 = np.minimum(x0 + 1, w - 1)
        y1 = np.minimum(y0 + 1, h - 1)
        x0 = np.maximum(x0, 0)
        y0 = np.maximum(y0, 0)

        Ia = image[y0, x0]
        Ib = image[y0, x1]
        Ic = image[y1, x0]
        Id = image[y1, x1]

        wx1 = x_coords - x0
        wy1 = y_coords - y0
        interpolated = (1 - wx1) * (1 - wy1) * Ia + wx1 * (1 - wy1) * Ib + (1 - wx1) * wy1 * Ic + wx1 * wy1 * Id

        center = image[R:h-R, R:w-R]
        binary = (interpolated >= center[:, :, np.newaxis]).astype(np.uint8)

        powers = np.array([2 ** p for p in range(P)], dtype=np.uint8)
        lbp[R:h-R, R:w-R] = np.dot(binary, powers)

        return lbp

    def register_face(self, image_path, name, passport_id, traveler_id):
        image = cv2.imread(image_path)
        if image is None:
            return False, "Could not load image"

        locations = self.detect_faces(image)
        if not locations:
            return False, "No face detected in image"
        if len(locations) > 1:
            return False, "Multiple faces detected. Please use image with one face."

        encoding = self.get_face_encoding(image, locations[0])
        if encoding is None:
            return False, "Could not extract face features"

        self.known_encodings.append(encoding)
        self.known_names.append(name)
        self.known_ids.append(traveler_id)
        self.known_passports.append(passport_id)
        self.save_encodings()

        return True, "Face registered successfully"

    def recognize_faces(self, image, tolerance=0.6):
        locations = self.detect_faces(image)
        if not locations:
            return []

        results = []
        for location in locations:
            encoding = self.get_face_encoding(image, location)
            if encoding is None:
                continue

            if len(self.known_encodings) == 0:
                results.append({
                    "name": "Unknown", "passport_id": None, "traveler_id": None,
                    "confidence": 0.0, "location": location, "authorized": False
                })
                continue

            best_score = -1
            best_idx = -1
            for idx, known_enc in enumerate(self.known_encodings):
                similarity = np.dot(known_enc, encoding) / (np.linalg.norm(known_enc) * np.linalg.norm(encoding) + 1e-8)
                if similarity > best_score:
                    best_score = similarity
                    best_idx = idx

            confidence = max(0, min(100, best_score * 100))

            if best_score > 0.10:
                results.append({
                    "name": self.known_names[best_idx],
                    "passport_id": self.known_passports[best_idx],
                    "traveler_id": self.known_ids[best_idx],
                    "confidence": round(confidence, 2),
                    "location": location,
                    "authorized": True
                })
            else:
                results.append({
                    "name": "Unknown", "passport_id": None, "traveler_id": None,
                    "confidence": round(confidence, 2), "location": location, "authorized": False
                })
        return results

    def draw_results(self, image, results):
        """Draw bounding boxes with high-contrast labels visible on any background"""
        for result in results:
            top, right, bottom, left = result["location"]

            # Colors - bright, visible on dark backgrounds
            if result["authorized"]:
                box_color = (0, 255, 128)      # Bright green
                text_color = (0, 0, 0)          # Black text
                bg_color = (0, 255, 128)        # Green background
            else:
                box_color = (0, 165, 255)       # Orange-red
                text_color = (255, 255, 255)    # White text
                bg_color = (0, 0, 139)          # Dark red background

            # Draw thicker box with subtle glow
            cv2.rectangle(image, (left, top), (right, bottom), box_color, 3)
            cv2.rectangle(image, (left-1, top-1), (right+1, bottom+1), (255, 255, 255), 1)

            # Build label text
            label = f"{result['name']} | {result['confidence']:.0f}%"

            # Get text size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            # Label position - above the box, or inside if no space
            label_y = top - 10
            if label_y < text_h + 10:
                label_y = bottom + text_h + 10

            # Draw label background with padding
            pad = 6
            bg_top = label_y - text_h - pad
            bg_bottom = label_y + baseline + pad
            bg_left = left
            bg_right = left + text_w + pad * 2

            # Ensure background stays within image
            bg_right = min(bg_right, image.shape[1])

            # Draw solid background
            cv2.rectangle(image, (bg_left, bg_top), (bg_right, bg_bottom), bg_color, -1)

            # Draw text with outline for maximum visibility
            text_x = bg_left + pad
            text_y = label_y

            # Black outline
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (0,-1), (0,1), (-1,0), (1,0)]:
                cv2.putText(image, label, (text_x + dx, text_y + dy), font, font_scale, (0,0,0), thickness)

            # Main text
            cv2.putText(image, label, (text_x, text_y), font, font_scale, text_color, thickness)

        return image

    def get_stats(self):
        return {
            "registered_travelers": len(self.known_encodings),
            "accuracy_threshold": 10.0,
            "engine": "OpenCV DEMO MODE (10% threshold - very permissive)"
        }
