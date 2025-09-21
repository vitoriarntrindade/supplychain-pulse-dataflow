from __future__ import annotations

from datetime import date
from typing import Iterable, Any, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .models import (
    Supplier,
    Sku,
    OrdersCreatedDaily,
    OrdersDelayedDaily,
    InventoryAlertsDaily,
)


# -----------------------------
# Helpers de dimensão (upsert)
# -----------------------------
def _ensure_supplier(db: Session, name: str) -> int:
    # tenta rápido no cache/DB
    sup = db.execute(
        select(Supplier).where(Supplier.name == name)
    ).scalar_one_or_none()
    if sup:
        return int(sup.id)

    stmt = (
        insert(Supplier)
        .values(name=name)
        .on_conflict_do_update(
            index_elements=[Supplier.name],
            set_={"name": name},
        )
        .returning(Supplier.id)
    )
    return int(db.execute(stmt).scalar_one())


def _ensure_sku(db: Session, sku_code: str) -> int:
    sku = db.execute(
        select(Sku).where(Sku.sku_code == sku_code)
    ).scalar_one_or_none()
    if sku:
        return int(sku.id)

    stmt = (
        insert(Sku)
        .values(sku_code=sku_code)
        .on_conflict_do_update(
            index_elements=[Sku.sku_code],
            set_={"sku_code": sku_code},
        )
        .returning(Sku.id)
    )
    return int(db.execute(stmt).scalar_one())


# -------------------------------------------
# Save: gold_orders_created.parquet (agregado)
# Espera rows com: supplier, date, total_orders, total_qty
# -------------------------------------------
def save_orders_created(db: Session, rows: Iterable[dict]) -> None:
    for r in rows:
        supplier_name = r.get("supplier")
        day_value = r.get("date")
        total_orders = int(r.get("total_orders", 0) or 0)
        total_qty = int(r.get("total_qty", 0) or 0)

        if supplier_name is None or day_value is None:
            continue

        # day_value pode ser date, datetime ou str YYYY-MM-DD
        if isinstance(day_value, str):
            day_value = date.fromisoformat(day_value)

        supplier_id = _ensure_supplier(db, supplier_name)

        stmt = (
            insert(OrdersCreatedDaily)
            .values(
                day=day_value,
                supplier_id=supplier_id,
                total_orders=total_orders,
                total_qty=total_qty,
            )
            .on_conflict_do_update(
                constraint="uq_ocd_day_supplier",
                set_={
                    "total_orders": total_orders,
                    "total_qty": total_qty,
                },
            )
            .returning(OrdersCreatedDaily.id)
        )
        result = db.execute(stmt)
        inserted_id = result.scalar_one_or_none()
        print(f"[DEBUG] ✅ Inserido/Atualizado com id = {inserted_id}")


# -------------------------------------------
# Save: gold_orders_delayed.parquet (agregado)
# Espera rows com: supplier, delayed_orders, avg_delay_days
# Usa snapshot do dia atual (ou ajuste se fornecer "date")
# -------------------------------------------
def save_orders_delayed(db: Session, rows: Iterable[dict]) -> None:
    for r in rows:
        supplier_name = r.get("supplier")
        delayed_orders = int(r.get("delayed_orders", 0) or 0)
        avg_delay_days = float(r.get("avg_delay_days", 0.0) or 0.0)
        # Permite opcionalmente passar 'date' no agregado de delays; caso contrário, usa hoje
        day_value = r.get("date")
        if isinstance(day_value, str):
            day_value = date.fromisoformat(day_value)
        if day_value is None:
            day_value = date.today()

        if supplier_name is None:
            continue

        supplier_id = _ensure_supplier(db, supplier_name)

        stmt = (
            insert(OrdersDelayedDaily)
            .values(
                day=day_value,
                supplier_id=supplier_id,
                delayed_orders=delayed_orders,
                avg_delay_days=avg_delay_days,
            )
            .on_conflict_do_update(
                constraint="uq_odd_day_supplier",
                set_={
                    "delayed_orders": delayed_orders,
                    "avg_delay_days": avg_delay_days,
                },
            )
        )
        db.execute(stmt)


# -------------------------------------------
# Save: gold_inventory_alerts.parquet (agregado)
# Espera rows com: sku, low_stock_alerts, min_threshold
# Usa snapshot do dia atual (ou ajuste se fornecer "date")
# -------------------------------------------
def save_inventory_alerts(db: Session, rows: Iterable[dict]) -> None:
    for r in rows:
        sku_code = r.get("sku")
        low_stock_alerts = int(r.get("low_stock_alerts", 0) or 0)
        min_threshold = int(r.get("min_threshold", 0) or 0)
        day_value = r.get("date")
        if isinstance(day_value, str):
            day_value = date.fromisoformat(day_value)
        if day_value is None:
            day_value = date.today()

        if sku_code is None:
            continue

        sku_id = _ensure_sku(db, sku_code)

        stmt = (
            insert(InventoryAlertsDaily)
            .values(
                day=day_value,
                sku_id=sku_id,
                low_stock_alerts=low_stock_alerts,
                min_threshold=min_threshold,
            )
            .on_conflict_do_update(
                constraint="uq_iad_day_sku",
                set_={
                    "low_stock_alerts": low_stock_alerts,
                    "min_threshold": min_threshold,
                },
            )
        )
        db.execute(stmt)


# -------------------------------------------
# GET: Orders Created
# -------------------------------------------
def get_orders_created(
    db: Session,
    supplier: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> Sequence[OrdersCreatedDaily] | Any:
    stmt = select(OrdersCreatedDaily).join(Supplier)
    if supplier:
        stmt = stmt.where(Supplier.name == supplier)
    if start:
        stmt = stmt.where(OrdersCreatedDaily.day >= start)
    if end:
        stmt = stmt.where(OrdersCreatedDaily.day <= end)
    stmt = stmt.order_by(OrdersCreatedDaily.day.desc())
    return db.scalars(stmt).all()


# -------------------------------------------
# GET: Orders Delayed
# -------------------------------------------
def get_orders_delayed(
    db: Session,
    supplier: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> Sequence[OrdersDelayedDaily] | Any:
    stmt = select(OrdersDelayedDaily).join(Supplier)
    if supplier:
        stmt = stmt.where(Supplier.name == supplier)
    if start:
        stmt = stmt.where(OrdersDelayedDaily.day >= start)
    if end:
        stmt = stmt.where(OrdersDelayedDaily.day <= end)
    stmt = stmt.order_by(OrdersDelayedDaily.day.desc())
    return db.scalars(stmt).all()


# -------------------------------------------
# GET: Inventory Alerts
# -------------------------------------------
def get_inventory_alerts(
    db: Session,
    sku: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> Sequence[InventoryAlertsDaily] | Any:
    stmt = select(InventoryAlertsDaily).join(Sku)
    if sku:
        stmt = stmt.where(Sku.sku_code == sku)
    if start:
        stmt = stmt.where(InventoryAlertsDaily.day >= start)
    if end:
        stmt = stmt.where(InventoryAlertsDaily.day <= end)
    stmt = stmt.order_by(InventoryAlertsDaily.day.desc())
    return db.scalars(stmt).all()
