import os
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, JSON, Sequence, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from shared.logger import IDBLogger
from shared.models import LogEntry, LogsFilter, Paging, LogSeverity, CommandInfo

_Base = declarative_base()


class LogEntryModel(_Base):
    __tablename__ = 'log_entries'

    id = Column(Integer, Sequence('log_entry_id_seq'), primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    severity = Column(Enum(LogSeverity))
    message = Column(String)
    trace_id = Column(String)
    command_info = Column(JSON)


class DBLogger(IDBLogger):
    """
    DBLogger class for managing database operations related to logging using SQLAlchemy.

    Required environment variables:
    - DB_HOST: The hostname of the database server
    - DB_PORT: The port number of the database server
    - DB_NAME: The name of the database
    - DB_USER: The username for database authentication
    - DB_PASSWORD: The password for database authentication

    Make sure to set these variables in your .env file or environment.
    """

    def __init__(self, is_test: bool = False):
        if is_test:
            return

        url = ("postgresql://" +
               f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}" +
               f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        _Base.metadata.create_all(self.engine)

    def insert_log(self, log_entry: LogEntry) -> None:
        with self.Session() as session:
            db_log_entry = LogEntryModel(
                timestamp=log_entry.timestamp,
                severity=log_entry.severity,
                message=log_entry.message,
                trace_id=str(log_entry.trace_id),
                command_info=log_entry.command_info.model_dump() if log_entry.command_info else None
            )
            session.add(db_log_entry)
            session.commit()

    def get_logs(self, filters: LogsFilter, paging: Paging) -> List[LogEntry]:
        with self.Session() as session:
            query = session.query(LogEntryModel)

            if filters.trace_id:
                query = query.filter(LogEntryModel.trace_id == filters.trace_id)

            if filters.commands_only:
                query = query.filter(LogEntryModel.command_info.isnot(None))

            query = query.filter(LogEntryModel.severity.in_([s.value for s in filters.severity]))

            query = query.order_by(LogEntryModel.timestamp.desc())
            query = query.limit(paging.page_size).offset((paging.page - 1) * paging.page_size)

            results = query.all()

            return [LogEntry(
                entry_id=result.id,
                timestamp=result.timestamp,
                severity=result.severity,
                message=result.message,
                trace_id=result.trace_id,
                command_info=CommandInfo.model_validate(result.command_info) if result.command_info else None
            ) for result in results]

    def get_log_entry(self, log_id: int) -> Optional[LogEntry]:
        with self.Session() as session:
            result = session.query(LogEntryModel).filter(LogEntryModel.id == log_id).first()
            if result:
                return LogEntry(
                    entry_id=result.id,
                    timestamp=result.timestamp,
                    severity=result.severity,
                    message=result.message,
                    trace_id=result.trace_id,
                    command_info=CommandInfo.model_validate(result.command_info) if result.command_info else None
                )
            return None

    def get_next_entry_id(self) -> int:
        with self.Session() as session:
            # TODO: test in real postgres
            return session.execute(Sequence('log_entry_id_seq')).scalar()
