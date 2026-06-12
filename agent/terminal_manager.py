"""
Terminal Manager — Handles persistent PTY sessions for the agent.
Supports non-blocking read/write and session lifecycle management.
"""
import re
import os
import pty
import select
import subprocess
import signal
import threading
import time
from typing import Dict, Optional
from loguru import logger

def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape sequences and OSC (Operating System Command) sequences.
    Also squashes excessive newlines and filters out known noisy banners.
    """
    # 1. Remove ANSI/OSC sequences
    ansi_escape = re.compile(r'''
        \x1B(?:          # ESC
            \[ [0-?]* [ -/]* [@-~] |    # CSI
            \] .*? (?:\x1B\\|\x07) |    # OSC
            [()#?] [0-?]* [ -/]* [@-~] | # Charset/Other
            [@-Z\\-_]                   # 7-bit controls
        )
    ''', re.VERBOSE | re.DOTALL)
    text = ansi_escape.sub('', text)

    # 2. Filter out the specific noisy Gemini CLI migration banner
    # This banner is large and repetitive in unpaid/Google One tiers.
    banner_patterns = [
        r"Gemini CLI will stop serving requests to Google One",
        r"migrate to Antigravity CLI",
        r"https://antigravity.google/cli/install.sh",
        r"Gemini CLI v\d+\.\d+\.\d+",
        r"Signed in with Google /auth",
        r"Plan: Gemini Code Assist",
        r"[▝▜▄▟▀▗]" # Catch the ASCII art blocks
    ]
    
    # We remove the whole lines containing these patterns
    lines = text.splitlines()
    filtered_lines = []
    skip_box = False
    
    for line in lines:
        # Detect start of the announcement box
        if "╭──" in line and "──╮" in line:
            skip_box = True
            continue
        if "╰──" in line and "──╯" in line:
            skip_box = False
            continue
            
        if skip_box:
            continue
            
        if any(re.search(p, line) for p in banner_patterns):
            continue
        
        filtered_lines.append(line)
    
    text = "\n".join(filtered_lines)

    # 3. Squash excessive newlines (3+ -> 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 4. Remove leading/trailing empty lines
    return text.strip('\n')

class TerminalSession:
    def __init__(self, user_id: str, shell: str = "/bin/bash"):
        self.user_id = user_id
        self.shell = shell
        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            [shell],
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            preexec_fn=os.setsid,
            cwd=os.path.expanduser("~"),
            env=os.environ.copy()
        )
        self.output_buffer = b""
        self.lock = threading.Lock()
        self.is_active = True
        self.last_activity = time.time()
        
        # Start background thread to read from PTY
        self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.reader_thread.start()

    def _read_loop(self):
        """Continuously read from PTY master and store in buffer."""
        while self.is_active:
            try:
                # Use select to wait for output with a timeout
                r, w, e = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    with self.lock:
                        self.output_buffer += data
                        self.last_activity = time.time()
            except (OSError, ValueError):
                break
        self.close()

    def write(self, data: str):
        """Write input to PTY master."""
        if not self.is_active:
            return
        try:
            os.write(self.master_fd, data.encode())
            self.last_activity = time.time()
        except OSError as e:
            logger.error(f"Failed to write to terminal for {self.user_id}: {e}")

    def read(self) -> str:
        """Read latest output from buffer, strip ANSI codes, and clear it."""
        with self.lock:
            if not self.output_buffer:
                return ""
            try:
                data = self.output_buffer.decode(errors="replace")
                self.output_buffer = b""
                return strip_ansi_codes(data)
            except Exception as e:
                logger.error(f"Error reading terminal buffer: {e}")
                return ""

    def close(self):
        """Close the terminal session and kill the process."""
        if not self.is_active:
            return
        self.is_active = False
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.terminate()
            os.close(self.master_fd)
            os.close(self.slave_fd)
        except Exception as e:
            logger.debug(f"Error closing terminal for {self.user_id}: {e}")
        logger.info(f"Terminal session closed for user {self.user_id}")

class TerminalManager:
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def start_session(self, user_id: str) -> bool:
        """Start a new terminal session for a user."""
        if user_id in self.sessions:
            self.sessions[user_id].close()
        
        try:
            # Detect shell
            shell = os.environ.get("SHELL", "/bin/bash")
            self.sessions[user_id] = TerminalSession(user_id, shell)
            logger.info(f"Started terminal session for user {user_id} using {shell}")
            return True
        except Exception as e:
            logger.error(f"Failed to start terminal for {user_id}: {e}")
            return False

    def write_to_session(self, user_id: str, data: str):
        """Send input to an active session."""
        if user_id in self.sessions:
            self.sessions[user_id].write(data)

    def read_from_session(self, user_id: str) -> Optional[str]:
        """Read output from an active session."""
        if user_id in self.sessions:
            return self.sessions[user_id].read()
        return None

    def stop_session(self, user_id: str):
        """Force stop a session."""
        if user_id in self.sessions:
            self.sessions[user_id].close()
            del self.sessions[user_id]

    def _cleanup_loop_once(self):
        """Perform one pass of the cleanup logic."""
        now = time.time()
        to_delete = []
        for uid, session in self.sessions.items():
            # Cleanup if idle for more than 15 minutes or process died
            if now - session.last_activity > 900 or session.process.poll() is not None:
                to_delete.append(uid)
        
        for uid in to_delete:
            logger.info(f"Cleaning up idle/dead terminal session for {uid}")
            self.stop_session(uid)

    def _cleanup_loop(self):
        """Periodically clean up idle sessions."""
        while True:
            time.sleep(60)
            self._cleanup_loop_once()

# Global manager instance
terminal_manager = TerminalManager()
