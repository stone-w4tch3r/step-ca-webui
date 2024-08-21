import os
import unittest
from unittest.mock import patch, mock_open
from uuid import UUID

from freezegun import freeze_time

from shared.logger import Logger, LogsFilter, Paging, LogSeverity
from shared.models import CommandInfo


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()

    @freeze_time("2023-08-21")
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_log_scoped(self, mock_file):
        with patch('core.trace_id_handler.TraceIdHandler.get_current_trace_id', return_value=UUID('12345678-1234-5678-1234-567812345678')):
            log_id = self.logger.log_scoped(LogSeverity.INFO, "Test message")
            self.assertEqual(log_id, 1)

            mock_file.assert_called_with(self.logger._json_file, 'a')
            mock_file().write.assert_called_with(
                '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
                + '"trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message", "command_info": null}\n'
            )

    @freeze_time("2023-08-21")
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_log_with_trace(self, mock_file):
        trace_id = UUID('12345678-1234-5678-1234-567812345678')
        log_id = self.logger.log_with_trace(LogSeverity.ERROR, "Test message", trace_id)
        self.assertEqual(log_id, 1)

        mock_file.assert_called_with(self.logger._json_file, 'a')
        mock_file().write.assert_called_with(
            '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "ERROR", '
            + '"trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message", "command_info": null}\n'
        )

    @patch('builtins.open', new_callable=mock_open, read_data='\n'.join([
        '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO",'
        + ' "trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message 1", "command_info": null}',
        '{"timestamp": "2023-08-21T00:00:01", "entry_id": 2, "severity": "ERROR",'
        + ' "trace_id": "12345678-1234-5678-1234-567812345679", "message": "Test message 2", "command_info": null}',
        '{"timestamp": "2023-08-21T00:00:02", "entry_id": 3, "severity": "WARNING",'
        + ' "trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message 3", "command_info": null}'
    ]))
    def test_get_logs(self, _):
        filters = LogsFilter(
            trace_id=UUID('12345678-1234-5678-1234-567812345678'),
            commands_only=False,
            severity=[LogSeverity.INFO, LogSeverity.WARNING]
        )
        paging = Paging(page=1, page_size=2)
        logs = self.logger.get_logs(filters, paging)

        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].entry_id, 3)
        self.assertEqual(logs[1].entry_id, 1)

    @patch('builtins.open', new_callable=mock_open, read_data='\n'.join([
        '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
        + '"trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message 1", "command_info": null}'
    ]))
    def test_get_log_entry(self, _):
        log_entry = self.logger.get_log_entry(1)
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.entry_id, 1)
        self.assertEqual(log_entry.message, "Test message 1")

    @freeze_time("2023-08-21")
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_log_with_command_info(self, mock_file):
        command_info = CommandInfo(
            command="test_command",
            output="test_output",
            exit_code=0,
            action="test_action"
        )
        log_id = self.logger.log_scoped(LogSeverity.INFO, "Test message with command info", command_info)
        self.assertEqual(log_id, 1)

        mock_file.assert_called_with(self.logger._json_file, 'a')
        mock_file().write.assert_called_with(
            '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
            + '"trace_id": "00000000-0000-0000-0000-000000000000", "message": "Test message with command info", '
            + '"command_info": {"command": "test_command", "output": "test_output", "exit_code": 0, "action": "test_action"}}\n'
        )

    @freeze_time("2023-08-21")
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_log_with_empty_json_file(self, mock_file):
        log_id1 = self.logger.log_scoped(LogSeverity.INFO, "Test message 1")
        self.assertEqual(log_id1, 1)

        log_id2 = self.logger.log_scoped(LogSeverity.ERROR, "Test message 2")
        self.assertEqual(log_id2, 2)

        mock_file.assert_any_call(self.logger._json_file, 'a')
        mock_file().write.assert_any_call(
            '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
            + '"trace_id": "00000000-0000-0000-0000-000000000000", "message": "Test message 1", "command_info": null}\n'
        )
        mock_file().write.assert_any_call(
            '{"timestamp": "2023-08-21T00:00:00", "entry_id": 2, "severity": "ERROR", '
            + '"trace_id": "00000000-0000-0000-0000-000000000000", "message": "Test message 2", "command_info": null}\n'
        )

    @freeze_time("2023-08-21")
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_log_with_non_existent_json_file(self, mock_file):
        log_id = self.logger.log_scoped(LogSeverity.INFO, "Test message")
        self.assertEqual(log_id, 1)

        mock_file.assert_called_with(self.logger._json_file, 'a')
        self.assertTrue(os.path.exists(self.logger._json_file))

        with open(self.logger._json_file, 'r') as f:
            self.assertEqual(
                f.read(),
                '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
                + '"trace_id": "00000000-0000-0000-0000-000000000000", "message": "Test message", "command_info": null}\n'
            )
        os.remove(self.logger._json_file)

    @patch('builtins.open', new_callable=mock_open, read_data='\n'.join([
        '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
        + '"trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message with \\\"quotes\\\" and special characters", '
        + '"command_info": null}'
    ]))
    def test_get_log_entry_with_special_characters(self, _):
        log_entry = self.logger.get_log_entry(1)
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.entry_id, 1)
        self.assertEqual(log_entry.message, "Test message with \"quotes\" and special characters")

    @patch('builtins.open', new_callable=mock_open, read_data='\n'.join([
        '{"timestamp": "2023-08-21T00:00:00", "entry_id": 1, "severity": "INFO", '
        + '"trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message 1", "command_info": null}',
        '{"timestamp": "2023-08-21T00:00:01", "entry_id": 2, "severity": "ERROR",'
        + ' "trace_id": "12345678-1234-5678-1234-567812345679", "message": "Test message 2", "command_info": null}',
        '{"timestamp": "2023-08-21T00:00:02", "entry_id": 3, "severity": "WARNING", '
        + '"trace_id": "12345678-1234-5678-1234-567812345678", "message": "Test message 3", "command_info": null}'
    ]))
    def test_get_logs_with_paging(self, _):
        filters = LogsFilter(
            trace_id=None,
            commands_only=False,
            severity=None
        )

        paging = Paging(page=1, page_size=2)
        logs = self.logger.get_logs(filters, paging)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].entry_id, 3)
        self.assertEqual(logs[1].entry_id, 2)

        paging = Paging(page=2, page_size=2)
        logs = self.logger.get_logs(filters, paging)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].entry_id, 1)


if __name__ == '__main__':
    unittest.main()
