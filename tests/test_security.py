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
        self.config_path = "config/allowed_commands.yaml"
        self.backup_path = "config/allowed_commands.yaml.bak"
        # Backup original config if exists
        if os.path.exists(self.config_path):
            import shutil
            shutil.copy2(self.config_path, self.backup_path)
            
        # Create a dummy allowed_commands.yaml for testing
        with open(self.config_path, "w") as f:
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

    def tearDown(self):
        # Restore original config
        if os.path.exists(self.backup_path):
            import shutil
            shutil.move(self.backup_path, self.config_path)

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
        # Sekarang semua folder diizinkan
        self.assertEqual(self.sanitizer.sanitize_filepath("/etc/passwd"), "/etc/passwd")
        cwd = Path.cwd()
        levels_to_root = len(cwd.parts) - 1
        rel_path = "../" * levels_to_root + "etc/passwd"
        self.assertEqual(self.sanitizer.sanitize_filepath(rel_path), "/etc/passwd")

if __name__ == '__main__':
    unittest.main()
