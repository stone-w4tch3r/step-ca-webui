import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Dict, Any, Callable
from uuid import UUID

from pydantic import BaseModel

from .models import LogEntry, LogSeverity, CommandInfo


class LogsFilter(BaseModel):
    trace_id: Optional[UUID]
    commands_only: bool
    severity: List[LogSeverity]


class Paging(BaseModel):
    page: int
    page_size: int


class DBHandler:
    def __init__(self, db_config: Dict[str, Any]):
        # Initialize database connection here
        self.db_config = db_config

    def insert_log(self, log_entry: LogEntry) -> None:
        # Insert log entry into the database
        pass

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        # Retrieve logs from the database based on filters and paging
        pass

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        # Retrieve a specific log entry from the database
        pass

    def get_nex_entry_id(self) -> int:
        # Retrieve the next available log entry ID from the database
        pass


class TraceIdProvider:
    def __init__(self, get_trace_id: Callable[[], UUID | None]):
        self.get_trace_id: Callable[[], UUID | None] = get_trace_id

    def get_current(self) -> UUID | None:
        return self.get_trace_id()


class Logger:
    _UNSCOPED_TRACE_ID = UUID("00000000-0000-0000-0000-000000000000")

    LOG_FILE = "application.log"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5
    LOGLEVEL = logging.DEBUG

    def __init__(self, db_handler: DBHandler, trace_id_provider: TraceIdProvider):
        self.db_handler = db_handler
        self.trace_id_provider = trace_id_provider
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.LOGLEVEL)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.LOGLEVEL)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

        # File handler with rotation
        file_handler = RotatingFileHandler(self.LOG_FILE, maxBytes=self.MAX_FILE_SIZE, backupCount=self.BACKUP_COUNT)
        file_handler.setLevel(self.LOGLEVEL)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

    def log(
        self, severity: LogSeverity, message: str,
        command_info: Optional[CommandInfo] = None
    ) -> int:
        log_entry = LogEntry(
            entry_id=self.db_handler.get_nex_entry_id(),
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=self.trace_id_provider.get_current() or self._UNSCOPED_TRACE_ID,  # TODO: maybe log_unscoped method is also needed?
            command_info=command_info
        )

        # Log to console and file
        log_message = f"[TraceID: {log_entry.trace_id}] - {log_entry.message}"
        if log_entry.command_info:
            log_message += f" - Command: {log_entry.command_info.command}"
        self.logger.log(logging.getLevelName(severity.name), log_message)

        # Log to database
        self.db_handler.insert_log(log_entry)

        return log_entry.entry_id

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        return self.db_handler.get_logs(filters, paging)

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        return self.db_handler.get_log_entry(log_id)
