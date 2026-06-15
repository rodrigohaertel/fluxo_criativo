"""Módulo Modo Demo — cenários D1-D7 com dados fictícios + "Ensine Isso".

Gera análises completas sem Meta API real. Para gravação de aula, apresentações
e alunos praticarem sem ter conta Meta configurada ainda.
"""

from __future__ import annotations

from typing import Any

from trafego_analysis.core import demo_data, report


def gerar_demo(cenario_id: str) -> tuple[str, Any]:
    """cenario_id: 'D1' | 'D2' | 'D3' | 'D4' | 'D5' | 'D6' | 'D7'."""
    cid = cenario_id.upper()

    if cid == "D6":
        dados = demo_data.get_cenario_d6()
        tpl = "demo_d6.md.j2"
    elif cid == "D7":
        dados = demo_data.get_cenario_d7()
        tpl = "demo_d7.md.j2"
    elif cid in ("D1", "D2", "D3", "D4", "D5"):
        dados = demo_data.get_cenario_base()
        tpl = "demo_base.md.j2"
    else:
        raise ValueError(f"Cenário desconhecido: {cenario_id}. Use D1-D7.")

    context = {
        "cenario_id": cid,
        "dados": dados,
        "ensine_isso": demo_data.ensine_isso_todos(),
    }
    filename = report.build_output_filename(f"demo-{cid.lower()}")
    return report.render_markdown(tpl, context, output_filename=filename)
