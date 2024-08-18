from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID


class LogSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class CommandInfo:
    command: str
    output: str
    exit_code: int
    action: str


@dataclass
class LogEntry:
    entry_id: int
    timestamp: datetime
    severity: LogSeverity
    message: str
    trace_id: UUID
    command_info: Optional[CommandInfo] = None
