# Projeto de Engenharia de Dados em Cibersegurança

Este pacote entrega um pipeline simples com camadas **Bronze** e **Prata** a partir dos datasets:

- `incidents_master.csv`
- `financial_impact.csv`
- `market_impact.csv`

## O que foi entregue

- **Notebook principal consolidado:** `pipeline_ciberseguranca.ipynb`
- **Camada Bronze em Parquet** com metadados de ingestão
- **Relatório de qualidade da Bronze** com regras automáticas
- **Camada Prata em Parquet**
- **Dataset final ML-ready:** `data/silver/silver_master_ml.parquet`
- **Checklist anti-leakage**
- **Data lineage** em JSON, Mermaid e PNG
- **4 gráficos exploratórios**
- **README** com instruções de execução

## Estrutura

```text
projeto_ciberseguranca_pipeline/
├── pipeline_ciberseguranca.ipynb
├── data/
│   ├── raw/
│   ├── bronze/
│   │   ├── incidents_master/
│   │   ├── financial_impact/
│   │   ├── market_impact/
│   │   ├── _meta/
│   │   └── _quality/
│   └── silver/
│       ├── incidents_master/
│       ├── financial_impact/
│       ├── market_impact/
│       ├── silver_master.parquet
│       └── silver_master_ml.parquet
├── docs/
└── reports/
    └── figures/
```

## Requisitos

Recomendado usar Python 3.10+ com:

- pandas
- numpy
- matplotlib
- pyarrow
- notebook / jupyter

## Como executar

1. Abra a pasta do projeto.
2. Instale as dependências:
   `pip install -r requirements.txt`
3. Execute o notebook principal:
   `jupyter notebook pipeline_ciberseguranca.ipynb`

## Regras da Bronze

As validações automáticas verificam:

- unicidade e nulidade da chave `incident_id`
- duplicatas completas
- parse de datas
- cronologia entre incidente, descoberta e divulgação
- domínios categóricos principais
- campos numéricos negativos
- integridade referencial entre tabelas
- colunas com alta taxa de nulos

## Estratégia da Prata

A camada Prata aplica:

- limpeza e imputação de nulos
- padronização textual
- conversão de datas
- remoção de duplicatas
- criação de colunas derivadas
- criação do label `flag_alto_impacto`
- geração de um dataset **ML-ready** com colunas de leakage removidas

## Observações importantes

- `silver_master.parquet` é o dataset consolidado para análise.
- `silver_master_ml.parquet` é a versão recomendada para tarefas futuras de Machine Learning.
- O checklist anti-leakage documenta quais colunas foram removidas ou marcadas como inadequadas para modelagem.
- O projeto teve auxílio de inteligência artificial no seu desenvolvimento. Utilizamos para melhor estruturação dos conhecimentos e estruturação de código.

## Resumo rápido dos resultados

- Regras de qualidade executadas: **36**
- Resultado das regras: **33 PASS / 3 WARN / 0 FAIL**
- Dataset final analítico: **850 linhas × 93 colunas**
- Dataset final ML-ready: **850 linhas × 38 colunas**
- Distribuição do label final: **435 baixo impacto / 415 alto impacto**