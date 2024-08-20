import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


class LogSeverity(enum.StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class KeyType(enum.StrEnum):
    RSA = "RSA"
    ECDSA = "ECDSA"


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
