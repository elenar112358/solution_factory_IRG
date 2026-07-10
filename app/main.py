from fastapi import FastAPI

from app.api.v1.obligations import router as obligations_router
# from app.api.v1.operations import router as operations_router
# from app.api.v1.users import router as users_router

app = FastAPI()

app.include_router(obligations_router, prefix="/api/v1", tags=["obligations"])
# app.include_router(operations_router, prefix="/api/v1", tags=["operations"])
# app.include_router(users_router, prefix="/api/v1", tags=["users"])
