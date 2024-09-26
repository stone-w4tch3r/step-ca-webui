from typing import List

from pydantic import BaseModel


class CertificateActionData(BaseModel):
    Id: str
    Name: str
    Status: str
    Actions: List[str]


class DashboardTemplateData(BaseModel):
    Certificates: List[CertificateActionData]


class LogData(BaseModel):
    entry_id: str
    timestamp: str
    severity: str
    trace_id: str


class LogsTemplateData(BaseModel):
    Logs: List[LogData]
