"""
Module for webcam motion detection security guard.
"""
import cv2
import threading
import time
import os
from loguru import logger

# Global list for guard alerts
guard_alerts = []

class WebcamGuard:
    def __init__(self):
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> bool:
        with self._lock:
            if self._running:
                return True
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("WebcamGuard: Kamera tidak dapat diakses.")
                return False
            cap.release()

            self._running = True
            self._thread = threading.Thread(target=self._guard_loop, daemon=True)
            self._thread.start()
            logger.info("WebcamGuard started.")
            return True

    def stop(self):
        with self._lock:
            if not self._running:
                return
            self._running = False
            logger.info("WebcamGuard stopped.")

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def _guard_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._running = False
            return

        prev_frame = None
        last_alert_time = 0

        # Berikan kamera waktu 1 detik untuk inisialisasi
        time.sleep(1)

        while self._running:
            try:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(1)
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if prev_frame is None:
                    prev_frame = gray
                    time.sleep(1.5)
                    continue

                frame_delta = cv2.absdiff(prev_frame, gray)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                
                non_zero = cv2.countNonZero(thresh)
                total_pixels = gray.shape[0] * gray.shape[1]
                threshold_pixels = int(total_pixels * 0.02) # 2% perubahan pixel

                if non_zero > threshold_pixels:
                    now = time.time()
                    if now - last_alert_time > 20: # Cooldown 20s
                        last_alert_time = now
                        cv2.imwrite("guard_alert.jpg", frame)
                        alert_msg = "🚨 GERAKAN TERDETEKSI di dekat laptop! Ketik !get guard_alert.jpg untuk mengunduh foto."
                        guard_alerts.append(alert_msg)
                        logger.warning("WebcamGuard: Motion detected!")

                prev_frame = gray
                
            except Exception as e:
                logger.error(f"WebcamGuard loop error: {e}")
                
            time.sleep(1.5)

        cap.release()

webcam_guard = WebcamGuard()
