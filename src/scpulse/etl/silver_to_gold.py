from pathlib import Path
import polars as pl


def silver_to_gold(input_path: Path, output_dir: Path) -> None:
    """
    Converte dados da camada Silver para a camada Gold, gerando métricas agregadas
    por tipo de evento (pedidos criados, pedidos atrasados e alertas de estoque).

    A função lê o arquivo Parquet da camada Silver, aplica transformações e validações
    específicas de negócio e grava os resultados em múltiplos arquivos Parquet na
    camada Gold.

    Args:
        input_path (Path):
            Caminho para o arquivo Parquet Silver contendo os eventos normalizados.
        output_dir (Path):
            Diretório de saída onde os arquivos Parquet da camada Gold serão gravados.
            Serão criados:
              - `gold_orders_created.parquet`
              - `gold_orders_delayed.parquet`
              - `gold_inventory_alerts.parquet`

    Raises:
        FileNotFoundError:
            Se o arquivo Silver não existir no caminho informado.
        polars.exceptions.ComputeError:
            Se ocorrer falha ao processar datas ou colunas obrigatórias estiverem ausentes.

    Example:
        >>> from pathlib import Path
        >>> silver_path = Path("data/silver/silver_events_2025-09-17.parquet")
        >>> gold_dir = Path("data/gold/events_2025-09-17")
        >>> silver_to_gold(silver_path, gold_dir)
        [GOLD] Wrote metrics → data/gold/events_2025-09-17

    Notes:
        - Datas são parseadas no formato ISO 8601 e convertidas para UTC.
        - O cálculo de `delay_days` é baseado na diferença entre `new_delivery` e
          `old_delivery`.
        - A função assume que colunas `supplier`, `sku`, `qty`, `threshold`,
          `old_delivery` e `new_delivery` podem estar presentes dependendo do tipo de evento.
    """

    df = pl.read_parquet(input_path)

    # 🔹 Converte colunas obrigatórias
    if "timestamp" in df.columns:
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
        df = df.with_columns(
            [
                pl.col("old_delivery")
                .str.strptime(
                    pl.Datetime("ns"),
                    format="%Y-%m-%dT%H:%M:%S%z",
                    strict=False,
                )
                .dt.convert_time_zone("UTC"),
                pl.col("new_delivery")
                .str.strptime(
                    pl.Datetime("ns"),
                    format="%Y-%m-%dT%H:%M:%S%z",
                    strict=False,
                )
                .dt.convert_time_zone("UTC"),
            ]
        )

    output_dir.mkdir(parents=True, exist_ok=True)

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
        orders_created.write_parquet(
            output_dir / "gold_orders_created.parquet", compression="snappy"
        )

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
        orders_delayed.write_parquet(
            output_dir / "gold_orders_delayed.parquet", compression="snappy"
        )

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
        inventory_alerts.write_parquet(
            output_dir / "gold_inventory_alerts.parquet", compression="snappy"
        )

    print(f"[GOLD] Wrote metrics → {output_dir}")
