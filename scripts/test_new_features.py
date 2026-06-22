#!/usr/bin/env python3
"""
Script untuk menguji fungsionalitas fitur remote baru secara lokal.
"""
import sys
import os
import asyncio

# Tambahkan root workspace ke python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.command_handler import CommandHandler

async def main():
    handler = CommandHandler()
    print("🧪 ================= UJI FITUR BARU ================= 🧪\n")

    # 1. Test Battery
    print("🔋 [1/4] Menguji !battery...")
    battery_res = await handler.handle_battery()
    print(battery_res)
    print("\n" + "="*50 + "\n")

    # 2. Test Brightness
    print("🔆 [2/4] Menguji !brightness (Pembacaan)...")
    brightness_res = await handler.handle_brightness([])
    print(brightness_res)
    print("\n" + "="*50 + "\n")

    # 3. Test Process List
    print("⚙️ [3/4] Menguji !process list...")
    process_res = await handler.handle_process(["list"])
    print(process_res)
    print("\n" + "="*50 + "\n")

    # 4. Test Desktop Notification
    print("🔔 [4/4] Menguji !notif...")
    notif_res = await handler.handle_notif("Uji coba fitur notifikasi remote baru sukses!")
    print(notif_res)
    print("\n" + "="*50 + "\n")
    print("✅ Semua pengujian selesai!")

if __name__ == "__main__":
    asyncio.run(main())
