"""
Battery Monitor - Checks battery status and manages alerts.
"""
import psutil
import threading
import time
from typing import List
from loguru import logger

class BatteryMonitor:
    def __init__(self):
        self.alerts: List[str] = []
        self.last_percent = -1
        self.last_plugged = None
        self.lock = threading.Lock()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def _monitor_loop(self):
        # Initial wait to let system settle
        time.sleep(10)
        while True:
            try:
                battery = psutil.sensors_battery()
                if battery is not None:
                    percent = battery.percent
                    plugged = battery.power_plugged
                    
                    # Check low battery
                    if percent < 20 and self.last_percent >= 20 and not plugged:
                        self.add_alert(f"🔋 *PERINGATAN BATERAI:* Baterai laptop tersisa {percent}%!")
                        
                    # Check plugged status change
                    if self.last_plugged is not None and plugged != self.last_plugged:
                        if plugged:
                            self.add_alert("⚡ *INFO DAYA:* Laptop sekarang terhubung ke pengisi daya.")
                        else:
                            self.add_alert("🔌 *INFO DAYA:* Charger dilepas, laptop menggunakan baterai.")
                            
                    self.last_percent = percent
                    self.last_plugged = plugged
            except Exception as e:
                logger.error(f"Battery monitor error: {e}")
                
            # Check every 60 seconds
            time.sleep(60)
            
    def add_alert(self, msg: str):
        with self.lock:
            self.alerts.append(msg)
            
    def get_alerts(self) -> List[str]:
        with self.lock:
            current_alerts = list(self.alerts)
            self.alerts.clear()
            return current_alerts

battery_monitor = BatteryMonitor()
