import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Callable, Protocol
from uuid import UUID

from .models import LogEntry, LogSeverity, CommandInfo, LogsFilter, Paging


class TraceIdProvider:
    def __init__(self, get_trace_id: Callable[[], UUID | None]):
        self.get_trace_id: Callable[[], UUID | None] = get_trace_id

    def get_current(self) -> UUID | None:
        return self.get_trace_id()


class IDBLogger(Protocol):
    def insert_log(self, log_entry: LogEntry) -> None:
        ...

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        ...

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        ...

    def get_next_entry_id(self) -> int:
        ...


class Logger:
    _UNSCOPED_TRACE_ID = UUID("00000000-0000-0000-0000-000000000000")

    LOG_FILE = "application.log"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5
    LOGLEVEL = logging.DEBUG

    def __init__(self, trace_id_provider: TraceIdProvider, db_handler: IDBLogger) -> None:
        self.db_logger = db_handler
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
            entry_id=self.db_logger.get_next_entry_id(),
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=self.trace_id_provider.get_current() or self._UNSCOPED_TRACE_ID,
            command_info=command_info
        )

        # Log to console and file
        log_message = f"[TraceID: {log_entry.trace_id}] - {log_entry.message}"
        if log_entry.command_info:
            log_message += f" - Command: {log_entry.command_info.command}"
        self.logger.log(logging.getLevelName(severity.name), log_message)

        # Log to database
        self.db_logger.insert_log(log_entry)

        return log_entry.entry_id

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        return self.db_logger.get_logs(filters, paging)

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        return self.db_logger.get_log_entry(log_id)
