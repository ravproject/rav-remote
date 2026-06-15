"""
Security Watchdog — Mendeteksi anomali keamanan dan sistem.
Integrasi dengan AuditLogger untuk pelaporan otomatis.
"""
from loguru import logger
from security.audit_logger import AuditLogger
import time

auditor = AuditLogger()

class SecurityWatchdog:
    def __init__(self):
        self.otp_failures = {}  # {user_id: [timestamps]}
        self.OTP_THRESHOLD = 3
        self.OTP_WINDOW = 300  # 5 menit
        
        # Metrics thresholds
        self.CPU_THRESHOLD = 90.0
        self.RAM_THRESHOLD = 85.0
        self.consecutive_high_cpu = 0

    def record_otp_failure(self, user_id: str):
        """Catat kegagalan OTP dan cek brute force."""
        now = time.time()
        failures = self.otp_failures.get(user_id, [])
        # Cleanup old failures
        failures = [t for t in failures if now - t < self.OTP_WINDOW]
        failures.append(now)
        self.otp_failures[user_id] = failures
        
        if len(failures) >= self.OTP_THRESHOLD:
            logger.critical(f"BRUTE FORCE DETECTED: User {user_id} failed OTP {len(failures)} times!")
            auditor.log_security_alert(user_id, "BRUTE_FORCE_OTP", f"Failed {len(failures)} times in {self.OTP_WINDOW}s")
            return True
        return False

    def check_system_anomalies(self, cpu_percent: float, ram_percent: float) -> list:
        """Cek apakah ada anomali pada penggunaan resource."""
        alerts = []
        if cpu_percent > self.CPU_THRESHOLD:
            self.consecutive_high_cpu += 1
            if self.consecutive_high_cpu >= 3:
                alerts.append(f"🔥 High CPU Usage: {cpu_percent}%")
        else:
            self.consecutive_high_cpu = 0

        if ram_percent > self.RAM_THRESHOLD:
            alerts.append(f"📉 Low Memory: {ram_percent}%")
            
        return alerts

watchdog = SecurityWatchdog()
