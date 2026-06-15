"""Setup wizard interativo — guia usuário zero-config até primeira análise.

Passos:
  1. Sanity check de ambiente
  2. System User Token da Meta (com guia passo-a-passo)
  3. Seleção e cadastro de ad accounts (com apelidos)
  4. Cadastro de produtos
  5. Escolha de template de fases do funil
  6. Ativação de perfis de análise (perpetuo / lancamento)
  7. Integrações opcionais (Google Ads, Hotmart)
"""

from __future__ import annotations

import json
import sys
import webbrowser
from importlib import resources

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from trafego_analysis.core import config as cfg
from trafego_analysis.core.meta_client import MetaAPIError, MetaClient, MetaClientConfig

console = Console()

BM_SYSTEM_USERS_URL = "https://business.facebook.com/settings/system-users"


def _banner(text: str, *, style: str = "bold cyan") -> None:
    console.print(Panel.fit(text, style=style))


def _confirm(question: str, default: bool = True) -> bool:
    return Confirm.ask(question, default=default)


def _prompt(question: str, default: str = "") -> str:
    return Prompt.ask(question, default=default)


def _load_default(relative_path: str) -> dict:
    """Lê um JSON em config_defaults/ do package."""
    pkg = resources.files("trafego_analysis")
    p = pkg / "config_defaults" / relative_path
    return json.loads(p.read_text(encoding="utf-8"))


def _list_fases_templates() -> list[tuple[str, dict]]:
    pkg = resources.files("trafego_analysis")
    tpl_dir = pkg / "config_defaults" / "fases_templates"
    out = []
    for p in sorted(tpl_dir.iterdir()):
        if p.suffix == ".json":
            out.append((p.stem, json.loads(p.read_text(encoding="utf-8"))))
    return out


# --- Passos -----------------------------------------------------------------

def passo_1_ambiente() -> None:
    _banner("[1/7] Ambiente", style="bold blue")
    py = sys.version_info
    if py < (3, 11):
        console.print(f"[red]Python 3.11+ necessário (encontrado: {py.major}.{py.minor})[/red]")
        raise SystemExit(1)
    console.print(f"[green]✓[/green] Python {py.major}.{py.minor}.{py.micro}")
    paths = cfg.get_paths()
    console.print(f"[green]✓[/green] Config: {paths.config_dir}")
    console.print(f"[green]✓[/green] Dados:  {paths.data_dir}")
    console.print()


def passo_2_token() -> str:
    _banner("[2/7] System User Token (Meta)", style="bold blue")

    existing = cfg.load_secret(cfg.get_paths().meta_token_file)
    if existing:
        if not _confirm("Já existe um token salvo. Substituir?", default=False):
            console.print("[green]✓[/green] Mantendo token existente.\n")
            return existing

    console.print(
        "Você precisa de um [bold]System User Token[/bold] da Meta (não expira)."
    )
    console.print()
    console.print("Passo-a-passo:")
    console.print(f"  1) Abra [cyan]{BM_SYSTEM_USERS_URL}[/cyan]")
    console.print("  2) Adicionar → crie System User (ex: 'Analytics Bot')")
    console.print("  3) Dê a ele role [bold]Admin[/bold]")
    console.print("  4) Gerar Novo Token → escolha um app → permissões:")
    console.print("     • ads_read")
    console.print("     • ads_management")
    console.print("     • business_management")
    console.print()

    if _confirm("Abrir o Business Manager agora no navegador?", default=True):
        try:
            webbrowser.open(BM_SYSTEM_USERS_URL)
        except Exception:
            console.print("[yellow]Abra manualmente: " + BM_SYSTEM_USERS_URL + "[/yellow]")

    token = _prompt("\nCole o token gerado")
    if not token or len(token) < 40:
        console.print("[red]Token inválido (muito curto).[/red]")
        raise SystemExit(1)

    # Valida token fazendo uma chamada
    client = MetaClient(MetaClientConfig(access_token=token))
    try:
        accounts = client.list_ad_accounts()
    except MetaAPIError as e:
        console.print(f"[red]Token rejeitado pela Meta: {e}[/red]")
        raise SystemExit(1) from e

    cfg.save_secret(cfg.get_paths().meta_token_file, token)
    console.print(f"[green]✓[/green] Token válido! {len(accounts)} ad account(s) encontrada(s).\n")
    return token


def passo_3_contas(token: str) -> None:
    _banner("[3/7] Contas de Anúncios", style="bold blue")

    client = MetaClient(MetaClientConfig(access_token=token))
    try:
        disponiveis = client.list_ad_accounts()
    except MetaAPIError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1) from e

    if not disponiveis:
        console.print("[yellow]Nenhuma ad account encontrada.[/yellow]")
        raise SystemExit(1)

    table = Table(title="Ad accounts disponíveis")
    table.add_column("#", style="dim")
    table.add_column("ID")
    table.add_column("Nome")
    table.add_column("Moeda", style="dim")
    table.add_column("Status", style="dim")

    for i, a in enumerate(disponiveis, 1):
        table.add_row(
            str(i),
            a["ad_account_id"],
            a["name"],
            a.get("currency") or "-",
            str(a.get("account_status") or "-"),
        )
    console.print(table)

    selecionadas_raw = _prompt(
        "\nQuais contas cadastrar? (ex: 1,3,4 ou 'todas')",
        default="todas",
    )
    if selecionadas_raw.strip().lower() == "todas":
        selecionadas = disponiveis
    else:
        indices = [int(x.strip()) for x in selecionadas_raw.split(",") if x.strip().isdigit()]
        selecionadas = [disponiveis[i - 1] for i in indices if 1 <= i <= len(disponiveis)]

    if not selecionadas:
        console.print("[red]Nenhuma conta selecionada.[/red]")
        raise SystemExit(1)

    accounts_payload = []
    for a in selecionadas:
        apelido = _prompt(
            f"Apelido para '{a['name']}'",
            default=a["name"].lower().replace(" ", "-")[:20],
        )
        accounts_payload.append(
            {
                "alias": apelido,
                "ad_account_id": a["ad_account_id"],
                "display_name": a["name"],
                "timezone": a.get("timezone") or "America/Sao_Paulo",
                "currency": a.get("currency") or "BRL",
            }
        )

    default_alias = accounts_payload[0]["alias"]
    if len(accounts_payload) > 1:
        default_alias = _prompt(
            "Conta padrão (apelido)",
            default=accounts_payload[0]["alias"],
        )

    cfg.save_json(
        cfg.get_paths().accounts_file,
        {"default_account": default_alias, "accounts": accounts_payload},
    )
    console.print(f"[green]✓[/green] {len(accounts_payload)} conta(s) cadastrada(s).\n")


def passo_4_produtos() -> None:
    _banner("[4/7] Produtos", style="bold blue")
    console.print("Cadastre os produtos que você vende (ENTER vazio em 'Nome' finaliza).\n")

    produtos: list[dict] = []
    while True:
        nome = _prompt(f"Nome do produto {len(produtos) + 1}", default="")
        if not nome:
            break
        ticket = float(_prompt("  Ticket (R$)", default="0") or "0")
        cpa_default = round(ticket * 0.4, 2) if ticket else 0
        cpa = float(_prompt(f"  CPA meta (R$) [{cpa_default}]", default=str(cpa_default)) or cpa_default)
        roas = float(_prompt("  ROAS meta", default="2.5") or "2.5")
        tipo = _prompt("  Tipo (perpetuo/lancamento)", default="perpetuo")
        produtos.append(
            {"nome": nome, "ticket": ticket, "cpa_meta": cpa, "roas_meta": roas, "tipo": tipo}
        )

    cfg.save_json(cfg.get_paths().produtos_file, produtos)
    console.print(f"[green]✓[/green] {len(produtos)} produto(s) cadastrado(s).\n")


def passo_5_fases() -> None:
    _banner("[5/7] Fases do Funil", style="bold blue")

    templates = _list_fases_templates()
    for i, (slug, tpl) in enumerate(templates, 1):
        n = len(tpl.get("fases", []))
        console.print(f"  {i}) [cyan]{tpl['nome_template']}[/cyan] — {n} fases")

    escolha = IntPrompt.ask(
        "Escolha um template", default=1, choices=[str(i) for i in range(1, len(templates) + 1)]
    )
    _slug, tpl = templates[escolha - 1]

    cfg.save_json(
        cfg.get_paths().fases_file,
        {"fases": tpl["fases"], "regex_match": tpl["regex_match"], "template_origem": _slug},
    )
    nomes = ", ".join(f["label"] for f in tpl["fases"])
    console.print(f"[green]✓[/green] Fases ativas: {nomes}\n")


def passo_6_perfis() -> None:
    _banner("[6/7] Perfis de Análise", style="bold blue")
    console.print("Perfis definem regras de fadiga e escalada por tipo de operação.\n")

    perfis_carregados: dict[str, dict] = {}
    ativos: list[str] = []

    templates_perfis = ["perpetuo", "lancamento"]
    for nome in templates_perfis:
        raw = _load_default(f"perfis_templates/{nome}.json")
        if _confirm(f"Ativar perfil [bold]{nome}[/bold]?", default=(nome == "perpetuo")):
            perfis_carregados[nome] = raw
            ativos.append(nome)

    if not ativos:
        console.print("[yellow]Nenhum perfil ativo. Ativando 'perpetuo' por padrão.[/yellow]")
        perfis_carregados["perpetuo"] = _load_default("perfis_templates/perpetuo.json")
        ativos = ["perpetuo"]

    cfg.save_json(
        cfg.get_paths().perfis_file,
        {"ativos": ativos, "perfis": perfis_carregados},
    )
    console.print(f"[green]✓[/green] Perfis ativos: {', '.join(ativos)}\n")


def passo_7_integracoes() -> None:
    _banner("[7/7] Integrações Opcionais (Cross-canal)", style="bold blue")

    google = _confirm("Ativar Google Ads?", default=False)
    if google:
        console.print("[yellow]Configuração Google Ads será solicitada na próxima execução.[/yellow]")
        console.print("[yellow]→ trafego setup --google-ads[/yellow]")

    hotmart = _confirm("Ativar Hotmart?", default=False)
    if hotmart:
        console.print("[yellow]Configuração Hotmart será solicitada na próxima execução.[/yellow]")
        console.print("[yellow]→ trafego setup --hotmart[/yellow]")

    cfg.save_json(
        cfg.get_paths().integracoes_file,
        {"google_ads": google, "hotmart": hotmart},
    )
    console.print()


def resumo_final() -> None:
    console.print()
    _banner(
        "✅ Setup concluído!\n\n"
        "Próximos passos:\n"
        "  • CLI:       [cyan]trafego[/cyan]\n"
        "  • Web UI:    [cyan]trafego web[/cyan]\n"
        "  • Fadiga:    [cyan]trafego fadiga --periodo last_7d[/cyan]\n"
        "  • Ajuda:     [cyan]trafego --help[/cyan]\n",
        style="bold green",
    )


def run(*, force: bool = False) -> None:
    """Ponto de entrada do wizard. `force=True` roda mesmo se já configurado."""
    if cfg.is_setup_complete() and not force:
        console.print("[yellow]Setup já concluído.[/yellow]")
        if not _confirm("Rodar novamente?", default=False):
            return

    passo_1_ambiente()
    token = passo_2_token()
    passo_3_contas(token)
    passo_4_produtos()
    passo_5_fases()
    passo_6_perfis()
    passo_7_integracoes()
    resumo_final()


# --- Setup cross-canal (comandos separados) --------------------------------

def run_google_ads() -> None:
    """Configura Google Ads — `trafego setup --google-ads`."""
    _banner("Setup Google Ads", style="bold blue")

    console.print(
        "Para integrar Google Ads você precisa de:\n"
        "  1) Developer Token do Google Ads\n"
        "  2) OAuth2 credentials (client_id + client_secret)\n"
        "  3) Refresh token gerado a partir do OAuth flow\n"
        "  4) Customer ID (10 dígitos, sem hífens)\n"
    )
    console.print(
        "[dim]Veja docs/SETUP_GOOGLE_ADS.md para o passo-a-passo detalhado.[/dim]\n"
    )

    if not _confirm("Continuar?", default=True):
        return

    customer_id = _prompt("Customer ID (sem hífens)").replace("-", "")
    developer_token = _prompt("Developer Token")
    client_id = _prompt("OAuth Client ID")
    client_secret = _prompt("OAuth Client Secret")
    refresh_token = _prompt("Refresh Token")
    login_customer_id = _prompt("Login Customer ID (MCC, opcional)", default="")

    integracoes = cfg.get_integracoes()
    integracoes["google_ads"] = True
    integracoes["google_ads_config"] = {
        "customer_id": customer_id,
        "developer_token": developer_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "login_customer_id": login_customer_id or None,
    }
    cfg.save_json(cfg.get_paths().integracoes_file, integracoes)
    cfg.save_secret(cfg.get_paths().google_ads_refresh_token_file, refresh_token)

    console.print("[green]OK[/green] Google Ads configurado.\n")
    console.print(
        "Instale a dependência opcional se ainda não tiver:\n"
        "  [cyan]pip install -e '.[google]'[/cyan]\n"
    )


def run_hotmart() -> None:
    """Configura Hotmart — `trafego setup --hotmart`."""
    _banner("Setup Hotmart", style="bold blue")

    console.print(
        "Para integrar Hotmart você precisa de:\n"
        "  1) Client ID (em Developers → Hotmart App)\n"
        "  2) Client Secret (mesmo lugar)\n"
    )
    console.print(
        "[dim]Veja docs/SETUP_HOTMART.md para o passo-a-passo detalhado.[/dim]\n"
    )

    if not _confirm("Continuar?", default=True):
        return

    client_id = _prompt("Hotmart Client ID")
    client_secret = _prompt("Hotmart Client Secret")
    sandbox = _confirm("Ambiente sandbox?", default=False)

    integracoes = cfg.get_integracoes()
    integracoes["hotmart"] = True
    integracoes["hotmart_config"] = {"sandbox": sandbox}
    cfg.save_json(cfg.get_paths().integracoes_file, integracoes)

    # O secret é armazenado como client_id:client_secret para simplificar o reload
    cfg.save_secret(
        cfg.get_paths().hotmart_basic_token_file,
        f"{client_id}:{client_secret}",
    )

    console.print("[green]OK[/green] Hotmart configurado.\n")
