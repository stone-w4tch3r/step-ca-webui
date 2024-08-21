import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class LogSeverity(enum.StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARN"
    ERROR = "ERROR"

    @staticmethod
    def as_list() -> List[str]:  # TODO use
        return [s.upper() for s in LogSeverity]


class KeyType(enum.StrEnum):
    RSA = "RSA"
    ECDSA = "ECDSA"

    @staticmethod
    def as_list() -> List[str]:  # TODO use
        return [s.upper() for s in KeyType]


class CommandInfo(BaseModel):
    command: str
    output: str
    exit_code: int
    action: str


class LogEntry(BaseModel):
    timestamp: datetime
    entry_id: int
    severity: LogSeverity
    trace_id: UUID
    message: str
    command_info: Optional[CommandInfo] = None
