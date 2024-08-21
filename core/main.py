from api_server import APIServer
from certificate_manager import CertificateManager
from shared.logger import Logger

if __name__ == "__main__":
    logger = Logger()
    certificate_manager = CertificateManager(logger)
    api_server = APIServer(certificate_manager, logger, "0.0.1", 5000)
    api_server.run()
