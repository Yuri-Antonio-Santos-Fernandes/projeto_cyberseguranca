# Relatório de qualidade - camadas Prata e Ouro

Gerado em UTC: 2026-05-28T11:02:41.444177+00:00

## Visão geral

| Dataset | Linhas | Colunas | Nulos totais | Duplicatas completas |
|---|---:|---:|---:|---:|
| silver_master.parquet | 850 | 93 | 17184 | 0 |
| silver_master_ml.parquet | 850 | 38 | 2676 | 0 |
| gold_train.parquet | 680 | 47 | 0 | 0 |
| gold_test.parquet | 170 | 47 | 0 | 0 |

## Representatividade do target

| Conjunto | Classe 0 | Classe 1 | Percentual classe 1 |
|---|---:|---:|---:|
| silver_master_ml | 435 | 415 | 48.82% |
| treino Gold | 348 | 332 | 48.82% |
| teste Gold | 87 | 83 | 48.82% |

A divisão treino/teste usa `train_test_split(..., stratify=y, random_state=42)`, preservando proporções semelhantes da variável alvo nos dois conjuntos.

## Nulos mais relevantes na Prata ML

| Coluna | Nulos |
|---|---:|
| earnings_announcement_within_7d | 492 |
| volume_avg_30d_baseline | 492 |
| price_7d_before | 492 |
| sector_index | 492 |
| pre_incident_volatility_30d | 492 |
| direct_loss_method | 72 |
| ransom_source | 72 |
| cpi_index_used | 72 |
| industry_secondary | 0 |
| industry_primary | 0 |


## Validação da Ouro

- Nulos no treino Gold: 0.
- Nulos no teste Gold: 0.
- Número de features após transformação: 46.
- Outliers tratados em `company_revenue_usd` e `employee_count` com limites calculados exclusivamente no treino.
- Objetos de pré-processamento fitados no treino e aplicados no teste via `transform`.

## Outliers

| Coluna | Limite inferior | Limite superior | Outliers no treino | Outliers no teste |
|---|---:|---:|---:|---:|
| company_revenue_usd | -11883076706.50 | 20435221823.12 | 100 | 31 |
| employee_count | -59559.88 | 102207.12 | 107 | 25 |


## Modelagem

As métricas estão em `reports/model_metrics.csv` e a comparação Prata vs Ouro em `reports/model_comparison_silver_gold.csv`.

| Dataset | Modelo | Accuracy | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
| Ouro | gold_tree_depth_3_gini | 0.6059 | 0.5952 | 0.6024 | 0.5988 |
| Ouro | gold_tree_depth_6_entropy | 0.5706 | 0.5500 | 0.6627 | 0.6011 |
| Prata | silver_baseline_tree_depth_6_entropy | 0.5529 | 0.5333 | 0.6747 | 0.5957 |

## Observações

- A matriz de confusão está em `reports/figures/confusion_matrix_gold_decision_tree.png`.
- A visualização da árvore está em `reports/figures/decision_tree_gold_best.png`.
- O objeto `preprocessor.pkl` contém o transformador, colunas removidas, limites de outlier e nomes das features.
