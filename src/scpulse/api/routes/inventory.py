from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional, Sequence

from src.scpulse.storage.models import InventoryAlertsDaily
from src.scpulse.storage.postgres import get_db
from src.scpulse.storage import crud
from src.scpulse.api.schemas import InventoryAlertOut

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/alerts", response_model=List[InventoryAlertOut])
def get_inventory_alerts(
    sku: Optional[str] = Query(None),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    db: Session = Depends(get_db),
) -> Sequence[InventoryAlertsDaily]:
    return crud.get_inventory_alerts(db, sku=sku, start=start, end=end)
