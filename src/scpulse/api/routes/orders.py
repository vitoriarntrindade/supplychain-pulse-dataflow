from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional, List, Sequence

from src.scpulse.storage.models.entities import (
    OrdersDelayedDaily,
    OrdersCreatedDaily,
)
from src.scpulse.storage.postgres import get_session
from src.scpulse.storage import crud
from src.scpulse.api.schemas.schemas import OrderCreatedOut, OrderDelayedOut
from sqlalchemy.orm import Session

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/created", response_model=List[OrderCreatedOut])
def list_orders_created(
    supplier: Optional[str] = Query(
        None, description="Filtrar por fornecedor"
    ),
    start: Optional[date] = Query(None, description="Data inicial"),
    end: Optional[date] = Query(None, description="Data final"),
    db: Session = Depends(get_session),
) -> Sequence[OrdersCreatedDaily]:
    return crud.get_orders_created(db, supplier=supplier, start=start, end=end)


@router.get("/delayed", response_model=List[OrderDelayedOut])
def list_orders_delayed(
    supplier: Optional[str] = Query(
        None, description="Filtrar por fornecedor"
    ),
    start: Optional[date] = Query(None, description="Data inicial"),
    end: Optional[date] = Query(None, description="Data final"),
    db: Session = Depends(get_session),
) -> Sequence[OrdersDelayedDaily]:
    return crud.get_orders_delayed(db, supplier=supplier, start=start, end=end)
