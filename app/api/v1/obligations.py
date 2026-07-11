from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import (
    ObligationSingleResponse,
    ObligationRequest,
    ObligationResponse,
    ObligationQuery,
)

from app.dependency import get_db
from app.service import obligations as obligations_service

router = APIRouter()

@router.post("/obligations/", response_model=ObligationResponse)
def add_obligation(
        obligation: ObligationRequest,
        db: Session = Depends(get_db)
):
    return obligations_service.add_obligation(db, obligation)

@router.get("/obligations/", response_model=list[ObligationSingleResponse])
def get_obligation(
        query_params: ObligationQuery = Depends(),
        db: Session = Depends(get_db)
):
    return obligations_service.get_obligations(db, query_params)