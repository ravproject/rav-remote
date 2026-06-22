"""
Terminal Manager — Handles persistent terminal sessions across platforms.
Supports PTY for Unix and standard subprocess for Windows.
"""
import re
import os
import subprocess
import signal
import threading
import time
import platform
from typing import Dict, Optional
from loguru import logger

# Conditional import for PTY (Unix only)
try:
    import pty
    import select
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences and OSC sequences."""
    ansi_escape = re.compile(r'''
        \x1B(?:          # ESC
            \[ [0-?]* [ -/]* [@-~] |    # CSI
            \] .*? (?:\x1B\\|\x07) |    # OSC
            [()#?] [0-?]* [ -/]* [@-~] | # Charset/Other
            [@-Z\\-_]                   # 7-bit controls
        )
    ''', re.VERBOSE | re.DOTALL)
    text = ansi_escape.sub('', text)
    # Squash excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip('\n')

class TerminalSession:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_os = platform.system()
        self.is_active = True
        self.output_buffer = b""
        self.lock = threading.Lock()
        self.last_activity = time.time()

        if HAS_PTY:
            self._init_unix()
        else:
            self._init_windows()

    def _init_unix(self):
        """Unix-specific PTY initialization."""
        shell = os.environ.get("SHELL", "/bin/bash")
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
        self.reader_thread = threading.Thread(target=self._read_loop_unix, daemon=True)
        self.reader_thread.start()

    def _init_windows(self):
        """Windows-specific initialization using cmd.exe."""
        # Note: True PTY is harder on Windows without winpty/pywinpty, 
        # so we use a standard subprocess pipe as fallback.
        shell = "cmd.exe"
        self.process = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.expanduser("~"),
            env=os.environ.copy(),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        self.reader_thread = threading.Thread(target=self._read_loop_windows, daemon=True)
        self.reader_thread.start()

    def _read_loop_unix(self):
        """Unix read loop using select."""
        while self.is_active:
            try:
                r, w, e = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if not data: break
                    with self.lock:
                        self.output_buffer += data
                        self.last_activity = time.time()
            except: break
        self.close()

    def _read_loop_windows(self):
        """Windows read loop using simple pipe read."""
        while self.is_active:
            try:
                data = self.process.stdout.read(1024)
                if not data: break
                with self.lock:
                    self.output_buffer += data
                    self.last_activity = time.time()
            except: break
        self.close()

    def write(self, data: str):
        """Write input to terminal."""
        if not self.is_active: return
        try:
            if HAS_PTY:
                os.write(self.master_fd, data.encode())
            else:
                self.process.stdin.write(data.encode())
                self.process.stdin.flush()
            self.last_activity = time.time()
        except OSError as e:
            logger.error(f"Write failed: {e}")

    def read(self) -> str:
        """Read output from buffer."""
        with self.lock:
            if not self.output_buffer: return ""
            try:
                data = self.output_buffer.decode(errors="replace")
                self.output_buffer = b""
                return strip_ansi_codes(data)
            except: return ""

    def close(self):
        """Close session."""
        if not self.is_active: return
        self.is_active = False
        try:
            if HAS_PTY:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                os.close(self.master_fd)
                os.close(self.slave_fd)
            else:
                self.process.terminate()
        except: pass
        logger.info(f"Terminal session closed for {self.user_id}")

class TerminalManager:
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def start_session(self, user_id: str) -> bool:
        if user_id in self.sessions: self.sessions[user_id].close()
        try:
            self.sessions[user_id] = TerminalSession(user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to start terminal: {e}")
            return False

    def write_to_session(self, user_id: str, data: str):
        if user_id in self.sessions: self.sessions[user_id].write(data)

    def read_from_session(self, user_id: str) -> Optional[str]:
        if user_id in self.sessions: return self.sessions[user_id].read()
        return None

    def stop_session(self, user_id: str):
        if user_id in self.sessions:
            self.sessions[user_id].close()
            del self.sessions[user_id]

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            self._cleanup_loop_once()

    def _cleanup_loop_once(self):
        now = time.time()
        to_delete = [uid for uid, s in self.sessions.items() if now - s.last_activity > 900 or s.process.poll() is not None]
        for uid in to_delete: self.stop_session(uid)

terminal_manager = TerminalManager()
