from typing import Optional, List, Protocol

from shared.models import LogEntry, Paging, LogsFilter


class IDBLogger(Protocol):
    def insert_log(self, log_entry: LogEntry) -> None: ...

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]: ...

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]: ...

    def get_next_entry_id(self) -> int: ...
