import os
# Guard: Set a placeholder to allow bootstrapping before .env exists
os.environ.setdefault("ENCRYPTION_KEY", "bootstrap_placeholder_secret_key_32_chars")

import secrets
import pyotp
import shutil
from datetime import datetime

ENV_FILE = ".env"
BACKUP_FILE = f".env.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Keys to regenerate
KEYS_TO_ROTATE = [
    "OTP_SECRET_KEY",
    "JWT_SECRET_KEY",
    "ENCRYPTION_KEY",
    "AGENT_API_KEY"
]

# External keys to PRESERVE
KEYS_TO_PRESERVE = [
    "TELEGRAM_BOT_TOKEN",
    "NVIDIA_NIM_API_KEY"
]

def generate_new_value(key):
    if key == "OTP_SECRET_KEY":
        return pyotp.random_base32()
    elif key == "JWT_SECRET_KEY":
        return secrets.token_hex(32)
    elif key == "ENCRYPTION_KEY":
        # AES-256 key (32 bytes) encoded in base64
        import base64
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    elif key == "AGENT_API_KEY":
        return secrets.token_urlsafe(32)
    return None

def rotate():
    if not os.path.exists(ENV_FILE):
        print(f"Error: {ENV_FILE} not found.")
        return

    # 1. Create backup
    shutil.copy2(ENV_FILE, BACKUP_FILE)
    print(f"Backup created: {BACKUP_FILE}")

    with open(ENV_FILE, "r") as f:
        lines = f.readlines()

    new_lines = []
    rotated_count = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            
            if key in KEYS_TO_ROTATE:
                new_val = generate_new_value(key)
                new_lines.append(f"{key}={new_val}\n")
                rotated_count += 1
                print(f"Rotating: {key}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)
    
    print(f"\nSuccessfully rotated {rotated_count} keys.")
    print("WARNING: Restart all services (Bot & Agent) to apply changes.")
    print("Active user sessions will be invalidated.")

if __name__ == "__main__":
    rotate()
