import subprocess
import shlex
import json


class CLIWrapper:
    def __init__(self, step_ca_path="/usr/local/bin/step-ca"):
        self.step_ca_path = step_ca_path

    def _sanitize_input(self, input_str):
        return shlex.quote(input_str)

    def _execute_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            stdout, stderr = process.communicate()
            return {
                "status": "success" if process.returncode == 0 else "error",
                "output": stdout,
                "error": stderr,
                "command": command
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "command": command
            }

    def run_step_ca_command(self, args):
        sanitized_args = [self._sanitize_input(arg) for arg in args]
        command = f"{self.step_ca_path} {' '.join(sanitized_args)}"
        return self._execute_command(command)
