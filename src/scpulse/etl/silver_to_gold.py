from pathlib import Path
import polars as pl
from ..storage import crud
from ..storage.postgres import SessionLocal


def silver_to_gold(input_path: Path, output_dir: Path) -> None:
    """
    Converte dados da camada Silver para a camada Gold, gerando métricas
    agregadas por tipo de evento (pedidos criados, atrasados e alertas).
    """

    print(f"[SILVER→GOLD] Lendo arquivo Silver: {input_path}")
    df = pl.read_parquet(input_path)
    print(f"[SILVER→GOLD] {df.shape[0]} linhas carregadas do Silver")

    # 🔹 Converte colunas obrigatórias
    if "timestamp" in df.columns and df["timestamp"].dtype == pl.Utf8:
        print("[SILVER→GOLD] Convertendo coluna timestamp para datetime UTC")
        df = df.with_columns(
            pl.col("timestamp")
            .str.strptime(
                pl.Datetime("ns"),
                format="%Y-%m-%dT%H:%M:%S%z",
                strict=False,
            )
            .dt.convert_time_zone("UTC")
        )

    # 🔹 Converte colunas de entrega se existirem
    if {"old_delivery", "new_delivery"}.issubset(df.columns):
        print("[SILVER→GOLD] Convertendo colunas old_delivery/new_delivery")
        df = df.with_columns(
            [
                pl.col("old_delivery")
                .str.strptime(
                    pl.Datetime("ns"), "%Y-%m-%dT%H:%M:%S%z", strict=False
                )
                .dt.convert_time_zone("UTC"),
                pl.col("new_delivery")
                .str.strptime(
                    pl.Datetime("ns"), "%Y-%m-%dT%H:%M:%S%z", strict=False
                )
                .dt.convert_time_zone("UTC"),
            ]
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Abre sessão do banco
    db = SessionLocal()

    try:
        # --- Orders Created ---
        if "supplier" in df.columns and "qty" in df.columns:
            orders_created = (
                df.filter(pl.col("event_type") == "order_created")
                .group_by(
                    pl.col("supplier"),
                    pl.col("timestamp").dt.date().alias("date"),
                )
                .agg(
                    total_orders=pl.count(),
                    total_qty=pl.col("qty").sum(),
                )
            )
            print(f"[ORDERS_CREATED] {orders_created.shape[0]} linhas geradas")
            orders_created.write_parquet(
                output_dir / "gold_orders_created.parquet",
                compression="snappy",
            )
            print("[ORDERS_CREATED] Gravando no banco...")
            crud.save_orders_created(db, orders_created.to_dicts())

        # --- Orders Delayed ---
        if {"supplier", "old_delivery", "new_delivery"}.issubset(df.columns):
            orders_delayed = (
                df.filter(pl.col("event_type") == "order_delayed")
                .with_columns(
                    (pl.col("new_delivery") - pl.col("old_delivery"))
                    .dt.total_days()
                    .alias("delay_days")
                )
                .group_by("supplier")
                .agg(
                    delayed_orders=pl.count(),
                    avg_delay_days=pl.col("delay_days").mean(),
                )
            )
            print(f"[ORDERS_DELAYED] {orders_delayed.shape[0]} linhas geradas")
            orders_delayed.write_parquet(
                output_dir / "gold_orders_delayed.parquet",
                compression="snappy",
            )
            print("[ORDERS_DELAYED] Gravando no banco...")
            crud.save_orders_delayed(db, orders_delayed.to_dicts())

        # --- Inventory Alerts ---
        if {"sku", "threshold"}.issubset(df.columns):
            inventory_alerts = (
                df.filter(pl.col("event_type") == "inventory_low")
                .group_by("sku")
                .agg(
                    low_stock_alerts=pl.count(),
                    min_threshold=pl.col("threshold").min(),
                )
            )
            print(
                f"[INVENTORY_ALERTS] {inventory_alerts.shape[0]} linhas geradas"
            )
            inventory_alerts.write_parquet(
                output_dir / "gold_inventory_alerts.parquet",
                compression="snappy",
            )
            print("[INVENTORY_ALERTS] Gravando no banco...")
            crud.save_inventory_alerts(db, inventory_alerts.to_dicts())

        db.commit()
        print("[DB] Commit realizado com sucesso ✅")

    except Exception as e:
        print(f"[DB ERROR] Falha ao persistir no banco: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    print(f"[GOLD] Wrote metrics → {output_dir}")
