import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Union

import uvicorn
from fastapi import FastAPI, Query, HTTPException, Request, Body
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from core.certificate_manager import CertificateManager
from shared.logger import Logger
from shared.models import LogSeverity, KeyType


class Certificate(BaseModel):
    id: str
    name: str
    status: str
    expiration_date: datetime


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


_app = FastAPI()
_cert_manager: CertificateManager
_logger: Logger


def setup(cert_manager: CertificateManager, logger: Logger) -> None:
    global _cert_manager
    global _logger
    _cert_manager = cert_manager
    _logger = logger


def run(
    host: str = "0.0.0.0",
    port: int = 5000
) -> None:
    if not _cert_manager or not _logger:
        raise RuntimeError("API server not set up")

    uvicorn.run(_app, host=host, port=port)


@_app.get("/certificates", response_model=Union[List[Certificate], CommandPreview])
async def list_certificates(preview: bool = Query(...)):
    if preview:
        command = _cert_manager.preview_list_certificates()
        return {"command": command}
    return _cert_manager.list_certificates()


@_app.post("/certificates/generate", response_model=Union[CertificateGenerateResult, CommandPreview])
async def generate_certificate(
    preview: bool = Query(...),
    body: CertificateGenerateRequest = Body(...)
):
    if preview:
        command = _cert_manager.preview_generate_certificate(body.keyName, body.keyType, body.duration)
        return {"command": command}
    return _cert_manager.generate_certificate(body.keyName, body.keyType, body.duration)


# noinspection PyPep8Naming
@_app.post("/certificates/renew", response_model=Union[CertificateRenewResult, CommandPreview])
async def renew_certificate(
    certId: str = Query(...),
    duration: int = Query(..., description="Duration in seconds"),
    preview: bool = Query(...)
):
    if preview:
        command = _cert_manager.preview_renew_certificate(certId, duration)
        return {"command": command}
    return _cert_manager.renew_certificate(certId, duration)


# noinspection PyPep8Naming
@_app.post("/certificates/revoke", response_model=Union[CertificateRevokeResult, CommandPreview])
async def revoke_certificate(
    certId: str = Query(...),
    preview: bool = Query(...)
):
    if preview:
        command = _cert_manager.preview_revoke_certificate(certId)
        return {"command": command}
    return _cert_manager.revoke_certificate(certId)


# noinspection PyPep8Naming
@_app.get("/logs/single", response_model=LogEntry)
async def get_log_entry(logId: int = Query(..., gt=0)):
    log_entry = _logger.get_log_entry(logId)
    if not log_entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return _map_log_entry(log_entry)


@_app.post("/logs", response_model=List[LogEntry])
async def get_logs(logs_request: LogsRequest) -> List[LogEntry]:
    logs = _logger.get_logs(logs_request.dict())
    logs_mapped = [_map_log_entry(log) for log in logs]
    return logs_mapped


@_app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@_app.exception_handler(Exception)
async def handle_all_exceptions(request: Request, exc: Exception):
    trace_id = getattr(request.state, 'trace_id', 'UNKNOWN')
    _logger.log_scoped(LogSeverity.ERROR, f"Unhandled exception, trace_id [{trace_id}]: {exc}")
    return PlainTextResponse(f"Internal server error, trace_id [{trace_id}]", status_code=500)


@contextmanager
def logging_scope():  # TODO implement
    """
    Context manager for setting up a unique trace ID for each request.
    """
    trace_id = str(uuid.uuid4())
    try:
        yield trace_id
    finally:
        pass


@_app.middleware("http")
async def add_trace_id(request: Request, call_next):  # TODO implement
    with logging_scope() as trace_id:
        request.state.trace_id = trace_id
        response = await call_next(request)
        return response


def _map_log_entry(log):
    return LogEntry(
        entryId=log.entry_id,
        timestamp=log.timestamp,
        severity=log.severity,
        message=log.message,
        traceId=log.trace_id,
        commandInfo=log.command_info
    )
