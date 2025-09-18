from datetime import date, datetime
from pydantic import BaseModel


# ========== ORDERS ==========
class OrderCreatedOut(BaseModel):
    id: int
    day: date
    supplier_id: int
    total_orders: int
    total_qty: int
    created_at: datetime

    class Config:
        orm_mode = True


class OrderDelayedOut(BaseModel):
    id: int
    day: date
    supplier_id: int
    delayed_orders: int
    avg_delay_days: float
    created_at: datetime

    class Config:
        orm_mode = True


# ========== INVENTORY ==========
class InventoryAlertOut(BaseModel):
    id: int
    day: date
    sku_id: int
    low_stock_alerts: int
    min_threshold: int
    created_at: datetime

    class Config:
        orm_mode = True


# ========== SUPPLIER / SKU ==========
class SupplierOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class SkuOut(BaseModel):
    id: int
    sku_code: str

    class Config:
        orm_mode = True
