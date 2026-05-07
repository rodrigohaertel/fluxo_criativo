# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versionamento [SemVer](https://semver.org/).

## [0.1.0] — 2026-04-24 — primeira versão alpha

### Python suportado

- **Recomendado:** Python 3.12 (melhor compatibilidade com `facebook-business` SDK)
- **Suportado:** 3.11, 3.12, 3.13
- **Não recomendado:** 3.14+ (wheels faltando em algumas deps)

Scripts `install.sh` e `install.bat` detectam `python3.12`/`py -3.12` automaticamente quando disponível.

### Adicionado

**Core**
- Package Python standalone com CLI `trafego` e UI Web Streamlit
- Setup wizard interativo de 7 passos
- Multi-conta nativo com aliases
- 15+ presets de período + 7 comparativos (WoW, MoM, YoY, custom)
- Cache SQLite local com TTL configurável
- Sistema de perfis (`perpetuo`, `lancamento`) com thresholds customizáveis
- Fases do funil configuráveis (4 templates prontos: genérico, TOFU/MOFU/BOFU, captura/relacionamento/venda, perpétuo 6 fases)
- Baseline rolling 30d por produto + fase (P25/P50/P75)
- Integração Meta Marketing API v25 (obrigatória)
- Integração Google Ads (opcional)
- Integração Hotmart (opcional)

**Módulo Campanhas (6 análises)**
- Fadiga Criativa — 5 sinais combinados
- Auditoria de Campanha — health check estrutural
- Top Performers & Escalada — sugestão de incremento de budget
- Comparativo Período a Período
- Performance por Fase do Funil
- Dayparting (heatmap dia × hora)

**Módulo Criativos**
- Ranking com score composto (40% hook + 30% hold + 20% CTR + 10% CPA)
- DNA dos winners (taxonomia visual + copy)
- Galeria HTML interativa standalone (lightbox, tema dark)

**Módulo Funil**
- Waterfall completo Impression → Purchase
- Detector automático de gargalo
- Playbook de correção por etapa

**Módulo Cross-canal**
- Meta + Google Ads + Hotmart agregados
- ROAS blended
- Hotmart como fonte de verdade de receita

**UI Web Streamlit**
- 7 páginas: Home, Campanhas, Criativos, Funil, Cross-canal, Configurações, Histórico
- Tema dark por default
- Download de relatórios markdown e HTML

**Documentação**
- 13 arquivos em `docs/` (instalação, setup, guias das análises, glossário, troubleshooting, FAQ, roteiro de aula)
- README com badges e quickstart
- CONTRIBUTING e CODE_OF_CONDUCT

**Testes**
- 127+ testes unitários cobrindo fórmulas, períodos, fadiga, taxonomia, classificação de fases, comparativo

### Conhecido / não implementado em v0.1

- Funil depende de pixel CAPI para eventos de checkout/purchase quando usa Hotmart
- Atribuição cross-canal é last-click (sem multi-touch)
- Face detection em criativos exige extra `[vision]` separado
- Sem alertas proativos automatizados (WhatsApp, Slack) — planejado para v0.2
- Sem anomaly detection (Z-score) — v0.2
- Sem export automatizado para PDF/PPT — v0.2
- Ranking de criativos penaliza imagens estáticas (hook rate zero) — ranking separado por formato em v0.2

[0.1.0]: https://github.com/trafegopaid/skill-analise/releases/tag/v0.1.0
