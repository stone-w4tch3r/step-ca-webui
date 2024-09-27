from datetime import datetime
from typing import List, Protocol
from pydantic import BaseModel
from shared.models import KeyType

class CertificateResult(BaseModel):
    success: bool
    message: str
    log_entry_id: int
    certificate_id: str
    certificate_name: str = None
    expiration_date: datetime = None
    new_expiration_date: datetime = None
    revocation_date: datetime = None

class Certificate(BaseModel):
    id: str
    name: str
    status: str
    expiration_date: datetime

class ICertificateManager(Protocol):
    def preview_list_certificates(self) -> str:
        ...

    def list_certificates(self) -> List[Certificate]:
        ...

    def preview_generate_certificate(self, key_name: str, key_type: KeyType, duration: int) -> str:
        ...

    def generate_certificate(self, key_name: str, key_type: KeyType, duration_in_seconds: int) -> CertificateResult:
        ...

    def preview_renew_certificate(self, cert_id: str, duration: int) -> str:
        ...

    def renew_certificate(self, cert_id: str, duration: int) -> CertificateResult:
        ...

    def preview_revoke_certificate(self, cert_id: str) -> str:
        ...

    def revoke_certificate(self, cert_id: str) -> CertificateResult:
        ...
