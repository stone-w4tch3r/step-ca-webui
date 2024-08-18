import re
from typing import List, Dict, Union
from datetime import datetime, timedelta
from uuid import uuid4
from shared.cli_wrapper import CLIWrapper
from shared.logger import Logger, LogSeverity
from shared.models import CommandInfo


class CertificateManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.cli_wrapper = CLIWrapper()

    # noinspection PyMethodMayBeStatic
    def preview_list_certificates(self) -> str:
        return "step-ca list certificates"

    def list_certificates(self) -> List[Dict[str, Union[str, datetime]]]:
        command = self.preview_list_certificates()
        output, exit_code = self.cli_wrapper.execute_command(command)

        # Parse the output and create a list of certificate dictionaries
        certificates = []
        # ... (parsing logic here)

        return certificates

    # TODO: Add type hints for params
    def preview_generate_certificate(self, params: Dict[str, str]) -> str:
        key_name = self.cli_wrapper.sanitize_input(params['keyName'])
        key_type = self.cli_wrapper.sanitize_input(params['keyType'])
        duration = self.cli_wrapper.sanitize_input(params['duration'])

        allowed_key_types = ["RSA", "ECDSA", "Ed25519"]
        if key_type not in allowed_key_types:
            raise ValueError(f"Invalid key type: {key_type}, must be one of {allowed_key_types}")
        if not self._is_valid_keyname(key_name):
            raise ValueError(f"Invalid key name: {key_name}")
        if not self._is_valid_duration(duration):
            raise ValueError(f"Invalid duration: {duration}")

        # TODO: extract command template into separate entity
        command = f"step-ca certificate {key_name} {key_name}.crt {key_name}.key --key-type {key_type} --not-after {duration}"
        return command

    # TODO: Add type hints for params
    def generate_certificate(self, params: Dict[str, str]) -> Dict[str, Union[bool, str, datetime]]:
        command = self.preview_generate_certificate(params)
        output, exit_code = self.cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate generated successfully" if success else "Failed to generate certificate"

        trace_id = uuid4()  # TODO: use scoped logging
        self.logger.log(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            trace_id,
            CommandInfo(command, output, exit_code, "GENERATE_CERT")
        )

        return {  # TODO: extract to dataclass or namedtuple or typed dict
            "success": success,
            "message": message,
            "logEntryId": str(trace_id),
            "certificateId": params['keyName'],
            "certificateName": params['keyName'],
            "expirationDate": (datetime.now() + self._parse_duration(params['duration'])).isoformat()  # TODO: remove _parse_duration
        }

    def preview_renew_certificate(self, cert_id: str, duration: int) -> str:
        cert_id = self.cli_wrapper.sanitize_input(cert_id)  # TODO: validate cert_id (what format is it?)
        command = f"step-ca renew {cert_id}.crt {cert_id}.key --force --expires-in {duration}s"
        return command

    def renew_certificate(self, cert_id: str, duration: int) -> Dict[str, Union[bool, str, datetime]]:
        command = self.preview_renew_certificate(cert_id, duration)
        output, exit_code = self.cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate renewed successfully" if success else "Failed to renew certificate"

        trace_id = uuid4()  # TODO: use scoped logging
        self.logger.log(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            trace_id,
            CommandInfo(command, output, exit_code, "RENEW_CERT")
        )

        return {
            "success": success,
            "message": message,
            "logEntryId": str(trace_id),
            "certificateId": cert_id,
            "newExpirationDate": (datetime.now() + timedelta(seconds=duration)).isoformat()
        }

    def preview_revoke_certificate(self, cert_id: str) -> str:
        cert_id = self.cli_wrapper.sanitize_input(cert_id)  # TODO: validate cert_id (what format is it?)
        command = f"step-ca revoke {cert_id}.crt"
        return command

    def revoke_certificate(self, cert_id: str) -> Dict[str, Union[bool, str, datetime]]:
        command = self.preview_revoke_certificate(cert_id)
        output, exit_code = self.cli_wrapper.execute_command(command)

        success = exit_code == 0
        message = "Certificate revoked successfully" if success else "Failed to revoke certificate"

        trace_id = uuid4()  # TODO: use scoped logging
        self.logger.log(
            LogSeverity.INFO if success else LogSeverity.ERROR,
            message,
            trace_id,
            CommandInfo(command, output, exit_code, "REVOKE_CERT")
        )

        return {
            "success": success,
            "message": message,
            "logEntryId": str(trace_id),
            "certificateId": cert_id,
            "revocationDate": datetime.now().isoformat()
        }

    # TODO: remove
    @staticmethod
    def _parse_duration(duration: str) -> timedelta:
        # Parse the duration string and return a timedelta object
        # This is a placeholder and would need to be implemented based on your duration format
        raise NotImplementedError

    @staticmethod
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
