import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from uuid import UUID

from core.api_server import APIServer
from core.certificate_manager import CertificateManager, Certificate, CertificateResult
from shared.logger import Logger
from shared.models import KeyType, LogSeverity, CommandInfo


class TestAPIServer(unittest.TestCase):
    def setUp(self):
        self.cert_manager_mock = Mock(spec=CertificateManager)
        self.logger_mock = Mock(spec=Logger)
        self.api_server = APIServer(self.cert_manager_mock, self.logger_mock, "1.0.0", 8000)
        self.client = TestClient(self.api_server._app)

    def test_list_certificates_preview(self):
        self.cert_manager_mock.preview_list_certificates.return_value = "step-ca list certificates"
        response = self.client.get("/certificates?preview=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"command": "step-ca list certificates"})

    def test_list_certificates(self):
        mock_certs = [
            Certificate(id="cert1", name="Cert 1", status="valid", expiration_date=datetime.now() + timedelta(days=30)),
            Certificate(id="cert2", name="Cert 2", status="expired", expiration_date=datetime.now() - timedelta(days=1))
        ]
        self.cert_manager_mock.list_certificates.return_value = mock_certs
        response = self.client.get("/certificates?preview=false")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["id"], "cert1")
        self.assertEqual(response.json()[1]["id"], "cert2")

    def test_generate_certificate_preview(self):
        self.cert_manager_mock.preview_generate_certificate.return_value = \
            "step-ca certificate test test.crt test.key --key-type rsa --not-after 3600"
        response = self.client.post("/certificates/generate?preview=true", json={
            "keyName": "test",
            "keyType": "RSA",
            "duration": 3600
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "command": "step-ca certificate test test.crt test.key --key-type rsa --not-after 3600"
        })

    def test_generate_certificate(self):
        mock_result = CertificateResult(
            success=True,
            message="Certificate generated successfully",
            log_entry_id=1,
            certificate_id="test",
            certificate_name="test",
            expiration_date=datetime.now() + timedelta(hours=1)
        )
        self.cert_manager_mock.generate_certificate.return_value = mock_result
        response = self.client.post("/certificates/generate?preview=false", json={
            "keyName": "test",
            "keyType": "RSA",
            "duration": 3600
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["certificateId"], "test")

    def test_renew_certificate_preview(self):
        self.cert_manager_mock.preview_renew_certificate.return_value = "step-ca renew test.crt test.key --force --expires-in 3600s"
        response = self.client.post("/certificates/renew?certId=test&duration=3600&preview=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"command": "step-ca renew test.crt test.key --force --expires-in 3600s"})

    def test_renew_certificate(self):
        mock_result = CertificateResult(
            success=True,
            message="Certificate renewed successfully",
            log_entry_id=2,
            certificate_id="test",
            new_expiration_date=datetime.now() + timedelta(hours=1)
        )
        self.cert_manager_mock.renew_certificate.return_value = mock_result
        response = self.client.post("/certificates/renew?certId=test&duration=3600&preview=false")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["certificateId"], "test")

    def test_revoke_certificate_preview(self):
        self.cert_manager_mock.preview_revoke_certificate.return_value = "step-ca revoke test.crt"
        response = self.client.post("/certificates/revoke?certId=test&preview=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"command": "step-ca revoke test.crt"})

    def test_revoke_certificate(self):
        mock_result = CertificateResult(
            success=True,
            message="Certificate revoked successfully",
            log_entry_id=3,
            certificate_id="test",
            revocation_date=datetime.now()
        )
        self.cert_manager_mock.revoke_certificate.return_value = mock_result
        response = self.client.post("/certificates/revoke?certId=test&preview=false")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["certificateId"], "test")

    def test_get_log_entry(self):
        mock_log_entry = Mock(
            entry_id=1,
            timestamp=datetime.now(),
            severity=LogSeverity.INFO,
            message="Test log entry",
            trace_id=UUID("12345678-1234-5678-1234-567812345678"),
            command_info=CommandInfo(command="test command", output="test output", exit_code=0, action="TEST")
        )
        self.logger_mock.get_log_entry.return_value = mock_log_entry
        response = self.client.get("/logs/single?logId=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["entryId"], 1)
        self.assertEqual(response.json()["message"], "Test log entry")

    def test_get_log_entry_not_found(self):
        self.logger_mock.get_log_entry.return_value = None
        response = self.client.get("/logs/single?logId=999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b"Log entry not found")

    def test_get_logs(self):
        mock_log_entries = [
            Mock(
                entry_id=1,
                timestamp=datetime.now(),
                severity=LogSeverity.INFO,
                message="Test log entry 1",
                trace_id=UUID("12345678-1234-5678-1234-567812345678"),
                command_info=None
            ),
            Mock(
                entry_id=2,
                timestamp=datetime.now(),
                severity=LogSeverity.ERROR,
                message="Test log entry 2",
                trace_id=UUID("87654321-4321-8765-4321-876543210987"),
                command_info=CommandInfo(command="test command", output="test output", exit_code=1, action="TEST")
            )
        ]
        self.logger_mock.get_logs.return_value = mock_log_entries
        response = self.client.post("/logs", json={
            "traceId": None,
            "commandsOnly": False,
            "severity": [],
            "page": 1,
            "pageSize": 10
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["entryId"], 1)
        self.assertEqual(response.json()[1]["entryId"], 2)


if __name__ == '__main__':
    unittest.main()
