
"""
Integration tests for Agent's HTTP API.
Verifies the full path from /command request to JSON response.
"""
import unittest
from fastapi.testclient import TestClient
import os
import base64
from unittest.mock import patch, AsyncMock, MagicMock

# Set env vars BEFORE importing app
os.environ["AGENT_API_KEY"] = "test_agent_key"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret"

from agent.main import app
from bot.auth import AuthManager

class TestAgentIntegration(unittest.TestCase):
    def setUp(self):
        from agent.main import AGENT_API_KEY
        self.client = TestClient(app)
        self.api_key = AGENT_API_KEY
        
        self.user_id = "12345"
        self.token = AuthManager.generate_session_token(self.user_id)
        self.headers = {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.token}"
        }

    def test_command_screenshot_json_flow(self):
        """Test that !screenshot returns the correct JSON structure for the bot."""
        with patch('agent.command_handler.CommandHandler.handle_screenshot', new_callable=AsyncMock) as mock_ss:
            mock_ss.return_value = b"fake_ss_bytes"
            
            response = self.client.post(
                "/command",
                json={"command": "!screenshot", "user_id": self.user_id},
                headers=self.headers
            )
            
            self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
            data = response.json()
            self.assertEqual(data["type"], "image")
            self.assertEqual(data["content"], base64.b64encode(b"fake_ss_bytes").decode())

    def test_command_sysinfo_json_flow(self):
        """Test that !sysinfo returns the correct JSON structure."""
        with patch('agent.command_handler.CommandHandler.handle_sysinfo', new_callable=AsyncMock) as mock_info:
            mock_info.return_value = "💻 *System Info*\nCPU: 10%"

            response = self.client.post(
                "/command",
                json={"command": "!sysinfo", "user_id": self.user_id},
                headers=self.headers
            )

            self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
            data = response.json()
            self.assertEqual(data["type"], "text")
            self.assertIn("System Info", data["content"])
    def test_command_video_json_flow(self):
        """Test that !video returns the correct JSON structure."""
        with patch('agent.command_handler.CommandHandler.handle_video', new_callable=AsyncMock) as mock_video:
            mock_video.return_value = {
                "type": "video",
                "data": b"fake_video_bytes",
                "filename": "video.mp4",
                "mimetype": "video/mp4"
            }
            
            response = self.client.post(
                "/command",
                json={"command": "!video", "user_id": self.user_id},
                headers=self.headers
            )
            
            self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
            data = response.json()
            self.assertEqual(data["type"], "video")
            self.assertEqual(data["content"]["data"], base64.b64encode(b"fake_video_bytes").decode())
            self.assertEqual(data["content"]["filename"], "video.mp4")

    def test_command_listen_json_flow(self):
        """Test that !listen returns the correct structured JSON response."""
        with patch('agent.command_handler.CommandHandler.handle_listen', new_callable=AsyncMock) as mock_listen:
            mock_listen.return_value = {
                "type": "audio",
                "data": b"fake_mp3_bytes",
                "filename": "audio.mp3",
                "mimetype": "audio/mpeg"
            }
            response = self.client.post(
                "/command",
                json={"command": "!listen 5", "user_id": self.user_id},
                headers=self.headers
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["type"], "audio")
            self.assertEqual(data["content"]["data"], base64.b64encode(b"fake_mp3_bytes").decode())

    def test_command_click_json_flow(self):
        """Test that !click is routed and executed."""
        with patch('agent.command_handler.CommandHandler.handle_click', new_callable=AsyncMock) as mock_click:
            mock_click.return_value = "🖱️ Clicked"
            response = self.client.post(
                "/command",
                json={"command": "!click 100 200", "user_id": self.user_id},
                headers=self.headers
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["content"], "🖱️ Clicked")

    def test_command_active_json_flow(self):
        """Test that !active is routed and executed."""
        with patch('agent.command_handler.CommandHandler.handle_active_window', new_callable=AsyncMock) as mock_active:
            mock_active.return_value = "🖥️ Jendela Aktif: **MyWindow**"
            response = self.client.post(
                "/command",
                json={"command": "!active", "user_id": self.user_id},
                headers=self.headers
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["content"], "🖥️ Jendela Aktif: **MyWindow**")

    def test_security_sanitization_flow(self):
        """Test that dangerous commands are caught by the sanitizer in the API."""
        response = self.client.post(
            "/command",
            json={"command": "!screenshot; rm -rf /", "user_id": self.user_id},
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {response.text}")
        self.assertIn("berbahaya", response.json()["detail"])

    def test_unauthorized_flow(self):
        """Test API key protection."""
        bad_headers = self.headers.copy()
        bad_headers["X-API-Key"] = "wrong_key"
        
        response = self.client.post(
            "/command",
            json={"command": "!sysinfo", "user_id": self.user_id},
            headers=bad_headers
        )
        self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()
