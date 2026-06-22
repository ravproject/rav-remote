"""
Voice Command — enable voice command processing from phone.
"""
import os
import asyncio
from pathlib import Path
from loguru import logger

class VoiceCommandManager:
    def __init__(self):
        self.active = False
        self.last_command = ""

    def start(self) -> str:
        self.active = True
        return "🎤 Voice Command AKTIF. Kirim pesan suara dari HP untuk dieksekusi."

    def stop(self) -> str:
        self.active = False
        return "🎤 Voice Command NONAKTIF."

    def process_voice(self, audio_path: str) -> str:
        if not self.active:
            return ""
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language="id-ID")
            self.last_command = text
            return text
        except ImportError:
            return "SpeechRecognition tidak terinstall. Jalankan: pip install SpeechRecognition"
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            return ""

voice_cmd_manager = VoiceCommandManager()
