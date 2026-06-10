"""
Module for executing scripts.
"""
from pathlib import Path
from security.sandbox import SandboxExecutor

async def run_script(script_name: str, user_id: str) -> str:
    """
    Run a script from the safe directory in a sandbox.
    """
    sandbox = SandboxExecutor()
    safe_dir = Path.home() / "safe_scripts"
    script_path = (safe_dir / script_name).resolve()

    # Make sure the script is in the safe directory
    try:
        script_path.relative_to(safe_dir)
    except ValueError:
        return "❌ Path traversal terdeteksi."

    if not script_path.exists():
        return f"❌ Script '{script_name}' tidak ditemukan di ~/safe_scripts."

    if script_path.suffix not in {".py", ".sh"}:
        return "❌ Hanya script .py dan .sh yang diizinkan."

    # Execute in sandbox
    result = await sandbox.run_in_sandbox(str(script_path), user_id)
    return result
