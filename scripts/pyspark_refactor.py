from __future__ import annotations

import os
from pathlib import Path
from time import perf_counter
import shutil

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from pyspark.sql import SparkSession, Window
    from pyspark.sql import functions as F
except ImportError as exc:
    raise SystemExit(
        "PySpark não está instalado. Instale com `pip install pyspark` e execute novamente."
    ) from exc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
OUT_DIR = PROJECT_ROOT / "data" / "pyspark_refactor"
DOCS_DIR = PROJECT_ROOT / "docs"
SPARK_INPUT_DIR = OUT_DIR / "spark_compatible_input"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def spark_local_writable() -> bool:
    """Checks whether the local Spark runtime is likely writable on Windows.

    Spark on Windows needs Hadoop helpers such as winutils.exe. When they are
    missing, Spark can start but fail when writing local Parquet output. In that
    case we keep the script useful by falling back to the Pandas benchmark path.
    """
    if os.name != "nt":
        return True

    hadoop_home = os.environ.get("HADOOP_HOME") or os.environ.get("hadoop.home.dir")
    if not hadoop_home:
        return False

    winutils = Path(hadoop_home) / "bin" / "winutils.exe"
    return winutils.exists()


def write_spark_compatible_parquet(source_path: Path, target_path: Path) -> None:
    """Regrava Parquet com timestamps em microssegundos, formato aceito pelo Spark.

    Alguns arquivos criados via Pandas/PyArrow podem armazenar timestamps como
    TIMESTAMP(NANOS,true), que certas versões do Spark não conseguem ler.
    Esta função preserva os dados e altera apenas a granularidade física dos
    timestamps para microssegundos.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(source_path)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(
        table,
        target_path,
        coerce_timestamps="us",
        allow_truncated_timestamps=True,
    )


# Cria entradas compatíveis para leitura Spark sem alterar a camada Prata original.
if SPARK_INPUT_DIR.exists():
    shutil.rmtree(SPARK_INPUT_DIR)
SPARK_INPUT_DIR.mkdir(parents=True, exist_ok=True)

incidents_compat = SPARK_INPUT_DIR / "incidents_master.parquet"
financial_compat = SPARK_INPUT_DIR / "financial_impact.parquet"
write_spark_compatible_parquet(
    SILVER_DIR / "incidents_master" / "incidents_master.parquet",
    incidents_compat,
)
write_spark_compatible_parquet(
    SILVER_DIR / "financial_impact" / "financial_impact.parquet",
    financial_compat,
)

# Benchmark Pandas: join + groupBy equivalente.
t0 = perf_counter()
inc_pd = pd.read_parquet(SILVER_DIR / "incidents_master" / "incidents_master.parquet")
fin_pd = pd.read_parquet(SILVER_DIR / "financial_impact" / "financial_impact.parquet")
pandas_join = inc_pd.merge(fin_pd, on="incident_id", how="left", suffixes=("", "_fin"))
pandas_agg = (
    pandas_join.groupby(["industry_primary", "attack_vector_primary"], dropna=False)
    .agg(
        incidentes=("incident_id", "count"),
        perda_mediana_usd=("direct_loss_usd", "median"),
        downtime_mediano_horas=("downtime_hours", "median"),
    )
    .reset_index()
)
pandas_seconds = perf_counter() - t0

spark_seconds = None
spark_ready = spark_local_writable()
output_path = OUT_DIR / "sector_attack_rankings.parquet"

if output_path.exists():
    if output_path.is_dir():
        shutil.rmtree(output_path)
    else:
        output_path.unlink()

if spark_ready:
    spark = (
        SparkSession.builder
        .appName("cybersecurity_refactor")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )

    # Refatoração 1: leitura Parquet + join.
    t1 = perf_counter()
    inc = spark.read.parquet(str(incidents_compat))
    fin = spark.read.parquet(str(financial_compat))
    joined = inc.join(fin, on="incident_id", how="left")

    # Refatoração 2: groupBy + função de janela para ranking por setor.
    agg = (
        joined.groupBy("industry_primary", "attack_vector_primary")
        .agg(
            F.count("incident_id").alias("incidentes"),
            F.expr("percentile_approx(direct_loss_usd, 0.5)").alias("perda_mediana_usd"),
            F.expr("percentile_approx(downtime_hours, 0.5)").alias("downtime_mediano_horas"),
        )
    )
    window = Window.partitionBy("industry_primary").orderBy(F.desc("perda_mediana_usd"))
    ranked = agg.withColumn("rank_perda_no_setor", F.dense_rank().over(window))
    ranked.write.mode("overwrite").parquet(str(output_path))
    spark_seconds = perf_counter() - t1
    spark.stop()
else:
    ranked = (
        pandas_join.groupby(["industry_primary", "attack_vector_primary"], dropna=False)
        .agg(
            incidentes=("incident_id", "count"),
            perda_mediana_usd=("direct_loss_usd", "median"),
            downtime_mediano_horas=("downtime_hours", "median"),
        )
        .reset_index()
    )
    ranked["rank_perda_no_setor"] = (
        ranked.groupby("industry_primary")["perda_mediana_usd"]
        .rank(method="dense", ascending=False)
        .astype("Int64")
    )
    output_path.mkdir(parents=True, exist_ok=True)
    ranked.to_parquet(output_path / "part-00000.parquet", index=False)

spark_time_text = f"{spark_seconds:.4f}" if spark_seconds is not None else "N/A"
summary = f"""# Benchmark Pandas vs PySpark

| Etapa | Tempo em segundos |
|---|---:|
| Pandas - join + groupBy | {pandas_seconds:.4f} |
| PySpark - join + groupBy + window + escrita Parquet | {spark_time_text} |

Saída Spark: `data/pyspark_refactor/sector_attack_rankings.parquet`.
Entradas compatibilizadas para Spark: `data/pyspark_refactor/spark_compatible_input/`.
"""
if not spark_ready:
    summary += "\n\nObservação: execução Spark ignorada neste Windows porque `HADOOP_HOME`/`winutils.exe` não estão configurados. Foi gerada a mesma agregação com Pandas para manter a saída disponível."

(DOCS_DIR / "pyspark_benchmark.md").write_text(summary, encoding="utf-8")
print(summary)
