"""
Sandbox Executor — Isolasi eksekusi script berbahaya
Menggunakan firejail (Linux) atau Docker container
"""
import os
import asyncio
import subprocess
import platform
import tempfile
from pathlib import Path
from loguru import logger

SANDBOX_TIMEOUT = 30  # detik
USE_DOCKER = os.environ.get("SANDBOX_USE_DOCKER", "false").lower() == "true"


class SandboxExecutor:

    def __init__(self):
        self.system = platform.system()
        self.has_firejail = self._check_firejail()
        self.has_docker = self._check_docker()

    def _check_firejail(self) -> bool:
        try:
            subprocess.run(["firejail", "--version"], capture_output=True, timeout=3)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_docker(self) -> bool:
        try:
            subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def run_in_sandbox(self, script_path: str, user_id: str) -> str:
        """
        Jalankan script dalam sandbox yang terisolasi.
        Pilih metode sandbox terbaik yang tersedia.
        """
        logger.info(f"Sandbox exec: {script_path} by {user_id}")

        if USE_DOCKER and self.has_docker:
            return await self._run_docker(script_path)
        elif self.has_firejail and self.system == "Linux":
            return await self._run_firejail(script_path)
        else:
            return await self._run_restricted(script_path)

    async def _run_firejail(self, script_path: str) -> str:
        """
        Eksekusi dengan firejail — isolasi filesystem, network, proses.
        """
        path = Path(script_path)
        cmd = [
            "firejail",
            "--quiet",
            "--noprofile",
            "--private",           # Filesystem sementara
            "--net=none",          # Tanpa akses internet
            "--noroot",            # Tidak bisa jadi root
            "--rlimit-cpu=10",     # Max 10 detik CPU
            "--rlimit-as=268435456",  # Max 256MB RAM
            "python3" if path.suffix == ".py" else "bash",
            script_path,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SANDBOX_TIMEOUT
            )

            if proc.returncode != 0:
                return f"""Script error:
{stderr.decode()[:500]}"""

            return stdout.decode()[:2000]  # Batasi output

        except asyncio.TimeoutError:
            proc.kill()
            return "❌ Timeout: script melebihi 30 detik."

    async def _run_docker(self, script_path: str) -> str:
        """
        Eksekusi dalam Docker container yang sangat terbatas.
        """
        path = Path(script_path)
        runtime = "python:3.11-slim" if path.suffix == ".py" else "bash:5"
        exec_cmd = f"python /script{path.suffix}" if path.suffix == ".py" else f"bash /script{path.suffix}"

        cmd = [
            "docker", "run",
            "--rm",                          # Hapus container setelah selesai
            "--network", "none",             # Tanpa internet
            "--memory", "256m",              # Max 256MB RAM
            "--cpus", "0.5",                 # Max 0.5 CPU
            "--read-only",                   # Filesystem read-only
            "--security-opt", "no-new-privileges",
            "--user", "nobody",              # Jalankan sebagai nobody
            "-v", f"{script_path}:/script{path.suffix}:ro",  # Mount script read-only
            "--timeout", str(SANDBOX_TIMEOUT),
            runtime,
            *exec_cmd.split(),
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SANDBOX_TIMEOUT + 5
            )

            if proc.returncode != 0:
                return f"""Docker exec error:
{stderr.decode()[:500]}"""

            return stdout.decode()[:2000]

        except asyncio.TimeoutError:
            return "❌ Timeout: Docker container dihentikan."

    async def _run_restricted(self, script_path: str) -> str:
        """
        Fallback: eksekusi dengan resource limits minimal.
        Gunakan jika firejail dan Docker tidak tersedia.
        """
        path = Path(script_path)
        cmd = (
            ["python3", script_path]
            if path.suffix == ".py"
            else ["bash", script_path]
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "HOME": str(Path.home()),
                    "PYTHONPATH": "",  # Bersihkan PYTHONPATH
                }
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SANDBOX_TIMEOUT
            )

            if proc.returncode != 0:
                return f"""Error:
{stderr.decode()[:500]}"""

            return stdout.decode()[:2000]

        except asyncio.TimeoutError:
            proc.kill()
            return "❌ Timeout: script dihentikan setelah 30 detik."
