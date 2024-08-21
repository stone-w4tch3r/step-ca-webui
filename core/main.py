from api_server import run as run_api_server
from certificate_manager import CertificateManager
from shared.logger import Logger

if __name__ == "__main__":
    logger = Logger("step-ca-webui.log")
    certificate_manager = CertificateManager(logger)

    run_api_server(
        certificate_manager,
        logger,
        version="0.1.0",
        port=5000
    )
