"""
Rate limiting logic
"""
import time
from loguru import logger
import os

_user_command_times: dict[str, list[float]] = {}
def check_rate_limit(user_id: str) -> bool:
    """
    Rate limiting: max N perintah per menit per user.
    Return True jika masih dalam batas.
    """
    max_per_minute = int(os.environ.get("MAX_COMMANDS_PER_MINUTE", "10"))
    now = time.time()
    user_times = _user_command_times.get(user_id, [])

    # Hapus entry lebih dari 60 detik yang lalu
    user_times = [t for t in user_times if now - t < 60]

    if len(user_times) >= max_per_minute:
        logger.warning(f"Rate limit exceeded for user: {user_id}")
        return False

    user_times.append(now)
    _user_command_times[user_id] = user_times
    return True
