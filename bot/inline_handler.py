"""
Inline mode handler untuk @botname query
Hanya merespon user yang terdaftar, tidak mengeksekusi perintah.
"""
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from html import escape
from .auth import AuthManager

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not AuthManager.is_user_allowed(user_id):
        await update.inline_query.answer([], cache_time=300, is_personal=True)
        return

    query = update.inline_query.query.strip()
    if not query:
        return

    results = [
        InlineQueryResultArticle(
            id="1",
            title=f"⚡ {query[:50]}",
            description="Kirim perintah ke laptop",
            input_message_content=InputTextMessageContent(
                f"⚡ Perintah: <code>{escape(query[:200])}</code>",
                parse_mode="HTML"
            ),
        ),
        InlineQueryResultArticle(
            id="2",
            title="📸 Screenshot",
            description="Ambil screenshot layar",
            input_message_content=InputTextMessageContent("!screenshot"),
        ),
        InlineQueryResultArticle(
            id="3",
            title="ℹ️ Sistem Info",
            description="Info CPU, RAM, Disk",
            input_message_content=InputTextMessageContent("!sysinfo"),
        ),
        InlineQueryResultArticle(
            id="4",
            title="📖 Bantuan",
            description="Tampilkan daftar perintah",
            input_message_content=InputTextMessageContent("!help"),
        ),
    ]

    await update.inline_query.answer(results, cache_time=5, is_personal=True)
