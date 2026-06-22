import re
with open('bot/telegram_bot.py', 'r') as f:
    content = f.read()

# Find where the malformed block begins
target = '    app.run_polling(drop_pending_updates=True)\n   elif res.status_code == 400:'
if target in content:
    idx = content.find('   elif res.status_code == 400:')
    # Keep the first part, but we need to fix message_handler.
    # Actually, it's easier to just strip the duplicated ending and fix message_handler.
