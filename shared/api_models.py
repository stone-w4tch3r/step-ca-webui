from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.models import LogSeverity, KeyType


class Certificate(BaseModel):
    id: str
    name: str
    status: str
    expirationDate: datetime


class CertificateGenerateRequest(BaseModel):
    keyName: str
    keyType: KeyType
    duration: int = Field(..., gt=0, description="Duration in seconds")


class CommandPreview(BaseModel):
    command: str


class CertificateGenerateResult(BaseModel):
    success: bool
    message: str
    logEntryId: int = Field(..., gt=0)
    certificateId: str
    certificateName: str
    expirationDate: datetime


class CertificateRenewResult(BaseModel):
    success: bool
    message: str
    logEntryId: int = Field(..., gt=0)
    certificateId: str
    newExpirationDate: datetime


class CertificateRevokeResult(BaseModel):
    success: bool
    message: str
    logEntryId: int = Field(..., gt=0)
    certificateId: str
    revocationDate: datetime


class CommandInfo(BaseModel):
    command: str
    output: str
    exitCode: int
    action: str


class LogEntry(BaseModel):
    entryId: int = Field(..., gt=0)
    timestamp: datetime
    severity: LogSeverity
    message: str
    traceId: uuid.UUID
    commandInfo: Optional[CommandInfo]


class LogsRequest(BaseModel):
    traceId: Optional[uuid.UUID]
    commandsOnly: bool
    severity: List[LogSeverity]
    page: int = Field(..., gt=0)
    pageSize: int = Field(..., gt=0)
