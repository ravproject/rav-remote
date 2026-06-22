"""
Quick Note — save markdown notes instantly.
"""
from pathlib import Path
from datetime import datetime

NOTES_DIR = Path.home() / "Documents" / "RAV-Notes"

def create_note(title: str, content: str = "") -> str:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip() or "untitled"
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title.replace(' ', '_')}.md"
    filepath = NOTES_DIR / filename
    with open(filepath, "w") as f:
        f.write(f"# {title}\n\nDate: {datetime.now().isoformat()}\n\n{content}\n")
    return f"Catatan tersimpan: {filepath}"

def list_notes(limit: int = 10) -> str:
    if not NOTES_DIR.exists():
        return "Belum ada catatan."
    files = sorted(NOTES_DIR.glob("*.md"), reverse=True)[:limit]
    if not files:
        return "Belum ada catatan."
    lines = [f"Catatan terbaru (terakhir {limit}):"]
    for f in files:
        lines.append(f"  {f.stem}")
    return "\n".join(lines)
