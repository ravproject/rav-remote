"""
Unit tests for CryptoManager
"""
import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from security.crypto import CryptoManager

class TestCryptoManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary key for testing
        os.environ["ENCRYPTION_KEY"] = "test_key_must_be_at_least_32_chars_long"
        self.crypto = CryptoManager()

    def test_encrypt_decrypt_roundtrip(self):
        """Test that data can be encrypted and then decrypted back to original."""
        original_text = "Hello, Secure World! 123"
        encrypted = self.crypto.encrypt(original_text)
        self.assertNotEqual(original_text, encrypted)
        
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(original_text, decrypted)

    def test_invalid_key_length(self):
        """Test that an error is raised if the key is too short."""
        os.environ["ENCRYPTION_KEY"] = "too_short"
        with self.assertRaises(ValueError):
            CryptoManager()

    def test_missing_key(self):
        """Test that an error is raised if the key is missing."""
        if "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]
        with self.assertRaises(RuntimeError):
            CryptoManager()

if __name__ == "__main__":
    unittest.main()
