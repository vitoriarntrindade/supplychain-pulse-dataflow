"""Orquestrador do pipeline Bronze → Silver → Gold."""

import asyncio
from pathlib import Path
from datetime import datetime

from scpulse.etl.ingest_stream import consume_kafka, consume_from_file
from scpulse.etl.bronze_to_silver import bronze_to_silver
from scpulse.etl.silver_to_gold import silver_to_gold

# Diretórios
BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")

BRONZE_DIR.mkdir(parents=True, exist_ok=True)
SILVER_DIR.mkdir(parents=True, exist_ok=True)
GOLD_DIR.mkdir(parents=True, exist_ok=True)


async def run_ingest() -> None:
    """Mantém ingestão contínua no Bronze via Kafka.

    Essa função cria um loop infinito consumindo mensagens do Kafka
    e salvando-as em arquivos Parquet no diretório Bronze.
    """
    print("▶️ Iniciando ingestão de eventos (Kafka → Bronze)...")
    await consume_kafka()  # loop infinito


def run_transform() -> None:
    """Executa a pipeline Bronze → Silver → Gold em micro-batch.

    Percorre os arquivos Parquet na camada Bronze,
    transforma em Silver e gera métricas Gold.

    Raises:
        Exception: Se houver falha em Bronze→Silver ou Silver→Gold,
        mas a execução continua para os demais arquivos.
    """
    print("▶️ Rodando transformações Bronze → Silver → Gold...")

    for bronze_file in BRONZE_DIR.glob("events_*.parquet"):
        silver_file: Path = SILVER_DIR / f"silver_{bronze_file.name}"
        gold_dir: Path = GOLD_DIR / bronze_file.stem
        gold_dir.mkdir(parents=True, exist_ok=True)

        # Bronze → Silver
        try:
            bronze_to_silver(bronze_file, silver_file)
        except Exception as e:
            print(f"⚠️ Erro Bronze→Silver em {bronze_file}: {e}")
            continue

        # Silver → Gold
        try:
            silver_to_gold(silver_file, gold_dir)
        except Exception as e:
            print(f"⚠️ Erro Silver→Gold em {silver_file}: {e}")
            continue


async def scheduler(interval: int = 5) -> None:
    """Agenda transformações periódicas Bronze→Silver→Gold.

    Args:
        interval (int, optional): Intervalo em segundos entre execuções.
            Default = 60.
    """
    while True:
        print(f"⏱️ {datetime.utcnow()} - Executando ciclo de transformação...")
        run_transform()
        await asyncio.sleep(interval)  # ✅ não bloqueia o loop


def main() -> None:
    """Ponto de entrada principal do orquestrador."""
    mode: str = "hybrid"  # pode ser "kafka", "file" ou "hybrid"

    if mode == "kafka":
        asyncio.run(run_ingest())
    elif mode == "file":
        consume_from_file()
        run_transform()
    else:  # híbrido
        loop = asyncio.get_event_loop()
        loop.create_task(run_ingest())
        loop.run_until_complete(scheduler(interval=60))


if __name__ == "__main__":
    main()
