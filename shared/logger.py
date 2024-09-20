import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Dict, Any
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


class Logger:
    _UNSCOPED_TRACE_ID = UUID("00000000-0000-0000-0000-000000000000")

    def __init__(self, db_handler: DBHandler, log_file: str, max_file_size: int, backup_count: int):
        self.db_handler = db_handler
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        file_handler = RotatingFileHandler(log_file, maxBytes=max_file_size, backupCount=backup_count)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def log(self, severity: LogSeverity, message: str, trace_id: Optional[UUID] = None,
            command_info: Optional[CommandInfo] = None) -> int:
        log_entry = LogEntry(
            entry_id=0,  # This will be set by the database
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=trace_id or self._UNSCOPED_TRACE_ID,
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
