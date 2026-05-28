# Scripts auxiliares

## `build_gold_ml_reports.py`

Regenera a camada Gold, métricas de modelagem, gráficos do melhor modelo e documentos técnicos derivados.

```bash
python scripts/build_gold_ml_reports.py
```

## `pyspark_refactor.py`

Executa a refatoração PySpark com leitura Parquet, `join`, `groupBy`, função de janela, escrita em Parquet e benchmark Pandas vs PySpark.

```bash
python scripts/pyspark_refactor.py
```

O script requer Java e PySpark instalados no ambiente.

Em Windows, se `HADOOP_HOME`/`winutils.exe` não estiverem configurados, o script usa um fallback em Pandas para gerar a mesma agregação e mantém o benchmark em `docs/pyspark_benchmark.md`.
