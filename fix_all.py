import re

with open('bot/telegram_bot.py', 'r') as f:
    content = f.read()

# Remove global AGENT_URL and AGENT_API_KEY
content = re.sub(r'AGENT_URL = f"http://{os\.environ\.get\(\'AGENT_HOST\'.*?\n', '', content)
content = re.sub(r'AGENT_API_KEY = os\.environ\["AGENT_API_KEY"\]\n', '', content)

# Fix message_handler
old_handler = '''async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message_text = update.message.text

    token = _user_sessions.get(user_id)
    if not token:
        await update.message.reply_text("🔐 Belum login. Gunakan /start untuk autentikasi.")
        return

    if not AuthManager.verify_session_token(token):
        del _user_sessions[user_id]
        save_current_sessions()
        await update.message.reply_text("⏰ Sesi expired. Silakan /start ulang.")
        return

    if message_text in ["!term", "!exit"]:
        if message_text == "!term":
            if _terminal_mode.get(user_id):
                await update.message.reply_text("⚠️ Anda sudah berada dalam Mode Terminal.")
                return
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(f"{AGENT_URL}/terminal/start", json={"user_id": user_id}, headers=headers)
                    if res.status_code == 200:
                        _terminal_mode[user_id] = True
                        await update.message.reply_text("💻 <b>Mode Terminal Aktif</b>", parse_mode="HTML")
                        task = asyncio.create_task(poll_terminal(user_id, context, update.effective_chat.id))
                        _terminal_tasks[user_id] = task
                    else:
                        await update.message.reply_text("❌ Gagal memulai terminal.")
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {e}")
        else:
            _terminal_mode[user_id] = False
            if user_id in _terminal_tasks:
                _terminal_tasks[user_id].cancel()
                del _terminal_tasks[user_id]
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                await client.post(f"{AGENT_URL}/terminal/stop", json={"user_id": user_id}, headers=headers)
            await update.message.reply_text("👋 Mode Terminal dinonaktifkan.")
        return

    if _terminal_mode.get(user_id):
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{AGENT_URL}/terminal/write", json={"user_id": user_id, "data": message_text + "\\n"}, headers=headers)
            except Exception as e:
                await update.message.reply_text(f"❌ Error writing to terminal: {e}")
        return

    if not AuthManager.check_rate_limit(user_id):
        await update.message.reply_text("⚠️ Terlalu banyak perintah.")
        return

    await update.message.reply_text("⏳ Memproses...")
    try:
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{AGENT_URL}/command", json={"command": message_text, "user_id": user_id}, headers=headers, timeout=30)

        if res.status_code == 200:
            result = res.json()
            res_type = result.get("type")
            content = result.get("content")
            if res_type == "text":
                await update.message.reply_text(f"<code>{content}</code>", parse_mode="HTML")
            elif res_type == "image":
                import base64
                await update.message.reply_photo(base64.b64decode(content))
        elif res.status_code == 400:
            await update.message.reply_text(f"❌ {res.json().get('detail')}")
    except Exception as e:
        logger.error(f"Command error: {e}")
        await update.message.reply_text("❌ Terjadi error.")'''

new_handler = '''async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message_text = update.message.text.strip() if update.message.text else ""

    token = _user_sessions.get(user_id)
    if not token:
        await update.message.reply_text("🔐 Belum login. Gunakan /start untuk autentikasi.")
        return

    if not AuthManager.verify_session_token(token):
        del _user_sessions[user_id]
        save_current_sessions()
        await update.message.reply_text("⏰ Sesi expired. Silakan /start ulang.")
        return

    # Handle Multi-Agent Commands
    if message_text == "!status" or message_text == "!agents":
        agents = registry.get_all()
        if not agents:
            await update.message.reply_text("📉 Belum ada agent yang terdaftar.")
            return
        
        msg = "🖥️ <b>Daftar Agent:</b>\\n"
        for aid in agents.keys():
            mark = "✅" if _user_active_agent.get(user_id) == aid else "▫️"
            msg += f"{mark} <code>{aid}</code>\\n"
        msg += "\\nGunakan <code>!select &lt;agent_id&gt;</code> untuk memilih target."
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if message_text.startswith("!select "):
        target_agent = message_text.split(" ", 1)[1].strip()
        if registry.get_agent(target_agent):
            _user_active_agent[user_id] = target_agent
            await update.message.reply_text(f"🎯 Target diubah ke Agent: <b>{target_agent}</b>", parse_mode="HTML")
        else:
            await update.message.reply_text(f"❌ Agent '{target_agent}' tidak ditemukan.")
        return

    # Determine Active Agent
    active_agent_id = _user_active_agent.get(user_id)
    agents = registry.get_all()
    if not active_agent_id:
        if len(agents) == 1:
            active_agent_id = list(agents.keys())[0]
            _user_active_agent[user_id] = active_agent_id
            await update.message.reply_text(f"ℹ️ Auto-select Agent: <b>{active_agent_id}</b>", parse_mode="HTML")
        elif len(agents) > 1:
            await update.message.reply_text("⚠️ Anda memiliki lebih dari 1 Agent.\\nGunakan <code>!select &lt;agent_id&gt;</code> terlebih dahulu.", parse_mode="HTML")
            return
        else:
            await update.message.reply_text("❌ Belum ada agent yang terdaftar pada sistem.")
            return

    agent_data = registry.get_agent(active_agent_id)
    if not agent_data:
        del _user_active_agent[user_id]
        await update.message.reply_text("❌ Agent yang dipilih sudah tidak tersedia di registry.")
        return
        
    AGENT_URL = f"http://{agent_data['host']}:{agent_data['port']}"
    AGENT_API_KEY = agent_data['api_key']

    if message_text in ["!term", "!exit"]:
        if message_text == "!term":
            if _terminal_mode.get(user_id):
                await update.message.reply_text("⚠️ Anda sudah berada dalam Mode Terminal.")
                return
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(f"{AGENT_URL}/terminal/start", json={"user_id": user_id}, headers=headers)
                    if res.status_code == 200:
                        _terminal_mode[user_id] = True
                        await update.message.reply_text(f"💻 <b>Mode Terminal Aktif ({active_agent_id})</b>", parse_mode="HTML")
                        # Pass AGENT_URL and AGENT_API_KEY directly since they are dynamically resolved
                        task = asyncio.create_task(poll_terminal(user_id, context, update.effective_chat.id, AGENT_URL, AGENT_API_KEY))
                        _terminal_tasks[user_id] = task
                    else:
                        await update.message.reply_text("❌ Gagal memulai terminal.")
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {e}")
        else:
            _terminal_mode[user_id] = False
            if user_id in _terminal_tasks:
                _terminal_tasks[user_id].cancel()
                del _terminal_tasks[user_id]
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                await client.post(f"{AGENT_URL}/terminal/stop", json={"user_id": user_id}, headers=headers)
            await update.message.reply_text("👋 Mode Terminal dinonaktifkan.")
        return

    if _terminal_mode.get(user_id):
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{AGENT_URL}/terminal/write", json={"user_id": user_id, "data": message_text + "\\n"}, headers=headers)
            except Exception as e:
                await update.message.reply_text(f"❌ Error writing to terminal: {e}")
        return

    if not AuthManager.check_rate_limit(user_id):
        await update.message.reply_text("⚠️ Terlalu banyak perintah.")
        return

    await update.message.reply_text(f"⏳ Memproses di <b>{active_agent_id}</b>...", parse_mode="HTML")
    try:
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{AGENT_URL}/command", json={"command": message_text, "user_id": user_id}, headers=headers, timeout=30)

        if res.status_code == 200:
            result = res.json()
            res_type = result.get("type")
            content = result.get("content")
            if res_type == "text":
                await update.message.reply_text(f"<code>{content}</code>", parse_mode="HTML")
            elif res_type == "image":
                import base64
                await update.message.reply_photo(base64.b64decode(content))
        elif res.status_code == 400:
            await update.message.reply_text(f"❌ {res.json().get('detail')}")
    except Exception as e:
        logger.error(f"Command error: {e}")
        await update.message.reply_text("❌ Terjadi error menghubungi agent.")'''

content = content.replace(old_handler, new_handler)

with open('bot/telegram_bot.py', 'w') as f:
    f.write(content)
