import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from .models import LogEntry, LogSeverity, CommandInfo


class Logger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def log_scoped(
        self,
        severity: LogSeverity,
        message: str,
        command_info: Optional[CommandInfo] = None
    ) -> int:
        # trace_id = g.trace_id if hasattr(g, 'trace_id') else uuid.UUID("00000000-0000-0000-0000-000000000000")
        trace_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        log_entry = LogEntry(
            entry_id=self._get_next_entry_id(),
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=trace_id,
            command_info=command_info
        )
        self._write_log_entry(log_entry)
        return log_entry.entry_id

    def log_with_trace(
        self,
        severity: LogSeverity,
        message: str,
        trace_id: UUID,
        command_info: Optional[CommandInfo] = None
    ) -> int:
        log_entry = LogEntry(
            entry_id=self._get_next_entry_id(),
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=trace_id,
            command_info=command_info
        )
        self._write_log_entry(log_entry)
        return log_entry.entry_id

    def get_logs(self, filters: Dict) -> List[LogEntry]:
        # Implementation for retrieving logs based on filters
        # This is a placeholder and would need to be implemented based on your storage mechanism
        return [
            LogEntry(
                entry_id=1,
                timestamp=datetime.now(),
                severity=LogSeverity.INFO,
                message="This is a log entry",
                trace_id=UUID("123e4567-e89b-12d3-a456-426614174000")
            ),
            LogEntry(
                entry_id=2,
                timestamp=datetime.now(),
                severity=LogSeverity.ERROR,
                message="This is an error log entry",
                trace_id=UUID("123e4567-e89b-12d3-a456-426614174000")
            )
        ]
        raise NotImplementedError

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        # Implementation for retrieving a single log entry
        # This is a placeholder and would need to be implemented based on your storage mechanism
        return LogEntry(
            entry_id=log_id,
            timestamp=datetime.now(),
            severity=LogSeverity.INFO,
            message="This is a log entry",
            trace_id=UUID("123e4567-e89b-12d3-a456-426614174000")
        )
        raise NotImplementedError

    def _write_log_entry(self, log_entry: LogEntry) -> None:
        log_message = f"{log_entry.timestamp} - {log_entry.severity.name} - {log_entry.message} - Trace ID: {log_entry.trace_id}"
        if log_entry.command_info:
            log_message += f" - Command: {log_entry.command_info.command}"
        logging.log(self._get_logging_level(log_entry.severity), log_message)

    def _get_next_entry_id(self) -> int:
        # Implementation for generating the next entry ID
        # This is a placeholder and would need to be implemented based on your storage mechanism
        return 1
        raise NotImplementedError

    @staticmethod
    def _get_logging_level(severity: LogSeverity) -> int:  # TODO simplify
        return {
            LogSeverity.DEBUG: logging.DEBUG,
            LogSeverity.INFO: logging.INFO,
            LogSeverity.WARN: logging.WARNING,
            LogSeverity.ERROR: logging.ERROR
        }[severity]
