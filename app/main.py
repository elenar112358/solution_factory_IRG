from fastapi import FastAPI

from app.api.v1.obligations import router as obligations_router

app = FastAPI()

app.include_router(obligations_router, prefix="/api/v1", tags=["obligations"])
