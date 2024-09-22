from api_server import APIServer
from certificate_manager import CertificateManager
from core.trace_id_handler import TraceIdHandler
from shared.db_logger import DBLogger
from shared.logger import Logger, TraceIdProvider

if __name__ == "__main__":
    logger = Logger(TraceIdProvider(lambda: TraceIdHandler.get_current_trace_id()), DBLogger)
    certificate_manager = CertificateManager(logger)
    api_server = APIServer(certificate_manager, logger, "0.0.1", 5000)
    api_server.run()
