import unittest
from unittest.mock import Mock, patch
from uuid import UUID
from datetime import datetime
from logging import Logger as PythonLogger

from shared.logger import Logger, TraceIdProvider, IDBLogger
from shared.models import LogEntry, LogSeverity, CommandInfo, LogsFilter, Paging


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.mock_db_logger = Mock(spec=IDBLogger)
        self.mock_trace_id_provider = Mock(spec=TraceIdProvider)
        # noinspection PyTypeChecker
        self.logger = Logger(self.mock_trace_id_provider, self.mock_db_logger)

    @patch.object(PythonLogger, 'log')
    def test_log_with_trace_id(self, mock_log):
        trace_id = UUID('12345678-1234-5678-1234-567812345678')
        self.mock_trace_id_provider.get_current.return_value = trace_id
        self.mock_db_logger.get_next_entry_id.return_value = 1

        log_id = self.logger.log(LogSeverity.INFO, "Test message")

        self.assertEqual(log_id, 1)
        self.mock_db_logger.insert_log.assert_called_once()
        mock_log.assert_called_once()
        log_entry = self.mock_db_logger.insert_log.call_args[0][0]
        self.assertEqual(log_entry.severity, LogSeverity.INFO)
        self.assertEqual(log_entry.message, "Test message")
        self.assertEqual(log_entry.trace_id, trace_id)

    @patch.object(PythonLogger, 'log')
    def test_log_without_trace_id(self, mock_log):
        self.mock_trace_id_provider.get_current.return_value = None
        self.mock_db_logger.get_next_entry_id.return_value = 1

        log_id = self.logger.log(LogSeverity.ERROR, "Error message")

        self.assertEqual(log_id, 1)
        self.mock_db_logger.insert_log.assert_called_once()
        mock_log.assert_called_once()
        log_entry = self.mock_db_logger.insert_log.call_args[0][0]
        self.assertEqual(log_entry.severity, LogSeverity.ERROR)
        self.assertEqual(log_entry.message, "Error message")
        self.assertEqual(log_entry.trace_id, Logger._UNSCOPED_TRACE_ID)

    @patch.object(PythonLogger, 'log')
    def test_log_with_command_info(self, mock_log):
        self.mock_trace_id_provider.get_current.return_value = None
        self.mock_db_logger.get_next_entry_id.return_value = 1
        command_info = CommandInfo(command="test_command", output="test_output", exit_code=0, action="TEST")

        log_id = self.logger.log(LogSeverity.DEBUG, "Debug message", command_info)

        self.assertEqual(log_id, 1)
        self.mock_db_logger.insert_log.assert_called_once()
        mock_log.assert_called_once()
        log_entry = self.mock_db_logger.insert_log.call_args[0][0]
        self.assertEqual(log_entry.severity, LogSeverity.DEBUG)
        self.assertEqual(log_entry.message, "Debug message")
        self.assertEqual(log_entry.command_info, command_info)

    def test_get_logs(self):
        filters = LogsFilter(severity=[LogSeverity.INFO], commands_only=False)
        paging = Paging(page=1, page_size=10)
        expected_logs = [
            LogEntry(
                entry_id=1,
                timestamp=datetime.now(),
                severity=LogSeverity.INFO,
                message="Test",
                trace_id=UUID('12345678-1234-5678-1234-567812345678')
            )
        ]
        self.mock_db_logger.get_logs.return_value = expected_logs

        logs = self.logger.get_logs(filters, paging)

        self.assertEqual(logs, expected_logs)
        self.mock_db_logger.get_logs.assert_called_once_with(filters, paging)

    def test_get_log_entry(self):
        log_id = 1
        expected_log = LogEntry(
            entry_id=log_id,
            timestamp=datetime.now(),
            severity=LogSeverity.INFO, message="Test",
            trace_id=UUID('12345678-1234-5678-1234-567812345678')
        )
        self.mock_db_logger.get_log_entry.return_value = expected_log

        log_entry = self.logger.get_log_entry(log_id)

        self.assertEqual(log_entry, expected_log)
        self.mock_db_logger.get_log_entry.assert_called_once_with(log_id)


if __name__ == '__main__':
    unittest.main()
