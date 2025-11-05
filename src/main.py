from fastapi import FastAPI

from src.home.router import router as home_router

app = FastAPI(title="Yuvabe App API")

app.include_router(home_router, prefix="/home", tags=["Home"])


@app.get("/")
def root():
    return {"message": "API is running fine!"}
