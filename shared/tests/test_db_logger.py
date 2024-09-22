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

if __name__ == '__main__':
    unittest.main()
