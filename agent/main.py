"""
Laptop Agent — FastAPI server yang menerima perintah dari bot
Jalankan di laptop yang ingin dikontrol
"""
import os
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from loguru import logger
from bot.command_router import CommandRouter
from security.audit_logger import AuditLogger
from security.sanitizer import InputSanitizer
from bot.auth import AuthManager

AGENT_API_KEY = os.environ["AGENT_API_KEY"]
api_key_header = APIKeyHeader(name="X-API-Key")

router = CommandRouter()
auditor = AuditLogger()
sanitizer = InputSanitizer()


class CommandRequest(BaseModel):
    command: str
    user_id: str


class OTPRequest(BaseModel):
    user_id: str
    otp: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Laptop Agent started")
    yield
    logger.info("Laptop Agent shutdown")


app = FastAPI(
    title="Remote Laptop Agent",
    docs_url=None,   # Sembunyikan docs di produksi
    redoc_url=None,
    lifespan=lifespan,
)


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@app.post("/auth/verify-otp")
async def verify_otp(request: OTPRequest, _=Depends(verify_api_key)):
    if AuthManager.verify_otp(request.otp):
        token = AuthManager.generate_session_token(request.user_id)
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid OTP")


@app.post("/command")
async def execute_command(
    request: CommandRequest,
    authorization: str = Header(...),
    _=Depends(verify_api_key),
):
    """Endpoint utama untuk eksekusi perintah."""
    # Verifikasi JWT dari bot
    token = authorization.replace("Bearer ", "")
    verified_user = AuthManager.verify_session_token(token)
    if not verified_user or verified_user != request.user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Sanitasi input
    clean_input = sanitizer.sanitize_command(request.command)
    if not clean_input:
        auditor.log_security_alert(request.user_id, "INJECTION_ATTEMPT", request.command)
        raise HTTPException(status_code=400, detail="Input tidak valid atau berbahaya")

    result = await router.route(clean_input, request.user_id)

    if isinstance(result, bytes):
        return {"type": "image", "content": base64.b64encode(result).decode()}
    elif isinstance(result, dict):
        return {"type": "document", "content": {
            "data": base64.b64encode(result["data"]).decode(),
            "filename": result["filename"],
            "mimetype": result["mimetype"],
        }}
    else:
        return {"type": "text", "content": result}


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    uvicorn.run(
        app,
        host="127.0.0.1",  # HANYA localhost — jangan 0.0.0.0
        port=int(os.environ.get("AGENT_PORT", "8765")),
        ssl_keyfile=os.environ.get("SSL_KEYFILE"),
        ssl_certfile=os.environ.get("SSL_CERTFILE"),
    )
