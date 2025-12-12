from src.wellbeing.router import router as wellbeing
from fastapi import FastAPI

import os
from src.auth.router import router as auth_router
from src.chatbot.router import router as chatbot_router
from src.core.database import init_db
from src.home.router import router as home_router
from src.notifications.router import router as notifications_router
from src.payslip.router import router as payslip_router
from src.profile.router import router as profile
from src.journaling.router import router as journal
from src.core.router import router as app_config
from fastapi.staticfiles import StaticFiles



app = FastAPI(title="Yuvabe App API")


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(home_router, prefix="/home", tags=["Home"])

app.include_router(app_config)

app.include_router(profile)

app.include_router(auth_router)

app.include_router(chatbot_router)

app.include_router(wellbeing)

app.include_router(notifications_router)

app.include_router(payslip_router)

app.include_router(journal)


@app.get("/")
def root():
    return {"message": "API is running fine!!!"}
