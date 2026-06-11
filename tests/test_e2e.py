"""
End-to-End tests for RAV-REMOTE.
Simulates user interaction with the Telegram bot and subsequent agent execution.
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import pyotp
import asyncio
from bot.telegram_bot import start_handler, otp_handler, message_handler
from bot.auth import AuthManager
import bot.telegram_bot as tg_bot

class TestE2E(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Setup environment variables for testing (some are still needed by other modules)
        os.environ["OTP_SECRET_KEY"] = "JBSWY3DPEHPK3PXP"
        os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_e2e"
        os.environ["ALLOWED_USER_IDS"] = "12345"
        os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
        os.environ["AGENT_API_KEY"] = "mock_agent_key"
        
        # Patching module-level constants in bot.auth
        self.auth_patchers = [
            patch('bot.auth.ALLOWED_USERS', {"12345"}),
            patch('bot.auth.OTP_SECRET', "JBSWY3DPEHPK3PXP"),
            patch('bot.auth.JWT_SECRET', "test_secret_key_for_e2e")
        ]
        for patcher in self.auth_patchers:
            patcher.start()

        # Clear sessions
        tg_bot._user_sessions = {}
        
        self.user_id = 12345
        self.totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")

    def tearDown(self):
        for patcher in self.auth_patchers:
            patcher.stop()

    def create_mock_update(self, text, user_id=None):
        if user_id is None:
            user_id = self.user_id
        update = MagicMock()
        update.effective_user.id = user_id
        update.message.text = text
        update.message.reply_text = AsyncMock()
        update.message.reply_photo = AsyncMock()
        return update

    def create_mock_context(self, args=None):
        context = MagicMock()
        context.args = args or []
        return context

    async def test_full_flow(self):
        # 1. User sends /start
        update = self.create_mock_update("/start")
        context = self.create_mock_context()
        await start_handler(update, context)
        
        update.message.reply_text.assert_called()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Autentikasi Diperlukan", args[0])
        
        # 2. User sends correct OTP
        valid_otp = self.totp.now()
        update = self.create_mock_update(f"/otp {valid_otp}")
        context = self.create_mock_context(args=[valid_otp])
        await otp_handler(update, context)
        
        update.message.reply_text.assert_called()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Login berhasil", args[0])
        
        # Verify session is created
        self.assertIn(str(self.user_id), tg_bot._user_sessions)
        
        # 3. User sends !sysinfo (explicit command)
        update = self.create_mock_update("!sysinfo")
        context = self.create_mock_context()
        
        with patch('bot.command_router.CommandRouter.route', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = "Mocked System Info: CPU 10%, RAM 4GB"
            await message_handler(update, context)
            
            self.assertEqual(update.message.reply_text.call_count, 2)
            last_call_args = update.message.reply_text.call_args_list[-1][0][0]
            self.assertIn("Mocked System Info", last_call_args)

    async def test_ai_natural_language_flow(self):
        # Setup login
        tg_bot._user_sessions[str(self.user_id)] = AuthManager.generate_session_token(str(self.user_id))
        
        # User sends "ambil screenshot" (natural language)
        update = self.create_mock_update("ambil screenshot")
        context = self.create_mock_context()
        
        # Mock AI translation and CommandRouter
        with patch('ai_module.nim_client.NIMClient.translate_to_command', new_callable=AsyncMock) as mock_translate:
            mock_translate.return_value = "!screenshot"
            with patch('bot.command_router.CommandRouter.route', new_callable=AsyncMock) as mock_route:
                mock_route.return_value = b"fake_image_bytes"
                await message_handler(update, context)
                
                # Verify reply_photo was called for image result
                update.message.reply_photo.assert_called_once()
                args, kwargs = update.message.reply_photo.call_args
                self.assertEqual(args[0], b"fake_image_bytes")

    async def test_unauthorized_user(self):
        # User not in whitelist
        update = self.create_mock_update("/start", user_id=99999)
        context = self.create_mock_context()
        await start_handler(update, context)
        
        update.message.reply_text.assert_called()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Akses ditolak", args[0])

    async def test_invalid_otp(self):
        # 1. User sends /start
        update = self.create_mock_update("/start")
        context = self.create_mock_context()
        await start_handler(update, context)
        
        # 2. User sends invalid OTP
        update = self.create_mock_update("/otp 000000")
        context = self.create_mock_context(args=["000000"])
        await otp_handler(update, context)
        
        update.message.reply_text.assert_called()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("OTP salah atau expired", args[0])
        
        # Verify no session created
        self.assertNotIn(str(self.user_id), tg_bot._user_sessions)

    async def test_command_without_login(self):
        # User sends command without login
        update = self.create_mock_update("!sysinfo")
        context = self.create_mock_context()
        await message_handler(update, context)
        
        update.message.reply_text.assert_called()
        args, kwargs = update.message.reply_text.call_args
        self.assertIn("Belum login", args[0])

if __name__ == '__main__':
    unittest.main()
