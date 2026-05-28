# Checklist Anti-Leakage

| dataset | coluna | tipo de risco | ação | justificativa |
|---|---|---|---|---|
| incidents_master | quality_score | retroativo | remover | score calculado após curadoria do caso |
| incidents_master | quality_grade | retroativo | remover | faixa derivada após avaliação do caso |
| incidents_master | review_flag | retroativo | remover | sinal de revisão humana posterior |
| incidents_master | discovery_date | futuro | remover | informação conhecida após o incidente |
| incidents_master | disclosure_date | futuro | remover | informação conhecida após o incidente |
| incidents_master | updated_at | técnico/retroativo | remover | carimbo de atualização posterior |
| incidents_master | created_at | técnico | remover | carimbo de carga/cadastro, sem valor preditivo |
| incidents_master | dias_ate_descoberta | futuro | remover | derivada de discovery_date |
| incidents_master | dias_ate_divulgacao | futuro | remover | derivada de disclosure_date |
| incidents_master | downtime_hours | target leakage | remover_do_ml | usado na definição do label de alto impacto |
| incidents_master | data_compromised_records | target leakage | remover_do_ml | usado na definição do label de alto impacto |
| financial_impact | direct_loss_usd | desfecho | remover_do_ml | valor conhecido após avaliação financeira |
| financial_impact | ransom_demanded_usd | desfecho | remover_do_ml | evento posterior ao incidente |
| financial_impact | ransom_paid_usd | desfecho | remover_do_ml | evento posterior ao incidente |
| financial_impact | recovery_cost_usd | desfecho | remover_do_ml | custo posterior ao incidente |
| financial_impact | legal_fees_usd | desfecho | remover_do_ml | custo posterior ao incidente |
| financial_impact | regulatory_fine_usd | desfecho | remover_do_ml | desdobramento regulatório posterior |
| financial_impact | insurance_payout_usd | desfecho | remover_do_ml | valor posterior ao incidente |
| financial_impact | total_loss_usd | desfecho consolidado | remover_do_ml | agrega consequências futuras |
| financial_impact | total_loss_method | desfecho consolidado | remover_do_ml | metadado de cálculo posterior |
| financial_impact | total_loss_lower_bound | desfecho consolidado | remover_do_ml | estimativa posterior |
| financial_impact | total_loss_upper_bound | desfecho consolidado | remover_do_ml | estimativa posterior |
| financial_impact | inflation_adjusted_usd | desfecho consolidado | remover_do_ml | valor ajustado retroativamente |
| financial_impact | updated_at | técnico/retroativo | remover_do_ml | carimbo de atualização posterior |
| financial_impact | created_at | técnico | remover_do_ml | carimbo operacional |
| financial_impact | proporcao_seguro | desfecho derivado | remover_do_ml | derivada de insurance_payout e total_loss |
| financial_impact | flag_resgate_pago | desfecho derivado | remover_do_ml | só conhecido após o caso |
| market_impact | price_disclosure_day | futuro | remover_do_ml | preço observado na divulgação |
| market_impact | price_1d_after | futuro | remover_do_ml | preço posterior ao evento |
| market_impact | price_7d_after | futuro | remover_do_ml | preço posterior ao evento |
| market_impact | price_30d_after | futuro | remover_do_ml | preço posterior ao evento |
| market_impact | volume_disclosure_day | futuro | remover_do_ml | volume observado na divulgação |
| market_impact | sector_return_same_period | futuro | remover_do_ml | janela posterior ao evento |
| market_impact | abnormal_return_1d | futuro | remover_do_ml | retorno calculado após divulgação |
| market_impact | abnormal_return_7d | futuro | remover_do_ml | retorno calculado após divulgação |
| market_impact | abnormal_return_30d | futuro | remover_do_ml | retorno calculado após divulgação |
| market_impact | car_neg1_to_pos1 | futuro | remover_do_ml | janela de evento com informação posterior |
| market_impact | car_0_to_7 | futuro | remover_do_ml | janela de evento posterior |
| market_impact | car_0_to_30 | futuro | remover_do_ml | janela de evento posterior |
| market_impact | car_0_to_90 | futuro | remover_do_ml | janela de evento posterior |
| market_impact | t_statistic_1d | futuro | remover_do_ml | estatística calculada após o evento |
| market_impact | p_value_1d | futuro | remover_do_ml | estatística calculada após o evento |
| market_impact | t_statistic_30d | futuro | remover_do_ml | estatística calculada após o evento |
| market_impact | p_value_30d | futuro | remover_do_ml | estatística calculada após o evento |
| market_impact | market_cap_at_disclosure | futuro | remover_do_ml | market cap observado na divulgação |
| market_impact | volume_ratio_disclosure | futuro | remover_do_ml | derivado da divulgação |
| market_impact | post_incident_volatility_30d | futuro | remover_do_ml | volatilidade após o incidente |
| market_impact | days_to_price_recovery | futuro | remover_do_ml | desfecho posterior |
| market_impact | aumento_volatilidade | futuro | remover_do_ml | derivada de volatilidade pós-incidente |
| market_impact | flag_queda_acentuada | futuro | remover_do_ml | derivada de abnormal_return pós-evento |
| market_impact | updated_at | técnico/retroativo | remover_do_ml | carimbo de atualização posterior |
| market_impact | created_at | técnico | remover_do_ml | carimbo operacional |

## Atualização da camada Ouro

- O split treino/teste é realizado antes de imputação, encoding, scaling e tratamento de outliers.
- Os limites de Winsorization por IQR são calculados exclusivamente no treino e aplicados no teste sem refit.
- O `ColumnTransformer` é ajustado com `fit` apenas no treino e aplicado no teste com `transform`.
- Colunas removidas antes da modelagem: `incident_id, company_name, stock_ticker, attack_chain, attributed_group, systems_affected, data_source_primary, data_source_secondary, notes, cpi_index_used, ransom_source, incident_date, industry_secondary, direct_loss_method, country_hq, attack_vector_secondary, sector_index`.
- Artefato persistido: `data/gold/preprocessor.pkl`, com colunas removidas, limites de outlier, transformador e nomes das features.
