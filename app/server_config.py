from step_ca_shared.cli_wrapper import CLIWrapper
import json


class ServerConfig:
    def __init__(self):
        self.cli = CLIWrapper()

    def get_config(self):
        result = self.cli.run_step_ca_command(["ca", "config"])
        if result["status"] == "success":
            return json.loads(result["output"])
        return result

    def update_config(self, new_config):
        # This is a placeholder. In reality, updating the CA config would be more complex
        # and might require restarting the CA service.
        result = self.cli.run_step_ca_command(["ca", "config", "update", json.dumps(new_config)])
        return result
