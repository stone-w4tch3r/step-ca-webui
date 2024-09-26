from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="front/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="front/templates")

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    # Dummy data for certificates
    certificates = [
        {"id": "1", "name": "Cert 1", "status": "Active", "actions": ["Renew", "Revoke"]},
        {"id": "2", "name": "Cert 2", "status": "Expired", "actions": ["Renew"]},
    ]
    return templates.TemplateResponse("dashboard.html.j2", {"request": request, "certificates": certificates})

@app.get("/logs", response_class=HTMLResponse)
async def read_logs(request: Request):
    # Dummy data for logs
    logs = [
        {"entry_id": "1", "timestamp": "2023-07-01 10:00:00", "severity": "INFO", "trace_id": "abc123", "message": "Certificate generated"},
        {"entry_id": "2", "timestamp": "2023-07-01 11:00:00", "severity": "WARN", "trace_id": "def456", "message": "Certificate expiring soon"},
    ]
    return templates.TemplateResponse("logs.html.j2", {"request": request, "logs": logs})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
