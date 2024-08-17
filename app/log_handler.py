import json
from datetime import datetime


class LogHandler:
    def __init__(self, log_file="logs/command_history.json"):
        self.log_file = log_file

    def log_command(self, command, output, status):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "output": output,
            "status": status
        }
        with open(self.log_file, 'a') as file:
            json.dump(log_entry, file)
            file.write('\n')

    def get_logs(self, filter_params=None):
        logs = []
        with open(self.log_file, 'r') as file:
            for line in file:
                log = json.loads(line)
                if self._matches_filter(log, filter_params):
                    logs.append(log)
        return logs

    def get_command_history(self):
        return self.get_logs()

    def _matches_filter(self, log, filter_params):
        if not filter_params:
            return True
        for key, value in filter_params.items():
            if key in log and log[key] != value:
                return False
        return True
