from typing import List, Optional

import httpx

from shared.api_models import (
    CertificateDTO,
    LogEntryDTO,
    CertificateGenerateRequest,
    CertificateGenerateResult,
    CertificateRenewResult,
    CertificateRevokeResult,
)


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def list_certificates(self) -> List[CertificateDTO]:
        response = await self.client.get("/certificates", params={"preview": False})
        response.raise_for_status()
        return [CertificateDTO(**cert) for cert in response.json()]

    async def generate_certificate(
        self, request: CertificateGenerateRequest
    ) -> CertificateGenerateResult:
        response = await self.client.post(
            "/certificates/generate", json=request.dict(), params={"preview": False}
        )
        response.raise_for_status()
        return CertificateGenerateResult(**response.json())

    async def renew_certificate(
        self, cert_id: str, duration: int
    ) -> CertificateRenewResult:
        response = await self.client.post(
            "/certificates/renew",
            params={"certId": cert_id, "duration": duration, "preview": False},
        )
        response.raise_for_status()
        return CertificateRenewResult(**response.json())

    async def revoke_certificate(self, cert_id: str) -> CertificateRevokeResult:
        response = await self.client.post(
            "/certificates/revoke", params={"certId": cert_id, "preview": False}
        )
        response.raise_for_status()
        return CertificateRevokeResult(**response.json())

    async def get_logs(
        self,
        trace_id: Optional[str] = None,
        commands_only: bool = False,
        severity: List[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[LogEntryDTO]:
        params = {
            "traceId": trace_id,
            "commandsOnly": commands_only,
            "severity": severity or ["DEBUG", "INFO", "WARN", "ERROR"],
            "page": page,
            "pageSize": page_size,
        }
        response = await self.client.post("/logs", json=params)
        response.raise_for_status()
        return [LogEntryDTO(**log) for log in response.json()]

    async def close(self):
        await self.client.aclose()
