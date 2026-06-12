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
from bot.rate_limiter import _user_command_times

class TestE2E(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Setup environment variables for testing
        os.environ["OTP_SECRET_KEY"] = "JBSWY3DPEHPK3PXP"
        os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_e2e"
        os.environ["ALLOWED_USER_IDS"] = "12345"
        os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
        os.environ["AGENT_API_KEY"] = "mock_agent_key"
        
        # Clear sessions and rate limit state
        tg_bot._user_sessions = {}
        _user_command_times.clear()
        
        self.user_id = 12345
        self.totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")

    def tearDown(self):
        pass

    def create_mock_update(self, text, user_id=None):
        if user_id is None:
            user_id = self.user_id
        update = MagicMock()
        update.effective_user.id = user_id
        update.message.text = text
        update.message.reply_text = AsyncMock()
        update.message.reply_photo = AsyncMock()
        update.message.reply_video = AsyncMock()
        update.message.reply_document = AsyncMock()
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
        
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, 
                json=lambda: {"type": "text", "content": "Mocked System Info: CPU 10%, RAM 4GB"}
            )
            await message_handler(update, context)
            
            # message_handler calls reply_text once with "⏳ Memproses..." and once with result
            self.assertEqual(update.message.reply_text.call_count, 2)
            last_call_args = update.message.reply_text.call_args_list[-1][0][0]
            self.assertIn("Mocked System Info", last_call_args)

    async def test_ai_natural_language_flow(self):
        # Setup login
        tg_bot._user_sessions[str(self.user_id)] = AuthManager.generate_session_token(str(self.user_id))
        
        # User sends "ambil screenshot" (natural language)
        update = self.create_mock_update("ambil screenshot")
        context = self.create_mock_context()
        
        import base64
        fake_data = base64.b64encode(b"fake_image_bytes").decode()

        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"type": "image", "content": fake_data}
            )
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

    async def test_terminal_mode_flow(self):
        # 1. Login
        otp = self.totp.now()
        update = self.create_mock_update(f"/otp {otp}")
        await otp_handler(update, self.create_mock_context([otp]))
        
        # Patch httpx in bot.telegram_bot where it is used
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            
            # 2. Start Terminal Mode
            update = self.create_mock_update("!term")
            await message_handler(update, self.create_mock_context())
            
            # Use string user_id as bot uses str(update.effective_user.id)
            uid_str = str(self.user_id)
            self.assertTrue(tg_bot._terminal_mode.get(uid_str))
            
            # 3. Send command to terminal
            update = self.create_mock_update("pwd")
            await message_handler(update, self.create_mock_context())
            
            # Verify data sent to agent terminal/write
            # Note: The second call to post is for terminal/write
            self.assertEqual(mock_post.call_count, 2)
            mock_post.assert_called_with(
                f"{tg_bot.AGENT_URL}/terminal/write",
                json={"user_id": uid_str, "data": "pwd\n"},
                headers=unittest.mock.ANY
            )

            # 4. Exit Terminal Mode
            update = self.create_mock_update("!exit")
            await message_handler(update, self.create_mock_context())
            
            self.assertFalse(tg_bot._terminal_mode.get(uid_str))
            update.message.reply_text.assert_any_call("👋 Mode Terminal dinonaktifkan.")

    async def test_mega_expansion_commands(self):
        """Test routing and response types for new features (!video, !webcam)."""
        tg_bot._user_sessions[str(self.user_id)] = AuthManager.generate_session_token(str(self.user_id))
        import base64

        # 1. Test !video
        update = self.create_mock_update("!video")
        fake_video = base64.b64encode(b"fake_mp4_bytes").decode()
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"type": "video", "content": fake_video}
            )
            await message_handler(update, self.create_mock_context())
            update.message.reply_video.assert_called_once_with(b"fake_mp4_bytes", caption="📹 Live Stream")

        # 2. Test !webcam
        update = self.create_mock_update("!webcam")
        fake_photo = base64.b64encode(b"fake_jpg_bytes").decode()
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"type": "image", "content": fake_photo}
            )
            await message_handler(update, self.create_mock_context())
            update.message.reply_photo.assert_called_once_with(b"fake_jpg_bytes", caption="📸 Berhasil")

    async def test_voice_handler(self):
        from bot.telegram_bot import voice_handler
        import tempfile
        
        tg_bot._user_sessions[str(self.user_id)] = AuthManager.generate_session_token(str(self.user_id))
        
        update = self.create_mock_update("")
        update.message.voice = MagicMock()
        update.message.voice.file_id = "test_voice_id"
        
        # Create real dummy files so os.remove and others don't fail
        dummy_ogg = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
        dummy_ogg.close()
        dummy_wav = dummy_ogg.name + ".wav"
        with open(dummy_wav, 'w') as f:
            f.write("fake wav content")
            
        mock_file = AsyncMock()
        mock_file.download_to_drive = AsyncMock()
        context = self.create_mock_context()
        context.bot.get_file = AsyncMock(return_value=mock_file)
        
        with patch('bot.telegram_bot.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_inst = MagicMock()
            mock_temp_inst.name = dummy_ogg.name
            mock_temp.return_value.__enter__.return_value = mock_temp_inst
            
            with patch('bot.telegram_bot.AudioSegment'):
                with patch('bot.telegram_bot.sr.AudioFile'): # Mock AudioFile to avoid real reading
                    with patch('bot.telegram_bot.sr.Recognizer') as MockRecognizer:
                        mock_recognizer_inst = MockRecognizer.return_value
                        mock_recognizer_inst.recognize_google.return_value = "!sysinfo"
                        
                        with patch('bot.telegram_bot.message_handler', new_callable=AsyncMock) as mock_msg_handler:
                            await voice_handler(update, context)
                            
                            update.message.reply_text.assert_any_call("🗣️ *Anda berkata:* !sysinfo", parse_mode="Markdown")
                            mock_msg_handler.assert_called_once()
                            
        # Cleanup
        if os.path.exists(dummy_ogg.name): os.remove(dummy_ogg.name)
        if os.path.exists(dummy_wav): os.remove(dummy_wav)

    async def test_ai_takeover_and_fallback(self):
        """Test AI takeover for natural language and fallback when AI fails/refuses."""
        # 1. Login
        tg_bot._user_sessions[str(self.user_id)] = AuthManager.generate_session_token(str(self.user_id))
        _user_command_times.clear() # Reset rate limit
        
        # 2. Case: Natural language translates to command
        update = self.create_mock_update("tunjukkan info laptop")
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"type": "text", "content": "CPU: 10%"}
            )
            await message_handler(update, self.create_mock_context())
            # Verify sysinfo output found
            calls = [str(c) for c in update.message.reply_text.call_args_list]
            self.assertTrue(any("CPU: 10%" in c for c in calls), f"CPU: 10% not in {calls}")

        # 3. Case: AI handles chat/non-command (AI "Chat" mode)
        update = self.create_mock_update("halo apa kabar?")
        _user_command_times.clear() # Reset rate limit
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            ai_msg = "Halo! Saya asisten remote Anda."
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"type": "text", "content": ai_msg}
            )
            await message_handler(update, self.create_mock_context())
            # Verify AI chat found
            calls = [str(c) for c in update.message.reply_text.call_args_list]
            self.assertTrue(any(ai_msg in c for c in calls), f"'{ai_msg}' not in {calls}")

        # 4. Case: AI fails -> Fallback to explicit
        update = self.create_mock_update("perintah ngaco")
        _user_command_times.clear() # Reset rate limit
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"type": "text", "content": "❓ Perintah tidak dikenali. Ketik `!help` untuk bantuan."}
            )
            await message_handler(update, self.create_mock_context())
            # Verify fallback message found
            calls = [str(c) for c in update.message.reply_text.call_args_list]
            self.assertTrue(any("tidak dikenali" in c for c in calls), f"'tidak dikenali' not in {calls}")

    async def test_ai_safety_validation(self):
        """Test that AI-generated dangerous commands are blocked."""
        tg_bot._user_sessions[str(self.user_id)] = AuthManager.generate_session_token(str(self.user_id))
        
        update = self.create_mock_update("jalankan rm -rf")
        with patch('bot.telegram_bot.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=400,
                json=lambda: {"detail": "Input tidak valid atau berbahaya"}
            )
            await message_handler(update, self.create_mock_context())
            
            last_call = update.message.reply_text.call_args_list[-1][0][0]
            self.assertIn("bahaya", last_call.lower())

if __name__ == '__main__':
    unittest.main()
