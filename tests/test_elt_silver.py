import polars as pl
from pathlib import Path
import pytest
from scpulse.etl.bronze_to_silver import bronze_to_silver


def test_silver_timestamp_is_datetime(tmp_path: Path) -> None:
    # cria bronze fake
    df = pl.DataFrame(
        {
            "event_id": ["EVT-1"],
            "event_type": ["order_created"],
            "timestamp": ["2025-09-17T20:18:02.761102+00:00"],
        }
    )
    bronze_path = tmp_path / "bronze.parquet"
    silver_path = tmp_path / "silver.parquet"
    df.write_parquet(bronze_path)

    # roda pipeline
    bronze_to_silver(bronze_path, silver_path)
    out = pl.read_parquet(silver_path)

    assert out["timestamp"].dtype == pl.Datetime("ns", "UTC")
    assert out["event_id"].dtype == pl.Utf8


def make_bronze_file(
    tmp_path: Path, rows: list[dict], filename: str = "bronze.parquet"
) -> Path:
    """Helper para criar arquivo Parquet Bronze."""
    df = pl.DataFrame(rows)
    path = tmp_path / filename
    df.write_parquet(path)
    return path


def test_silver_has_expected_schema(tmp_path: Path) -> None:
    input_path = make_bronze_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "timestamp": "2025-09-17T12:00:00+00:00",
            }
        ],
    )
    output_path = tmp_path / "silver.parquet"

    bronze_to_silver(input_path, output_path)

    df = pl.read_parquet(output_path)
    assert set(df.columns) == {"event_id", "event_type", "timestamp"}
    assert df.schema["timestamp"] == pl.Datetime("ns", "UTC")


def test_silver_has_no_nulls_in_required(tmp_path: Path) -> None:
    input_path = make_bronze_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "timestamp": None,
            },
            {
                "event_id": "EVT-2",
                "event_type": "order_created",
                "timestamp": "2025-09-17T12:00:00+00:00",
            },
        ],
    )
    output_path = tmp_path / "silver.parquet"

    bronze_to_silver(input_path, output_path)
    df = pl.read_parquet(output_path)

    # Nenhum nulo deve sobrar
    assert (
        df.select(
            [
                pl.col(c).null_count()
                for c in ["event_id", "event_type", "timestamp"]
            ]
        )
        .sum()
        .row(0)[0]
        == 0
    )


def test_silver_deduplicates_events(tmp_path: Path) -> None:
    input_path = make_bronze_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "timestamp": "2025-09-17T12:00:00+00:00",
            },
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "timestamp": "2025-09-17T12:00:00+00:00",
            },
        ],
    )
    output_path = tmp_path / "silver.parquet"

    bronze_to_silver(input_path, output_path)
    df = pl.read_parquet(output_path)

    assert df.shape[0] == 1  # só 1 evento único


def test_silver_raises_if_missing_required_cols(tmp_path: Path) -> None:
    input_path = make_bronze_file(
        tmp_path,
        [
            {"foo": "bar"}  # faltam colunas obrigatórias
        ],
    )
    output_path = tmp_path / "silver.parquet"

    with pytest.raises(ValueError, match="Colunas ausentes"):
        bronze_to_silver(input_path, output_path)


def test_silver_integration_pipeline(tmp_path: Path) -> None:
    """Pipeline end-to-end: Bronze → Silver com vários eventos."""
    input_path = make_bronze_file(
        tmp_path,
        [
            {
                "event_id": "EVT-1",
                "event_type": "order_created",
                "timestamp": "2025-09-17T10:00:00+00:00",
            },
            {
                "event_id": "EVT-2",
                "event_type": "inventory_low",
                "timestamp": "2025-09-17T11:00:00+00:00",
            },
            {
                "event_id": "EVT-3",
                "event_type": "order_delayed",
                "timestamp": "2025-09-17T12:00:00+00:00",
            },
        ],
    )
    output_path = tmp_path / "silver.parquet"

    bronze_to_silver(input_path, output_path)
    df = pl.read_parquet(output_path)

    assert df.shape[0] == 3
    assert sorted(df["event_id"].to_list()) == ["EVT-1", "EVT-2", "EVT-3"]
    assert df.schema["timestamp"] == pl.Datetime("ns", "UTC")
