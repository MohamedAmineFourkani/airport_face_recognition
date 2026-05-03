"""
Optimized Camera handler for live video processing
High quality, visible labels, proper contrast on dark backgrounds
"""

import cv2
import numpy as np
import threading
import time
from utils.face_recognizer import FaceRecognizer

class Camera:
    def __init__(self, source=0):
        self.source = source
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.face_recognizer = FaceRecognizer()
        self.last_results = []
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()

        # Performance settings - balanced for quality
        self.skip_frames = 3
        self.process_width = 480

    def start(self):
        if self.running:
            return True

        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            return False

        # Higher resolution for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        return True

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            with self.lock:
                self.frame = frame.copy()
                self.frame_count += 1

                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_time = current_time

                if self.frame_count % self.skip_frames == 0:
                    h, w = frame.shape[:2]
                    scale = self.process_width / w
                    small_frame = cv2.resize(frame, (self.process_width, int(h * scale)))

                    small_results = self.face_recognizer.recognize_faces(small_frame)

                    self.last_results = []
                    for r in small_results:
                        top, right, bottom, left = r["location"]
                        self.last_results.append({
                            **r,
                            "location": (
                                int(top / scale),
                                int(right / scale),
                                int(bottom / scale),
                                int(left / scale)
                            )
                        })

    def get_frame(self, draw_boxes=True):
        with self.lock:
            if self.frame is None:
                return None, []

            display_frame = self.frame.copy()
            results = self.last_results.copy()

            if draw_boxes:
                display_frame = self.face_recognizer.draw_results(display_frame, results)

            # FPS overlay - cyan on black for visibility
            cv2.putText(display_frame, f"FPS: {self.fps}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # Checkpoint info - white with black outline for contrast
            text = "AIRPORT SECURITY - CHECKPOINT A1"
            cv2.putText(display_frame, text, (15, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
            cv2.putText(display_frame, text, (15, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Processing info
            info = f"Process: {self.process_width}px | Skip: {self.skip_frames}f"
            cv2.putText(display_frame, info, (15, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            ret, jpeg = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return jpeg.tobytes(), results

    def process_image(self, image_bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return None, []

        results = self.face_recognizer.recognize_faces(frame)
        display_frame = self.face_recognizer.draw_results(frame.copy(), results)

        ret, jpeg = cv2.imencode('.jpg', display_frame)
        return jpeg.tobytes(), results

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
