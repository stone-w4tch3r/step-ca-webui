from api_server import APIServer
from certificate_manager import CertificateManager
from shared.logger import Logger


class MainApplication:
    def __init__(self):
        self.logger = Logger("app.log")
        self.cert_manager = CertificateManager(self.logger)
        self.api_server = APIServer(self.cert_manager, self.logger)

    def run(self):
        self.api_server.run()


if __name__ == "__main__":
    app = MainApplication()
    app.run()
