"""
Tests for the command module.
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from agent.command_handler import CommandHandler
import platform
import asyncio

class TestCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = CommandHandler()

    @patch('agent.command_handler.take_screenshot', return_value=b'screenshot_bytes')
    async def test_handle_screenshot(self, mock_take_screenshot):
        result = await self.handler.handle_screenshot()
        self.assertEqual(result, b'screenshot_bytes')

    @patch('agent.command_handler.sys_monitor.get_system_summary', return_value='system_info')
    async def test_handle_sysinfo(self, mock_get_system_info):
        result = await self.handler.handle_sysinfo()
        self.assertEqual(result, 'system_info')

    @patch('agent.command_handler.list_files', return_value='file_list')
    async def test_handle_list_files(self, mock_list_files):
        result = await self.handler.handle_list_files('some_path')
        self.assertEqual(result, 'file_list')

    @patch('agent.command_handler.get_file', return_value={'data': b'file_data', 'filename': 'test.txt', 'mimetype': 'text/plain'})
    async def test_handle_get_file(self, mock_get_file):
        result = await self.handler.handle_get_file('some_path')
        self.assertEqual(result, {'data': b'file_data', 'filename': 'test.txt', 'mimetype': 'text/plain'})

    @patch('agent.command_handler.run_script', new_callable=AsyncMock)
    async def test_handle_run_script(self, mock_run_script):
        mock_run_script.return_value = 'script_result'
        result = await self.handler.handle_run_script('some_script.py', 'user123')
        self.assertEqual(result, 'script_result')

    @patch('platform.system', return_value='Linux')
    @patch('subprocess.run')
    async def test_handle_lock_screen(self, mock_subprocess_run, mock_platform_system):
        result = await self.handler.handle_lock_screen()
        self.assertEqual(result, '🔒 Layar dikunci.')

    @patch('platform.system', return_value='Linux')
    @patch('subprocess.Popen')
    async def test_handle_reboot(self, mock_subprocess_popen, mock_platform_system):
        result = await self.handler.handle_reboot(confirmed=True)
        self.assertEqual(result, '🔄 Laptop akan restart dalam 10 detik...')
        result = await self.handler.handle_reboot(confirmed=False)
        self.assertEqual(result, """⚠️ Yakin ingin restart?
Balas: `!reboot confirm`""")


if __name__ == '__main__':
    unittest.main()
