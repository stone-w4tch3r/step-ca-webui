from datetime import datetime, timedelta
from typing import List

from core.certificate_manager_interface import ICertificateManager, CertificateResult, Certificate
from shared.cli_wrapper import CLIWrapper
from shared.logger import Logger, LogSeverity
from shared.models import CommandInfo, KeyType


class CertificateManager(ICertificateManager):
    def __init__(self, logger: Logger):
        self._logger = logger
        self._cli_wrapper = CLIWrapper()

    def preview_list_certificates(self) -> str:
        return _Commands.list_certificates()

    def list_certificates(self) -> List[Certificate]:
        command = self.preview_list_certificates()
        output, exit_code = self._cli_wrapper.execute_command(command)

        # Parse the output and create a list of Certificate objects
        certificates = []
        # ... (parsing logic here)
        return certificates

    def preview_generate_certificate(self, key_name: str, key_type: KeyType, duration: int) -> str:
        command = _Commands.generate_certificate(key_name, key_type, duration)
        return command

    def generate_certificate(self, key_name: str, key_type: KeyType, duration_in_seconds: int) -> CertificateResult:
        command = self.preview_generate_certificate(key_name, key_type, duration_in_seconds)
        output, exit_code = self._cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate generated successfully" if success else "Failed to generate certificate"

        entry_id = self._logger.log(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            CommandInfo(coommand=command, output=output, exit_code=exit_code, action="GENERATE_CERT")
        )

        return CertificateResult(
            success=success,
            message=message,
            log_entry_id=entry_id,
            certificate_id=key_name,
            certificate_name=key_name,
            expiration_date=(datetime.now() + timedelta(seconds=duration_in_seconds))
            # TODO: parse expiration date from output
        )

    def preview_renew_certificate(self, cert_id: str, duration: int) -> str:
        cert_id = self._cli_wrapper.sanitize_input(cert_id)  # TODO: validate cert_id (what format is it?)
        command = _Commands.renew_certificate(cert_id, duration)
        return command

    def renew_certificate(self, cert_id: str, duration: int) -> CertificateResult:
        command = self.preview_renew_certificate(cert_id, duration)
        output, exit_code = self._cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate renewed successfully" if success else "Failed to renew certificate"

        entry_id = self._logger.log(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            CommandInfo(comand=command, output=output, exit_code=exit_code, action="RENEW_CERT")
        )

        return CertificateResult(
            success=success,
            message=message,
            log_entry_id=entry_id,
            certificate_id=cert_id,
            new_expiration_date=(datetime.now() + timedelta(seconds=duration))
        )

    def preview_revoke_certificate(self, cert_id: str) -> str:
        cert_id = self._cli_wrapper.sanitize_input(cert_id)  # TODO: validate cert_id (what format is it?)
        command = _Commands.revoke_certificate(cert_id)
        return command

    def revoke_certificate(self, cert_id: str) -> CertificateResult:
        command = self.preview_revoke_certificate(cert_id)
        output, exit_code = self._cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate revoked successfully" if success else "Failed to revoke certificate"

        entry_id = self._logger.log(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            CommandInfo(command=command, output=output, exit_code=exit_code, action="REVOKE_CERT")
        )

        return CertificateResult(
            success=success,
            message=message,
            log_entry_id=entry_id,
            certificate_id=cert_id,
            revocation_date=datetime.now()
        )


class _Commands:
    @staticmethod
    def list_certificates():
        return "step-ca list certificates"

    @staticmethod
    def generate_certificate(key_name: str, key_type: KeyType, duration: int):
        key_type = key_type.value
        return f"step-ca certificate {key_name} {key_name}.crt {key_name}.key --key-type {key_type} --not-after {duration}"

    @staticmethod
    def renew_certificate(cert_id: str, duration: int):
        return f"step-ca renew {cert_id}.crt {cert_id}.key --force --expires-in {duration}s"

    @staticmethod
    def revoke_certificate(cert_id: str):
        return f"step-ca revoke {cert_id}.crt"
