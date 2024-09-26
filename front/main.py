from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from front.template_models import CertificateData, LogData

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    certificates = [
        CertificateData(id="123", name="cert1", status="active", actions=["View", "Renew"]),
        CertificateData(id="123", name="cert1", status="active", actions=["View", "Renew"]),
        CertificateData(id="123", name="cert1", status="active", actions=["View", "Renew"]),
    ]
    return templates.TemplateResponse("dashboard.html.j2", {"request": request, "certificates": certificates})


@app.get("/logs", response_class=HTMLResponse)
async def read_logs(request: Request):
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
    return templates.TemplateResponse("logs.html.j2", {"request": request, "logs": logs})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
