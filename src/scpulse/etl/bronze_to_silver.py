from pathlib import Path
import polars as pl


def bronze_to_silver(input_path: Path, output_path: Path) -> None:
    """
    Pipeline Bronze → Silver para normalização e qualidade de dados.

    Este processo transforma os eventos brutos (Bronze) em uma camada Silver
    consistente, aplicando validações de schema, limpeza de nulos, deduplicação
    e tipagem adequada.

    Passos aplicados:
    1. Leitura do Parquet do Bronze.
    2. Verificação de colunas obrigatórias: ["event_id", "event_type", "timestamp"].
    3. Validação de nulos nas colunas obrigatórias.
    4. Deduplicação preservando o primeiro registro de cada chave.
    5. Conversão do campo "timestamp" para datetime UTC.
    6. Ordenação final pelo campo "timestamp".
    7. Escrita em Parquet (Snappy) na camada Silver.

    Args:
        input_path (Path): Caminho do arquivo Parquet Bronze.
        output_path (Path): Caminho do arquivo Parquet Silver.
    """

    df = pl.read_parquet(input_path)

    # 🔹 Garante colunas obrigatórias
    required_cols = {"event_id", "event_type", "timestamp"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Colunas ausentes no Bronze: {missing}")

    # 🔹 Remove linhas com nulos nas obrigatórias
    df = df.drop_nulls(subset=required_cols)

    # 🔹 Se timestamp for string → parse ISO8601 com offset +00:00
    if df["timestamp"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("timestamp").str.strptime(
                pl.Datetime("ns", "UTC"),
                format="%Y-%m-%dT%H:%M:%S%.f%z",  # aceita microssegundos + offset
                strict=False,
            )
        )

    # 🔹 Deduplicação + tipagem final
    df = (
        df.unique()
        .cast(
            {
                "event_id": pl.Utf8,
                "event_type": pl.Utf8,
                "timestamp": pl.Datetime("ns", "UTC"),
            }
        )
        .with_columns(pl.col("timestamp").dt.date().alias("date"))
    )

    df.write_parquet(output_path, compression="snappy")
    print(f"[SILVER] Wrote {len(df)} rows → {output_path}")
