from datetime import date
from typing import List, Optional, Literal, Union

from fastapi import FastAPI, Request, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from api_client import APIClient

API_BASE_URL = "http://localhost:5000"
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


async def get_api_client():
    client = APIClient(API_BASE_URL)
    try:
        yield client
    finally:
        await client.close()


class LogFilterTemplateData(BaseModel):
    commands_only: bool = False
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    keywords: Optional[str] = None
    severity: List[str] = ["INFO", "WARN", "DEBUG", "ERROR"]


class CertificateTemplateData(BaseModel):
    id: str
    name: str
    status: str
    actions: List[str]


class LogTemplateData(BaseModel):
    entry_id: str
    timestamp: str
    severity: str
    trace_id: str


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(
    request: Request, api_client: APIClient = Depends(get_api_client)
):
    certificates = [
        CertificateTemplateData(
            id=cert.id,
            name=cert.name,
            status=cert.status,
            actions=["renew", "revoke", "download"],
        )
        for cert in (await api_client.list_certificates())
    ]

    return templates.TemplateResponse(
        "dashboard.html.j2", {"request": request, "certificates": certificates}
    )


@app.get("/logs", response_class=HTMLResponse)
async def read_logs(
    request: Request,
    commands_only: bool = Query(False),
    date_from: Union[date, Literal[""], None] = Query(None),
    date_to: Union[date, Literal[""], None] = Query(None),
    keywords: Optional[str] = Query(None),
    severity: List[str] = Query(["INFO", "WARN", "DEBUG", "ERROR"]),
    api_client: APIClient = Depends(get_api_client),
):
    filter_data = LogFilterTemplateData(
        commands_only=commands_only,
        date_from=date_from if date_from != "" else None,
        date_to=date_to if date_to != "" else None,
        keywords=keywords,
        severity=severity,
    )
    logs = [
        LogTemplateData(
            entry_id=str(log.entryId),
            timestamp=log.timestamptz.isoformat(),
            severity=log.severity.name,
            trace_id=str(log.traceId),
        )
        for log in (
            await api_client.get_logs(
                commands_only=filter_data.commands_only, severity=filter_data.severity
            )
        )
    ]

    return templates.TemplateResponse(
        "logs.html.j2",
        {"request": request, "logs": logs, "filter_data": filter_data},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
