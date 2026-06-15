"""CLI `trafego` — dispatcher + menu interativo + subcomandos diretos.

Subcomandos:
  trafego                  — menu interativo
  trafego setup            — wizard de configuração
  trafego fadiga           — análise de fadiga criativa
  trafego auditoria        — health check de campanhas
  trafego top-performers   — candidatos a escalada
  trafego comparativo      — período a período (WoW/MoM/YoY)
  trafego fases            — performance por fase do funil
  trafego dayparting       — heatmap dia × hora
  trafego criativos        — ranking + galeria visual
  trafego accounts         — lista contas cadastradas
  trafego produtos         — lista produtos cadastrados
  trafego periods          — lista presets de período
  trafego cache            — status / limpar cache
  trafego web              — inicia UI Streamlit (requer extra [web])
  trafego --version

Todos os subcomandos de análise aceitam `--conta`, `--produto`, `--periodo`.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from trafego_analysis.core import cache as cache_mod
from trafego_analysis.core import config as cfg
from trafego_analysis.core.periods import PeriodComparison, list_presets, resolve_period
from trafego_analysis.version import __version__

console = Console()


# --- Helpers ----------------------------------------------------------------

def _require_setup() -> None:
    if not cfg.is_setup_complete():
        console.print(
            "[yellow]Setup ainda não foi concluído.[/yellow]\n"
            "Rode: [cyan]trafego setup[/cyan]"
        )
        sys.exit(1)


def _pick_account(explicit: str | None) -> dict:
    if explicit:
        a = cfg.get_account_by_alias(explicit)
        if not a:
            console.print(f"[red]Conta '{explicit}' não encontrada.[/red]")
            sys.exit(1)
        return a
    default = cfg.get_default_account_alias()
    if default:
        a = cfg.get_account_by_alias(default)
        if a:
            return a
    console.print("[red]Nenhuma conta cadastrada.[/red]")
    sys.exit(1)


def _pick_produto(explicit: str | None) -> dict | None:
    if not explicit:
        return None
    for p in cfg.get_produtos():
        if p["nome"].lower() == explicit.lower():
            return p
    console.print(f"[yellow]Produto '{explicit}' não cadastrado — ignorando filtro.[/yellow]")
    return None


def _resolve_period_or_exit(spec: str):
    try:
        return resolve_period(spec, today=date.today())
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


def _ensure_single_period(spec: str):
    """Garante que o spec resolve para Period (não PeriodComparison)."""
    p = _resolve_period_or_exit(spec)
    if isinstance(p, PeriodComparison):
        console.print(
            f"[yellow]'{spec}' é um comparativo — usando a janela atual ({p.current.label}).[/yellow]"
        )
        return p.current
    return p


def _ensure_comparison(spec: str):
    """Garante que o spec resolve para PeriodComparison (constrói um do Period se preciso)."""
    p = _resolve_period_or_exit(spec)
    if isinstance(p, PeriodComparison):
        return p
    # Constrói comparação com janela anterior do mesmo tamanho
    from trafego_analysis.core.periods import Period
    from trafego_analysis.core.periods import PeriodComparison as PC

    days = p.days
    previous = Period(
        since=p.since - timedelta(days=days),
        until=p.until - timedelta(days=days),
        label=f"{days} dias anteriores",
    )
    return PC(current=p, previous=previous, label=f"{p.label} vs período anterior")


def _render_output(text: str, path) -> None:
    """Renderiza markdown do relatório + path de saída.

    `rich` tenta detectar encoding do terminal — em Windows cp1252 alguns
    emojis Unicode quebram. Fallback: stdout.write direto com errors='replace'.
    """
    try:
        console.print()
        console.print(text)
    except (UnicodeEncodeError, UnicodeError):
        import sys as _sys
        safe = text.encode("utf-8", "replace").decode("utf-8", "replace")
        # stdout.write com replace evita crash; rich styling é sacrificado
        try:
            _sys.stdout.buffer.write(safe.encode("utf-8"))
            _sys.stdout.buffer.write(b"\n")
        except Exception:
            _sys.stdout.write(safe.encode("ascii", "replace").decode("ascii"))
            _sys.stdout.write("\n")
    if path:
        try:
            console.print(f"\n[dim]Relatório salvo em:[/dim] [cyan]{path}[/cyan]")
        except Exception:
            print(f"\nRelatorio salvo em: {path}")


# --- Grupo raiz -------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="trafego")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """trafego — análise de tráfego pago Meta Ads."""
    if ctx.invoked_subcommand is None:
        menu_interativo()


# --- Comandos utilitários ---------------------------------------------------

@cli.command("setup")
@click.option("--force", is_flag=True, help="Reconfigura mesmo se já setado.")
@click.option("--google-ads", "google_ads", is_flag=True, help="Só configura integração Google Ads.")
@click.option("--hotmart", is_flag=True, help="Só configura integração Hotmart.")
def cmd_setup(force: bool, google_ads: bool, hotmart: bool) -> None:
    """Executa o wizard de configuração inicial (ou integrações específicas)."""
    from trafego_analysis import setup_wizard

    if google_ads:
        setup_wizard.run_google_ads()
        return
    if hotmart:
        setup_wizard.run_hotmart()
        return
    setup_wizard.run(force=force)


@cli.command("accounts")
def cmd_accounts() -> None:
    """Lista contas cadastradas."""
    _require_setup()
    contas = cfg.get_accounts()
    default = cfg.get_default_account_alias()

    table = Table(title="Contas cadastradas")
    table.add_column("Apelido")
    table.add_column("ID")
    table.add_column("Nome")
    table.add_column("Padrão", justify="center")

    for c in contas:
        is_default = "*" if c["alias"] == default else ""
        table.add_row(c["alias"], c["ad_account_id"], c["display_name"], is_default)
    console.print(table)


@cli.command("produtos")
def cmd_produtos() -> None:
    """Lista produtos cadastrados."""
    _require_setup()
    produtos = cfg.get_produtos()
    if not produtos:
        console.print("[yellow]Nenhum produto cadastrado.[/yellow]")
        return

    table = Table(title="Produtos")
    table.add_column("Nome")
    table.add_column("Ticket")
    table.add_column("CPA meta")
    table.add_column("ROAS meta")
    table.add_column("Tipo")
    for p in produtos:
        table.add_row(
            p["nome"],
            f"R$ {p['ticket']:.2f}",
            f"R$ {p['cpa_meta']:.2f}",
            f"{p['roas_meta']:.2f}x",
            p.get("tipo", "-"),
        )
    console.print(table)


@cli.command("periods")
def cmd_periods() -> None:
    """Lista presets e comparativos de período."""
    table = Table(title="Períodos disponíveis")
    table.add_column("Spec")
    table.add_column("Descrição (PT-BR)")
    for spec, label in list_presets():
        table.add_row(f"[cyan]{spec}[/cyan]", label)
    table.add_row("[cyan]YYYY-MM-DD..YYYY-MM-DD[/cyan]", "Custom — qualquer intervalo")
    console.print(table)


@cli.command("cache")
@click.option("--clear", is_flag=True, help="Limpa todo o cache.")
def cmd_cache(clear: bool) -> None:
    """Mostra estatísticas ou limpa o cache local."""
    if clear:
        n = cache_mod.invalidate_all()
        console.print(f"[green]OK[/green] {n} entradas removidas.")
        return
    st = cache_mod.stats()
    console.print(Panel.fit(
        f"Entradas: {st['total_entries']}\n"
        f"Tamanho:  {st['approx_size_kb']} KB\n"
        f"Path:     {st['db_path']}",
        title="Cache",
    ))


# --- Comandos de análise ----------------------------------------------------

def _common_options(func):
    """Decorator pra evitar duplicação das flags comuns."""
    func = click.option("--perfil", default="perpetuo", help="Perfil de análise (default perpetuo).")(func)
    func = click.option("--periodo", default="last_7d", help="Preset de período (default last_7d).")(func)
    func = click.option("--produto", help="Nome do produto para filtro (opcional).")(func)
    func = click.option("--conta", help="Apelido da conta (default: conta padrão).")(func)
    return func


@cli.command("fadiga")
@_common_options
def cmd_fadiga(conta, produto, periodo, perfil):
    """Análise de fadiga criativa (5 sinais combinados)."""
    _require_setup()
    from trafego_analysis.analyses import fadiga_criativa
    from trafego_analysis.core.meta_client import MetaClient
    from trafego_analysis.core.perfis import get_perfil
    from trafego_analysis.core.periods import Period

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    perfil_obj = get_perfil(perfil)

    p = _resolve_period_or_exit(periodo)
    if isinstance(p, PeriodComparison):
        periodo_atual, periodo_anterior = p.current, p.previous
    else:
        periodo_atual = p
        days = periodo_atual.days
        periodo_anterior = Period(
            since=periodo_atual.since - timedelta(days=days),
            until=periodo_atual.until - timedelta(days=days),
            label=f"{days} dias anteriores",
        )

    console.print(
        f"[dim]Conta:[/dim] {account['alias']}  "
        f"[dim]Período:[/dim] {periodo_atual.label}  "
        f"[dim]Perfil:[/dim] {perfil}"
    )

    try:
        meta = MetaClient.from_saved_config()
        text, path = fadiga_criativa.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_atual,
            periodo_anterior=periodo_anterior,
            produto_nome=produto_obj["nome"] if produto_obj else None,
            perfil=perfil_obj,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)

    _render_output(text, path)


@cli.command("auditoria")
@_common_options
def cmd_auditoria(conta, produto, periodo, perfil):
    """Health check estrutural das campanhas."""
    _require_setup()
    from trafego_analysis.analyses import auditoria_campanha
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = auditoria_campanha.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("escalabilidade")
@_common_options
def cmd_escalabilidade(conta, produto, periodo, perfil):
    """Avalia saturação de público e indica incremento seguro (Análise 1.2)."""
    _require_setup()
    from trafego_analysis.analyses import escalabilidade
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = escalabilidade.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("conjuntos")
@_common_options
def cmd_conjuntos(conta, produto, periodo, perfil):
    """Comparativo HOT/COLD/SUPERCOLD adset-level (Análise 1.3)."""
    _require_setup()
    from trafego_analysis.analyses import comparativo_conjuntos
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = comparativo_conjuntos.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("orcamento")
@_common_options
def cmd_orcamento(conta, produto, periodo, perfil):
    """Eficiência de orçamento — Pareto 80/20 (Análise 1.4)."""
    _require_setup()
    from trafego_analysis.analyses import eficiencia_orcamento
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = eficiencia_orcamento.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("prospeccao")
@click.option("--fase", default="evergreen", help="Fase VTSD: evergreen | pico | caixa_rapido | teste_inicial")
@_common_options
def cmd_prospeccao(conta, produto, periodo, perfil, fase):
    """Prospecção vs Retargeting — mix HOT/COLD/SUPERCOLD (Análise 1.5)."""
    _require_setup()
    from trafego_analysis.analyses import prospeccao_retargeting
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = prospeccao_retargeting.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
            fase=fase,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("top-performers")
@_common_options
def cmd_top_performers(conta, produto, periodo, perfil):
    """Identifica candidatos a escalada de budget."""
    _require_setup()
    from trafego_analysis.analyses import top_performers
    from trafego_analysis.core.meta_client import MetaClient
    from trafego_analysis.core.perfis import get_perfil

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)
    perfil_obj = get_perfil(perfil)

    try:
        meta = MetaClient.from_saved_config()
        text, path = top_performers.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
            perfil=perfil_obj,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("comparativo")
@_common_options
def cmd_comparativo(conta, produto, periodo, perfil):
    """Comparativo período a período (WoW/MoM/YoY/custom)."""
    _require_setup()
    from trafego_analysis.analyses import comparativo_periodo
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    comparison = _ensure_comparison(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = comparativo_periodo.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            comparison=comparison,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("fases")
@_common_options
def cmd_fases(conta, produto, periodo, perfil):
    """Performance por fase do funil."""
    _require_setup()
    from trafego_analysis.analyses import fases_funil
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = fases_funil.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("dayparting")
@_common_options
def cmd_dayparting(conta, produto, periodo, perfil):
    """Heatmap dia × hora + janela recomendada."""
    _require_setup()
    from trafego_analysis.analyses import dayparting
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = dayparting.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("criativos")
@_common_options
@click.option("--galeria", is_flag=True, help="Gera galeria HTML visual dos top.")
@click.option("--top", "top_n", default=10, help="Top N no ranking / galeria (default 10).")
def cmd_criativos(conta, produto, periodo, perfil, galeria, top_n):
    """Ranking de criativos + DNA dos winners + galeria HTML (opcional)."""
    _require_setup()
    from trafego_analysis.analyses import criativos_galeria, criativos_ranking
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()

        if galeria:
            out_path, meta_info = criativos_galeria.analisar(
                meta=meta,
                ad_account_id=account["ad_account_id"],
                account_alias=account["alias"],
                periodo=periodo_obj,
                produto_nome=produto_obj["nome"] if produto_obj else None,
                top_n=top_n,
            )
            if out_path:
                console.print(f"[green]Galeria gerada:[/green] [cyan]{out_path}[/cyan]")
                console.print("[dim]Abra o arquivo no navegador.[/dim]")
            else:
                console.print("[yellow]Nenhum criativo elegível.[/yellow]")
        else:
            text, path = criativos_ranking.analisar(
                meta=meta,
                ad_account_id=account["ad_account_id"],
                account_alias=account["alias"],
                periodo=periodo_obj,
                produto_nome=produto_obj["nome"] if produto_obj else None,
                top_n=top_n,
                baixar_assets=True,
            )
            _render_output(text, path)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


@cli.command("mandala")
@_common_options
def cmd_mandala(conta, produto, periodo, perfil):
    """Mandala VTSD — 18 tipos + Gap Finder (Análise 2.3)."""
    _require_setup()
    from trafego_analysis.analyses import mandala_vtsd
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = mandala_vtsd.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("testes-ab")
@_common_options
def cmd_testes_ab(conta, produto, periodo, perfil):
    """Sugere testes A/B (demografia, formato, hook, CBO vs ABO) — Análise 2.6."""
    _require_setup()
    from trafego_analysis.analyses import criativos_comparativo
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = criativos_comparativo.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("funil")
@_common_options
def cmd_funil(conta, produto, periodo, perfil):
    """Funil waterfall (Impression -> Purchase) + detector de gargalo."""
    _require_setup()
    from trafego_analysis.analyses import funil_waterfall
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = funil_waterfall.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("projecao")
@_common_options
def cmd_projecao(conta, produto, periodo, perfil):
    """Projeção de CPA ao escalar budget 1.5x / 2x / 3x (Análise 3.3)."""
    _require_setup()
    from trafego_analysis.analyses import projecao_escala
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = projecao_escala.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("caixa-rapido")
@click.option("--ticket", default=97.0, help="Ticket do produto (R$).")
@_common_options
def cmd_caixa_rapido(conta, produto, periodo, perfil, ticket):
    """Caixa Rápido Health Check — ROAS 3x mínimo (Análise 3.4)."""
    _require_setup()
    from trafego_analysis.analyses import caixa_rapido
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = caixa_rapido.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
            ticket=ticket,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("pico-evergreen")
@click.option("--periodo-pico", default="last_14d", help="Período do Pico.")
@click.option("--periodo-evergreen", default="last_30d", help="Período Evergreen (deve ser DIFERENTE do pico).")
@click.option("--conta", help="Apelido da conta.")
@click.option("--produto", help="Nome do produto (opcional).")
def cmd_pico_evergreen(conta, produto, periodo_pico, periodo_evergreen):
    """Comparativo Pico vs Evergreen (Análise 3.5)."""
    _require_setup()
    from trafego_analysis.analyses import pico_vs_evergreen
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    p_pico = _ensure_single_period(periodo_pico)
    p_ever = _ensure_single_period(periodo_evergreen)

    try:
        meta = MetaClient.from_saved_config()
        text, path = pico_vs_evergreen.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo_pico=p_pico,
            periodo_evergreen=p_ever,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("checkout")
@_common_options
def cmd_checkout(conta, produto, periodo, perfil):
    """Análise do checkout — abandono LPV->IC->Compra (Análise 3.6)."""
    _require_setup()
    from trafego_analysis.analyses import checkout_analise
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = checkout_analise.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("cross-canal")
@_common_options
def cmd_cross_canal(conta, produto, periodo, perfil):
    """Análise cross-canal — Meta + Google Ads + Hotmart agregados."""
    _require_setup()
    from trafego_analysis.analyses import cross_canal
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = cross_canal.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("health")
@click.option("--ticket", default=297.0, help="Ticket do produto principal.")
@_common_options
def cmd_health(conta, produto, periodo, perfil, ticket):
    """Health Score 0-100 da conta em 5 dimensões (Análise 4.1)."""
    _require_setup()
    from trafego_analysis.analyses import conta_health
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = conta_health.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
            ticket=ticket,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("alertas")
@_common_options
def cmd_alertas(conta, produto, periodo, perfil):
    """Alertas prioritários consolidados (Análise 4.2)."""
    _require_setup()
    from trafego_analysis.analyses import alertas_prioritarios
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = alertas_prioritarios.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("advantage")
@_common_options
def cmd_advantage(conta, produto, periodo, perfil):
    """Revisão de campanhas Advantage+ (Análise 4.3)."""
    _require_setup()
    from trafego_analysis.analyses import advantage_plus
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = advantage_plus.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("pausar")
@_common_options
def cmd_pausar(conta, produto, periodo, perfil):
    """Pausa Hierárquica — decide nível (ad/adset/campanha) — Análise 4.5."""
    _require_setup()
    from trafego_analysis.analyses import pausa_hierarquica
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = pausa_hierarquica.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("plano-executivo")
@click.option("--ticket", default=297.0, help="Ticket do produto.")
@_common_options
def cmd_plano(conta, produto, periodo, perfil, ticket):
    """Plano de Otimização Executivo (consolida tudo) — Análise 4.6."""
    _require_setup()
    from trafego_analysis.analyses import plano_executivo
    from trafego_analysis.core.meta_client import MetaClient

    account = _pick_account(conta)
    produto_obj = _pick_produto(produto)
    periodo_obj = _ensure_single_period(periodo)

    try:
        meta = MetaClient.from_saved_config()
        text, path = plano_executivo.analisar(
            meta=meta,
            ad_account_id=account["ad_account_id"],
            periodo=periodo_obj,
            produto_nome=produto_obj["nome"] if produto_obj else None,
            ticket=ticket,
        )
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    _render_output(text, path)


@cli.command("demo")
@click.option(
    "--cenario",
    type=click.Choice(["D1", "D2", "D3", "D4", "D5", "D6", "D7"], case_sensitive=False),
    default="D1",
    help="Cenário fictício: D1-D5 (padrão) / D6 (crise) / D7 (escala).",
)
def cmd_demo(cenario):
    """Modo Demo — análise com dados fictícios (para gravação de aula)."""
    from trafego_analysis.analyses import demo as demo_mod

    try:
        text, path = demo_mod.gerar_demo(cenario)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    _render_output(text, path)


@cli.command("web")
def cmd_web() -> None:
    """Inicia a UI Web Streamlit."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        console.print(
            "[red]Streamlit não instalado.[/red]\n"
            "Instale com: [cyan]pip install -e '.[web]'[/cyan]"
        )
        sys.exit(1)

    import subprocess
    from pathlib import Path

    web_entry = Path(__file__).parent / "web.py"
    if not web_entry.exists():
        console.print("[yellow]UI Web será adicionada na Fase 3 do roadmap.[/yellow]")
        return

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(web_entry)],
        check=False,
    )


# --- Menu interativo --------------------------------------------------------

def menu_interativo() -> None:
    if not cfg.is_setup_complete():
        console.print(
            Panel.fit(
                "Bem-vindo ao [bold cyan]trafego[/bold cyan]!\n\n"
                "Ainda não rodou o setup. Rode agora com:\n"
                "  [cyan]trafego setup[/cyan]",
                title="Primeira execução",
            )
        )
        return

    alias = cfg.get_default_account_alias() or "?"
    console.print(
        Panel.fit(
            f"trafego — análise de tráfego pago Meta Ads\n"
            f"Conta padrão: [cyan]{alias}[/cyan]",
            style="bold cyan",
        )
    )

    console.print("\nMódulos:")
    console.print("  [cyan]1[/cyan]) Análise de Campanhas (6 modos)")
    console.print("  [cyan]2[/cyan]) Análise de Criativos")
    console.print("  [cyan]3[/cyan]) Análise de Funil (waterfall)")
    console.print("  [cyan]4[/cyan]) Cross-canal (Meta + Google + Hotmart)")
    console.print("  [cyan]0[/cyan]) Sair\n")

    escolha = Prompt.ask("Escolha", choices=["0", "1", "2", "3", "4"], default="0")
    if escolha == "0":
        return
    if escolha == "1":
        _menu_campanhas()
    elif escolha == "2":
        _menu_criativos()
    elif escolha == "3":
        _menu_funil()
    elif escolha == "4":
        _menu_cross_canal()


def _menu_campanhas() -> None:
    console.print()
    console.print(Panel.fit(
        "CAMPANHAS — 6 análises\n\n"
        "  [cyan]1[/cyan]) Fadiga Criativa\n"
        "  [cyan]2[/cyan]) Auditoria\n"
        "  [cyan]3[/cyan]) Top Performers\n"
        "  [cyan]4[/cyan]) Comparativo Período\n"
        "  [cyan]5[/cyan]) Performance por Fase\n"
        "  [cyan]6[/cyan]) Dayparting\n"
        "  [cyan]0[/cyan]) Voltar\n"
    ))
    escolha = Prompt.ask("Escolha", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")
    if escolha == "0":
        return

    periodo = Prompt.ask("Período", default="last_7d")
    produto = Prompt.ask("Produto (ENTER = todos)", default="")
    prod_arg = produto.strip() or None

    ctx = click.Context(cli)
    if escolha == "1":
        ctx.invoke(cmd_fadiga, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo")
    elif escolha == "2":
        ctx.invoke(cmd_auditoria, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo")
    elif escolha == "3":
        ctx.invoke(cmd_top_performers, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo")
    elif escolha == "4":
        ctx.invoke(cmd_comparativo, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo")
    elif escolha == "5":
        ctx.invoke(cmd_fases, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo")
    elif escolha == "6":
        ctx.invoke(cmd_dayparting, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo")


def _menu_criativos() -> None:
    console.print()
    console.print(Panel.fit(
        "CRIATIVOS\n\n"
        "  [cyan]1[/cyan]) Ranking (com DNA dos winners)\n"
        "  [cyan]2[/cyan]) Galeria visual HTML\n"
        "  [cyan]0[/cyan]) Voltar\n"
    ))
    escolha = Prompt.ask("Escolha", choices=["0", "1", "2"], default="0")
    if escolha == "0":
        return

    periodo = Prompt.ask("Período", default="last_7d")
    produto = Prompt.ask("Produto (ENTER = todos)", default="")
    prod_arg = produto.strip() or None
    top_n = int(Prompt.ask("Top N", default="10") or "10")

    ctx = click.Context(cli)
    if escolha == "1":
        ctx.invoke(
            cmd_criativos,
            conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo",
            galeria=False, top_n=top_n,
        )
    elif escolha == "2":
        ctx.invoke(
            cmd_criativos,
            conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo",
            galeria=True, top_n=top_n,
        )


def _menu_funil() -> None:
    console.print()
    periodo = Prompt.ask("Período", default="last_7d")
    produto = Prompt.ask("Produto (ENTER = todos)", default="")
    prod_arg = produto.strip() or None
    ctx = click.Context(cli)
    ctx.invoke(
        cmd_funil, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo",
    )


def _menu_cross_canal() -> None:
    console.print()
    periodo = Prompt.ask("Período", default="last_30d")
    produto = Prompt.ask("Produto (ENTER = todos)", default="")
    prod_arg = produto.strip() or None
    ctx = click.Context(cli)
    ctx.invoke(
        cmd_cross_canal, conta=None, produto=prod_arg, periodo=periodo, perfil="perpetuo",
    )


def main() -> None:
    """Entry point declarado em pyproject.toml."""
    cli()


if __name__ == "__main__":
    main()
