from fastapi import FastAPI

from src.core.database import init_db
from src.home.router import router as home_router

app = FastAPI(title="Yuvabe App API")

app.include_router(home_router, prefix="/home", tags=["Home"])

init_db()


@app.get("/")
def root():
    return {"message": "API is running fine!"}
