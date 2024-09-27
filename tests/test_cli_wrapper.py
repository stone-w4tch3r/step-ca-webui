import subprocess
import unittest
from unittest.mock import patch

from shared.cli_wrapper import CLIWrapper


class TestCLIWrapper(unittest.TestCase):

    @patch("subprocess.run")
    def test_execute_command_success(self, mock_run):
        mock_run.return_value.stdout = "Command output"
        mock_run.return_value.returncode = 0

        output, return_code = CLIWrapper.execute_command("test command")

        self.assertEqual(output, "Command output")
        self.assertEqual(return_code, 0)
        mock_run.assert_called_once_with(
            "test command", shell=True, check=True, text=True, capture_output=True
        )

    @patch("subprocess.run")
    def test_execute_command_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "test command", output="Error output"
        )

        output, return_code = CLIWrapper.execute_command("test command")

        self.assertEqual(output, "Error output")
        self.assertEqual(return_code, 1)
        mock_run.assert_called_once_with(
            "test command", shell=True, check=True, text=True, capture_output=True
        )


if __name__ == "__main__":
    unittest.main()
