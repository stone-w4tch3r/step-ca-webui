import json
import logging
import re
import uuid
from datetime import datetime
from typing import Callable
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from .models import LogEntry, LogSeverity, CommandInfo


class LogsFilter(BaseModel):
    trace_id: Optional[uuid.UUID]
    commands_only: bool
    severity: List[LogSeverity]


class Paging(BaseModel):
    page: int
    page_size: int


class TraceIdProvider:
    def __init__(self, get_trace_id: Callable[[], uuid.UUID | None]):
        self.get_trace_id: Callable[[], uuid.UUID | None] = get_trace_id

    def get_current(self) -> uuid.UUID | None:
        return self.get_trace_id()


class Logger:
    _UNSCOPED_TRACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

    def __init__(self, trace_id_provider: TraceIdProvider):
        self._trace_id_provider = trace_id_provider
        self._log_file = f"step-ca-webui-{datetime.now().strftime('%Y-%m-%d')}.log"
        self._json_file = f"step-ca-webui-{datetime.now().strftime('%Y-%m-%d')}.json"
        logging.basicConfig(filename=self._log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def log_scoped(
        self,
        severity: LogSeverity,
        message: str,
        command_info: Optional[CommandInfo] = None
    ) -> int:
        """
        This method logs a message with a trace_id if it exists in the current context.
        Context is managed externally, encapsulated in the TraceIdProvider.
        """
        trace_id = self._trace_id_provider.get_current() or self._UNSCOPED_TRACE_ID  # if trace_id not found/no context

        log_entry = LogEntry(
            entry_id=self._get_next_entry_id(),
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=trace_id,
            command_info=command_info
        )
        self._write(log_entry)
        return log_entry.entry_id

    def log_unscoped(
        self,
        severity: LogSeverity,
        message: str,
        command_info: Optional[CommandInfo] = None
    ) -> int:
        log_entry = LogEntry(
            entry_id=self._get_next_entry_id(),
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            trace_id=self._UNSCOPED_TRACE_ID,
            command_info=command_info
        )
        self._write(log_entry)
        return log_entry.entry_id

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        log_entries = []
        try:
            with open(self._json_file, "r") as f:
                for line in f:
                    log_data = json.loads(line)
                    log_entry = self._create_log_entry_from_data(log_data)
                    if log_entry and _match_filters(log_entry, filters):
                        log_entries.append(log_entry)
        except FileNotFoundError:
            self.log_scoped(LogSeverity.WARNING, f"File not found when trying to read logs: {self._json_file}")

        log_entries.sort(key=lambda x: x.timestamp, reverse=True)
        start = (paging.page - 1) * paging.page_size
        end = start + paging.page_size
        return log_entries[start:end]

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        try:
            with open(self._json_file, "r") as f:
                for line in f:
                    log_data = json.loads(line)
                    if log_data["entry_id"] == log_id:
                        return self._create_log_entry_from_data(log_data)
        except FileNotFoundError:
            self.log_scoped(LogSeverity.WARNING, f"File not found when trying to read log entry: {self._json_file}")
        return None

    def _write(self, log_entry: LogEntry) -> None:
        self._write_native(log_entry)
        self._write_json(log_entry)

    @staticmethod
    def _write_native(log_entry: LogEntry) -> None:
        log_message = f"{log_entry.timestamp} - {log_entry.severity.name} - [TraceID: {log_entry.trace_id}] - {log_entry.message}"
        if log_entry.command_info:
            log_message += f" - Command: {log_entry.command_info.command}"

        logging.log(logging.getLevelName(log_entry.severity.name), log_message)

    def _write_json(self, log_entry: LogEntry) -> None:
        json_entry = {
            "timestamp": log_entry.timestamp.isoformat(),
            "entry_id": log_entry.entry_id,
            "severity": log_entry.severity.name,
            "trace_id": str(log_entry.trace_id),
            "message": _escape_quotes(log_entry.message),
            "command_info": {
                "command": _escape_quotes(log_entry.command_info.command),
                "output": _escape_quotes(log_entry.command_info.output),
                "exit_code": log_entry.command_info.exit_code,
                "action": log_entry.command_info.action,
            } if log_entry.command_info else None
        }

        with open(self._json_file, "a") as f:
            f.write(json.dumps(json_entry) + "\n")

    def _get_next_entry_id(self) -> int:
        try:
            with open(self._json_file, "r") as f:
                last_line = f.readlines()[-1]
            last_entry = json.loads(last_line)
            return last_entry["entry_id"] + 1
        except (IndexError, FileNotFoundError, KeyError) as e:
            # self.log_scoped(LogSeverity.WARNING, f"Failed to get next entry ID: {e}")
            self._write_native(LogEntry(
                entry_id=1,
                timestamp=datetime.now(),
                severity=LogSeverity.WARNING,
                message=f"Failed to get next entry ID: {e}",
                trace_id=uuid.UUID("00000000-0000-0000-0000-000000000000")
            ))
            return 1

    def _create_log_entry_from_data(self, log_data: Dict) -> LogEntry | None:
        try:
            return LogEntry(
                entry_id=log_data["entry_id"],
                timestamp=_parse_datetime(log_data["timestamp"]),
                severity=LogSeverity[log_data["severity"]],
                message=log_data["message"],
                trace_id=UUID(log_data["trace_id"]),
                command_info=CommandInfo(
                    command=log_data["command_info"]["command"],
                    output=log_data["command_info"]["output"],
                    exit_code=log_data["command_info"]["exit_code"],
                    action=log_data["command_info"]["action"]
                ) if log_data["command_info"] else None
            )
        except KeyError:
            self.log_scoped(LogSeverity.WARNING, f"Failed to parse log entry: {log_data['entry_id']}", )
            return None


def _match_filters(log_entry: LogEntry, filters: LogsFilter) -> bool:
    if filters.trace_id and log_entry.trace_id != filters.trace_id:
        return False
    if filters.commands_only and log_entry.command_info is None:
        return False
    if filters.severity and log_entry.severity not in filters.severity:
        return False
    return True


def _parse_datetime(timestamp_str: str) -> datetime:
    return datetime.fromisoformat(timestamp_str)


def _escape_quotes(text: str) -> str:
    return re.sub(r'"', r'\\"', text)
