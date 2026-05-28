# Interpretação das visualizações da EDA

| Visualização | Hipótese/objetivo | Interpretação orientada a decisão |
|---|---|---|
| `distribuicao_label_alto_impacto.png` | Distribuição da variável-alvo | A distribuição confirma a necessidade de manter divisão estratificada para preservar a proporção das classes em treino e teste. |
| `h1_perda_por_vetor_boxplot.png` | H1 / outliers por vetor | A presença de caudas longas e perdas extremas justifica tratamento robusto de outliers e uso de modelos menos sensíveis a escala. |
| `h1_cdf_ransomware_vs_outros.png` | H1 / comparação ransomware vs demais vetores | A comparação acumulada ajuda a verificar se ransomware concentra perdas maiores; a decisão é manter `attack_vector_primary` como feature categórica relevante. |
| `h2_heatmap_setor_impacto.png` | H2 / recorte por setor | Saúde e Finanças não concentram sozinhos o maior impacto; a decisão é usar setor como variável de segmentação sem regra manual fixa. |
| `h2_correlacao_variaveis_chave.png` | Correlação de variáveis-chave | As correlações lineares são limitadas, reforçando o uso de Árvores de Decisão para capturar relações não-lineares. |
| `h3_deteccao_por_porte.png` | H3 / distribuição por porte | O porte da empresa mostra diferenças operacionais relevantes e permanece como feature segura para modelagem. |
| `h3_scatter_deteccao_downtime.png` | H3 / detecção tardia vs downtime | Como tempo até descoberta é informação posterior ao incidente, ele fica restrito à análise operacional e não entra no ML-ready. |
| `downtime_mediano_por_vetor.png` | Recorte por vetor | Apoia a seleção de variáveis relacionadas ao tipo de ataque e ajuda a interpretar diferenças operacionais entre vetores. |
| `incidentes_por_ano_e_vetor.png` | Evolução temporal | Ajuda a observar padrões de volume por ano e vetor, sem inserir variáveis temporais posteriores ao evento no modelo. |
| `top_paises_incidentes.png` | Recorte geográfico | Mostra concentração geográfica dos incidentes e apoia decisões de segmentação, embora `country_hq` tenha sido removido do ML-ready por escolha de simplificação e risco de cardinalidade/viés. |
