# Checklist de aderência à lauda técnica

> Escopo: comparação entre os requisitos técnicos da lauda e os artefatos presentes no projeto. A parte de apresentação oral foi desconsiderada.

## 1. EDA orientada a hipóteses

| Requisito | Status | Evidência no projeto | Observação |
|---|---:|---|---|
| Formular no mínimo 3 hipóteses | Atendido | `pipeline_ciberseguranca.ipynb`, seção EDA: H1, H2 e H3 | As hipóteses cobrem vetor de ataque, setor/severidade e tempo de detecção/impacto operacional. |
| Produzir visualizações para cada hipótese | Atendido | `reports/figures/h1_*`, `h2_*`, `h3_*` | Cada hipótese possui pelo menos duas visualizações. |
| Totalizar no mínimo 6 gráficos | Atendido | `reports/figures/` | Há mais de 6 gráficos disponíveis. |
| Contemplar distribuição de variáveis-chave | Atendido | `distribuicao_label_alto_impacto.png`, `h3_deteccao_por_porte.png` | Inclui distribuição do target e distribuição de tempo de detecção por porte. |
| Contemplar análise de outliers | Atendido | `h1_perda_por_vetor_boxplot.png` | Boxplot em escala log evidencia caudas longas e perdas extremas. |
| Contemplar matriz de correlação | Atendido | `h2_correlacao_variaveis_chave.png` | Correlação entre variáveis numéricas-chave. |
| Contemplar análise por recorte | Atendido | `h2_heatmap_setor_impacto.png`, `downtime_mediano_por_vetor.png`, `top_paises_incidentes.png` | Recortes por setor, vetor de ataque e país. |
| Incluir interpretação textual orientada a decisão | Atendido | `pipeline_ciberseguranca.ipynb` e `docs/eda_interpretations.md` | Foi incluído resumo interpretativo das visualizações com decisões de modelagem/uso operacional. |

## 2. Camada Ouro e ML-ready

| Requisito | Status | Evidência no projeto | Observação |
|---|---:|---|---|
| Construir camada Ouro a partir da Prata | Atendido | `data/gold/gold_train.parquet`, `data/gold/gold_test.parquet` | A Gold é gerada a partir de `silver_master_ml.parquet`. |
| Aplicar ao menos 2 técnicas de encoding | Atendido | `scripts/build_gold_ml_reports.py`, `data/gold/preprocessor.pkl` | Usa `OrdinalEncoder` e `OneHotEncoder`. |
| Aplicar 1 estratégia de scaling | Atendido | `scripts/build_gold_ml_reports.py`, `data/gold/preprocessor.pkl` | Usa `RobustScaler`. |
| Aplicar ao menos 2 estratégias de missing values | Atendido | `docs/gold_transformations.csv` | Usa mediana para numéricas, constante para categóricas e moda para booleanas. |
| Identificar e tratar outliers em pelo menos 2 colunas | Atendido | `docs/quality_report_silver_gold.md`, `scripts/build_gold_ml_reports.py` | Outliers tratados em `company_revenue_usd` e `employee_count`. |
| Justificar abordagem de outliers | Atendido | `docs/quality_report_silver_gold.md`, `docs/gold_transformations.csv` | Winsorization por IQR com limites calculados no treino. |
| Remover ou justificar colunas com risco de leakage | Atendido | `docs/anti_leakage_checklist.md` | Colunas futuras/desfecho são removidas ou justificadas. |
| Seguir padrão `fit/transform` | Atendido | `scripts/build_gold_ml_reports.py`, `data/gold/preprocessor.pkl` | `fit` é feito no treino e `transform` no teste. |
| Evitar vazamento do teste no treino | Atendido | `docs/anti_leakage_checklist.md`, `docs/quality_report_silver_gold.md` | Split ocorre antes de imputação, encoding, scaling e limites de outliers. |
| Salvar dataset em Parquet | Atendido | `data/gold/gold_train.parquet`, `data/gold/gold_test.parquet` | Treino e teste salvos separadamente. |
| Documentar transformações em tabela | Atendido | `docs/gold_transformations.csv` | Tabela com transformação, colunas, método e justificativa. |

## 3. Modelagem preditiva

| Requisito | Status | Evidência no projeto | Observação |
|---|---:|---|---|
| Treinar pelo menos 2 modelos de Árvore de Decisão com configurações distintas | Atendido | `reports/model_metrics.csv`, `scripts/build_gold_ml_reports.py` | Modelos Gold com critérios/profundidades diferentes. |
| Justificar divisão treino/teste | Atendido | `docs/quality_report_silver_gold.md` | Uso de `train_test_split(..., stratify=y, random_state=42)`. |
| Garantir representatividade de classes | Atendido | `docs/quality_report_silver_gold.md` | Treino e teste preservam 48,82% de classe positiva. |
| Avaliar com pelo menos 3 métricas | Atendido | `reports/model_metrics.csv` | Usa accuracy, precision, recall e F1. |
| Gerar matriz de confusão para o melhor modelo | Atendido | `reports/figures/confusion_matrix_gold_decision_tree.png` | Matriz salva em `reports/figures/`. |
| Visualizar a árvore resultante | Atendido | `reports/figures/decision_tree_gold_best.png` | Árvore do melhor modelo Gold. |
| Comparar resultados Prata vs Ouro | Atendido | `reports/model_comparison_silver_gold.csv` | Compara baseline Prata com melhor modelo Gold. |

## 4. Refatoração com PySpark

| Requisito | Status | Evidência no projeto | Observação |
|---|---:|---|---|
| Refatorar ao menos 2 etapas do pipeline usando PySpark | Atendido com ressalva | `scripts/pyspark_refactor.py`, `docs/pyspark_refactor_notes.md` | A implementação está em script externo, chamado pelo notebook. |
| Ler dados em formato Parquet ou Delta | Atendido com ressalva | `scripts/pyspark_refactor.py` | O script lê Parquet; também cria cópias compatíveis para evitar erro de timestamp nanos. |
| Fazer ao menos 1 operação de `join` | Atendido com ressalva | `scripts/pyspark_refactor.py` | Join entre incidentes e impacto financeiro. |
| Fazer ao menos 1 `groupBy` com agregação | Atendido com ressalva | `scripts/pyspark_refactor.py` | Agrega incidentes, perda mediana e downtime mediano. |
| Usar ao menos 1 função de janela | Atendido com ressalva | `scripts/pyspark_refactor.py` | Usa `dense_rank` com `Window.partitionBy`. |
| Escrever resultado em Parquet ou Delta | Atendido com ressalva | `scripts/pyspark_refactor.py` | Escreve `data/pyspark_refactor/sector_attack_rankings.parquet` após execução. |
| Comparar tempo Pandas vs PySpark | Parcial | `scripts/pyspark_refactor.py` | O script mede e grava `docs/pyspark_benchmark.md`, mas o benchmark precisa ser executado em ambiente com Java/PySpark. |

## 5. Arquivos e documentação técnica

| Requisito | Status | Evidência no projeto | Observação |
|---|---:|---|---|
| Notebook principal com etapas documentadas | Atendido com ressalva | `pipeline_ciberseguranca.ipynb` | O notebook documenta todas as etapas; a execução detalhada de PySpark fica em script externo. |
| Arquivos da camada Ouro em Parquet | Atendido | `data/gold/` | `gold_train.parquet` e `gold_test.parquet`. |
| Relatório de qualidade atualizado Prata/Ouro | Atendido | `docs/quality_report_silver_gold.md` | Cobre Silver, Gold, nulos, duplicatas, target e outliers. |
| Tabela de transformações da Ouro | Atendido | `docs/gold_transformations.csv` | Tabela disponível em CSV. |
| Checklist anti-leakage atualizado | Atendido | `docs/anti_leakage_checklist.md` | Inclui colunas de risco e ações. |
| README com instruções de execução | Atendido | `README.md` | Contém ambiente, comandos e estrutura. |
| Data lineage atualizado até Ouro | Atendido | `docs/data_lineage.md`, `docs/data_lineage.json`, `docs/data_lineage.png` | Contempla fluxo até Gold, modelagem e PySpark. |

## Pendência prática recomendada

Para fechar a única ressalva operacional, execute em um ambiente com Java e PySpark:

```bash
python scripts/pyspark_refactor.py
```

Após a execução, devem aparecer/atualizar:

- `docs/pyspark_benchmark.md`
- `data/pyspark_refactor/sector_attack_rankings.parquet`
- `data/pyspark_refactor/spark_compatible_input/`

Com esses arquivos gerados, a parte PySpark deixa de ser apenas implementada e passa a ficar evidenciada com saída e benchmark local.
