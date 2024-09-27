import random
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from core.certificate_manager_interface import (
    ICertificateManager,
    CertificateResult,
    Certificate,
)
from shared.models import KeyType


class CertificateManagerMock(ICertificateManager):
    SEED = 42  # Constant seed for random generation

    def __init__(self):
        self.random = random.Random(self.SEED)
        self.certificates = self._generate_initial_certificates()

    def _generate_initial_certificates(self) -> List[Certificate]:
        return [
            Certificate(
                id=str(uuid4()),
                name=f"test-cert-{i}",
                status="active" if self.random.random() > 0.2 else "revoked",
                expiration_date=datetime.now()
                + timedelta(days=self.random.randint(1, 365)),
            )
            for i in range(10)
        ]

    def preview_list_certificates(self) -> str:
        return "step-ca list certificates"

    def list_certificates(self) -> List[Certificate]:
        return self.certificates

    def preview_generate_certificate(
        self, key_name: str, key_type: KeyType, duration: int
    ) -> str:
        return (
            f"step-ca certificate {key_name} {key_name}.crt {key_name}.key "
            + f"--key-type {key_type.value} --not-after {duration}"
        )

    def generate_certificate(
        self, key_name: str, key_type: KeyType, duration_in_seconds: int
    ) -> CertificateResult:
        new_cert = Certificate(
            id=str(uuid4()),
            name=key_name,
            status="active",
            expiration_date=datetime.now() + timedelta(seconds=duration_in_seconds),
        )
        self.certificates.append(new_cert)
        return CertificateResult(
            success=True,
            message="Certificate generated successfully",
            log_entry_id=self.random.randint(1000, 9999),
            certificate_id=new_cert.id,
            certificate_name=new_cert.name,
            expiration_date=new_cert.expiration_date,
        )

    def preview_renew_certificate(self, cert_id: str, duration: int) -> str:
        return f"step-ca renew {cert_id}.crt {cert_id}.key --force --expires-in {duration}s"

    def renew_certificate(self, cert_id: str, duration: int) -> CertificateResult:
        cert = next((c for c in self.certificates if c.id == cert_id), None)
        if cert:
            new_expiration = datetime.now() + timedelta(seconds=duration)
            cert.expiration_date = new_expiration
            return CertificateResult(
                success=True,
                message="Certificate renewed successfully",
                log_entry_id=self.random.randint(1000, 9999),
                certificate_id=cert_id,
                new_expiration_date=new_expiration,
            )
        return CertificateResult(
            success=False,
            message="Certificate not found",
            log_entry_id=self.random.randint(1000, 9999),
            certificate_id=cert_id,
        )

    def preview_revoke_certificate(self, cert_id: str) -> str:
        return f"step-ca revoke {cert_id}.crt"

    def revoke_certificate(self, cert_id: str) -> CertificateResult:
        cert = next((c for c in self.certificates if c.id == cert_id), None)
        if cert:
            cert.status = "revoked"
            return CertificateResult(
                success=True,
                message="Certificate revoked successfully",
                log_entry_id=self.random.randint(1000, 9999),
                certificate_id=cert_id,
                revocation_date=datetime.now(),
            )
        return CertificateResult(
            success=False,
            message="Certificate not found",
            log_entry_id=self.random.randint(1000, 9999),
            certificate_id=cert_id,
        )
