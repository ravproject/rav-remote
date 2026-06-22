import os
import pyotp
import datetime
from dotenv import load_dotenv

load_dotenv()

secret = os.environ.get("OTP_SECRET_KEY")
if not secret:
    print("Error: OTP_SECRET_KEY not found in .env")
else:
    totp = pyotp.TOTP(secret)
    print(f"Current laptop time: {datetime.datetime.now()}")
    print(f"Expected OTP code NOW: {totp.now()}")
    print(f"OTP Secret (First 4 chars): {secret[:4]}...")
