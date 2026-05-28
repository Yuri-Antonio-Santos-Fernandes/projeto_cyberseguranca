# Projeto de Engenharia de Dados em Cibersegurança

Pipeline de engenharia de dados para análise de incidentes de cibersegurança, com camadas **Bronze**, **Prata**, **Ouro** e dataset **ML-ready**. O projeto integra bases de incidentes, impacto financeiro e impacto de mercado; aplica validações de qualidade; gera análises exploratórias; prepara features para machine learning; treina modelos de Árvore de Decisão; e inclui uma refatoração de etapas do pipeline com PySpark.

## Bases utilizadas

- `incidents_master.csv`
- `financial_impact.csv`
- `market_impact.csv`

## Estrutura do projeto

```text
projeto_cyberseguranca_corrigido/
├── bronze.ipynb
├── silver.ipynb
├── pipeline_ciberseguranca.ipynb
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   │   ├── incidents_master/
│   │   ├── financial_impact/
│   │   ├── market_impact/
│   │   ├── silver_master.parquet
│   │   └── silver_master_ml.parquet
│   ├── gold/
│   │   ├── gold_train.parquet
│   │   ├── gold_test.parquet
│   │   └── preprocessor.pkl
│   └── pyspark_refactor/
├── docs/
│   ├── anti_leakage_checklist.md
│   ├── data_lineage.md
│   ├── data_lineage.json
│   ├── eda_interpretations.md
│   ├── gold_transformations.csv
│   ├── quality_report_silver_gold.md
│   ├── pyspark_refactor_notes.md
│   └── lauda_checklist.md
├── models/
│   ├── decision_tree_gold_best.pkl
│   └── decision_tree_silver_baseline.pkl
├── reports/
│   ├── model_metrics.csv
│   ├── model_comparison_silver_gold.csv
│   └── figures/
├── scripts/
│   ├── build_gold_ml_reports.py
│   └── pyspark_refactor.py
└── requirements.txt
```

## Ambiente

Recomendado usar Python 3.10+.

```bash
pip install -r requirements.txt
```

Para executar a etapa de PySpark, o ambiente precisa ter Java disponível além do pacote `pyspark`.

## Como executar

### Notebook principal

```bash
jupyter notebook pipeline_ciberseguranca.ipynb
```

### Regenerar camada Gold, métricas e relatórios

```bash
python scripts/build_gold_ml_reports.py
```

### Refatoração PySpark

```bash
python scripts/pyspark_refactor.py
```

O script PySpark lê arquivos Parquet da camada Prata, cria cópias temporárias compatíveis com Spark quando necessário, executa `join`, `groupBy`, função de janela e salva o resultado em Parquet.

## Camadas do pipeline

### Bronze

- Ingestão dos arquivos CSV.
- Padronização de nomes de colunas.
- Persistência em Parquet.
- Metadados de carga e relatório de qualidade inicial.

### Prata

- Limpeza e padronização textual.
- Conversão de datas.
- Remoção de duplicatas.
- Criação de variáveis derivadas.
- Integração das tabelas de incidentes, impacto financeiro e impacto de mercado.
- Criação do label `flag_alto_impacto`.
- Remoção de colunas com risco de data leakage na versão `silver_master_ml.parquet`.

### Ouro / ML-ready

- Split treino/teste estratificado.
- Tratamento de outliers com Winsorization por IQR em `company_revenue_usd` e `employee_count`, com limites calculados apenas no treino.
- Imputação de nulos com estratégias diferentes para variáveis numéricas, categóricas e booleanas.
- Encoding com `OrdinalEncoder` e `OneHotEncoder`.
- Scaling com `RobustScaler`.
- Persistência de `gold_train.parquet`, `gold_test.parquet` e `preprocessor.pkl`.

## Modelagem

Foram treinados modelos de Árvore de Decisão com configurações distintas e comparados com uma baseline da camada Prata.

Arquivos principais:

- `reports/model_metrics.csv`: métricas dos modelos.
- `reports/model_comparison_silver_gold.csv`: comparação Prata vs Ouro.
- `reports/figures/confusion_matrix_gold_decision_tree.png`: matriz de confusão do melhor modelo Gold.
- `reports/figures/decision_tree_gold_best.png`: visualização da árvore do melhor modelo Gold.
- `models/decision_tree_gold_best.pkl`: melhor modelo Gold serializado.

## Documentação gerada

- `docs/eda_interpretations.md`: interpretação orientada a decisão das visualizações da EDA.
- `docs/gold_transformations.csv`: tabela de transformações da camada Ouro.
- `docs/quality_report_silver_gold.md`: relatório de qualidade das camadas Prata e Ouro.
- `docs/anti_leakage_checklist.md`: checklist anti-leakage atualizado.
- `docs/data_lineage.md`: fluxo do pipeline até Gold, modelagem e PySpark.
- `docs/pyspark_refactor_notes.md`: descrição das etapas refatoradas com PySpark.
- `docs/lauda_checklist.md`: checklist de aderência aos requisitos técnicos.

## Resultados rápidos

- `silver_master.parquet`: 850 linhas x 93 colunas.
- `silver_master_ml.parquet`: 850 linhas x 38 colunas.
- `gold_train.parquet`: 680 linhas x 47 colunas.
- `gold_test.parquet`: 170 linhas x 47 colunas.
- Melhor modelo Gold: `gold_tree_depth_6_entropy`.
- Métricas e comparação estão em `reports/`.
