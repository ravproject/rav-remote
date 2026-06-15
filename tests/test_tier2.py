"""
Tests for Tier 2 Monitoring & Watchdog
"""
import unittest
import time
import asyncio
from security.watchdog import SecurityWatchdog
from bot.monitor_task import MonitorTask
from unittest.mock import AsyncMock, MagicMock

class TestTier2(unittest.TestCase):
    def setUp(self):
        self.watchdog = SecurityWatchdog()
        # Mock Telegram Application
        self.app = MagicMock()
        self.app.bot.send_message = AsyncMock()
        self.monitor = MonitorTask(self.app)

    def test_otp_brute_force_detection(self):
        """Test that excessive OTP failures trigger brute force detection."""
        user_id = "test_user_123"
        
        # 1st failure
        self.assertFalse(self.watchdog.record_otp_failure(user_id))
        # 2nd failure
        self.assertFalse(self.watchdog.record_otp_failure(user_id))
        # 3rd failure -> Trigger
        self.assertTrue(self.watchdog.record_otp_failure(user_id))

    def test_system_anomaly_detection(self):
        """Test that high CPU usage triggers alert after consecutive hits."""
        # 1 hit
        self.assertEqual(len(self.watchdog.check_system_anomalies(95.0, 50.0)), 0)
        # 2 hits
        self.assertEqual(len(self.watchdog.check_system_anomalies(95.0, 50.0)), 0)
        # 3 hits -> Alert
        alerts = self.watchdog.check_system_anomalies(95.0, 50.0)
        self.assertIn("High CPU Usage", alerts[0])

    def test_monitor_logic(self):
        """Run the async test for monitor logic."""
        asyncio.run(self.async_test_monitor_state_transition_mocked())

    async def async_test_monitor_state_transition_mocked(self):
        """Mocked version of monitor state transition test."""
        agent_id = "test_agent"
        metrics = {"cpu": 10, "ram": 20}
        
        # Reset state for test
        from bot.monitor_task import _agent_status
        _agent_status.clear()

        # Initial ONLINE
        await self.monitor.update_heartbeat(agent_id, metrics)
        self.assertEqual(_agent_status[agent_id]["state"], "ONLINE")
        self.app.bot.send_message.assert_called() # Alert for ONLINE
        self.app.bot.send_message.reset_mock()

        # Mock time to trigger DEGRADED
        start_time = time.time()
        await self.monitor._check_status_once(start_time + 100)
        self.assertEqual(_agent_status[agent_id]["state"], "DEGRADED")
        self.app.bot.send_message.assert_called() # Alert for DEGRADED
        self.app.bot.send_message.reset_mock()

        # Mock time to trigger OFFLINE
        await self.monitor._check_status_once(start_time + 200)
        self.assertEqual(_agent_status[agent_id]["state"], "OFFLINE")
        self.app.bot.send_message.assert_called() # Alert for OFFLINE

if __name__ == "__main__":
    unittest.main()
