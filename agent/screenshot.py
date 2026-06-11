"""
Module for taking screenshots.
"""
import mss
import mss.tools
from loguru import logger

import os
import subprocess
import tempfile
from typing import Union

def take_screenshot() -> bytes | str:
    """
    Take a screenshot and return as PNG bytes, or string on error.
    """
    # 1. Coba mss dahulu (sangat cepat, bekerja di X11/Windows/macOS)
    try:
        # Set DISPLAY just in case
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            return mss.tools.to_png(screenshot.rgb, screenshot.size)
    except Exception as mss_err:
        logger.warning(f"MSS screenshot failed: {mss_err}. Mencoba fallback Wayland/CLI...")

    # 2. Fallback untuk Wayland / CLI tools
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    try:
        # Coba gnome-screenshot (GNOME Wayland/X11)
        try:
            subprocess.run(["gnome-screenshot", "-f", temp_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            with open(temp_path, "rb") as f:
                data = f.read()
            if data and len(data) > 0:
                return data
            raise ValueError("Screenshot file is empty")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            logger.warning(f"gnome-screenshot failed or timed out: {e}")

        # Coba grim (Sway/wlroots Wayland)
        try:
            subprocess.run(["grim", temp_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            with open(temp_path, "rb") as f:
                data = f.read()
            if data and len(data) > 0:
                return data
            raise ValueError("Screenshot file is empty")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        # Coba spectacle (KDE Wayland/X11)
        try:
            subprocess.run(["spectacle", "-b", "-n", "-o", temp_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            with open(temp_path, "rb") as f:
                data = f.read()
            if data and len(data) > 0:
                return data
            raise ValueError("Screenshot file is empty")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        return (
            "❌ Gagal mengambil screenshot.\n\n"
            "Sistem Anda menggunakan **Wayland** (bukan X11) dan memblokir akses tangkapan layar dari aplikasi latar belakang (seperti VS Code Terminal).\n\n"
            "**Solusi**:\n"
            "1. Jalankan aplikasi menggunakan terminal sistem bawaan (bukan terminal VS Code) dengan perintah `npm start`.\n"
            "2. Atau, beralih ke sesi **Xorg/X11** saat masuk login Ubuntu jika ingin dukungan kendali jarak jauh penuh."
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
