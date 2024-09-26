from typing import List

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
