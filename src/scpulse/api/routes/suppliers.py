from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Sequence, Any

from src.scpulse.storage.postgres import get_session
from src.scpulse.storage.models.entities import Supplier, Sku
from src.scpulse.api.schemas.schemas import SupplierOut, SkuOut

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/", response_model=List[SupplierOut])
def list_suppliers(
    db: Session = Depends(get_session),
) -> Sequence[Supplier] | Any:
    return db.execute(select(Supplier)).scalars().all()


@router.get("/skus", response_model=List[SkuOut])
def list_skus(db: Session = Depends(get_session)) -> Sequence[Sku] | Any:
    return db.execute(select(Sku)).scalars().all()
