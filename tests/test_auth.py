"""
Tests for the auth module.
"""
import unittest
from unittest.mock import patch
import os
import time
import asyncio

class TestAuth(unittest.TestCase):
    def setUp(self):
        os.environ["OTP_SECRET_KEY"] = "JBSWY3DPEHPK3PXP"
        os.environ["JWT_SECRET_KEY"] = "test_secret"
        os.environ["ALLOWED_USER_IDS"] = "123,456"
        os.environ["MAX_COMMANDS_PER_MINUTE"] = "2"
        from bot.auth import AuthManager
        self.auth_manager = AuthManager()

    def test_is_user_allowed(self):
        from bot.auth import AuthManager
        self.assertTrue(AuthManager.is_user_allowed("123"))
        self.assertTrue(AuthManager.is_user_allowed("456"))
        self.assertFalse(AuthManager.is_user_allowed("789"))

    def test_verify_otp(self):
        from bot.auth import AuthManager
        # This is a time-based test, so it might fail if the test runs too slow
        import pyotp
        totp = pyotp.TOTP(os.environ["OTP_SECRET_KEY"])
        self.assertTrue(AuthManager.verify_otp(totp.now()))
        self.assertFalse(AuthManager.verify_otp("123456"))

    def test_jwt_token(self):
        from bot.auth import AuthManager
        token = AuthManager.generate_session_token("123")
        self.assertEqual(AuthManager.verify_session_token(token), "123")

    def test_revoke_token(self):
        from bot.auth import AuthManager
        token = AuthManager.generate_session_token("123")
        AuthManager.revoke_token(token)
        self.assertIsNone(AuthManager.verify_session_token(token))

    def test_rate_limit(self):
        from bot.auth import AuthManager
        from bot import rate_limiter
        # Clear the rate limit state before running the test
        rate_limiter._user_command_times.clear()
        
        user_id = "test_user_rate_limit"
        # First 2 calls should be fine (MAX is 2)
        self.assertTrue(AuthManager.check_rate_limit(user_id))
        self.assertTrue(AuthManager.check_rate_limit(user_id))
        # 3rd call should fail
        self.assertFalse(AuthManager.check_rate_limit(user_id))
        time.sleep(61)
        self.assertTrue(AuthManager.check_rate_limit("123"))

    @patch('bot.auth.AuthManager.is_user_allowed', return_value=True)
    @patch('bot.auth.AuthManager.verify_session_token', return_value="123")
    @patch('bot.auth.AuthManager.check_rate_limit', return_value=True)
    def test_require_auth_decorator(self, mock_check_rate_limit, mock_verify_session_token, mock_is_user_allowed):
        from bot.auth import require_auth
        @require_auth
        async def my_handler(user_id, token):
            return "ok"

        result = asyncio.run(my_handler("123", "some_token"))
        self.assertEqual(result, "ok")


if __name__ == '__main__':
    unittest.main()
