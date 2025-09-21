"""Models do banco (tabelas Gold)."""

from sqlalchemy import (
    Integer,
    Date,
    Text,
    BigInteger,
    ForeignKey,
    TIMESTAMP,
    UniqueConstraint,
    Index,
    Numeric,
)
from src.scpulse.storage.postgres import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    orders_created_daily: Mapped[list["OrdersCreatedDaily"]] = relationship(
        back_populates="supplier"
    )
    orders_delayed_daily: Mapped[list["OrdersDelayedDaily"]] = relationship(
        back_populates="supplier"
    )


class Sku(Base):
    __tablename__ = "skus"
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    sku_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    inventory_alerts_daily: Mapped[list["InventoryAlertsDaily"]] = (
        relationship(back_populates="sku")
    )


# =======================
# Fatos agregados (Gold)
# =======================
class OrdersCreatedDaily(Base):
    __tablename__ = "orders_created_daily"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    day: Mapped[object] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    total_orders: Mapped[int] = mapped_column(Integer, nullable=False)
    total_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )

    supplier: Mapped[Supplier] = relationship(
        back_populates="orders_created_daily"
    )

    __table_args__ = (
        UniqueConstraint("day", "supplier_id", name="uq_ocd_day_supplier"),
        Index("idx_ocd_day", day.desc()),
        Index("idx_ocd_supplier", supplier_id),
    )


class OrdersDelayedDaily(Base):
    __tablename__ = "orders_delayed_daily"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    day: Mapped[object] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    delayed_orders: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_delay_days: Mapped[object] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )

    supplier: Mapped[Supplier] = relationship(
        back_populates="orders_delayed_daily"
    )

    __table_args__ = (
        UniqueConstraint("day", "supplier_id", name="uq_odd_day_supplier"),
        Index("idx_odd_day", day.desc()),
        Index("idx_odd_supplier", supplier_id),
    )


class InventoryAlertsDaily(Base):
    __tablename__ = "inventory_alerts_daily"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    day: Mapped[object] = mapped_column(Date, nullable=False)
    sku_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False
    )
    low_stock_alerts: Mapped[int] = mapped_column(Integer, nullable=False)
    min_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default="now()"
    )

    sku: Mapped[Sku] = relationship(back_populates="inventory_alerts_daily")

    __table_args__ = (
        UniqueConstraint("day", "sku_id", name="uq_iad_day_sku"),
        Index("idx_iad_day", day.desc()),
        Index("idx_iad_sku", sku_id),
    )
