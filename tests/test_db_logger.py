import unittest
from datetime import datetime
from random import random
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# noinspection PyProtectedMember
from shared.db_logger import DBLogger, _Base as Base, LogEntryModel
from shared.models import LogEntry, LogsFilter, Paging, LogSeverity, CommandInfo


class TestDBLogger(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Create a DBLogger instance with the test database
        self.db_logger = DBLogger(is_test=True)
        self.db_logger.engine = self.engine
        self.db_logger.Session = self.Session

    def test_insert_log(self):
        timestamp = datetime.now()
        trace_id = uuid4()
        command_info = CommandInfo(command="test_command", output="test output", exit_code=0, action="TEST")
        log_entry = LogEntry(
            entry_id=1,
            timestamp=timestamp,
            severity=LogSeverity.INFO,
            message="Test log message",
            trace_id=trace_id,
            command_info=command_info
        )

        self.db_logger.insert_log(log_entry)

        # Verify the log was inserted
        with self.Session() as session:
            result = session.query(LogEntryModel).first()
            self.assertIsNotNone(result)
            self.assertEqual(result.timestamp, timestamp)
            self.assertEqual(result.id, 1)
            self.assertEqual(result.severity, LogSeverity.INFO)
            self.assertEqual(result.message, "Test log message")
            self.assertEqual(result.trace_id, str(trace_id))
            self.assertEqual(CommandInfo.model_validate(result.command_info), command_info)

    def test_get_logs(self):
        # Insert some test logs
        for i in range(5):
            log_entry = LogEntry(
                entry_id=i,
                timestamp=datetime.now(),
                severity=LogSeverity.INFO,
                message=f"Test log message {i}",
                trace_id=uuid4(),
                command_info=CommandInfo(command="test_command", output="test output", exit_code=0, action="TEST")
            )
            self.db_logger.insert_log(log_entry)

        # Test getting logs
        filters = LogsFilter(severity=[LogSeverity.INFO], commands_only=False)
        paging = Paging(page=1, page_size=3)
        logs = self.db_logger.get_logs(filters, paging)

        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].message, "Test log message 4")

    def test_get_log_entry(self):
        log_entry = LogEntry(
            entry_id=1,
            timestamp=datetime.now(),
            severity=LogSeverity.WARNING,
            message="Test specific log",
            trace_id=uuid4(),
            command_info=None
        )
        self.db_logger.insert_log(log_entry)

        # Get the ID of the inserted log
        with self.Session() as session:
            inserted_id = session.query(LogEntryModel).first().id

        # Test getting the specific log entry
        retrieved_log = self.db_logger.get_log_entry(inserted_id)
        self.assertIsNotNone(retrieved_log)
        self.assertEqual(retrieved_log.message, "Test specific log")
        self.assertEqual(retrieved_log.severity, LogSeverity.WARNING)

    def test_get_next_entry_id(self):
        # impossible to test without a real database
        pass

    def test_filter_logs_by_severity(self):
        # Insert logs with different severities
        severities = [LogSeverity.INFO, LogSeverity.WARNING, LogSeverity.ERROR]
        for severity in severities:
            log_entry = LogEntry(
                entry_id=int(random() * 1000000),
                timestamp=datetime.now(),
                severity=severity,
                message=f"Test log message with {severity.name} severity",
                trace_id=uuid4(),
                command_info=None
            )
            self.db_logger.insert_log(log_entry)

        # Test filtering by severity
        filters = LogsFilter(severity=[LogSeverity.WARNING, LogSeverity.ERROR], commands_only=False)
        paging = Paging(page=1, page_size=10)
        logs = self.db_logger.get_logs(filters, paging)

        self.assertEqual(len(logs), 2)
        self.assertIn(logs[0].severity, [LogSeverity.WARNING, LogSeverity.ERROR])
        self.assertIn(logs[1].severity, [LogSeverity.WARNING, LogSeverity.ERROR])

    def test_pagination(self):
        # Insert 10 log entries
        for i in range(10):
            log_entry = LogEntry(
                entry_id=i,
                timestamp=datetime.now(),
                severity=LogSeverity.INFO,
                message=f"Test log message {i}",
                trace_id=uuid4(),
                command_info=None
            )
            self.db_logger.insert_log(log_entry)

        # Test first page
        filters = LogsFilter(severity=[LogSeverity.INFO], commands_only=False)
        paging = Paging(page=1, page_size=3)
        logs = self.db_logger.get_logs(filters, paging)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].message, "Test log message 9")

        # Test second page
        paging = Paging(page=2, page_size=3)
        logs = self.db_logger.get_logs(filters, paging)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].message, "Test log message 6")

    def test_no_logs_found(self):
        # Test when no logs match the filter
        filters = LogsFilter(severity=[LogSeverity.INFO], commands_only=False)
        paging = Paging(page=1, page_size=10)
        logs = self.db_logger.get_logs(filters, paging)
        self.assertEqual(len(logs), 0)


if __name__ == '__main__':
    unittest.main()
