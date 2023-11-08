import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as v1_router

from app.api.v1.setting.event import create_start_app_handler, create_stop_app_handler
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

load_dotenv('.env')
app = FastAPI(
    title=os.getenv("PROJECT_NAME", "NOTIFICATION"),
    debug=bool(os.getenv("DEBUG", True)),
    version=os.getenv("VERSION"),
    docs_url="/docs",
    openapi_url="/openapi.json" if bool(os.getenv("DEBUG", True)) else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory=r"D:\test\Notification-system\app\templates")


@app.get("/", response_class=HTMLResponse)
async def maintenance_notice(request: Request):
    print("vaof ")
    return templates.TemplateResponse("noti.html", {"request": request})

app.add_event_handler("startup", create_start_app_handler(app))
app.add_event_handler("shutdown", create_stop_app_handler(app))

app.include_router(router=v1_router.router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run('app.main:app', host="127.0.0.1", port=7111, reload=True)
