import unittest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.db_logger import DBLogger, Base
from shared.models import LogEntry, LogsFilter, Paging, Severity, CommandInfo

class TestDBLogger(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Create a DBLogger instance with the test database
        self.db_logger = DBLogger()
        self.db_logger.engine = self.engine
        self.db_logger.Session = self.Session

    def test_insert_log(self):
        log_entry = LogEntry(
            timestamp=datetime.now(),
            severity=Severity.INFO,
            message="Test log message",
            trace_id=uuid4(),
            command_info=CommandInfo(command="test_command", args={"arg1": "value1"})
        )
        self.db_logger.insert_log(log_entry)

        # Verify the log was inserted
        with self.Session() as session:
            result = session.query(self.db_logger.LogEntryModel).first()
            self.assertIsNotNone(result)
            self.assertEqual(result.message, "Test log message")

    def test_get_logs(self):
        # Insert some test logs
        for i in range(5):
            log_entry = LogEntry(
                timestamp=datetime.now(),
                severity=Severity.INFO,
                message=f"Test log message {i}",
                trace_id=uuid4(),
                command_info=CommandInfo(command=f"test_command_{i}", args={"arg1": f"value{i}"})
            )
            self.db_logger.insert_log(log_entry)

        # Test getting logs
        filters = LogsFilter(severity=[Severity.INFO], commands_only=False)
        paging = Paging(page=1, page_size=3)
        logs = self.db_logger.get_logs(filters, paging)

        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].message, "Test log message 4")

    def test_get_log_entry(self):
        log_entry = LogEntry(
            timestamp=datetime.now(),
            severity=Severity.WARNING,
            message="Test specific log",
            trace_id=uuid4(),
            command_info=None
        )
        self.db_logger.insert_log(log_entry)

        # Get the ID of the inserted log
        with self.Session() as session:
            inserted_id = session.query(self.db_logger.LogEntryModel).first().id

        # Test getting the specific log entry
        retrieved_log = self.db_logger.get_log_entry(inserted_id)
        self.assertIsNotNone(retrieved_log)
        self.assertEqual(retrieved_log.message, "Test specific log")
        self.assertEqual(retrieved_log.severity, Severity.WARNING)

    def test_get_next_entry_id(self):
        # Insert a log to ensure the sequence has started
        log_entry = LogEntry(
            timestamp=datetime.now(),
            severity=Severity.INFO,
            message="Test log for ID",
            trace_id=uuid4(),
            command_info=None
        )
        self.db_logger.insert_log(log_entry)

        # Get the next entry ID
        next_id = self.db_logger.get_next_entry_id()
        self.assertIsInstance(next_id, int)
        self.assertGreater(next_id, 0)

    def test_filter_logs_by_severity(self):
        # Insert logs with different severities
        severities = [Severity.INFO, Severity.WARNING, Severity.ERROR]
        for severity in severities:
            log_entry = LogEntry(
                timestamp=datetime.now(),
                severity=severity,
                message=f"Test log message with {severity.name} severity",
                trace_id=uuid4(),
                command_info=None
            )
            self.db_logger.insert_log(log_entry)

        # Test filtering by severity
        filters = LogsFilter(severity=[Severity.WARNING, Severity.ERROR], commands_only=False)
        paging = Paging(page=1, page_size=10)
        logs = self.db_logger.get_logs(filters, paging)

        self.assertEqual(len(logs), 2)
        self.assertIn(logs[0].severity, [Severity.WARNING, Severity.ERROR])
        self.assertIn(logs[1].severity, [Severity.WARNING, Severity.ERROR])

    def test_filter_logs_by_command(self):
        # Insert logs with different commands
        commands = ["command1", "command2", "command3"]
        for command in commands:
            log_entry = LogEntry(
                timestamp=datetime.now(),
                severity=Severity.INFO,
                message=f"Test log message for {command}",
                trace_id=uuid4(),
                command_info=CommandInfo(command=command, args={})
            )
            self.db_logger.insert_log(log_entry)

        # Test filtering by command
        filters = LogsFilter(commands=["command1", "command3"], commands_only=True)
        paging = Paging(page=1, page_size=10)
        logs = self.db_logger.get_logs(filters, paging)

        self.assertEqual(len(logs), 2)
        self.assertIn(logs[0].command_info.command, ["command1", "command3"])
        self.assertIn(logs[1].command_info.command, ["command1", "command3"])

    def test_pagination(self):
        # Insert 10 log entries
        for i in range(10):
            log_entry = LogEntry(
                timestamp=datetime.now(),
                severity=Severity.INFO,
                message=f"Test log message {i}",
                trace_id=uuid4(),
                command_info=None
            )
            self.db_logger.insert_log(log_entry)

        # Test first page
        filters = LogsFilter(severity=[Severity.INFO], commands_only=False)
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
        filters = LogsFilter(severity=[Severity.CRITICAL], commands_only=False)
        paging = Paging(page=1, page_size=10)
        logs = self.db_logger.get_logs(filters, paging)
        self.assertEqual(len(logs), 0)

if __name__ == '__main__':
    unittest.main()
