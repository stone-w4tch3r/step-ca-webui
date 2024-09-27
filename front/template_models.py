from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class CertificateData(BaseModel):
    id: str
    name: str
    status: str
    actions: List[str]


class LogData(BaseModel):
    entry_id: str
    timestamp: str
    severity: str
    trace_id: str


class LogFilterData(BaseModel):
    commands_only: bool = False
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    keywords: Optional[str] = None
    severity: List[str] = ["INFO", "WARN", "DEBUG", "ERROR"]
