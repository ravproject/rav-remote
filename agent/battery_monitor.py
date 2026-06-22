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
        logger.info("Battery monitor loop started.")
        while True:
            try:
                battery = psutil.sensors_battery()
                if battery is not None:
                    percent = battery.percent
                    # Treat None as False (not plugged) for stability on some Linux systems
                    plugged = bool(battery.power_plugged)
                    
                    logger.debug(f"Battery Check: {percent}%, Plugged: {plugged} (Raw: {battery.power_plugged})")
                    
                    # Check low battery
                    if percent < 20 and self.last_percent >= 20 and not plugged:
                        logger.info(f"Low battery alert triggered: {percent}%")
                        self.add_alert(f"🔋 *PERINGATAN BATERAI:* Baterai laptop tersisa {percent}%!")
                        
                    # Check plugged status change
                    if self.last_plugged is not None and plugged != self.last_plugged:
                        if plugged:
                            logger.info("Power connected alert triggered")
                            self.add_alert("⚡ *INFO DAYA:* Laptop sekarang terhubung ke pengisi daya.")
                        else:
                            logger.info("Power disconnected alert triggered")
                            self.add_alert("🔌 *INFO DAYA:* Charger dilepas, laptop menggunakan baterai.")
                            
                    self.last_percent = percent
                    self.last_plugged = plugged
                else:
                    logger.warning("psutil.sensors_battery() returned None")
            except Exception as e:
                logger.error(f"Battery monitor error: {e}")
                
            # Check every 30 seconds for faster response
            time.sleep(30)
            
    def add_alert(self, msg: str):
        with self.lock:
            self.alerts.append(msg)
            
    def get_alerts(self) -> List[str]:
        with self.lock:
            current_alerts = list(self.alerts)
            self.alerts.clear()
            return current_alerts

battery_monitor = BatteryMonitor()
