"""
Laptop Agent — FastAPI server yang menerima perintah dari bot
Jalankan di laptop yang ingin dikontrol
"""
import os
import base64
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from loguru import logger
from bot.command_router import CommandRouter
from security.audit_logger import AuditLogger
from security.sanitizer import InputSanitizer
from bot.auth import AuthManager
from .file_manager import save_file
from .battery_monitor import battery_monitor
from .system_monitor import sys_monitor
from security.watchdog import watchdog

AGENT_API_KEY = os.environ["AGENT_API_KEY"]
api_key_header = APIKeyHeader(name="X-API-Key")

router = CommandRouter()
auditor = AuditLogger()
sanitizer = InputSanitizer()


from .terminal_manager import terminal_manager

class CommandRequest(BaseModel):
    command: str
    user_id: str

class TerminalWriteRequest(BaseModel):
    user_id: str
    data: str

class TerminalRequest(BaseModel):
    user_id: str

class OTPRequest(BaseModel):
    user_id: str
    otp: str

import shutil
import platform

def check_system_dependencies():
    """Environment Health Check: Memastikan system dependencies tersedia."""
    missing = []
    current_os = platform.system()
    
    if current_os == "Linux":
        if not shutil.which("ffmpeg"):
            missing.append("ffmpeg (Dibutuhkan untuk perekaman video)")
        if not shutil.which("ydotool"):
            missing.append("ydotool (Dibutuhkan untuk fitur !unlock paksa)")
        if not shutil.which("wl-copy") and not shutil.which("xclip") and not shutil.which("xsel"):
            missing.append("wl-clipboard atau xclip (Dibutuhkan untuk sinkronisasi clipboard !clip)")
            
    if missing:
        logger.warning("⚠️ BEBERAPA DEPENDENSI SISTEM TIDAK DITEMUKAN:")
        for m in missing:
            logger.warning(f"  - {m}")
        if current_os == "Linux":
            logger.info("💡 Saran perbaikan: sudo apt-get install ffmpeg ydotool wl-clipboard xclip")
    else:
        logger.info("✅ Environment Health Check: Semua dependensi sistem terpenuhi.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Laptop Agent starting...")
    check_system_dependencies()
    yield
    logger.info("Laptop Agent shutdown")

app = FastAPI(
    title="Remote Laptop Agent",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.get("/system/heartbeat")
async def heartbeat(_=Depends(verify_api_key)):
    """Heartbeat endpoint for Bot polling (Scenario C/VPN)."""
    metrics = sys_monitor.get_metrics()
    # Check for anomalies and battery
    anomalies = watchdog.check_system_anomalies(metrics["cpu"], metrics["ram"])
    battery = battery_monitor.get_alerts()
    return {
        "status": "ONLINE",
        "metrics": metrics,
        "alerts": anomalies + battery
    }

@app.get("/system/alerts")
async def get_alerts(_=Depends(verify_api_key)):
    # Combine battery alerts with watchdog anomalies
    metrics = sys_monitor.get_metrics()
    anomalies = watchdog.check_system_anomalies(metrics["cpu"], metrics["ram"])
    battery = battery_monitor.get_alerts()
    return {"alerts": anomalies + battery}


@app.post("/auth/verify-otp")
async def verify_otp(request: OTPRequest, _=Depends(verify_api_key)):
    if AuthManager.verify_otp(request.otp):
        token = AuthManager.generate_session_token(request.user_id)
        return {"token": token}
    else:
        # Record failure for watchdog
        is_brute = watchdog.record_otp_failure(request.user_id)
        if is_brute:
             logger.critical(f"Suspicious activity: Excessive OTP failures for {request.user_id}")
        raise HTTPException(status_code=401, detail="Invalid OTP")


@app.post("/terminal/start")
async def terminal_start(request: TerminalRequest, authorization: str = Header(...), _=Depends(verify_api_key)):
    token = authorization.replace("Bearer ", "")
    if AuthManager.verify_session_token(token) == request.user_id:
        if terminal_manager.start_session(request.user_id):
            return {"status": "success"}
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/terminal/write")
async def terminal_write(request: TerminalWriteRequest, authorization: str = Header(...), _=Depends(verify_api_key)):
    token = authorization.replace("Bearer ", "")
    if AuthManager.verify_session_token(token) == request.user_id:
        terminal_manager.write_to_session(request.user_id, request.data)
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/terminal/read/{user_id}")
async def terminal_read(user_id: str, authorization: str = Header(...), _=Depends(verify_api_key)):
    token = authorization.replace("Bearer ", "")
    if AuthManager.verify_session_token(token) == user_id:
        output = terminal_manager.read_from_session(user_id)
        return {"output": output or ""}
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/terminal/stop")
async def terminal_stop(request: TerminalRequest, authorization: str = Header(...), _=Depends(verify_api_key)):
    token = authorization.replace("Bearer ", "")
    if AuthManager.verify_session_token(token) == request.user_id:
        terminal_manager.stop_session(request.user_id)
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/file/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    authorization: str = Header(...),
    _=Depends(verify_api_key)
):
    token = authorization.replace("Bearer ", "")
    if AuthManager.verify_session_token(token) == user_id:
        content = await file.read()
        result = save_file(file.filename, content)
        return {"status": "success", "message": result}
    raise HTTPException(status_code=401, detail="Unauthorized")

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

    if isinstance(result, bytes): # Legacy fallback
        return {"type": "image", "content": base64.b64encode(result).decode()}
    elif isinstance(result, dict):
        res_type = result.get("type")
        if res_type == "photo":
            return {"type": "image", "content": base64.b64encode(result["data"]).decode()}
        elif res_type == "video":
            return {"type": "video", "content": {
                "data": base64.b64encode(result["data"]).decode(),
                "filename": result.get("filename", "screen_record.mp4"),
                "mimetype": result.get("mimetype", "video/mp4"),
            }}
        elif res_type == "document" or ("filename" in result and "data" in result):
            return {"type": "document", "content": {
                "data": base64.b64encode(result["data"]).decode(),
                "filename": result.get("filename", "file.dat"),
                "mimetype": result.get("mimetype", "application/octet-stream"),
            }}
        elif "error" in result:
             return {"type": "text", "content": f"❌ {result['error']}"}
        else:
            final_text = str(result)
            if len(final_text) > 4000:
                return {"type": "document", "content": {
                    "data": base64.b64encode(final_text.encode()).decode(),
                    "filename": "output.txt",
                    "mimetype": "text/plain",
                }}
            return {"type": "text", "content": final_text}
    else:
        # Check if result is the specific summary from sys_monitor
        final_text = str(result)
        if request.command.strip() == "!sysinfo":
             final_text = sys_monitor.get_system_summary()
             
        if len(final_text) > 4000:
            return {"type": "document", "content": {
                "data": base64.b64encode(final_text.encode()).decode(),
                "filename": "output.txt",
                "mimetype": "text/plain",
            }}
        return {"type": "text", "content": final_text}


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",  # HANYA localhost — jangan 0.0.0.0
            port=int(os.environ.get("AGENT_PORT", "8765")),
            ssl_keyfile=os.environ.get("SSL_KEYFILE"),
            ssl_certfile=os.environ.get("SSL_CERTFILE"),
            loop="asyncio",
        )
    except KeyboardInterrupt:
        logger.info("Laptop Agent stopped by user request.")
