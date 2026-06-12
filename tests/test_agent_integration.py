
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
        self.client = TestClient(app)
        self.api_key = os.environ["AGENT_API_KEY"]
        
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
            mock_info.return_value = "CPU: 10%"
            
            response = self.client.post(
                "/command",
                json={"command": "!sysinfo", "user_id": self.user_id},
                headers=self.headers
            )
            
            self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
            data = response.json()
            self.assertEqual(data["type"], "text")
            self.assertEqual(data["content"], "CPU: 10%")

    def test_command_video_json_flow(self):
        """Test that !video returns the correct JSON structure."""
        with patch('agent.command_handler.CommandHandler.handle_video', new_callable=AsyncMock) as mock_video:
            mock_video.return_value = b"fake_video_bytes"
            
            response = self.client.post(
                "/command",
                json={"command": "!video", "user_id": self.user_id},
                headers=self.headers
            )
            
            self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
            data = response.json()
            self.assertEqual(data["type"], "video")
            self.assertEqual(data["content"], base64.b64encode(b"fake_video_bytes").decode())

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
