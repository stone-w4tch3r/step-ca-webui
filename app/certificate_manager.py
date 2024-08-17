from step_ca_shared.cli_wrapper import CLIWrapper


class CertManager:
    def __init__(self):
        self.cli = CLIWrapper()

    def list_certificates(self):
        result = self.cli.run_step_ca_command(["certificate", "list"])
        # Parse the output and return a list of certificates
        return result

    def generate_certificate(self, params):
        command = ["certificate", "create", params["name"], params["domain"]]
        result = self.cli.run_step_ca_command(command)
        return result

    def revoke_certificate(self, cert_id):
        result = self.cli.run_step_ca_command(["certificate", "revoke", cert_id])
        return result

    def renew_certificate(self, cert_id):
        result = self.cli.run_step_ca_command(["certificate", "renew", cert_id])
        return result
