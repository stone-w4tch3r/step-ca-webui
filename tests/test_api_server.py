import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from core.api_server import APIServer
from core.certificate_manager import CertificateManager
from shared.logger import Logger
from shared.models import Certificate, CertificateResult, LogEntry, LogSeverity
from datetime import datetime, timedelta
import uuid

@pytest.fixture
def mock_cert_manager():
    return Mock(spec=CertificateManager)

@pytest.fixture
def mock_logger():
    return Mock(spec=Logger)

@pytest.fixture
def api_client(mock_cert_manager, mock_logger):
    server = APIServer(mock_cert_manager, mock_logger, version="1.0", port=8000)
    return TestClient(server._app)

def test_list_certificates_preview(api_client, mock_cert_manager):
    mock_cert_manager.preview_list_certificates.return_value = "step-cli list"
    response = api_client.get("/certificates?preview=true")
    assert response.status_code == 200
    assert response.json() == {"command": "step-cli list"}

def test_list_certificates(api_client, mock_cert_manager):
    mock_certs = [
        Certificate(id="1", name="cert1", status="valid", expiration_date=datetime.now() + timedelta(days=30)),
        Certificate(id="2", name="cert2", status="expired", expiration_date=datetime.now() - timedelta(days=1))
    ]
    mock_cert_manager.list_certificates.return_value = mock_certs
    response = api_client.get("/certificates?preview=false")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "1"
    assert response.json()[1]["id"] == "2"

def test_generate_certificate_preview(api_client, mock_cert_manager):
    mock_cert_manager.preview_generate_certificate.return_value = "step-cli generate"
    response = api_client.post("/certificates/generate?preview=true", json={
        "keyName": "test",
        "keyType": "EC",
        "duration": 3600
    })
    assert response.status_code == 200
    assert response.json() == {"command": "step-cli generate"}

def test_generate_certificate(api_client, mock_cert_manager):
    mock_result = CertificateResult(
        success=True,
        message="Certificate generated",
        log_entry_id=1,
        certificate_id="cert1",
        certificate_name="test",
        expiration_date=datetime.now() + timedelta(days=30)
    )
    mock_cert_manager.generate_certificate.return_value = mock_result
    response = api_client.post("/certificates/generate?preview=false", json={
        "keyName": "test",
        "keyType": "EC",
        "duration": 3600
    })
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["certificateId"] == "cert1"

def test_get_log_entry(api_client, mock_logger):
    mock_log_entry = LogEntry(
        entry_id=1,
        timestamp=datetime.now(),
        severity=LogSeverity.INFO,
        message="Test log",
        trace_id=uuid.uuid4(),
        command_info=None
    )
    mock_logger.get_log_entry.return_value = mock_log_entry
    response = api_client.get("/logs/single?logId=1")
    assert response.status_code == 200
    assert response.json()["entryId"] == 1
    assert response.json()["severity"] == "INFO"

def test_get_log_entry_not_found(api_client, mock_logger):
    mock_logger.get_log_entry.return_value = None
    response = api_client.get("/logs/single?logId=999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log entry not found"

# Add more tests for other endpoints (renew, revoke, get_logs) following similar patterns
