from core.api_server import APIServer
from core.certificate_manager_mock import CertificateManagerMock
from core.trace_id_handler import TraceIdHandler
from shared.db_logger_mock import DBLoggerMock
from shared.logger import Logger, TraceIdProvider

logger = Logger(
    TraceIdProvider(lambda: TraceIdHandler.get_current_trace_id()), DBLoggerMock()
)
certificate_manager = CertificateManagerMock()
api_server = APIServer(certificate_manager, logger, "0.0.1", 5000)
app = api_server.App

if __name__ == "__main__":
    api_server.run()
