"""
Module for file management operations.
"""
import os
from pathlib import Path
from security.sanitizer import InputSanitizer

def list_files(path: str) -> str:
    """
    List files in a directory.
    """
    sanitizer = InputSanitizer()
    safe_path = sanitizer.sanitize_filepath(path)
    if not safe_path:
        return "❌ Path tidak diizinkan atau tidak valid."

    target = Path(safe_path)
    if not target.exists() or not target.is_dir():
        return "❌ Direktori tidak ditemukan."

    entries = []
    for item in sorted(target.iterdir()):
        if item.is_dir():
            entries.append(f"📁 {item.name}/")
        else:
            size = item.stat().st_size
            size_str = f"{size // 1024}KB" if size > 1024 else f"{size}B"
            entries.append(f"📄 {item.name} ({size_str})")

    return f"""📂 `{safe_path}`:
""" + """
""".join(entries[:50])  # Max 50 entries

def get_file(filepath: str) -> dict:
    """
    Get a file.
    """
    sanitizer = InputSanitizer()
    safe_path = sanitizer.sanitize_filepath(filepath)
    if not safe_path:
        return {"error": "Path tidak diizinkan."}

    target = Path(safe_path)
    if not target.exists() or not target.is_file():
        return {"error": "File tidak ditemukan."}

    # Cek ekstensi
    allowed_ext = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".log"}
    if target.suffix.lower() not in allowed_ext:
        return {"error": f"Ekstensi {target.suffix} tidak diizinkan."}

    # Cek ukuran (max 50MB)
    max_size = int(os.environ.get("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
    if target.stat().st_size > max_size:
        return {"error": "File terlalu besar (max 50MB)."}

    with open(target, "rb") as f:
        return {
            "filename": target.name,
            "data": f.read(),
            "mimetype": _guess_mimetype(target.suffix),
        }

def _guess_mimetype(suffix: str) -> str:
    mimetypes = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".log": "text/plain",
    }
    return mimetypes.get(suffix.lower(), "application/octet-stream")
