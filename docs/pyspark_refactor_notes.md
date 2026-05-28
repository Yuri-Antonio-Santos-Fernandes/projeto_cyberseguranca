# Refatoração com PySpark

O script `scripts/pyspark_refactor.py` contém duas etapas refatoradas com Spark:

1. leitura de Parquet e `join` entre incidentes e impacto financeiro;
2. `groupBy` com agregações e função de janela (`dense_rank`) para ranquear vetores de ataque por perda mediana dentro de cada setor.

A escrita final é feita em Parquet em `data/pyspark_refactor/sector_attack_rankings.parquet`.

Antes da leitura com Spark, o script cria cópias temporárias compatíveis em `data/pyspark_refactor/spark_compatible_input/`, regravando timestamps em microssegundos. Isso evita problemas de leitura em ambientes Spark que não aceitam Parquet com `TIMESTAMP(NANOS,true)`.

O mesmo script mede o tempo de uma etapa equivalente em Pandas e grava o resumo em `docs/pyspark_benchmark.md` quando executado em um ambiente com Java e PySpark instalados.
