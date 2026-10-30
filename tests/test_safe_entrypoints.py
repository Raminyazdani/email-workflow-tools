"""Isolated synthetic checks: never access a real clipboard, browser or mailbox."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def forbidden(*args, **kwargs):
    raise AssertionError('Unexpected external effect in safe-mode test')


def load(relative):
    keyboard = types.ModuleType('keyboard')
    for name in ['add_hotkey', 'wait', 'send', 'is_pressed']:
        setattr(keyboard, name, forbidden)
    clipboard = types.ModuleType('pyperclip')
    clipboard.copy = clipboard.paste = forbidden
    with patch.dict(sys.modules, {'keyboard': keyboard, 'pyperclip': clipboard}), patch('socket.socket', forbidden), patch('sqlite3.connect', forbidden):
        return runpy.run_path(str(ROOT / relative), run_name='__publication_test__')


class SafetyTests(unittest.TestCase):
    def test_safe_modes_never_start_devices_database_or_network(self):
        for path in ['main.py', 'variants/clipboard/main.py', 'variants/clipboard/sqlite_history.py', 'by_steps/step_8_parse_prompt_find_data.py', 'by_steps/step_9_browser.py']:
            with self.subTest(path=path):
                scope = load(path)
                with patch('socket.socket', forbidden), patch('sqlite3.connect', forbidden), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(scope['main'](['--dry-run']), 0)

    def test_offline_dry_run_checks_paths_without_reading_inputs(self):
        scope = load('by_steps/step_6_api_ready_prompts.py')
        operation = scope['main']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); inputs = root / 'inputs'; inputs.mkdir()
            prompt = root / 'prompt.txt'; prompt.write_text('fictional', encoding='utf-8')
            output = root / 'new-output'
            with patch.dict(operation.__globals__, {'load_source_prompt': forbidden, 'collect_step4_items': forbidden}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(operation(['--input-dir', str(inputs), '--prompt-file', str(prompt), '--output-dir', str(output), '--dry-run']), 0)
            self.assertFalse(output.exists())

    def test_offline_write_uses_only_fictional_local_records(self):
        operation = load('by_steps/step_6_api_ready_prompts.py')['main']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); inputs = root / 'inputs'; inputs.mkdir()
            record = inputs / 'one.json'; original = '{"items":[{"label":"fictional example"}]}'
            record.write_text(original, encoding='utf-8')
            prompt = root / 'prompt.txt'; prompt.write_text('Process the fictional example.', encoding='utf-8')
            output = root / 'new-output'
            with patch('socket.socket', forbidden), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(operation(['--input-dir', str(inputs), '--prompt-file', str(prompt), '--output-dir', str(output), '--write']), 0)
            self.assertEqual(json.loads((output / 'manifest_step_6.json').read_text())['prompt_count'], 1)
            self.assertEqual(record.read_text(), original)

    def test_an_existing_output_directory_is_preserved(self):
        operation = load('by_steps/step_6_api_ready_prompts.py')['main']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); inputs = root / 'inputs'; inputs.mkdir()
            prompt = root / 'prompt.txt'; prompt.write_text('fictional', encoding='utf-8')
            output = root / 'preserved'; output.mkdir(); marker = output / 'keep.txt'; marker.write_text('preserved', encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                operation(['--input-dir', str(inputs), '--prompt-file', str(prompt), '--output-dir', str(output), '--write'])
            self.assertEqual(result.exception.code, 2)
            self.assertEqual(marker.read_text(), 'preserved')


if __name__ == '__main__':
    unittest.main()
