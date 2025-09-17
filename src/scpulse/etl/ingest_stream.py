import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime, UTC

import polars as pl

try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "supplychain_events")

DATA_DIR = Path("data/bronze")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _write_parquet(
    events: List[Dict], filename: str = "events.parquet"
) -> Path:
    """Grava eventos em Parquet na camada Bronze."""
    if not events:
        return DATA_DIR / filename

    df = pl.DataFrame(events)

    # Garante que timestamp esteja timezone-aware
    #            .fill_null(datetime.now(UTC))   # substitui nulos por agora

    if "timestamp" in df.columns:
        df = df.with_columns(
            pl.col("timestamp")
            .str.strptime(
                pl.Datetime("ns"),
                "%Y-%m-%dT%H:%M:%S%.f%z",
                strict=True,  # suporta +00:00
            )
            .dt.convert_time_zone("UTC")  # normaliza para UTC
        )

    print(df["timestamp"].head())

    file_path = DATA_DIR / filename
    df.write_parquet(file_path, compression="snappy")
    print(f"[BRONZE] Wrote {len(events)} events → {file_path}")
    return file_path


async def consume_kafka() -> None:
    """Consome mensagens do Kafka e grava em Bronze."""
    if AIOKafkaConsumer is None:
        raise RuntimeError(
            "aiokafka não instalado. Rode `poetry add aiokafka`."
        )

    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    await consumer.start()
    try:
        buffer: List[Dict] = []
        async for msg in consumer:
            event = msg.value
            buffer.append(event)
            print(f"[CONSUMER] Received: {event}")

            # Salva em batch de 10 eventos
            if len(buffer) >= 10:
                _write_parquet(
                    buffer,
                    filename=f"events_{datetime.now(UTC).date()}.parquet",
                )
                buffer.clear()
    finally:
        await consumer.stop()


def consume_from_file(
    filepath: Path = Path("data/landing/events.jsonl"),
) -> Path:
    """Consome eventos de um arquivo JSONL e grava em Bronze (fallback)."""
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo {filepath} não encontrado.")

    with open(filepath, "r", encoding="utf-8") as f:
        events = [json.loads(line.strip()) for line in f if line.strip()]

    return _write_parquet(
        events, filename=f"events_{datetime.now(UTC).date()}.parquet"
    )


if __name__ == "__main__":
    mode = os.getenv("INGEST_MODE", "kafka")  # "kafka" ou "file"
    if mode == "kafka":
        asyncio.run(consume_kafka())
    else:
        consume_from_file()
