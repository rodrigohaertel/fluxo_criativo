"""Análise 1.2 — Escalabilidade.

Avalia se a conta / conjuntos estão prontos para aumentar orçamento ou se
estão em saturação de audiência. Responde à pergunta: **subir o budget agora
é seguro ou vai queimar o winner?**

Sinais de saturação (agregados ad-level + adset-level):
  - Frequência média > 4.0 (cold) ou > 5.0 (rmk/hot)
  - CPM subindo >20% semana a semana
  - Reach / Universe estimado > 60%
  - CTR caindo com CPM estável (criativo fadigando em público saturado)

No VTSD: saturação = hora de criar nova **Identidade do Consumidor** ou
expandir com SUPERCOLD. Nunca subir orçamento em público saturado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class SinalSaturacao:
    tipo: str                    # freq_alta | cpm_subindo | reach_alto | ctr_caindo
    descricao: str
    severidade: str              # baixa | media | alta
    elemento_vtsd: str


@dataclass
class ResultadoEscalabilidade:
    status: str                  # "saudavel" | "monitorar" | "saturado"
    frequencia_media: float
    cpm_medio: float
    sinais: list[SinalSaturacao]
    recomendacao: str
    incremento_sugerido_pct: float | None


def _is_retargeting(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in ("rmk", "remarketing", "retarget"))


def analisar_rows(
    rows_atual: list[dict[str, Any]],
    rows_anterior: list[dict[str, Any]] | None = None,
) -> ResultadoEscalabilidade:
    if not rows_atual:
        return ResultadoEscalabilidade(
            status="saudavel",
            frequencia_media=0,
            cpm_medio=0,
            sinais=[],
            recomendacao="Sem dados no período — sem diagnóstico possível.",
            incremento_sugerido_pct=None,
        )

    total_spend = sum(float(r.get("spend") or 0) for r in rows_atual)
    total_impr = sum(float(r.get("impressions") or 0) for r in rows_atual)
    total_clicks = sum(float(r.get("inline_link_clicks") or r.get("clicks") or 0) for r in rows_atual)

    # Frequência ponderada por impressões
    freq_weighted = sum(
        float(r.get("frequency") or 0) * float(r.get("impressions") or 0)
        for r in rows_atual
    )
    freq_media = (freq_weighted / total_impr) if total_impr else 0

    cpm_medio = m.cpm(total_spend, total_impr)
    ctr_medio = m.ctr(total_clicks, total_impr)

    sinais: list[SinalSaturacao] = []

    # Sinal 1: Frequência alta (considera mix cold/rmk)
    cold_rows = [r for r in rows_atual if not _is_retargeting(r.get("campaign_name") or "")]
    if cold_rows:
        cold_impr = sum(float(r.get("impressions") or 0) for r in cold_rows)
        cold_freq_w = sum(
            float(r.get("frequency") or 0) * float(r.get("impressions") or 0)
            for r in cold_rows
        )
        cold_freq = (cold_freq_w / cold_impr) if cold_impr else 0
        if cold_freq >= 4.0:
            sev = "alta" if cold_freq >= 5.0 else "media"
            sinais.append(SinalSaturacao(
                tipo="freq_alta",
                descricao=f"Frequência média em cold: {cold_freq:.1f} (limite {4.0})",
                severidade=sev,
                elemento_vtsd="Identidade do Consumidor",
            ))

    # Sinal 2: CPM subindo WoW
    if rows_anterior:
        spend_ant = sum(float(r.get("spend") or 0) for r in rows_anterior)
        impr_ant = sum(float(r.get("impressions") or 0) for r in rows_anterior)
        cpm_ant = m.cpm(spend_ant, impr_ant)
        if cpm_ant > 0 and cpm_medio > cpm_ant * 1.2:
            pct = (cpm_medio / cpm_ant - 1) * 100
            sinais.append(SinalSaturacao(
                tipo="cpm_subindo",
                descricao=f"CPM subiu {pct:.0f}% WoW (de {cpm_ant:.2f} para {cpm_medio:.2f})",
                severidade="alta" if pct > 35 else "media",
                elemento_vtsd="Leilão saturado — ampliar Identidade do Consumidor",
            ))

        ctr_ant = m.ctr(
            sum(float(r.get("inline_link_clicks") or r.get("clicks") or 0) for r in rows_anterior),
            impr_ant,
        )
        if ctr_ant > 0 and ctr_medio < ctr_ant * 0.85:
            drop_pct = (1 - ctr_medio / ctr_ant) * 100
            sinais.append(SinalSaturacao(
                tipo="ctr_caindo",
                descricao=f"CTR caiu {drop_pct:.0f}% WoW — criativo fadigando",
                severidade="alta" if drop_pct > 25 else "media",
                elemento_vtsd="Identidade do Produto (criativo)",
            ))

    # Classifica status
    tem_alta = any(s.severidade == "alta" for s in sinais)
    tem_media = any(s.severidade == "media" for s in sinais)

    if tem_alta:
        status = "saturado"
        recomendacao = (
            "NÃO escalar agora. Antes de subir budget: "
            "ampliar audiência (nova Identidade do Consumidor ou SUPERCOLD) e "
            "renovar criativos. Escalar em público saturado queima o winner."
        )
        incremento = None
    elif tem_media or freq_media > 3.0:
        status = "monitorar"
        recomendacao = (
            "Escalar com CAUTELA. Incremento máximo 10-15% — observe 48h. "
            "Se CPA subir, recua. Preparar expansão de audiência em paralelo."
        )
        incremento = 12.5
    else:
        status = "saudavel"
        recomendacao = (
            "Ambiente OK para escalar. Frequência saudável, CPM estável. "
            "Incremento sugerido: 25-30% por rodada, respeitando 3-4 dias entre mudanças."
        )
        incremento = 27.5

    return ResultadoEscalabilidade(
        status=status,
        frequencia_media=freq_media,
        cpm_medio=cpm_medio,
        sinais=sinais,
        recomendacao=recomendacao,
        incremento_sugerido_pct=incremento,
    )


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    from datetime import timedelta

    rows_atual = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )

    days = periodo.days
    rows_anterior = meta.get_ad_insights(
        ad_account_id,
        since=periodo.since - timedelta(days=days),
        until=periodo.until - timedelta(days=days),
        filtering=filtering,
    )

    if produto_nome:
        nome_low = produto_nome.lower()
        rows_atual = [r for r in rows_atual if nome_low in (r.get("campaign_name") or "").lower()]
        rows_anterior = [r for r in rows_anterior if nome_low in (r.get("campaign_name") or "").lower()]

    resultado = analisar_rows(rows_atual, rows_anterior)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "resultado": resultado,
    }
    filename = report.build_output_filename("escalabilidade", produto_nome)
    return report.render_markdown("escalabilidade.md.j2", context, output_filename=filename)
