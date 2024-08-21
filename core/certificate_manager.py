import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Union

from shared.cli_wrapper import CLIWrapper
from shared.logger import Logger, LogSeverity
from shared.models import CommandInfo, KeyType


@dataclass
class CertificateResult:
    success: bool
    message: str
    log_entry_id: int
    certificate_id: str
    certificate_name: str = None
    expiration_date: datetime = None
    new_expiration_date: datetime = None
    revocation_date: datetime = None


@dataclass
class Certificate:
    id: str
    name: str
    status: str
    expiration_date: datetime


class CertificateManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.cli_wrapper = CLIWrapper()

    # noinspection PyMethodMayBeStatic
    def preview_list_certificates(self) -> str:
        return "step-ca list certificates"

    def list_certificates(self) -> List[Certificate]:
        command = self.preview_list_certificates()
        output, exit_code = self.cli_wrapper.execute_command(command)

        # Parse the output and create a list of Certificate objects
        certificates = []
        # ... (parsing logic here)
        return certificates

    def preview_generate_certificate(self, key_name: str, key_type: KeyType, duration: int) -> str:
        key_name = self.cli_wrapper.sanitize_input(key_name)
        key_type = self.cli_wrapper.sanitize_input(key_type.upper())
        duration = self.cli_wrapper.sanitize_input(str(duration))

        allowed_key_types = [kt.upper for kt in KeyType]
        if key_type not in allowed_key_types:
            raise ValueError(f"Invalid key type: {key_type}, must be one of {allowed_key_types}")
        if not self._is_valid_keyname(key_name):
            raise ValueError(f"Invalid key name: {key_name}")
        if not self._is_valid_duration(duration):
            raise ValueError(f"Invalid duration: {duration}")

        # TODO: extract command template into separate entity
        command = f"step-ca certificate {key_name} {key_name}.crt {key_name}.key --key-type {key_type} --not-after {duration}"
        return command

    def generate_certificate(self, key_name: str, key_type: KeyType, duration: int) -> CertificateResult:
        command = self.preview_generate_certificate(key_name, key_type, duration)
        output, exit_code = self.cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate generated successfully" if success else "Failed to generate certificate"

        entry_id = self.logger.log_scoped(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            CommandInfo(command, output, exit_code, "GENERATE_CERT")
        )

        return CertificateResult(
            success=success,
            message=message,
            log_entry_id=entry_id,
            certificate_id=key_name,
            certificate_name=key_name,
            expiration_date=(datetime.now() + self._parse_duration(str(duration)))
        )

    def preview_renew_certificate(self, cert_id: str, duration: int) -> str:
        cert_id = self.cli_wrapper.sanitize_input(cert_id)  # TODO: validate cert_id (what format is it?)
        command = f"step-ca renew {cert_id}.crt {cert_id}.key --force --expires-in {duration}s"
        return command

    def renew_certificate(self, cert_id: str, duration: int) -> CertificateResult:
        command = self.preview_renew_certificate(cert_id, duration)
        output, exit_code = self.cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate renewed successfully" if success else "Failed to renew certificate"

        entry_id = self.logger.log_scoped(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            CommandInfo(command, output, exit_code, "RENEW_CERT")
        )

        return CertificateResult(
            success=success,
            message=message,
            log_entry_id=entry_id,
            certificate_id=cert_id,
            new_expiration_date=(datetime.now() + timedelta(seconds=duration))
        )

    def preview_revoke_certificate(self, cert_id: str) -> str:
        cert_id = self.cli_wrapper.sanitize_input(cert_id)  # TODO: validate cert_id (what format is it?)
        command = f"step-ca revoke {cert_id}.crt"
        return command

    def revoke_certificate(self, cert_id: str) -> CertificateResult:
        command = self.preview_revoke_certificate(cert_id)
        output, exit_code = self.cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate revoked successfully" if success else "Failed to revoke certificate"

        entry_id = self.logger.log_scoped(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            CommandInfo(command, output, exit_code, "REVOKE_CERT")
        )

        return CertificateResult(
            success=success,
            message=message,
            log_entry_id=entry_id,
            certificate_id=cert_id,
            revocation_date=datetime.now()
        )

    # TODO: remove
    @staticmethod
    def _parse_duration(duration: str) -> timedelta:
        # Parse the duration string and return a timedelta object
        # This is a placeholder and would need to be implemented based on your duration format
        raise NotImplementedError

    @staticmethod  # TODO move to api validation
    def _is_valid_keyname(key_name: str) -> bool:
        """
        :param key_name: Name of the key, must be alphanumeric with dashes and underscores
        """
        return re.match(r"^[a-zA-Z0-9_-]+$", key_name) is not None

    @staticmethod
    def _is_valid_duration(duration_str: str) -> bool:
        """
        :param duration_str: Duration in seconds, must be a positive integer
        """
        return isinstance(duration_str, int) and duration_str > 0
