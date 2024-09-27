import shlex
import subprocess
from typing import Tuple


class CLIWrapper:
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        return shlex.quote(input_str)

    @staticmethod
    def execute_command(command: str) -> Tuple[str, int]:
        try:
            result = subprocess.run(
                command, shell=True, check=True, text=True, capture_output=True
            )
            return result.stdout, result.returncode
        except subprocess.CalledProcessError as e:
            return e.stdout, e.returncode
