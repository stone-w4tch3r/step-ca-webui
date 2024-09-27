from typing import List, Optional
from shared.models import LogEntry, Paging, LogsFilter
from shared.db_logger_interface import IDBLogger


class DBLoggerMock(IDBLogger):
    def __init__(self):
        self.logs: List[LogEntry] = []
        self.next_id: int = 1

    def insert_log(self, log_entry: LogEntry) -> None:
        log_entry.entry_id = self.next_id
        self.logs.append(log_entry)
        self.next_id += 1

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        filtered_logs = self.logs

        if filters.trace_id:
            filtered_logs = [log for log in filtered_logs if log.trace_id == filters.trace_id]

        if filters.commands_only:
            filtered_logs = [log for log in filtered_logs if log.command_info is not None]

        if filters.severity:
            filtered_logs = [log for log in filtered_logs if log.severity in filters.severity]

        start = (paging.page - 1) * paging.page_size
        end = start + paging.page_size

        return filtered_logs[start:end]

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        for log in self.logs:
            if log.entry_id == log_id:
                return log
        return None

    def get_next_entry_id(self) -> int:
        return self.next_id
