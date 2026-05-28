# Benchmark Pandas vs PySpark

| Etapa | Tempo em segundos |
|---|---:|
| Pandas - join + groupBy | 0.0491 |
| PySpark - join + groupBy + window + escrita Parquet | 7.6346 |

Saída Spark: `data/pyspark_refactor/sector_attack_rankings.parquet`.
Entradas compatibilizadas para Spark: `data/pyspark_refactor/spark_compatible_input/`.
