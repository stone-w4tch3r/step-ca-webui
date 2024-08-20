from api_server import run as run_api_server
from api_server import setup as setup_api_server
from certificate_manager import CertificateManager
from shared.logger import Logger


class MainApplication:
    def __init__(self):
        self.logger = Logger("app.log")
        self.cert_manager = CertificateManager(self.logger)
        setup_api_server(self.cert_manager, self.logger)

    @staticmethod
    def run():
        run_api_server()


if __name__ == "__main__":
    app = MainApplication()
    app.run()
