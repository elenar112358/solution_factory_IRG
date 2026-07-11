from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas import (
    ObligationSingleResponse,
    ObligationRequest,
    ObligationResponse,
    ObligationParamsQuery,
    DaysQuery,
    ObligationUpcomingResponse,
    PaymentResponse,
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
def get_obligations(
        query_params: ObligationParamsQuery = Depends(),
        db: Session = Depends(get_db)
):
    return obligations_service.get_obligations(db, query_params)

@router.get("/obligations/upcoming/", response_model=ObligationUpcomingResponse)
def get_upcoming_obligations(
        query_days: DaysQuery = Depends(),
        db: Session = Depends(get_db)
):
    return obligations_service.get_upcoming_obligations(db, query_days)

@router.post("/obligations/{id}/pay", response_model=PaymentResponse)
def add_payment(
        id: UUID,
        db: Session = Depends(get_db)
):
    return obligations_service.add_payment(db, id)

@router.patch("/obligations/{id}/cancel", response_model=ObligationSingleResponse)
def cancel_obligation(
        id: UUID,
        db: Session = Depends(get_db)
):
    return obligations_service.cancel_obligation(db, id)

