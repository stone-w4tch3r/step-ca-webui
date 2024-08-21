import threading
import uuid
from contextlib import contextmanager
from typing import List, Union

import uvicorn
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import PlainTextResponse

from core.certificate_manager import CertificateManager
from shared.api_models import (
    Certificate,
    CertificateGenerateRequest,
    CertificateGenerateResult,
    CertificateRenewResult,
    CertificateRevokeResult,
    CommandPreview,
    LogEntry,
    LogsRequest
)
from shared.logger import Logger
from shared.models import LogSeverity


# noinspection PyPep8Naming
class APIServer:
    def __init__(self, cert_manager: CertificateManager, logger: Logger, version: str, port: int, prod_url: str = None):
        self._cert_manager = cert_manager
        self._logger = logger
        self._port = port
        self._app = FastAPI(
            title="Step-CA Management API",
            version=version,
            description="API for managing step-ca Certificate Authority",
            openapi_url="/openapi.json",
            docs_url="/swagger",
            redoc_url="/redoc",
            servers=[
                {"url": f"http://localhost:{port}", "description": "Local development environment"},
                {"url": prod_url, "description": "Production environment"} if prod_url else None
            ]
        )

        self._setup_routes()
        self._setup_handlers()

    def run(self):
        uvicorn.run(self._app, host="0.0.0.0", port=self._port)

    def _setup_routes(self):
        @self._app.get("/certificates", response_model=Union[List[Certificate], CommandPreview])
        async def list_certificates(preview: bool = Query(...)) -> Union[List[Certificate], CommandPreview]:
            if preview:
                command = self._cert_manager.preview_list_certificates()
                return CommandPreview(command=command)
            certs = self._cert_manager.list_certificates()
            return [
                Certificate(
                    id=cert["id"],
                    name=cert["name"],
                    status=cert["status"],
                    expirationDate=cert["expirationDate"]
                ) for cert in certs
            ]

        @self._app.post("/certificates/generate", response_model=Union[CertificateGenerateResult, CommandPreview])
        async def generate_certificate(
            cert_request: CertificateGenerateRequest,
            preview: bool = Query(...)
        ):
            if preview:
                command = self._cert_manager.preview_generate_certificate(cert_request.dict())
                return CommandPreview(command=command)
            cert = self._cert_manager.generate_certificate(cert_request.dict())
            return CertificateGenerateResult(
                success=cert["success"],
                message=cert["message"],
                logEntryId=cert["logEntryId"],
                certificateId=cert["certificateId"],
                certificateName=cert["certificateName"],
                expirationDate=cert["expirationDate"]
            )

        @self._app.post("/certificates/renew", response_model=Union[CertificateRenewResult, CommandPreview])
        async def renew_certificate(
            certId: str = Query(...),
            duration: int = Query(..., description="Duration in seconds"),
            preview: bool = Query(...)
        ):
            if preview:
                command = self._cert_manager.preview_renew_certificate(certId, duration)
                return CommandPreview(command=command)
            cert = self._cert_manager.renew_certificate(certId, duration)
            return CertificateRenewResult(
                success=cert["success"],
                message=cert["message"],
                logEntryId=cert["logEntryId"],
                certificateId=cert["certificateId"],
                newExpirationDate=cert["newExpirationDate"]
            )

        @self._app.post("/certificates/revoke", response_model=Union[CertificateRevokeResult, CommandPreview])
        async def revoke_certificate(
            certId: str = Query(...),
            preview: bool = Query(...)
        ):
            if preview:
                command = self._cert_manager.preview_revoke_certificate(certId)
                return CommandPreview(command=command)
            cert = self._cert_manager.revoke_certificate(certId)
            return CertificateRevokeResult(
                success=cert["success"],
                message=cert["message"],
                logEntryId=cert["logEntryId"],
                certificateId=cert["certificateId"],
                revocationDate=cert["revocationDate"]
            )

        @self._app.post("/logs/single", response_model=LogEntry)
        async def get_log_entry(logId: int = Query(..., gt=0)):
            log_entry = self._logger.get_log_entry(logId)
            if not log_entry:
                raise HTTPException(status_code=404, detail="Log entry not found")
            return self._map_log_entry(log_entry)

        @self._app.post("/logs", response_model=List[LogEntry])
        async def get_logs(logs_request: LogsRequest) -> List[LogEntry]:
            logs = self._logger.get_logs(logs_request.dict())
            logs_mapped = [self._map_log_entry(log) for log in logs]
            return logs_mapped

    def _setup_handlers(self):
        @self._app.exception_handler(HTTPException)
        async def custom_http_exception_handler(request: Request, exc: HTTPException):
            return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

        @self._app.exception_handler(Exception)
        async def handle_all_exceptions(request: Request, exc: Exception):
            trace_id = getattr(request.state, 'trace_id', 'UNKNOWN')
            self._logger.log_scoped(LogSeverity.ERROR, f"Unhandled exception, trace_id [{trace_id}]: {exc}")
            return PlainTextResponse(f"Internal server error, trace_id [{trace_id}]", status_code=500)

        @self._app.middleware("http")
        async def setup_logging_scope(request: Request, call_next):
            async with TraceIdHandler.logging_scope():
                response = await call_next(request)
            return response

    @staticmethod
    def _map_log_entry(log) -> LogEntry:
        return LogEntry(
            entryId=log.entry_id,
            timestamp=log.timestamp,
            severity=log.severity,
            message=log.message,
            traceId=log.trace_id,
            commandInfo=log.command_info
        )


class TraceIdHandler:
    _thread_local = threading.local()

    @staticmethod
    @contextmanager
    def logging_scope():
        TraceIdHandler._thread_local.trace_id = uuid.uuid4()
        try:
            yield
        finally:
            del TraceIdHandler._thread_local.trace_id

    @staticmethod
    def get_current_trace_id() -> uuid.UUID | None:
        return getattr(TraceIdHandler._thread_local, 'trace_id', None)
