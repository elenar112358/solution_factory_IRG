from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.event_manager import broadcaster
import json

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

@router.post(
    "/obligations/",
    response_model=ObligationResponse,
    summary="Добавить новое обязательство"
)
def add_obligation(
        obligation: ObligationRequest,
        db: Session = Depends(get_db)
):
    return obligations_service.add_obligation(db, obligation)

@router.get(
    "/obligations/",
    response_model=list[ObligationSingleResponse],
    summary="Получить список обязательств по параметрам"
)
def get_obligations(
        query_params: ObligationParamsQuery = Depends(),
        db: Session = Depends(get_db)
):
    return obligations_service.get_obligations(db, query_params)

@router.get(
    "/obligations/upcoming/",
    response_model=ObligationUpcomingResponse,
    summary="Получить предстоящие платежи из диапазона [today, today + N days]"
)
def get_upcoming_obligations(
        query_days: DaysQuery = Depends(),
        db: Session = Depends(get_db)
):
    return obligations_service.get_upcoming_obligations(db, query_days)

@router.post(
    "/obligations/{id}/pay",
    response_model=PaymentResponse,
    tags=["Платежи"],
    summary="Оплатить обязательство по id"
)
def add_payment(
        id: UUID,
        db: Session = Depends(get_db)
):
    return obligations_service.add_payment(db, id)

@router.patch(
    "/obligations/{id}/cancel",
    response_model=ObligationSingleResponse,
    summary="Отменить обязательство по id"
)
def cancel_obligation(
        id: UUID,
        db: Session = Depends(get_db)
):
    return obligations_service.cancel_obligation(db, id)

@router.delete(
    "/obligations/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить обязательство по id"
)
def delete_obligation(
        id: UUID,
        db: Session = Depends(get_db)
) -> None:
    obligations_service.delete_obligation(db, id)

@router.get("/events", summary="SSE трансляция")
async def events():
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                event = await queue.get()

                yield (
                    f"event: {event['type']}\n"
                    f"data: {json.dumps(event)}\n\n"
                )
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
