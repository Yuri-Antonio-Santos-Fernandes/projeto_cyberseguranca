# Relatório de Qualidade de Dados — Bronze

## Visão geral
- Datasets avaliados: **3**
- Regras executadas: **36**
- PASS: **33**
- WARN: **3**
- FAIL: **0**

## Principais achados
- Não foram encontrados problemas críticos de unicidade, integridade referencial, parse de datas ou valores negativos.
- O principal ponto de atenção da Bronze é a **incompletude em colunas opcionais**, especialmente campos secundários, notas e indicadores retroativos.
- A tabela `market_impact` possui menor cobertura por natureza do negócio: ela existe apenas para empresas com contexto de mercado disponível.

## Regras com WARN/FAIL

| dataset | regra | status | registros afetados | critério |
|---|---|---|---:|---|
| financial_impact | high_missing_columns | WARN | 5 | até 50% de nulos por coluna |
| incidents_master | high_missing_columns | WARN | 7 | até 50% de nulos por coluna |
| market_impact | high_missing_columns | WARN | 1 | até 50% de nulos por coluna |

## Top colunas com nulos

### financial_impact

| coluna | nulos | % nulos |
|---|---:|---:|
| ransom_paid_usd | 692 | 88.95% |
| ransom_source | 692 | 88.95% |
| regulatory_fine_usd | 646 | 83.03% |
| ransom_demanded_usd | 572 | 73.52% |
| notes | 530 | 68.12% |
| insurance_payout_usd | 343 | 44.09% |

### incidents_master

| coluna | nulos | % nulos |
|---|---:|---:|
| review_flag | 780 | 91.76% |
| industry_secondary | 697 | 82.00% |
| attack_vector_secondary | 639 | 75.18% |
| notes | 636 | 74.82% |
| data_source_secondary | 464 | 54.59% |
| stock_ticker | 438 | 51.53% |
| downtime_hours | 430 | 50.59% |
| attributed_group | 368 | 43.29% |

### market_impact

| coluna | nulos | % nulos |
|---|---:|---:|
| notes | 266 | 74.30% |
| days_to_price_recovery | 36 | 10.06% |


## Conclusão
A Bronze foi **aprovada com observações**: as regras críticas passaram, mas há colunas com alta taxa de nulos que exigem tratamento na camada Prata.