from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import ObligationResponse, ObligationRequest, ObligationFullResponse

from app.dependency import get_db
from app.service import obligations as obligations_service

router = APIRouter()

@router.post("/obligations/", response_model=ObligationFullResponse)
def add_obligation(obligation: ObligationRequest, db: Session = Depends(get_db)):
    return obligations_service.add_obligation(db, obligation)

