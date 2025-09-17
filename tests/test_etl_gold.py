import polars as pl
from pathlib import Path
from scpulse.etl.silver_to_gold import silver_to_gold


def make_silver_file(
    tmp_path: Path,
    rows: list[dict[str, object]],
    filename: str = "silver.parquet",
) -> Path:
    """Helper para criar arquivo Parquet Silver."""
    df: pl.DataFrame = pl.DataFrame(rows)  # tipo explícito
    path: Path = tmp_path / filename
    df.write_parquet(path)
    return path


def test_gold_generates_expected_files(tmp_path: Path) -> None:
    input_path: Path = make_silver_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "supplier": "Fornecedor_A",
                "timestamp": "2025-09-17T10:00:00+00:00",
                "qty": 100,
            },
            {
                "event_id": "EVT-2",
                "event_type": "order_delayed",
                "supplier": "Fornecedor_B",
                "timestamp": "2025-09-17T12:00:00+00:00",
                "old_delivery": "2025-09-20T10:00:00+00:00",
                "new_delivery": "2025-09-23T10:00:00+00:00",
            },
            {
                "event_id": "EVT-3",
                "event_type": "inventory_low",
                "sku": "SKU123",
                "timestamp": "2025-09-17T15:00:00+00:00",
                "threshold": 10,
            },
        ],
    )

    output_dir: Path = tmp_path / "gold"
    silver_to_gold(input_path, output_dir)

    expected_files: list[str] = [
        "gold_orders_created.parquet",
        "gold_orders_delayed.parquet",
        "gold_inventory_alerts.parquet",
    ]
    for f in expected_files:
        assert (output_dir / f).exists()


def test_gold_orders_created_metrics(tmp_path: Path) -> None:
    input_path: Path = make_silver_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "supplier": "Fornecedor_A",
                "timestamp": "2025-09-17T10:00:00+00:00",
                "qty": 50,
            },
            {
                "event_id": "EVT-2",
                "event_type": "order_created",
                "supplier": "Fornecedor_A",
                "timestamp": "2025-09-17T11:00:00+00:00",
                "qty": 70,
            },
        ],
    )

    output_dir: Path = tmp_path / "gold"
    silver_to_gold(input_path, output_dir)

    df: pl.DataFrame = pl.read_parquet(
        output_dir / "gold_orders_created.parquet"
    )
    assert df["total_orders"].sum() == 2
    assert df["total_qty"].sum() == 120


def test_gold_orders_delayed_metrics(tmp_path: Path) -> None:
    input_path: Path = make_silver_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_delayed",
                "supplier": "Fornecedor_B",
                "timestamp": "2025-09-17T10:00:00+00:00",
                "old_delivery": "2025-09-20T10:00:00+00:00",
                "new_delivery": "2025-09-23T10:00:00+00:00",
            },
            {
                "event_id": "EVT-2",
                "event_type": "order_delayed",
                "supplier": "Fornecedor_B",
                "timestamp": "2025-09-18T10:00:00+00:00",
                "old_delivery": "2025-09-22T10:00:00+00:00",
                "new_delivery": "2025-09-24T10:00:00+00:00",
            },
        ],
    )

    output_dir: Path = tmp_path / "gold"
    silver_to_gold(input_path, output_dir)

    df: pl.DataFrame = pl.read_parquet(
        output_dir / "gold_orders_delayed.parquet"
    )
    assert df["delayed_orders"].sum() == 2
    # (3 dias + 2 dias) / 2 = 2.5
    assert abs(df["avg_delay_days"][0] - 2.5) < 0.01


def test_gold_inventory_alerts_metrics(tmp_path: Path) -> None:
    input_path: Path = make_silver_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "inventory_low",
                "sku": "SKU123",
                "timestamp": "2025-09-17T10:00:00+00:00",
                "threshold": 5,
            },
            {
                "event_id": "EVT-2",
                "event_type": "inventory_low",
                "sku": "SKU123",
                "timestamp": "2025-09-17T11:00:00+00:00",
                "threshold": 3,
            },
        ],
    )

    output_dir: Path = tmp_path / "gold"
    silver_to_gold(input_path, output_dir)

    df: pl.DataFrame = pl.read_parquet(
        output_dir / "gold_inventory_alerts.parquet"
    )
    assert df["low_stock_alerts"].sum() == 2
    assert df["min_threshold"][0] == 3  # menor valor
