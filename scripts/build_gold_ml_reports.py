from __future__ import annotations

import json
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, RobustScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
SILVER_DIR = DATA_DIR / 'silver'
GOLD_DIR = DATA_DIR / 'gold'
DOCS_DIR = PROJECT_ROOT / 'docs'
REPORTS_DIR = PROJECT_ROOT / 'reports'
FIG_DIR = REPORTS_DIR / 'figures'
MODELS_DIR = PROJECT_ROOT / 'models'
for d in [GOLD_DIR, DOCS_DIR, REPORTS_DIR, FIG_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 2. Leak-safe Gold preprocessing and Decision Tree modeling
# -----------------------------------------------------------------------------
TARGET = 'flag_alto_impacto'
RANDOM_STATE = 42
TEST_SIZE = 0.20

silver_master = pd.read_parquet(SILVER_DIR / 'silver_master.parquet')
silver_ml = pd.read_parquet(SILVER_DIR / 'silver_master_ml.parquet')

DROP_COLS = [
    'incident_id',
    'company_name',
    'stock_ticker',
    'attack_chain',
    'attributed_group',
    'systems_affected',
    'data_source_primary',
    'data_source_secondary',
    'notes',
    'cpi_index_used',
    'ransom_source',
    'incident_date',
    'industry_secondary',
    'direct_loss_method',
    'country_hq',
    'attack_vector_secondary',
    'sector_index',
]

df_gold_raw = silver_ml.drop(columns=[c for c in DROP_COLS if c in silver_ml.columns])
X = df_gold_raw.drop(columns=[TARGET])
y = df_gold_raw[TARGET].astype(int)

X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

OUTLIER_COLS = ['company_revenue_usd', 'employee_count']

def iqr_caps_from_train(series: pd.Series) -> tuple[float, float]:
    q1, q3 = series.dropna().quantile([0.25, 0.75])
    iqr = q3 - q1
    return float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr)

outlier_caps: dict[str, dict[str, float | int]] = {}
for col in OUTLIER_COLS:
    lower, upper = iqr_caps_from_train(X_train_raw[col])
    train_outliers = int(((X_train_raw[col] < lower) | (X_train_raw[col] > upper)).sum())
    test_outliers = int(((X_test_raw[col] < lower) | (X_test_raw[col] > upper)).sum())
    outlier_caps[col] = {
        'lower': lower,
        'upper': upper,
        'train_outliers_capped': train_outliers,
        'test_outliers_capped': test_outliers,
        'fit_scope': 'treino',
    }

X_train = X_train_raw.copy()
X_test = X_test_raw.copy()
for col, caps in outlier_caps.items():
    X_train[col] = X_train[col].clip(lower=caps['lower'], upper=caps['upper'])
    X_test[col] = X_test[col].clip(lower=caps['lower'], upper=caps['upper'])

ORDINAL_COLS = ['attack_vector_primary', 'attribution_confidence', 'porte_empresa']
ORDINAL_CATS = [
    ['phishing', 'ddos', 'malware', 'trojan', 'data_breach', 'supply_chain', 'backdoor', 'apt', 'ransomware'],
    ['unknown', 'suspected', 'probable', 'confirmed'],
    ['micro', 'pequena', 'media', 'grande'],
]
OHE_COLS = ['industry_primary', 'data_source_type', 'data_type']
NUMERIC_COLS = [
    c for c in X_train.select_dtypes(include='number').columns
    if c not in ['flag_ransomware', 'flag_atribuicao_conhecida', 'ano_incidente',
                 'mes_incidente', 'trimestre_incidente', 'confidence_tier']
]
BOOL_COLS = [
    'is_public_company',
    'incident_date_estimated',
    'earnings_announcement_within_7d',
    'flag_ransomware',
    'flag_atribuicao_conhecida',
]
PASSTHROUGH_COLS = ['ano_incidente', 'mes_incidente', 'trimestre_incidente', 'confidence_tier']

# Keep only columns present in case source schema changes.
ORDINAL_COLS = [c for c in ORDINAL_COLS if c in X_train.columns]
OHE_COLS = [c for c in OHE_COLS if c in X_train.columns]
NUMERIC_COLS = [c for c in NUMERIC_COLS if c in X_train.columns]
BOOL_COLS = [c for c in BOOL_COLS if c in X_train.columns]
PASSTHROUGH_COLS = [c for c in PASSTHROUGH_COLS if c in X_train.columns]

ordinal_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='nao_informado')),
    ('encoder', OrdinalEncoder(
        categories=ORDINAL_CATS[:len(ORDINAL_COLS)],
        handle_unknown='use_encoded_value',
        unknown_value=-1,
    )),
])

ohe_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='nao_informado')),
    ('encoder', OneHotEncoder(sparse_output=False, handle_unknown='ignore', drop='first')),
])

numeric_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', RobustScaler()),
])

bool_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
])

preprocessor = ColumnTransformer(
    transformers=[
        ('ordinal', ordinal_pipe, ORDINAL_COLS),
        ('ohe', ohe_pipe, OHE_COLS),
        ('numeric', numeric_pipe, NUMERIC_COLS),
        ('bool', bool_pipe, BOOL_COLS),
        ('passthrough', 'passthrough', PASSTHROUGH_COLS),
    ],
    remainder='drop',
)
preprocessor.fit(X_train)

# Feature names
feature_names = []
feature_names.extend(ORDINAL_COLS)
if OHE_COLS:
    feature_names.extend(
        preprocessor.named_transformers_['ohe'].named_steps['encoder'].get_feature_names_out(OHE_COLS).tolist()
    )
feature_names.extend(NUMERIC_COLS)
feature_names.extend(BOOL_COLS)
feature_names.extend(PASSTHROUGH_COLS)

X_train_gold = pd.DataFrame(preprocessor.transform(X_train), columns=feature_names, index=X_train.index)
X_test_gold = pd.DataFrame(preprocessor.transform(X_test), columns=feature_names, index=X_test.index)

df_train_gold = X_train_gold.copy()
df_train_gold[TARGET] = y_train.values
df_test_gold = X_test_gold.copy()
df_test_gold[TARGET] = y_test.values

df_train_gold.to_parquet(GOLD_DIR / 'gold_train.parquet', index=False)
df_test_gold.to_parquet(GOLD_DIR / 'gold_test.parquet', index=False)
with open(GOLD_DIR / 'preprocessor.pkl', 'wb') as f:
    pickle.dump({
        'drop_cols': DROP_COLS,
        'outlier_caps': outlier_caps,
        'preprocessor': preprocessor,
        'feature_names': feature_names,
        'target': TARGET,
        'random_state': RANDOM_STATE,
        'test_size': TEST_SIZE,
    }, f)

# Train Gold models
models = {
    'gold_tree_depth_3_gini': DecisionTreeClassifier(
        criterion='gini', max_depth=3, min_samples_leaf=10, random_state=RANDOM_STATE
    ),
    'gold_tree_depth_6_entropy': DecisionTreeClassifier(
        criterion='entropy', max_depth=6, min_samples_leaf=5, random_state=RANDOM_STATE
    ),
}

metrics_rows = []
fitted_models = {}
for name, clf in models.items():
    clf.fit(X_train_gold, y_train)
    pred = clf.predict(X_test_gold)
    metrics_rows.append({
        'dataset': 'Ouro',
        'model': name,
        'criterion': clf.criterion,
        'max_depth': clf.max_depth,
        'min_samples_leaf': clf.min_samples_leaf,
        'accuracy': accuracy_score(y_test, pred),
        'precision': precision_score(y_test, pred, zero_division=0),
        'recall': recall_score(y_test, pred, zero_division=0),
        'f1': f1_score(y_test, pred, zero_division=0),
    })
    fitted_models[name] = clf

# Baseline Silver model: same split, minimal preprocessing, no outlier capping or scaling.
X_train_silver = X_train_raw.copy()
X_test_silver = X_test_raw.copy()
cat_cols = X_train_silver.select_dtypes(include=['object', 'string', 'category']).columns.tolist()
bool_baseline_cols = X_train_silver.select_dtypes(include=['boolean']).columns.tolist()
for _col in cat_cols:
    X_train_silver[_col] = X_train_silver[_col].astype('object').where(X_train_silver[_col].notna(), np.nan)
    X_test_silver[_col] = X_test_silver[_col].astype('object').where(X_test_silver[_col].notna(), np.nan)
for _col in bool_baseline_cols:
    X_train_silver[_col] = X_train_silver[_col].astype('object').where(X_train_silver[_col].notna(), np.nan)
    X_test_silver[_col] = X_test_silver[_col].astype('object').where(X_test_silver[_col].notna(), np.nan)
num_cols = [c for c in X_train_silver.columns if c not in cat_cols + bool_baseline_cols]

silver_preprocessor = ColumnTransformer(
    transformers=[
        ('categorical', Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='nao_informado')),
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
        ]), cat_cols),
        ('boolean', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
        ]), bool_baseline_cols),
        ('numeric', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
        ]), num_cols),
    ],
    remainder='drop',
)
X_train_silver_tr = silver_preprocessor.fit_transform(X_train_silver)
X_test_silver_tr = silver_preprocessor.transform(X_test_silver)
silver_model = DecisionTreeClassifier(
    criterion='entropy', max_depth=6, min_samples_leaf=5, random_state=RANDOM_STATE
)
silver_model.fit(X_train_silver_tr, y_train)
silver_pred = silver_model.predict(X_test_silver_tr)
metrics_rows.append({
    'dataset': 'Prata',
    'model': 'silver_baseline_tree_depth_6_entropy',
    'criterion': silver_model.criterion,
    'max_depth': silver_model.max_depth,
    'min_samples_leaf': silver_model.min_samples_leaf,
    'accuracy': accuracy_score(y_test, silver_pred),
    'precision': precision_score(y_test, silver_pred, zero_division=0),
    'recall': recall_score(y_test, silver_pred, zero_division=0),
    'f1': f1_score(y_test, silver_pred, zero_division=0),
})

metrics_df = pd.DataFrame(metrics_rows)
metrics_df.sort_values(['dataset', 'f1'], ascending=[True, False]).to_csv(REPORTS_DIR / 'model_metrics.csv', index=False)
comparison_df = metrics_df.loc[
    metrics_df['model'].isin(['gold_tree_depth_6_entropy', 'silver_baseline_tree_depth_6_entropy'])
].copy()
comparison_df.to_csv(REPORTS_DIR / 'model_comparison_silver_gold.csv', index=False)

best_gold_name = metrics_df[metrics_df['dataset'].eq('Ouro')].sort_values('f1', ascending=False).iloc[0]['model']
best_gold_model = fitted_models[best_gold_name]
best_gold_pred = best_gold_model.predict(X_test_gold)

# Figures: confusion matrix and tree visualization
cm = confusion_matrix(y_test, best_gold_pred)
fig, ax = plt.subplots(figsize=(6, 5))
ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['baixo impacto', 'alto impacto']).plot(ax=ax, values_format='d', colorbar=False)
ax.set_title(f'Matriz de confusão - {best_gold_name}')
plt.tight_layout()
plt.savefig(FIG_DIR / 'confusion_matrix_gold_decision_tree.png', dpi=180, bbox_inches='tight')
plt.close(fig)

fig, ax = plt.subplots(figsize=(24, 12))
plot_tree(
    best_gold_model,
    feature_names=feature_names,
    class_names=['baixo impacto', 'alto impacto'],
    filled=False,
    rounded=True,
    max_depth=3,
    fontsize=8,
    ax=ax,
)
ax.set_title(f'Árvore de decisão - {best_gold_name} (visualização até profundidade 3)')
plt.tight_layout()
plt.savefig(FIG_DIR / 'decision_tree_gold_best.png', dpi=180, bbox_inches='tight')
plt.close(fig)

with open(MODELS_DIR / 'decision_tree_gold_best.pkl', 'wb') as f:
    pickle.dump({'model_name': best_gold_name, 'model': best_gold_model, 'feature_names': feature_names}, f)
with open(MODELS_DIR / 'decision_tree_silver_baseline.pkl', 'wb') as f:
    pickle.dump({'model': silver_model, 'preprocessor': silver_preprocessor}, f)

# -----------------------------------------------------------------------------
# 3. Transformation table, quality report, leakage checklist and lineage
# -----------------------------------------------------------------------------
outlier_text = '; '.join(
    f"{col}: treino={caps['train_outliers_capped']}, teste={caps['test_outliers_capped']}, limites=[{caps['lower']:.2f}, {caps['upper']:.2f}]"
    for col, caps in outlier_caps.items()
)
transf_rows = [
    ('company_revenue_usd', 'Outlier - Winsorization IQR fitado no treino', f"Capping aplicado com limites calculados somente no treino. {outlier_text}"),
    ('employee_count', 'Outlier - Winsorization IQR fitado no treino', f"Capping aplicado com limites calculados somente no treino. {outlier_text}"),
    (', '.join(NUMERIC_COLS), 'Scaling - RobustScaler', 'Escalas numéricas distintas; scaler fitado somente no treino e aplicado no teste via transform.'),
    (', '.join(NUMERIC_COLS), 'Missing - SimpleImputer(strategy=median)', 'Medianas calculadas somente no treino para variáveis numéricas.'),
    (', '.join(ORDINAL_COLS + OHE_COLS), 'Missing - SimpleImputer(strategy=constant, fill_value=nao_informado)', 'Cria categoria explícita para ausência em campos categóricos.'),
    (', '.join(BOOL_COLS), 'Missing - SimpleImputer(strategy=most_frequent)', 'Imputação por moda para flags booleanos.'),
    (', '.join(ORDINAL_COLS), 'Encoding 1 - OrdinalEncoder', 'Categorias com ordenação operacional definida: vetor, confiança de atribuição e porte.'),
    (', '.join(OHE_COLS), 'Encoding 2 - OneHotEncoder(drop=first)', 'Categorias nominais sem ordem: setor, tipo de fonte e tipo de dado.'),
    (', '.join(PASSTHROUGH_COLS), 'Passthrough', 'Variáveis discretas já numéricas preservadas sem transformação adicional.'),
    (', '.join(DROP_COLS), 'Descarte - leakage, alta cardinalidade ou texto livre', 'Remove identificadores, URLs, texto livre, datas brutas ou metadados sem uso preditivo seguro.'),
    ('Pipeline completo', 'fit/transform', 'Split estratificado antes de outliers, imputação, encoding e scaling; todos os objetos são fitados no treino.'),
]
pd.DataFrame(transf_rows, columns=['Coluna(s)', 'Técnica', 'Justificativa']).to_csv(DOCS_DIR / 'gold_transformations.csv', index=False)

# Quality report
silver_target_dist = silver_ml[TARGET].value_counts().sort_index().to_dict()
gold_train_target_dist = df_train_gold[TARGET].value_counts().sort_index().to_dict()
gold_test_target_dist = df_test_gold[TARGET].value_counts().sort_index().to_dict()
null_top_silver = silver_ml.isna().sum().sort_values(ascending=False).head(10)
quality_md = f"""# Relatório de qualidade - camadas Prata e Ouro

Gerado em UTC: {datetime.now(timezone.utc).isoformat()}

## Visão geral

| Dataset | Linhas | Colunas | Nulos totais | Duplicatas completas |
|---|---:|---:|---:|---:|
| silver_master.parquet | {silver_master.shape[0]} | {silver_master.shape[1]} | {int(silver_master.isna().sum().sum())} | {int(silver_master.duplicated().sum())} |
| silver_master_ml.parquet | {silver_ml.shape[0]} | {silver_ml.shape[1]} | {int(silver_ml.isna().sum().sum())} | {int(silver_ml.duplicated().sum())} |
| gold_train.parquet | {df_train_gold.shape[0]} | {df_train_gold.shape[1]} | {int(df_train_gold.isna().sum().sum())} | {int(df_train_gold.duplicated().sum())} |
| gold_test.parquet | {df_test_gold.shape[0]} | {df_test_gold.shape[1]} | {int(df_test_gold.isna().sum().sum())} | {int(df_test_gold.duplicated().sum())} |

## Representatividade do target

| Conjunto | Classe 0 | Classe 1 | Percentual classe 1 |
|---|---:|---:|---:|
| silver_master_ml | {silver_target_dist.get(0, 0)} | {silver_target_dist.get(1, 0)} | {silver_ml[TARGET].mean():.2%} |
| treino Gold | {gold_train_target_dist.get(0, 0)} | {gold_train_target_dist.get(1, 0)} | {df_train_gold[TARGET].mean():.2%} |
| teste Gold | {gold_test_target_dist.get(0, 0)} | {gold_test_target_dist.get(1, 0)} | {df_test_gold[TARGET].mean():.2%} |

A divisão treino/teste usa `train_test_split(..., stratify=y, random_state=42)`, preservando proporções semelhantes da variável alvo nos dois conjuntos.

## Nulos mais relevantes na Prata ML

| Coluna | Nulos |
|---|---:|
"""
for col, n in null_top_silver.items():
    quality_md += f"| {col} | {int(n)} |\n"
quality_md += f"""

## Validação da Ouro

- Nulos no treino Gold: {int(df_train_gold.isna().sum().sum())}.
- Nulos no teste Gold: {int(df_test_gold.isna().sum().sum())}.
- Número de features após transformação: {len(feature_names)}.
- Outliers tratados em `company_revenue_usd` e `employee_count` com limites calculados exclusivamente no treino.
- Objetos de pré-processamento fitados no treino e aplicados no teste via `transform`.

## Outliers

| Coluna | Limite inferior | Limite superior | Outliers no treino | Outliers no teste |
|---|---:|---:|---:|---:|
"""
for col, caps in outlier_caps.items():
    quality_md += f"| {col} | {caps['lower']:.2f} | {caps['upper']:.2f} | {caps['train_outliers_capped']} | {caps['test_outliers_capped']} |\n"
quality_md += f"""

## Modelagem

As métricas estão em `reports/model_metrics.csv` e a comparação Prata vs Ouro em `reports/model_comparison_silver_gold.csv`.

| Dataset | Modelo | Accuracy | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
"""
for _, r in metrics_df.iterrows():
    quality_md += f"| {r['dataset']} | {r['model']} | {r['accuracy']:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1']:.4f} |\n"
quality_md += "\n## Observações\n\n- A matriz de confusão está em `reports/figures/confusion_matrix_gold_decision_tree.png`.\n- A visualização da árvore está em `reports/figures/decision_tree_gold_best.png`.\n- O objeto `preprocessor.pkl` contém o transformador, colunas removidas, limites de outlier e nomes das features.\n"
(DOCS_DIR / 'quality_report_silver_gold.md').write_text(quality_md, encoding='utf-8')

# Anti-leakage checklist update
anti_path = DOCS_DIR / 'anti_leakage_checklist.md'
anti_existing = anti_path.read_text(encoding='utf-8') if anti_path.exists() else '# Checklist anti-leakage\n'
anti_add = f"""

## Atualização da camada Ouro

- O split treino/teste é realizado antes de imputação, encoding, scaling e tratamento de outliers.
- Os limites de Winsorization por IQR são calculados exclusivamente no treino e aplicados no teste sem refit.
- O `ColumnTransformer` é ajustado com `fit` apenas no treino e aplicado no teste com `transform`.
- Colunas removidas antes da modelagem: `{', '.join(DROP_COLS)}`.
- Artefato persistido: `data/gold/preprocessor.pkl`, com colunas removidas, limites de outlier, transformador e nomes das features.
"""
if '## Atualização da camada Ouro' not in anti_existing:
    anti_existing += anti_add
else:
    anti_existing = anti_existing.split('## Atualização da camada Ouro')[0] + anti_add
anti_path.write_text(anti_existing, encoding='utf-8')

# Lineage JSON/MD/Mermaid/PNG
lineage = {
    'pipeline': 'cybersecurity_bronze_silver_gold_mlready',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'nodes': [
        {'id': 'src_inc', 'label': 'incidents_master.csv', 'type': 'source'},
        {'id': 'src_fin', 'label': 'financial_impact.csv', 'type': 'source'},
        {'id': 'src_mkt', 'label': 'market_impact.csv', 'type': 'source'},
        {'id': 'bronze', 'label': 'Bronze: ingestão + qualidade', 'type': 'process'},
        {'id': 'silver_clean', 'label': 'Prata: limpeza + integração', 'type': 'process'},
        {'id': 'silver_master', 'label': 'silver_master.parquet', 'type': 'sink'},
        {'id': 'anti_leakage', 'label': 'Filtro anti-leakage', 'type': 'process'},
        {'id': 'silver_ml', 'label': 'silver_master_ml.parquet', 'type': 'sink'},
        {'id': 'eda', 'label': 'EDA orientada a hipóteses', 'type': 'analysis'},
        {'id': 'gold_preprocess', 'label': 'Ouro: split + outliers + imputação + encoding + scaling', 'type': 'process'},
        {'id': 'gold_train', 'label': 'gold_train.parquet', 'type': 'sink'},
        {'id': 'gold_test', 'label': 'gold_test.parquet', 'type': 'sink'},
        {'id': 'dt_models', 'label': 'Decision Trees + métricas', 'type': 'model'},
        {'id': 'comparison', 'label': 'Comparação Prata vs Ouro', 'type': 'analysis'},
        {'id': 'pyspark', 'label': 'Refatoração PySpark', 'type': 'process'},
    ],
    'edges': [
        ['src_inc', 'bronze'], ['src_fin', 'bronze'], ['src_mkt', 'bronze'],
        ['bronze', 'silver_clean'], ['silver_clean', 'silver_master'], ['silver_clean', 'anti_leakage'],
        ['anti_leakage', 'silver_ml'], ['silver_master', 'eda'], ['silver_ml', 'gold_preprocess'],
        ['gold_preprocess', 'gold_train'], ['gold_preprocess', 'gold_test'],
        ['gold_train', 'dt_models'], ['gold_test', 'dt_models'], ['silver_ml', 'comparison'],
        ['dt_models', 'comparison'], ['silver_master', 'pyspark'], ['silver_ml', 'pyspark'],
    ],
}
(DOCS_DIR / 'data_lineage.json').write_text(json.dumps(lineage, indent=2, ensure_ascii=False), encoding='utf-8')
mermaid = """flowchart LR
    A[incidents_master.csv] --> D[Bronze: ingestão + qualidade]
    B[financial_impact.csv] --> D
    C[market_impact.csv] --> D
    D --> E[Prata: limpeza + integração]
    E --> F[silver_master.parquet]
    E --> G[Filtro anti-leakage]
    G --> H[silver_master_ml.parquet]
    F --> I[EDA orientada a hipóteses]
    H --> J[Ouro: split + outliers + imputação + encoding + scaling]
    J --> K[gold_train.parquet]
    J --> L[gold_test.parquet]
    K --> M[Decision Trees + métricas]
    L --> M
    H --> N[Comparação Prata vs Ouro]
    M --> N
    F --> O[Refatoração PySpark]
    H --> O
"""
(DOCS_DIR / 'data_lineage.mmd').write_text(mermaid, encoding='utf-8')
(DOCS_DIR / 'data_lineage.md').write_text('# Data Lineage\n\n```mermaid\n' + mermaid + '\n```\n', encoding='utf-8')

# Draw simple lineage PNG
positions = {
    'A': (0.06, 0.80, 'incidents\nmaster.csv'), 'B': (0.06, 0.62, 'financial\nimpact.csv'), 'C': (0.06, 0.44, 'market\nimpact.csv'),
    'D': (0.22, 0.62, 'Bronze\ningestão + qualidade'), 'E': (0.38, 0.62, 'Prata\nlimpeza + integração'),
    'F': (0.54, 0.76, 'silver_master\n.parquet'), 'G': (0.54, 0.52, 'Filtro\nanti-leakage'),
    'H': (0.68, 0.52, 'silver_master_ml\n.parquet'), 'I': (0.68, 0.82, 'EDA\nhipóteses'),
    'J': (0.82, 0.52, 'Ouro\npreprocessamento'), 'K': (0.94, 0.64, 'gold_train\n.parquet'),
    'L': (0.94, 0.44, 'gold_test\n.parquet'), 'M': (0.82, 0.28, 'Decision Trees\n+ métricas'),
    'N': (0.94, 0.28, 'Comparação\nPrata vs Ouro'), 'O': (0.54, 0.24, 'PySpark\nrefatoração'),
}
edges = [('A','D'),('B','D'),('C','D'),('D','E'),('E','F'),('E','G'),('G','H'),('F','I'),('H','J'),('J','K'),('J','L'),('K','M'),('L','M'),('H','N'),('M','N'),('F','O'),('H','O')]
fig, ax = plt.subplots(figsize=(22, 9))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

def draw_box(x, y, text):
    w, h = 0.12, 0.10
    patch = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle='round,pad=0.02', fill=False, linewidth=1.2)
    ax.add_patch(patch)
    ax.text(x, y, text, ha='center', va='center', fontsize=9)

for x, y, text in positions.values():
    draw_box(x, y, text)
for a, b in edges:
    xa, ya, _ = positions[a]
    xb, yb, _ = positions[b]
    ax.add_patch(FancyArrowPatch((xa + 0.06, ya), (xb - 0.06, yb), arrowstyle='->', mutation_scale=12, linewidth=1.0))
plt.tight_layout()
plt.savefig(DOCS_DIR / 'data_lineage.png', dpi=180, bbox_inches='tight')
plt.close(fig)

# -----------------------------------------------------------------------------
print('Artefatos Gold/ML atualizados com sucesso.')
print(metrics_df.to_string(index=False))
