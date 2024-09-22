from typing import List, Union

import uvicorn
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import PlainTextResponse

from core.certificate_manager import CertificateManager
from core.trace_id_handler import TraceIdHandler
from shared.api_models import (
    CertificateDTO,
    CertificateGenerateRequest,
    CertificateGenerateResult,
    CertificateRenewResult,
    CertificateRevokeResult,
    CommandPreviewDTO,
    LogEntryDTO,
    LogsRequest
)
from shared.logger import Logger, LogsFilter, Paging
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
                    ] + [{"url": prod_url, "description": "Production environment"}] if prod_url else []
        )

        self._setup_routes()
        self._setup_handlers()

    def run(self):
        uvicorn.run(self._app, host="0.0.0.0", port=self._port)

    def _setup_routes(self):
        @self._app.get("/certificates", response_model=Union[List[CertificateDTO], CommandPreviewDTO])
        async def list_certificates(preview: bool = Query(...)) -> Union[List[CertificateDTO], CommandPreviewDTO]:
            if preview:
                command = self._cert_manager.preview_list_certificates()
                return CommandPreviewDTO(command=command)
            certs = self._cert_manager.list_certificates()

            return [
                CertificateDTO(
                    id=cert.id,
                    name=cert.name,
                    status=cert.status,
                    expirationDate=cert.expiration_date
                ) for cert in certs
            ]

        @self._app.post("/certificates/generate", response_model=Union[CertificateGenerateResult, CommandPreviewDTO])
        async def generate_certificate(
            cert_request: CertificateGenerateRequest,
            preview: bool = Query(...)
        ):
            if preview:
                command = self._cert_manager.preview_generate_certificate(cert_request.keyName, cert_request.keyType, cert_request.duration)
                return CommandPreviewDTO(command=command)
            cert = self._cert_manager.generate_certificate(cert_request.keyName, cert_request.keyType, cert_request.duration)

            return CertificateGenerateResult(
                success=cert.success,
                message=cert.message,
                logEntryId=cert.log_entry_id,
                certificateId=cert.certificate_id,
                certificateName=cert.certificate_name,
                expirationDate=cert.expiration_date
            )

        @self._app.post("/certificates/renew", response_model=Union[CertificateRenewResult, CommandPreviewDTO])
        async def renew_certificate(
            certId: str = Query(...),
            duration: int = Query(..., description="Duration in seconds"),
            preview: bool = Query(...)
        ):
            if preview:
                command = self._cert_manager.preview_renew_certificate(certId, duration)
                return CommandPreviewDTO(command=command)
            cert = self._cert_manager.renew_certificate(certId, duration)

            return CertificateRenewResult(
                success=cert.success,
                message=cert.message,
                logEntryId=cert.log_entry_id,
                certificateId=cert.certificate_id,
                newExpirationDate=cert.new_expiration_date
            )

        @self._app.post("/certificates/revoke", response_model=Union[CertificateRevokeResult, CommandPreviewDTO])
        async def revoke_certificate(
            certId: str = Query(...),
            preview: bool = Query(...)
        ):
            if preview:
                command = self._cert_manager.preview_revoke_certificate(certId)
                return CommandPreviewDTO(command=command)
            cert = self._cert_manager.revoke_certificate(certId)

            return CertificateRevokeResult(
                success=cert.success,
                message=cert.message,
                logEntryId=cert.log_entry_id,
                certificateId=cert.certificate_id,
                revocationDate=cert.revocation_date
            )

        @self._app.get("/logs/single", response_model=LogEntryDTO)
        async def get_log_entry(logId: int = Query(..., gt=0)):
            log_entry = self._logger.get_log_entry(logId)
            if not log_entry:
                raise HTTPException(status_code=404, detail="Log entry not found")

            return LogEntryDTO(
                entryId=log_entry.entry_id,
                timestamp=log_entry.timestamp,
                severity=log_entry.severity,
                message=log_entry.message,
                traceId=log_entry.trace_id,
                commandInfo=log_entry.command_info
            )

        @self._app.post("/logs", response_model=List[LogEntryDTO])
        async def get_logs(logs_request: LogsRequest) -> List[LogEntryDTO]:
            logs = self._logger.get_logs(
                LogsFilter(trace_id=logs_request.traceId, commands_only=logs_request.commandsOnly, severity=logs_request.severity),
                Paging(page=logs_request.page, page_size=logs_request.pageSize)
            )

            return [
                LogEntryDTO(
                    entryId=log.entry_id,
                    timestamp=log.timestamp,
                    severity=log.severity,
                    message=log.message,
                    traceId=log.trace_id,
                    commandInfo=log.command_info
                ) for log in logs
            ]

    def _setup_handlers(self):
        @self._app.exception_handler(HTTPException)
        async def custom_http_exception_handler(request: Request, exc: HTTPException):
            return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

        @self._app.exception_handler(Exception)
        async def handle_all_exceptions(request: Request, exc: Exception):
            trace_id = getattr(request.state, 'trace_id', 'UNKNOWN')
            self._logger.log(LogSeverity.ERROR, f"Unhandled exception, trace_id [{trace_id}]: {exc}")
            return PlainTextResponse(f"Internal server error, trace_id [{trace_id}]", status_code=500)

        @self._app.middleware("http")
        async def setup_logging_scope(request: Request, call_next):
            async with TraceIdHandler.logging_scope():
                response = await call_next(request)
            return response
