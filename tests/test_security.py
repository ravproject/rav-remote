"""
Tests for the security module.
"""
import unittest
import os
from pathlib import Path
from security.sanitizer import InputSanitizer

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.sanitizer = InputSanitizer()
        # Create a dummy allowed_commands.yaml for testing
        with open("config/allowed_commands.yaml", "w") as f:
            f.write("""
safe_commands:
  screenshot:
    description: "Ambil screenshot layar"
    requires_confirmation: false
    sandbox_required: false

  list_files:
    description: "List isi direktori (path terbatas)"
    requires_confirmation: false
    sandbox_required: false
    allowed_paths:
      - "~/Documents"
      - "~/Downloads"
      - "~/Desktop"
""")

    def test_sanitize_command_safe(self):
        self.assertEqual(self.sanitizer.sanitize_command("!screenshot"), "!screenshot")
        self.assertEqual(self.sanitizer.sanitize_command("  !list_files ~/Documents  "), "!list_files ~/Documents")

    def test_sanitize_command_dangerous(self):
        self.assertIsNone(self.sanitizer.sanitize_command("!screenshot; rm -rf /"))
        self.assertIsNone(self.sanitizer.sanitize_command("!list_files | ls"))
        self.assertIsNone(self.sanitizer.sanitize_command("!get `cat /etc/passwd`"))
        self.assertIsNone(self.sanitizer.sanitize_command("!get $(cat /etc/passwd)"))
        self.assertIsNone(self.sanitizer.sanitize_command("!get ../../../etc/passwd"))

    def test_validate_command_whitelist(self):
        self.assertEqual(self.sanitizer.validate_command_whitelist("!screenshot"), (True, "screenshot"))
        self.assertEqual(self.sanitizer.validate_command_whitelist("!list_files"), (True, "list_files"))
        self.assertEqual(self.sanitizer.validate_command_whitelist("!unknown_command"), (False, "unknown_command"))

    def test_sanitize_filepath_safe(self):
        home = Path.home()
        self.assertEqual(self.sanitizer.sanitize_filepath(str(home / "Documents" / "test.txt")), str(home / "Documents" / "test.txt"))
        self.assertEqual(self.sanitizer.sanitize_filepath(str(home / "Downloads" / "test.pdf")), str(home / "Downloads" / "test.pdf"))

    def test_sanitize_filepath_unsafe(self):
        self.assertIsNone(self.sanitizer.sanitize_filepath("/etc/passwd"))
        self.assertIsNone(self.sanitizer.sanitize_filepath("../../../etc/passwd"))

if __name__ == '__main__':
    unittest.main()
