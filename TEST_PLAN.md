# Rencana Test Manual — 50 Fitur RAV-REMOTE

Jalankan dari folder `/home/rav/Development/RAV-REMOTE`:
```bash
source venv/bin/activate
cd /home/rav/Development/RAV-REMOTE
```

---

## FASE 1: Productivity & Scheduling

### 1. !focus (Pomodoro)
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_focus([])))
print(asyncio.run(ch.handle_focus(['25'])))
"
```

### 2. !workspace
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_workspace([])))
print(asyncio.run(ch.handle_workspace(['save', 'dev'])))
print(asyncio.run(ch.handle_workspace(['list'])))
print(asyncio.run(ch.handle_workspace(['delete', 'dev'])))
"
```

### 3. !calendar
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_calendar(['today'])))
"
```

### 4. !quicknote
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_quicknote(['Test', 'note', 'dari', 'CLI'])))
"
```

### 5. !browser
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_browser(['open', 'https://google.com'])))
print(asyncio.run(ch.handle_browser(['close'])))
"
```

### 6. !daily
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_daily([])))
"
```

### 7. !reminder
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_reminder(['10s', 'Test', 'reminder'])))
"
```

### 8. !task
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_task(['add', 'Belajar Python'])))
print(asyncio.run(ch.handle_task(['list'])))
print(asyncio.run(ch.handle_task(['done', '1'])))
"
```

### 9. !meeting mode
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_meeting([])))
print(asyncio.run(ch.handle_meeting(['mode', 'on', 'Daily Standup'])))
print(asyncio.run(ch.handle_meeting(['mode', 'off'])))
"
```

### 10. !custom alias
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_custom(['alias', 'st', '!system dash'])))
print(asyncio.run(ch.handle_custom(['list'])))
print(asyncio.run(ch.handle_custom(['delete', 'st'])))
"
```

---

## FASE 2: AI & Smart Automation

### 11-16. !ai (work/write/automate/summarize/research/insight)
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
# Butuh NVIDIA_NIM_API_KEY di .env
print(asyncio.run(ch.handle_ai_work(['buatkan outline artikel tentang AI'])))
print(asyncio.run(ch.handle_ai_insight(['CPU 70%, RAM 80%, apa yang perlu diperbaiki?'])))
"
```

### 17. !smart clipboard
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_smart_clip(['copy', 'test@email.com'])))
print(asyncio.run(ch.handle_smart_clip(['paste'])))
print(asyncio.run(ch.handle_smart_clip(['history'])))
"
```

### 18. !macro
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_macro(['record', 'test'])))
print(asyncio.run(ch.handle_macro(['stop'])))
print(asyncio.run(ch.handle_macro(['list'])))
print(asyncio.run(ch.handle_macro(['delete', 'test'])))
"
```

### 19. !schedule
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_scheduler(['add', '10s', '!system dash'])))
print(asyncio.run(ch.handle_scheduler(['list'])))
print(asyncio.run(ch.handle_scheduler(['delete', '1'])))
"
```

### 20. !voice cmd
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_voice_cmd([])))
print(asyncio.run(ch.handle_voice_cmd(['on'])))
print(asyncio.run(ch.handle_voice_cmd(['off'])))
"
```

---

## FASE 3: File, Sync & Data Management

### 21. !sync
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_sync(['/tmp/test-sync', 'local'])))
"
```

### 22. !quick upload
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_quick_upload([])))
"
```

### 23. !recent
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_recent(['files', '5'])))
print(asyncio.run(ch.handle_recent(['folders', '5'])))
"
```

### 24. !search content
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_search_content(['content', 'import', '/home/rav/Development/RAV-REMOTE'])))
"
```

### 25. !convert
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_convert([])))
"
```

### 26. !backup
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_backup(['/home/rav/Documents', 'quick'])))
"
```

### 27. !organize
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_organize(['/tmp', 'by', 'type'])))
"
```

### 28. !file watcher
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_file_watcher(['watcher', 'on', '/tmp'])))
print(asyncio.run(ch.handle_file_watcher(['watcher', 'status'])))
print(asyncio.run(ch.handle_file_watcher(['watcher', 'off', '/tmp'])))
"
```

### 29. !version
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_version(['commit', '/home/rav/Development/RAV-REMOTE/README.md'])))
print(asyncio.run(ch.handle_version(['history', '/home/rav/Development/RAV-REMOTE/README.md'])))
"
```

### 30. !clean
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_clean(['temp'])))
print(asyncio.run(ch.handle_clean(['cache'])))
"
```

---

## FASE 4: System Enhancement

### 31. !volume
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_volume_app(['80'])))
print(asyncio.run(ch.handle_volume_app(['up'])))
print(asyncio.run(ch.handle_volume_app(['down'])))
print(asyncio.run(ch.handle_volume_app(['mute'])))
"
```

### 32. !power
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_power(['balanced'])))
print(asyncio.run(ch.handle_power(['saver'])))
"
```

### 33. !multi monitor
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_multi_monitor(['monitor', 'list'])))
print(asyncio.run(ch.handle_multi_monitor(['switch', 'auto'])))
"
```

### 34. !sleep (HATI-HATI: bikin laptop tidur)
```bash
# SLEEP AKAN MEMATIKAN LAPTOP — JALANKAN DENGAN HATI-HATI
# python3 -c "
# import sys; sys.path.insert(0, '.')
# from agent.command_handler import CommandHandler
# ch = CommandHandler()
# import asyncio
# print(asyncio.run(ch.handle_sleep([])))
# "
```

### 35. !quick app
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_quick_app(['firefox'])))
"
```

### 36. !battery health
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_battery(['health'])))
"
```

### 37. !night mode
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_night_mode(['mode', 'on'])))
print(asyncio.run(ch.handle_night_mode(['off'])))
"
```

### 38. !window
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_window_arrange(['arrange', 'cascade'])))
print(asyncio.run(ch.handle_window_arrange(['snap', 'left'])))
print(asyncio.run(ch.handle_window_arrange(['minimize', 'all'])))
print(asyncio.run(ch.handle_window_arrange(['close', 'all'])))
"
```

### 39. !hotkey
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_hotkey(['create', 'test', 'Ctrl+Shift+T'])))
print(asyncio.run(ch.handle_hotkey(['list'])))
print(asyncio.run(ch.handle_hotkey(['delete', 'test'])))
"
```

### 40. !launch advanced
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_launch_advanced(['firefox', '--private-window'])))
"
```

---

## FASE 5: Advanced & Pro

### 41. !time track
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_time_track(['track', 'start', 'Testing'])))
print(asyncio.run(ch.handle_time_track(['status'])))
print(asyncio.run(ch.handle_time_track(['stop'])))
print(asyncio.run(ch.handle_time_track(['report', '7'])))
"
```

### 42. !session
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_session(['list'])))
print(asyncio.run(ch.handle_session(['save', 'test-session'])))
print(asyncio.run(ch.handle_session(['list'])))
print(asyncio.run(ch.handle_session(['delete', 'test-session'])))
"
```

### 43. !share screen
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_share_screen([])))
"
```

### 44. !multi device
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_multi_device(['register', 'phone', '10.0.0.2'])))
print(asyncio.run(ch.handle_multi_device([])))
print(asyncio.run(ch.handle_multi_device(['delete', 'phone'])))
"
```

### 45. !profile
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_profile(['create', 'work', 'firefox', 'code'])))
print(asyncio.run(ch.handle_profile(['list'])))
print(asyncio.run(ch.handle_profile(['apply', 'work'])))
print(asyncio.run(ch.handle_profile(['delete', 'work'])))
"
```

### 46. !dash
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_dash([])))
"
```

### 47. !activity log
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_activity_log(['log', '7'])))
"
```

### 48. !vpn
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_vpn([])))
print(asyncio.run(ch.handle_vpn(['status'])))
"
```

### 49. !tunnel
```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
print(asyncio.run(ch.handle_tunnel(['create', 'dev', 'example.com', '8080'])))
print(asyncio.run(ch.handle_tunnel(['list'])))
print(asyncio.run(ch.handle_tunnel(['delete', 'dev'])))
"
```

### 50. !ai agent
```bash
python3 -c "
import sys; sys.path.insert(0, '.'
from agent.command_handler import CommandHandler
ch = CommandHandler()
import asyncio
# Butuh NVIDIA_NIM_API_KEY
print(asyncio.run(ch.handle_ai_agent(['history'])))
print(asyncio.run(ch.handle_ai_agent(['Apa penggunaan CPU saat ini?'])))
"
```
