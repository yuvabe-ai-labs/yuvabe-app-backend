# from src.profile.router import router as profile
from fastapi import FastAPI


from src.auth.router import router as auth_router
from src.chatbot.router import router as chatbot
from src.core.database import init_db
from src.home.router import router as home_router

# from src.profile.router import router as profile

app = FastAPI(title="Yuvabe App API")

app.include_router(home_router, prefix="/home", tags=["Home"])

init_db()

app.include_router(auth_router)

# app.include_router(profile)

app.include_router(chatbot)


@app.get("/")
def root():
    return {"message": "API is running fine!"}
