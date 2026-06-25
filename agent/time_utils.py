"""
Utility untuk parse durasi waktu dari format fleksibel.
Support: 30s, 5m, 2h, 1jam, 30menit, 10detik, atau angka saja (default menit).
"""
import re

def parse_duration(value: str, default_unit: str = "m") -> int:
    """
    Parse string durasi ke detik.
    
    Format:
      "30"     -> 30 * default_unit (default: menit)
      "30s"    -> 30 detik
      "5m"     -> 5 menit
      "2h"     -> 2 jam
      "1jam"   -> 1 jam
      "30menit"-> 30 menit
      "10detik"-> 10 detik
    
    Returns: jumlah detik (int)
    """
    if not value:
        return 0
    s = value.lower().strip()

    pairs = [
        ("detik", 1), ("menit", 60), ("jam", 3600),
        ("d", 1), ("m", 60), ("h", 3600), ("s", 1),
    ]

    for unit, mult in pairs:
        if s.endswith(unit):
            num = s[: -len(unit)].strip()
            try:
                return int(float(num) * mult)
            except ValueError:
                raise ValueError(f"Format waktu salah: {value}")

    # Coba parse sebagai angka saja (default unit)
    unit_map = {"d": 1, "m": 60, "h": 3600, "s": 1, "detik": 1, "menit": 60, "jam": 3600}
    try:
        num = float(s)
    except ValueError:
        raise ValueError(f"Format waktu salah: {value}. Gunakan format seperti: 30s, 5m, 2h, 1jam")

    mult = unit_map.get(default_unit, 60)
    return int(num * mult)


def format_duration(seconds: int) -> str:
    """Konversi detik ke format baca: '2 jam 30 menit'"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if secs > 0 or not parts:
        parts.append(f"{secs} detik")
    return " ".join(parts)
