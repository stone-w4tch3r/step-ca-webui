from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import date

from front.template_models import CertificateData, LogData, LogFilterData

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    certificates = [
        CertificateData(id="123", name="cert1", status="active", actions=["View", "Renew"]),
        CertificateData(id="456", name="cert2", status="expired", actions=["View", "Renew"]),
        CertificateData(id="789", name="cert3", status="active", actions=["View", "Renew"]),
    ]
    return templates.TemplateResponse("dashboard.html.j2", {"request": request, "certificates": certificates})


@app.get("/logs", response_class=HTMLResponse)
async def read_logs(
    request: Request,
    commands_only: bool = Query(False),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    keywords: Optional[str] = Query(None),
    severity: List[str] = Query(["INFO", "WARN", "DEBUG", "ERROR"])
):
    filter_data = LogFilterData(
        commands_only=commands_only,
        date_from=date_from,
        date_to=date_to,
        keywords=keywords,
        severity=severity
    )
    
    # Here you would typically use the filter_data to query your logs
    # For now, we'll just use the sample logs
    logs = [
        LogData(
            entry_id="1ab2",
            timestamp="05.06.2023 12:00:00",
            message="Test message",
            severity="DEBUG",
            trace_id="222"
        ),
        LogData(
            entry_id="2cc",
            timestamp="05.01.2022 14:02:00",
            message="Test message",
            severity="INFO",
            trace_id="111"
        ),
    ]
    return templates.TemplateResponse("logs.html.j2", {"request": request, "logs": logs, "filter_data": filter_data})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
