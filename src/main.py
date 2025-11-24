from fastapi import FastAPI

import os
from src.auth.router import router as auth_router
from src.chatbot.router import router as chatbot
from src.core.database import init_db
from src.home.router import router as home_router
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Yuvabe App API")


app.include_router(home_router, prefix="/home", tags=["Home"])

# init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")

app.mount("/static/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
print("Serving audio from:", AUDIO_DIR)

app.include_router(auth_router)

app.include_router(chatbot)


@app.get("/")
def root():
    return {"message": "API is running fine!"}
