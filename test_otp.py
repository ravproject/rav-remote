import pyotp
import os
from dotenv import load_dotenv

load_dotenv()
s = os.getenv("OTP_SECRET_KEY")
print("Secret:", s[:4] if s else "None")
t = pyotp.TOTP(s)
print("Code:", t.now())
