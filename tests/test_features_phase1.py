"""
Tests for Phase 1 Productivity Features:
!focus, !workspace, !quicknote, !browser, !daily, !reminder, !task, !meeting, !custom
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from agent.command_handler import CommandHandler


class TestFocus(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.focus.focus_manager')
    async def test_focus_no_args(self, mock_focus):
        mock_focus.get_remaining.return_value = "Focus Mode: sisa 24:30 dari 25 menit."
        res = await self.handler.handle_focus([])
        self.assertIn("24:30", res)
        mock_focus.get_remaining.assert_called_once()

    @patch('agent.focus.focus_manager')
    async def test_focus_on_default(self, mock_focus):
        mock_focus.start.return_value = "Focus Mode AKTIF selama 25 menit. Notifikasi dimatikan, situs diblokir."
        res = await self.handler.handle_focus(["on"])
        self.assertIn("AKTIF", res)
        mock_focus.start.assert_called_with(25)

    @patch('agent.focus.focus_manager')
    async def test_focus_on_with_minutes(self, mock_focus):
        mock_focus.start.return_value = "Focus Mode AKTIF selama 50 menit."
        res = await self.handler.handle_focus(["on", "50"])
        self.assertIn("AKTIF", res)
        mock_focus.start.assert_called_with(50)

    @patch('agent.focus.focus_manager')
    async def test_focus_on_with_duration_parse(self, mock_focus):
        mock_focus.start.return_value = "Focus Mode AKTIF selama 45 menit."
        res = await self.handler.handle_focus(["on", "45m"])
        self.assertIn("AKTIF", res)
        mock_focus.start.assert_called_with(45)

    @patch('agent.focus.focus_manager')
    async def test_focus_off(self, mock_focus):
        mock_focus.stop.return_value = "Focus Mode DINONAKTIFKAN."
        res = await self.handler.handle_focus(["off"])
        self.assertIn("DINONAKTIFKAN", res)
        mock_focus.stop.assert_called_once()

    @patch('agent.focus.focus_manager')
    async def test_focus_unknown_subcommand(self, mock_focus):
        res = await self.handler.handle_focus(["invalid"])
        self.assertIn("Gunakan", res)


class TestWorkspace(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_no_args(self, mock_ws):
        res = await self.handler.handle_workspace([])
        self.assertIn("Gunakan", res)

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_save(self, mock_ws):
        mock_ws.save.return_value = "Workspace 'coding' tersimpan (5 app): code, terminal, chrome +2 lainnya"
        res = await self.handler.handle_workspace(["save", "coding"])
        self.assertIn("coding", res)
        self.assertIn("tersimpan", res)
        mock_ws.save.assert_called_with("coding")

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_load(self, mock_ws):
        mock_ws.load.return_value = "Workspace 'coding' dimuat (5 app dipulihkan)."
        res = await self.handler.handle_workspace(["load", "coding"])
        self.assertIn("coding", res)
        self.assertIn("dimuat", res)
        mock_ws.load.assert_called_with("coding")

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_list(self, mock_ws):
        mock_ws.list_workspaces.return_value = "Daftar Workspace:\n  coding (hari ini, linux, 5 app)"
        res = await self.handler.handle_workspace(["list"])
        self.assertIn("Daftar Workspace", res)
        mock_ws.list_workspaces.assert_called_once()

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_delete(self, mock_ws):
        mock_ws.delete.return_value = "Workspace 'coding' dihapus."
        res = await self.handler.handle_workspace(["delete", "coding"])
        self.assertIn("coding", res)
        self.assertIn("dihapus", res)
        mock_ws.delete.assert_called_with("coding")

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_delete_aliased(self, mock_ws):
        mock_ws.delete.return_value = "Workspace 'test' dihapus."
        res = await self.handler.handle_workspace(["del", "test"])
        self.assertIn("test", res)
        mock_ws.delete.assert_called_with("test")

    @patch('agent.workspace.workspace_manager')
    async def test_workspace_unknown_subcommand(self, mock_ws):
        res = await self.handler.handle_workspace(["invalid"])
        self.assertIn("Subperintah tidak dikenal", res)


class TestQuicknote(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.quicknote.list_notes')
    @patch('agent.quicknote.create_note')
    async def test_quicknote_no_args_lists_notes(self, mock_create, mock_list):
        mock_list.return_value = "Catatan terbaru (terakhir 10):\n  20260101_1200_meeting"
        res = await self.handler.handle_quicknote([])
        self.assertIn("Catatan terbaru", res)
        mock_list.assert_called_once()
        mock_create.assert_not_called()

    @patch('agent.quicknote.list_notes')
    @patch('agent.quicknote.create_note')
    async def test_quicknote_with_title(self, mock_create, mock_list):
        mock_create.return_value = "Catatan tersimpan: /home/user/Documents/RAV-Notes/note.md"
        res = await self.handler.handle_quicknote(["meeting", "hasil", "rapat"])
        mock_create.assert_called_with("meeting", "hasil rapat")
        self.assertIn("Catatan tersimpan", res)

    @patch('agent.quicknote.list_notes')
    @patch('agent.quicknote.create_note')
    async def test_quicknote_title_only(self, mock_create, mock_list):
        mock_create.return_value = "Catatan tersimpan: /home/user/Documents/RAV-Notes/note.md"
        res = await self.handler.handle_quicknote(["ide"])
        mock_create.assert_called_with("ide", "")
        self.assertIn("Catatan tersimpan", res)


class TestBrowser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.browser_controller.browser_new')
    async def test_browser_no_args(self, mock_new):
        res = await self.handler.handle_browser([])
        self.assertIn("Gunakan", res)

    @patch('agent.browser_controller.browser_new')
    async def test_browser_new(self, mock_new):
        mock_new.return_value = "Browser membuka: https://example.com"
        res = await self.handler.handle_browser(["new", "example.com"])
        mock_new.assert_called_once_with("example.com")
        self.assertIn("Browser membuka", res)

    @patch('agent.browser_controller.browser_search')
    async def test_browser_search(self, mock_search):
        mock_search.return_value = "Browser membuka: https://www.google.com/search?q=test+query"
        res = await self.handler.handle_browser(["search", "test", "query"])
        mock_search.assert_called_once_with("test query")
        self.assertIn("search", res.lower())

    @patch('agent.browser_controller.browser_scroll')
    async def test_browser_scroll_down_default(self, mock_scroll):
        mock_scroll.return_value = "Page down pressed"
        res = await self.handler.handle_browser(["scroll"])
        mock_scroll.assert_called_once_with("down")

    @patch('agent.browser_controller.browser_scroll')
    async def test_browser_scroll_up(self, mock_scroll):
        mock_scroll.return_value = "Page up pressed"
        res = await self.handler.handle_browser(["scroll", "up"])
        mock_scroll.assert_called_once_with("up")

    @patch('agent.browser_controller.browser_refresh')
    async def test_browser_refresh(self, mock_refresh):
        mock_refresh.return_value = "F5 pressed"
        res = await self.handler.handle_browser(["refresh"])
        mock_refresh.assert_called_once()

    @patch('agent.browser_controller.browser_close')
    async def test_browser_close_default(self, mock_close):
        mock_close.return_value = "Tab aktif ditutup."
        res = await self.handler.handle_browser(["close"])
        mock_close.assert_called_once_with(None)

    @patch('agent.browser_controller.browser_close')
    async def test_browser_close_specific_tab(self, mock_close):
        mock_close.return_value = "Tab 2 ditutup."
        res = await self.handler.handle_browser(["close", "2"])
        mock_close.assert_called_once_with(2)

    @patch('agent.browser_controller.browser_new')
    async def test_browser_unknown_subcommand(self, mock_new):
        res = await self.handler.handle_browser(["invalid"])
        self.assertIn("Subperintah tidak dikenal", res)


class TestDaily(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.daily_report.generate_daily_report')
    @patch('ai_module.fast_ai.fast_ai')
    async def test_daily_today(self, mock_fast_ai, mock_report):
        mock_report.return_value = "Laporan Aktivitas Hari Ini (23/06/2026)"
        mock_fast_ai.enabled = False
        res = await self.handler.handle_daily([])
        self.assertIn("Hari Ini", res)
        mock_report.assert_called_with("today")

    @patch('agent.daily_report.generate_daily_report')
    @patch('ai_module.fast_ai.fast_ai')
    async def test_daily_yesterday(self, mock_fast_ai, mock_report):
        mock_report.return_value = "Laporan Aktivitas Kemarin (22/06/2026)"
        mock_fast_ai.enabled = False
        res = await self.handler.handle_daily(["yesterday"])
        self.assertIn("Kemarin", res)
        mock_report.assert_called_with("yesterday")

    @patch('agent.daily_report.generate_daily_report')
    @patch('ai_module.fast_ai.fast_ai')
    async def test_daily_with_ai_insight(self, mock_fast_ai, mock_report):
        mock_report.return_value = "Laporan Aktivitas Hari Ini"
        mock_fast_ai.enabled = True
        mock_fast_ai.summarize = AsyncMock(return_value="CPU normal, RAM cukup, disk aman.")
        res = await self.handler.handle_daily([])
        self.assertIn("Analisis", res)
        mock_fast_ai.summarize.assert_awaited_once()

    @patch('agent.daily_report.generate_daily_report')
    @patch('ai_module.fast_ai.fast_ai')
    async def test_daily_ai_fallback_on_error(self, mock_fast_ai, mock_report):
        mock_report.return_value = "Laporan Aktivitas Hari Ini"
        mock_fast_ai.enabled = True
        mock_fast_ai.summarize = AsyncMock(side_effect=Exception("API down"))
        res = await self.handler.handle_daily([])
        self.assertIn("Laporan Aktivitas", res)
        self.assertNotIn("Analisis", res)


class TestReminder(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_no_args(self, mock_rm):
        mock_rm.list_reminders.return_value = "Tidak ada pengingat."
        res = await self.handler.handle_reminder([])
        self.assertIn("Tidak ada", res)
        mock_rm.list_reminders.assert_called_once()

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_add(self, mock_rm):
        mock_rm.add.return_value = "Pengingat: 'meeting' pada 14:00 23/06/2026"
        res = await self.handler.handle_reminder(["add", "meeting", "14:00"])
        mock_rm.add.assert_called_with("meeting", "14:00")
        self.assertIn("Pengingat", res)

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_add_multi_word(self, mock_rm):
        mock_rm.add.return_value = "Pengingat: 'beli susu' pada 14:00 23/06/2026"
        res = await self.handler.handle_reminder(["add", "beli", "susu", "30m"])
        mock_rm.add.assert_called_with("beli susu", "30m")
        self.assertIn("Pengingat", res)

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_add_too_few_args(self, mock_rm):
        res = await self.handler.handle_reminder(["add"])
        self.assertIn("Gunakan", res)

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_list(self, mock_rm):
        mock_rm.list_reminders.return_value = "Daftar Pengingat:\n  1. [PENDING] meeting (14:00 23/06)"
        res = await self.handler.handle_reminder(["list"])
        self.assertIn("Daftar Pengingat", res)
        mock_rm.list_reminders.assert_called_once()

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_delete(self, mock_rm):
        mock_rm.delete.return_value = "Pengingat 'meeting' dihapus."
        res = await self.handler.handle_reminder(["delete", "1"])
        mock_rm.delete.assert_called_with(1)
        self.assertIn("dihapus", res)

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_delete_aliased(self, mock_rm):
        mock_rm.delete.return_value = "Pengingat 'test' dihapus."
        res = await self.handler.handle_reminder(["del", "1"])
        mock_rm.delete.assert_called_with(1)
        self.assertIn("dihapus", res)

    @patch('agent.reminder.reminder_manager')
    async def test_reminder_delete_missing_id(self, mock_rm):
        res = await self.handler.handle_reminder(["delete"])
        self.assertIn("Gunakan", res)


class TestTask(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.task_sync.task_manager')
    async def test_task_no_args(self, mock_tm):
        mock_tm.list_tasks.return_value = "Belum ada tugas."
        res = await self.handler.handle_task([])
        self.assertIn("Belum ada", res)
        mock_tm.list_tasks.assert_called_once()

    @patch('agent.task_sync.task_manager')
    async def test_task_add(self, mock_tm):
        mock_tm.add.return_value = "Tugas ditambahkan: coding feature (deadline: 23:59)"
        res = await self.handler.handle_task(["add", "coding", "feature"])
        mock_tm.add.assert_called_with("coding feature", None)
        self.assertIn("Tugas ditambahkan", res)

    @patch('agent.task_sync.task_manager')
    async def test_task_add_with_deadline(self, mock_tm):
        mock_tm.add.return_value = "Tugas ditambahkan: coding feature (deadline: 23:59)"
        res = await self.handler.handle_task(["add", "coding feature | 23:59"])
        mock_tm.add.assert_called_with("coding feature", "23:59")
        self.assertIn("deadline", res)

    @patch('agent.task_sync.task_manager')
    async def test_task_sync_alias(self, mock_tm):
        mock_tm.add.return_value = "Tugas ditambahkan: sync task"
        res = await self.handler.handle_task(["sync", "sync", "task"])
        mock_tm.add.assert_called_with("sync task", None)

    @patch('agent.task_sync.task_manager')
    async def test_task_list(self, mock_tm):
        mock_tm.list_tasks.return_value = "Daftar Tugas:\n  #1 [PENDING] coding feature"
        res = await self.handler.handle_task(["list"])
        self.assertIn("Daftar Tugas", res)
        mock_tm.list_tasks.assert_called_once()

    @patch('agent.task_sync.task_manager')
    async def test_task_done(self, mock_tm):
        mock_tm.done.return_value = "Tugas #1 'coding feature' selesai."
        res = await self.handler.handle_task(["done", "1"])
        mock_tm.done.assert_called_with(1)
        self.assertIn("selesai", res)

    @patch('agent.task_sync.task_manager')
    async def test_task_delete(self, mock_tm):
        mock_tm.delete.return_value = "Tugas #1 'coding feature' dihapus."
        res = await self.handler.handle_task(["delete", "1"])
        mock_tm.delete.assert_called_with(1)
        self.assertIn("dihapus", res)

    @patch('agent.task_sync.task_manager')
    async def test_task_delete_aliased(self, mock_tm):
        mock_tm.delete.return_value = "Tugas #1 'coding feature' dihapus."
        res = await self.handler.handle_task(["del", "1"])
        mock_tm.delete.assert_called_with(1)

    @patch('agent.task_sync.task_manager')
    async def test_task_unknown_subcommand(self, mock_tm):
        res = await self.handler.handle_task(["invalid"])
        self.assertIn("Gunakan", res)


class TestMeeting(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    async def test_meeting_no_args(self):
        res = await self.handler.handle_meeting([])
        self.assertIn("Gunakan", res)

    @patch('agent.meeting_mode.prepare_meeting')
    async def test_meeting_mode_on_default(self, mock_prep):
        mock_prep.return_value = "Mode Meeting 'Meeting': Notifikasi dimatikan."
        res = await self.handler.handle_meeting(["mode", "on"])
        mock_prep.assert_called_with("Meeting")
        self.assertIn("Mode Meeting", res)

    @patch('agent.meeting_mode.prepare_meeting')
    async def test_meeting_mode_on_with_name(self, mock_prep):
        mock_prep.return_value = "Mode Meeting 'Zoom Standup': Notifikasi dimatikan, Zoom dibuka."
        res = await self.handler.handle_meeting(["mode", "on", "Zoom", "Standup"])
        mock_prep.assert_called_with("Zoom Standup")
        self.assertIn("Zoom", res)

    @patch('agent.meeting_mode.prepare_meeting')
    @patch('agent.focus.focus_manager')
    async def test_meeting_mode_off(self, mock_focus, mock_prep):
        mock_focus.stop.return_value = "Focus Mode DINONAKTIFKAN."
        res = await self.handler.handle_meeting(["mode", "off"])
        mock_focus.stop.assert_called_once()
        self.assertIn("DINONAKTIFKAN", res)
        mock_prep.assert_not_called()

    @patch('agent.meeting_mode.prepare_meeting')
    async def test_meeting_unknown_subcommand(self, mock_prep):
        res = await self.handler.handle_meeting(["invalid"])
        self.assertIn("Gunakan", res)


class TestCustomAlias(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_no_args(self, mock_am):
        mock_am.list_aliases.return_value = "Belum ada alias."
        res = await self.handler.handle_custom([])
        self.assertIn("Belum ada", res)
        mock_am.list_aliases.assert_called_once()

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_set_alias(self, mock_am):
        mock_am.set.return_value = "Alias '!ssg' -> screenshot grid describe"
        res = await self.handler.handle_custom(["alias", "ssg", "screenshot", "grid", "describe"])
        mock_am.set.assert_called_with("ssg", "screenshot grid describe")
        self.assertIn("Alias", res)

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_list(self, mock_am):
        mock_am.list_aliases.return_value = "Daftar Alias:\n  !ssg -> screenshot grid describe"
        res = await self.handler.handle_custom(["list"])
        self.assertIn("Daftar Alias", res)
        mock_am.list_aliases.assert_called_once()

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_delete(self, mock_am):
        mock_am.delete.return_value = "Alias 'ssg' dihapus."
        res = await self.handler.handle_custom(["delete", "ssg"])
        mock_am.delete.assert_called_with("ssg")
        self.assertIn("dihapus", res)

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_delete_aliased(self, mock_am):
        mock_am.delete.return_value = "Alias 'test' dihapus."
        res = await self.handler.handle_custom(["del", "test"])
        mock_am.delete.assert_called_with("test")

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_too_few_args(self, mock_am):
        res = await self.handler.handle_custom(["alias"])
        self.assertIn("Gunakan", res)

    @patch('agent.custom_aliases.alias_manager')
    async def test_custom_unknown_subcommand(self, mock_am):
        res = await self.handler.handle_custom(["invalid"])
        self.assertIn("Gunakan", res)


if __name__ == '__main__':
    unittest.main()
