import os
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

from .models import LogEntry, LogSeverity, CommandInfo, LogsFilter, Paging


class DBHandler:
    """
    DBHandler class for managing database operations related to logging.

    Required environment variables:
    - DB_HOST: The hostname of the database server
    - DB_PORT: The port number of the database server
    - DB_NAME: The name of the database
    - DB_USER: The username for database authentication
    - DB_PASSWORD: The password for database authentication

    Make sure to set these variables in your .env file or environment.
    """

    # TODO: how to setup db schema?
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

    def insert_log(self, log_entry: LogEntry) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO log_entries (timestamp, severity, message, trace_id, command_info)
                VALUES (%s, %s, %s, %s, %s)
            """, (log_entry.timestamp, log_entry.severity.value, log_entry.message,
                  log_entry.trace_id, log_entry.command_info.model_dump_json() if log_entry.command_info else None))
        self.conn.commit()

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM log_entries
                WHERE (%s IS NULL OR trace_id = %s)
                AND (%s = FALSE OR command_info IS NOT NULL)
                AND severity = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(query, (
                filters.trace_id, filters.trace_id,
                filters.commands_only,
                [s.value for s in filters.severity],
                paging.page_size, (paging.page - 1) * paging.page_size
            ))
            return [LogEntry(**row) for row in cur.fetchall()]

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM log_entries WHERE id = %s", (log_id,))
            row = cur.fetchone()
            return LogEntry(**row) if row else None

    def get_next_entry_id(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute("SELECT nextval('log_entries_id_seq')")
            return cur.fetchone()[0]
