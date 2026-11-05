#!/usr/bin/env python3
"""Apoio da skill /peca: brief da peça, estado da pasta e próximos códigos.

Uso:
  py -3 peca.py brief R035 [--diretrizes caminho.html]
      Lê a linha da peça nas Diretrizes do mês (o arquivo mais recente em
      entregas/conteudo-social/Diretrizes_Editoracao_*.html), as peças vizinhas no
      calendário (regra da grade) e os Reels publicados recentes (tema e cor da legenda).
      Carrossel (C012): a mesma linha, mais os carrosséis recentes com o layout de cada um.
      Anúncio (A58) [--briefing caminho.html]: a linha da peça no briefing-{leva}.html mais
      recente de dono-14/entregas/criativos/ e os anúncios recentes (título, nota, Mandala).

  py -3 peca.py estado R035 [--nome NomeEmCamelCase] [--renomear NovoNome]
                            [--fase brief] [--brief] [--set chave=valor ...]
      Lê a pasta da peça (o que há dentro e a fase que os arquivos sugerem) e o
      _peca_R035.json. Com --nome cria a pasta se não existir. Com --fase registra a
      fase no histórico. Com --brief grava o brief das Diretrizes dentro do estado.
      --set aceita chave com ponto (roteiro.nota=9.4) e valor em JSON quando der.

  py -3 peca.py proximo
      Próximo código livre de Reel (R), carrossel (C) e anúncio (A), e as peças das
      Diretrizes que ainda não têm pasta.

  py -3 peca.py limpar R035 [--apagar] [--trabalho]
      Depois da aprovação do vídeo: lista o que sai da pasta (versões anteriores, prévias,
      testes, prévias de capa, cópias de transcrição) e o que fica (bruto, final, roteiro,
      capa, telas, legenda, _edicao_*.json, estado, fotos). Só apaga com --apagar;
      --trabalho remove também a pasta de trabalho da edição no computador.

Saída sempre em JSON (UTF-8). Nenhum segredo é lido aqui.
"""
import html as html_mod
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
PRODUTOS = RAIZ / "meus-produtos"
REELS = PRODUTOS / "linha-editorial" / "entregas" / "reels"
CARROSSEIS = PRODUTOS / "linha-editorial" / "entregas" / "carrosseis"
CRIATIVOS = PRODUTOS / "dono-14" / "entregas" / "criativos"
CONTEUDO_SOCIAL = PRODUTOS / "linha-editorial" / "entregas" / "conteudo-social"

FASES = ["brief", "angulo", "roteiro_aprovado", "editada", "programada", "publicada"]


# ---------------------------------------------------------------- utilidades

def falhar(msg: str) -> None:
    print(json.dumps({"erro": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


def normalizar(codigo: str) -> str:
    """R35 -> R035, c12 -> C012, a58 -> A58."""
    m = re.fullmatch(r"\s*([RrCcAa])\s*(\d{1,3})\s*", codigo or "")
    if not m:
        falhar(f"Não entendi o código da peça: {codigo!r}. Esperado R035, C012 ou A58.")
    letra, num = m.group(1).upper(), int(m.group(2))
    return f"{letra}{num:03d}" if letra in "RC" else f"{letra}{num:02d}"


def numero(codigo: str) -> int:
    return int(codigo[1:])


def limpar(texto: str) -> str:
    texto = re.sub(r"<br\s*/?>", " ", texto)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html_mod.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8", errors="replace")


def bases(letra: str):
    if letra == "R":
        return [REELS, REELS / "Publicados"]
    if letra == "C":
        return [CARROSSEIS, CARROSSEIS / "Publicados"]
    return [CRIATIVOS, CRIATIVOS / "Publicados"]


def pasta_bate(nome: str, codigo: str) -> bool:
    letra, num = codigo[0], numero(codigo)
    if letra == "R":
        return re.match(rf"R0*{num}\b", nome) is not None
    if letra == "C":
        return re.match(rf"Carrossel_0*{num}_", nome) is not None
    # anúncio: "A52 - Mentoria - 9x16" ou faixa "A54 a A57 - Mentoria - 9x16"
    m = re.match(r"A(\d+)\s+a\s+A(\d+)\b", nome)
    if m and int(m.group(1)) <= num <= int(m.group(2)):
        return True
    return re.match(rf"A0*{num}\b", nome) is not None


def achar_pasta(codigo: str):
    for base in bases(codigo[0]):
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name != "Publicados" and pasta_bate(d.name, codigo):
                return d
    return None


def maior_numero(letra: str) -> int:
    maior = 0
    for base in bases(letra):
        if not base.exists():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
            if letra == "R":
                m = re.match(r"R(\d{3})\b", d.name)
            elif letra == "C":
                m = re.match(r"Carrossel_(\d{3})_", d.name)
            else:
                m = re.match(r"A(\d+)(?:\s+a\s+A(\d+))?\b", d.name)
            if m:
                n = int(m.group(2) or m.group(1)) if letra == "A" else int(m.group(1))
                maior = max(maior, n)
    return maior


# ---------------------------------------------------------------- diretrizes

def arquivo_diretrizes(explicito=None) -> Path:
    if explicito:
        p = Path(explicito)
        if not p.is_absolute():
            p = RAIZ / p
        if not p.exists():
            falhar(f"Arquivo de Diretrizes não encontrado: {p}")
        return p
    candidatos = sorted(CONTEUDO_SOCIAL.glob("Diretrizes_Editoracao_*.html"),
                        key=lambda f: f.stat().st_mtime, reverse=True)
    if not candidatos:
        falhar(f"Nenhum Diretrizes_Editoracao_*.html em {CONTEUDO_SOCIAL}")
    return candidatos[0]


MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5, "junho": 6,
         "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


def ano_do_arquivo(p: Path) -> int:
    m = re.search(r"(20\d{2})", p.name)
    return int(m.group(1)) if m else datetime.now().year


def parse_diretrizes(doc: str, ano: int):
    """Devolve a lista de peças do calendário, na ordem, com a semana de cada uma."""
    pecas, semana = [], ""
    for tr in re.finditer(r"<tr([^>]*)>(.*?)</tr>", doc, flags=re.S):
        attrs, corpo = tr.group(1), tr.group(2)
        if 'class="sem"' in attrs or "colspan" in corpo:
            semana = limpar(corpo)
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", corpo, flags=re.S)
        if len(tds) < 5:
            continue
        pc = re.search(r'<span class="pc">\s*([RCA]\d+)\s*</span>', tds[1])
        if not pc:
            continue
        codigo = normalizar(pc.group(1))
        fmt = re.search(r'<span class="fmt[^"]*">(.*?)</span>', tds[1], flags=re.S)
        titulo = limpar(re.sub(r"<span.*?</span>", "", tds[1], flags=re.S))
        quote = re.search(r'<div class="quote">(.*?)</div>', tds[2], flags=re.S)
        detalhe = limpar(re.sub(r'<div class="quote">.*?</div>', "", tds[2], flags=re.S))
        dia_txt = limpar(tds[0])
        partes = [p.strip() for p in dia_txt.split("·")]
        dia = partes[0] if partes else dia_txt
        hora = partes[1] if len(partes) > 1 else ""
        obs_dia = " · ".join(partes[2:]) if len(partes) > 2 else ""
        data = ""
        md = re.search(r"(\d{1,2})/(\d{1,2})", dia)
        if md:
            data = f"{ano:04d}-{int(md.group(2)):02d}-{int(md.group(1)):02d}"
        pecas.append({
            "codigo": codigo,
            "semana": semana,
            "dia": dia,
            "data": data,
            "hora": hora,
            "obs_dia": obs_dia,
            "formato": limpar(fmt.group(1)) if fmt else "",
            "titulo": titulo,
            "gancho": limpar(quote.group(1)) if quote else "",
            "detalhe": detalhe,
            "fonte": limpar(tds[3]),
            "capa": limpar(tds[4]),
        })
    return pecas


def brief_da_peca(codigo: str, caminho_diretrizes=None):
    arq = arquivo_diretrizes(caminho_diretrizes)
    pecas = parse_diretrizes(ler(arq), ano_do_arquivo(arq))
    idx = next((i for i, p in enumerate(pecas) if p["codigo"] == codigo), None)
    resultado = {"diretrizes": str(arq), "codigo": codigo}
    if idx is None:
        resultado["peca"] = None
        resultado["aviso"] = (f"{codigo} não está nas Diretrizes {arq.name}. Perguntar ao Rodrigo o papel "
                              "do dia (descoberta, aula, notícia) e a data.")
        return resultado, pecas
    resultado["peca"] = pecas[idx]
    anteriores = [p for p in pecas[:idx]][-3:]
    seguintes = [p for p in pecas[idx + 1:]][:2]
    chave = lambda p: {k: p[k] for k in ("codigo", "dia", "hora", "formato", "titulo", "capa")}
    resultado["vizinhas"] = {"antes": [chave(p) for p in anteriores], "depois": [chave(p) for p in seguintes]}
    # regra da grade: as duas publicações anteriores e a seguinte, só pelo tipo de capa.
    # Carrossel entra na grade como capa de número (lâmina 1), pela REGUA-CAPAS-E-GRADE.
    tipo_grade = lambda c: "número (carrossel)" if c.strip().lower() == "carrossel" else c
    tipos = [tipo_grade(p["capa"]) for p in anteriores[-2:]] + ["(esta)"] + [tipo_grade(p["capa"]) for p in seguintes[:1]]
    resultado["grade_em_volta"] = tipos
    resultado["grade_regra"] = ("cada linha de três da grade precisa de pelo menos uma capa de rosto e uma de número, "
                                "e nunca duas iguais lado a lado")
    return resultado, pecas


# ---------------------------------------------------------------- pastas de Reel

def meta_do_roteiro(pasta: Path):
    """Lê do Reels_*.html o essencial: tipo, pilar, publicação, nota, capa."""
    htmls = sorted(pasta.glob("Reels_*.html")) or sorted(pasta.glob("*roteiro*.html"))
    if not htmls:
        return {}
    doc = ler(htmls[0])
    info = {"roteiro": htmls[0].name}
    meta = re.search(r'<div class="meta">(.*?)</div>\s*(?=<(?:div|h2|table|section))', doc, flags=re.S)
    texto_meta = limpar(meta.group(1)) if meta else limpar(doc[:6000])
    for campo in ("Formato", "Tipo", "Publicação", "Pilar", "CTA"):
        m = re.search(rf"{campo}:\s*(.*?)(?=\s(?:Formato|Tipo|Duração|Publicação|Objetivo|Pilar|CTA|De onde vem|Ajuste)\b|$)",
                      texto_meta)
        if m:
            info[campo.lower().replace("ç", "c").replace("ã", "a")] = m.group(1).strip()[:220]
    nota = re.search(r'<div class="nota">.*?(\d{1,2}[,.]\d)\s*/\s*10', doc, flags=re.S)
    if nota:
        info["nota"] = nota.group(1).replace(",", ".")
    tags = re.search(r'<div class="tags">(.*?)</div>', doc, flags=re.S)
    if tags:
        info["tags"] = limpar(tags.group(1))[:200]
    return info


def cor_legenda(pasta: Path):
    for ed in sorted(pasta.glob("_edicao_*.json")):
        try:
            cfg = json.loads(ler(ed))
        except ValueError:
            continue
        if cfg.get("cor_legenda"):
            return cfg["cor_legenda"]
    return None


def inventario(pasta: Path):
    """O que há na pasta de uma peça R, pelo nome dos arquivos."""
    arqs = [f for f in pasta.iterdir() if f.is_file()]
    nome = lambda f: f.name
    videos = [f for f in arqs if f.suffix.lower() in (".mp4", ".mov")]
    brutos = [nome(f) for f in videos if not f.name.startswith("_") and "editado" not in f.name.lower()
              and not re.search(r"brut[ao]|previa|teste", f.name, re.I)]
    editados = [nome(f) for f in videos if "editado" in f.name.lower() and not f.name.startswith("_")]
    previas = [nome(f) for f in videos if f.name.startswith("_PREVIA")]
    return {
        "roteiro_html": [nome(f) for f in arqs if f.suffix == ".html" and not f.name.startswith("_")
                         and (re.match(r"(Reels|Carrossel)_\d{3}_", f.name) or "roteiro" in f.name.lower())],
        "laminas_png": [nome(f) for f in arqs if re.match(r"Carrossel_\d{3}_.*_\d{2}\.png$", f.name)],
        "fundos": [nome(f) for f in arqs if re.search(r"_fundo_\d+\.(jpg|jpeg|png)$", f.name, re.I)],
        "legenda_txt": [nome(f) for f in arqs if f.name == "legenda.txt"],
        "capa_html": [nome(f) for f in arqs if f.name.startswith("_CAPA_") and f.suffix == ".html"],
        "capa_png": [nome(f) for f in arqs if f.name.startswith("CAPA_") and f.suffix.lower() in (".png", ".jpg", ".jpeg")],
        "telas_html": [nome(f) for f in arqs if f.name.startswith("_TELA") and f.suffix == ".html"],
        "cartoes_png": [nome(f) for f in arqs if f.name.startswith("TELA_") and f.suffix.lower() == ".png"],
        "fotos": [nome(f) for f in arqs if f.suffix.lower() in (".jpg", ".jpeg", ".png")
                  and not f.name.startswith(("CAPA_", "_CAPA_", "TELA_", "_"))],
        "brutos": brutos,
        "editados": editados,
        "previas": previas,
        "edicao_json": [nome(f) for f in arqs if f.name.startswith("_edicao_") and f.suffix == ".json"],
        "estado_json": [nome(f) for f in arqs if f.name.startswith("_peca_") and f.suffix == ".json"],
    }


def fase_pelos_arquivos(pasta, inv) -> str:
    if pasta is None:
        return "sem_pasta"
    if pasta.parent.name == "Publicados":
        return "publicada"
    if inv["editados"]:
        return "editada"
    if inv["brutos"]:
        return "gravada"
    if inv["laminas_png"]:
        return "produzida"   # carrossel com as lâminas exportadas
    if inv["roteiro_html"]:
        return "roteiro"
    return "pasta_vazia"


def publicados_recentes(quantos=8):
    base = REELS / "Publicados"
    if not base.exists():
        return []
    pastas = [d for d in base.iterdir() if d.is_dir() and re.match(r"R\d{3}\b", d.name)]
    pastas.sort(key=lambda d: int(re.match(r"R(\d{3})", d.name).group(1)), reverse=True)
    saida = []
    for d in pastas[:quantos]:
        item = {"codigo": re.match(r"R\d{3}", d.name).group(0), "pasta": d.name}
        item.update(meta_do_roteiro(d))
        item["cor_legenda"] = cor_legenda(d)
        saida.append(item)
    return saida


def em_andamento():
    """Peças R, C e A fora de Publicados, com a fase que os arquivos sugerem."""
    saida = []
    for base, padrao in ((REELS, r"R\d{3}\b"), (CARROSSEIS, r"Carrossel_(\d{3})_"), (CRIATIVOS, r"A\d{2,3}(?:\s+a\s+A\d{2,3})?\b")):
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            m = re.match(padrao, d.name)
            if d.is_dir() and m:
                inv = inventario(d)
                codigo = f"C{m.group(1)}" if base is CARROSSEIS else m.group(0)
                saida.append({"codigo": codigo, "pasta": d.name,
                              "fase_arquivos": fase_pelos_arquivos(d, inv),
                              "estado": bool(inv["estado_json"])})
    return saida


# ---------------------------------------------------------------- anúncios (trilha A)

ROTULOS_ANUNCIO = ["Produto", "Mandala", "Estrutura de roteiro", "Fase", "Formato", "Conceito nomeado",
                   "Inimigo concreto", "CTA / Botão", "CTA", "Público", "Fonte", "Duração", "Tema único",
                   "O que muda entre as quatro", "Posicionamento"]


def meta_do_anuncio(pasta: Path):
    """Lê do roteiro do anúncio o essencial: título, nota, Mandala, conceito, inimigo, CTA, duração."""
    htmls = sorted(h for h in pasta.glob("*roteiro*.html") if not h.name.startswith("_"))
    if not htmls:
        return {}
    doc = ler(htmls[0])
    info = {"roteiro": htmls[0].name}
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", doc, flags=re.S)
    if h1:
        info["titulo"] = limpar(h1.group(1))[:160]
    nota = (re.search(r'class="score-big"[^>]*>\s*(\d{1,2}[.,]\d)', doc)
            or re.search(r"(\d{1,2}[.,]\d)\s*/\s*10", doc))
    if nota:
        info["nota"] = nota.group(1).replace(",", ".")
    # o .meta tem divs aninhadas: ler até o próximo h2 ou até o scorecard, não até o primeiro </div>
    meta = re.search(r'<div class="meta">(.*?)(?=<h2|<div class="scorecard"|<section)', doc, flags=re.S)
    texto = limpar(meta.group(1)) if meta else limpar(re.sub(r"<(script|style)[^>]*>.*?</\1>", "", doc[:12000], flags=re.S))
    alvo = "|".join(re.escape(r) for r in ROTULOS_ANUNCIO)
    for campo in ("Mandala", "Conceito nomeado", "Inimigo concreto", "CTA / Botão", "Duração", "Formato"):
        m = re.search(rf"{re.escape(campo)}:\s*(.*?)(?=\s(?:{alvo}):|$)", texto)
        if m:
            chave = campo.lower().replace(" / botão", "").replace(" ", "_").replace("ç", "c").replace("ã", "a")
            info[chave] = m.group(1).strip()[:220]
    return info


def anuncios_recentes(quantos=8):
    """Anúncios mais recentes (em andamento e publicados), para não repetir DNA."""
    pastas = []
    for base in (CRIATIVOS, CRIATIVOS / "Publicados"):
        if base.exists():
            pastas += [d for d in base.iterdir() if d.is_dir() and re.match(r"A\d{2,3}\b", d.name)]

    def maior(d):
        m = re.match(r"A(\d+)(?:\s+a\s+A(\d+))?", d.name)
        return int(m.group(2) or m.group(1))
    pastas.sort(key=maior, reverse=True)
    saida = []
    for d in pastas[:quantos]:
        m = re.match(r"A\d+(?:\s+a\s+A\d+)?", d.name)
        item = {"codigo": m.group(0), "pasta": d.name, "publicado": d.parent.name == "Publicados"}
        item.update(meta_do_anuncio(d))
        saida.append(item)
    return saida


def parse_briefing(doc: str):
    """Linhas da tabela de peças de um briefing-{leva}.html (ver roteiro-anuncio.md, seção 6)."""
    pecas = []
    for tr in re.finditer(r"<tr([^>]*)>(.*?)</tr>", doc, flags=re.S):
        corpo = tr.group(2)
        pc = re.search(r'class="pc"[^>]*>\s*(A\d{2,3})\s*<', corpo)
        if not pc:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", corpo, flags=re.S)
        if len(tds) < 3:
            continue
        codigo = normalizar(pc.group(1))
        titulo = re.sub(rf"^{codigo}\s*", "", limpar(tds[0])).strip()
        quote = re.search(r'<div class="quote">(.*?)</div>', tds[2], flags=re.S)
        pecas.append({
            "codigo": codigo,
            "titulo": titulo,
            "angulo": limpar(tds[1]),
            "gancho": limpar(quote.group(1)) if quote else "",
            "detalhe": limpar(re.sub(r'<div class="quote">.*?</div>', "", tds[2], flags=re.S)),
            "fonte": limpar(tds[3]) if len(tds) > 3 else "",
            "teste_capa": limpar(tds[4]) if len(tds) > 4 else "",
        })
    return pecas


def brief_do_anuncio(codigo: str, caminho=None):
    if caminho:
        arquivos = [Path(caminho) if Path(caminho).is_absolute() else RAIZ / caminho]
    else:
        arquivos = sorted(CRIATIVOS.glob("briefing-*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    resultado = {"codigo": codigo, "briefing": None, "peca": None}
    for arq in arquivos:
        if not arq.exists():
            continue
        pecas = parse_briefing(ler(arq))
        achada = next((p for p in pecas if p["codigo"] == codigo), None)
        if achada:
            resultado["briefing"] = str(arq)
            resultado["peca"] = achada
            resultado["mesma_leva"] = [p for p in pecas if p["codigo"] != codigo]
            break
    if resultado["peca"] is None:
        resultado["aviso"] = (f"{codigo} não está em nenhum briefing-*.html de {CRIATIVOS}. Perguntar ao Rodrigo o ângulo "
                              "e a prova da peça (uma pergunta) e seguir; o formato do briefing está em roteiro-anuncio.md, seção 6.")
    return resultado


def brief_qualquer(codigo: str, caminho=None):
    """Brief de qualquer letra: Diretrizes (R e C) ou briefing de leva (A)."""
    if codigo[0] == "A":
        return brief_do_anuncio(codigo, caminho)
    resultado, _ = brief_da_peca(codigo, caminho)
    return resultado


def carrosseis_recentes(quantos=6):
    """Carrosséis mais recentes (em andamento e publicados): layout, capa e cor, para a rotação."""
    pastas = []
    for base in (CARROSSEIS, CARROSSEIS / "Publicados"):
        if base.exists():
            pastas += [d for d in base.iterdir() if d.is_dir() and re.match(r"Carrossel_\d{3}_", d.name)]
    pastas.sort(key=lambda d: int(re.match(r"Carrossel_(\d{3})", d.name).group(1)), reverse=True)
    saida = []
    for d in pastas[:quantos]:
        item = {"codigo": f"C{re.match(r'Carrossel_(\d{3})', d.name).group(1)}", "pasta": d.name,
                "publicado": d.parent.name == "Publicados"}
        htmls = [h for h in d.glob("Carrossel_*.html") if not h.name.startswith("_")]
        if htmls:
            doc = ler(htmls[0])
            t = re.search(r"<title>(.*?)</title>", doc, flags=re.S)
            if t:
                item["titulo"] = limpar(t.group(1))
            # o nome do layout fica num comentário do CSS: "/* layout placar: duas colunas... */"
            # (ou, nos antigos, "/* --- Artes 1080 x 1350: layout Caderno do dono --- */")
            lay = re.search(r"/\*[^*]*?\blayout\s+(.+?)\s*\*/", doc, flags=re.S)
            if lay:
                item["layout"] = re.sub(r"[\s\-]+$", "", lay.group(1).strip())[:90]
            capa = re.search(r'<div class="s[^"]*">(.*?)</div>\s*(?=<!--|<div class="s)', doc, flags=re.S)
            if capa:
                item["capa_texto"] = limpar(re.sub(r'<div class="pg">.*?</div>', "", capa.group(1), flags=re.S))[:160]
            cor_capa = re.search(r'<div class="s\s+(esm|creme|terra)', doc)
            if cor_capa:
                item["cor_capa"] = cor_capa.group(1)
            item["laminas"] = len(re.findall(r'<div class="s[\s"]', doc))
            item["com_foto"] = bool(re.search(r"_fundo_0|_foto_capa", doc))
        saida.append(item)
    return saida


# ---------------------------------------------------------------- comandos

def cmd_brief(args):
    codigo = normalizar(args[0] if args else "")
    caminho = None
    for flag in ("--diretrizes", "--briefing"):
        if flag in args:
            caminho = args[args.index(flag) + 1]
    resultado = brief_qualquer(codigo, caminho)
    pasta = achar_pasta(codigo)
    resultado["pasta_existente"] = str(pasta) if pasta else None
    resultado["em_andamento"] = em_andamento()
    if codigo[0] == "R":
        resultado["publicados_recentes"] = publicados_recentes()
        cores = [p["cor_legenda"] for p in resultado["publicados_recentes"] if p.get("cor_legenda")]
        resultado["cores_legenda_a_evitar"] = cores[:2]
    elif codigo[0] == "C":
        resultado["carrosseis_recentes"] = carrosseis_recentes()
        resultado["layouts_a_evitar"] = [c["layout"] for c in resultado["carrosseis_recentes"] if c.get("layout")][:3]
    elif codigo[0] == "A":
        resultado["anuncios_recentes"] = anuncios_recentes()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


def atribuir(dic: dict, chave: str, valor):
    partes = chave.split(".")
    for p in partes[:-1]:
        dic = dic.setdefault(p, {})
        if not isinstance(dic, dict):
            falhar(f"A chave {chave} atravessa um valor que não é objeto.")
    dic[partes[-1]] = valor


def valor_json(txt: str):
    try:
        return json.loads(txt)
    except ValueError:
        return txt


def cmd_estado(args):
    if not args:
        falhar("Uso: peca.py estado R035 [--nome Nome] [--renomear Novo] [--fase X] [--brief] [--set k=v]")
    codigo = normalizar(args[0])
    letra = codigo[0]
    opcoes = args[1:]

    def opcao(flag):
        return opcoes[opcoes.index(flag) + 1] if flag in opcoes else None

    nome, renomear, fase = opcao("--nome"), opcao("--renomear"), opcao("--fase")
    sets = [opcoes[i + 1] for i, a in enumerate(opcoes) if a == "--set" and i + 1 < len(opcoes)]
    gravar_brief = "--brief" in opcoes
    if fase and fase not in FASES:
        falhar(f"Fase desconhecida: {fase}. Fases: {', '.join(FASES)}")

    pasta = achar_pasta(codigo)
    if pasta is None and nome:
        if letra == "R":
            pasta = REELS / f"{codigo} - {nome}"
        elif letra == "C":
            pasta = CARROSSEIS / f"Carrossel_{codigo[1:]}_{nome}"
        else:
            pasta = CRIATIVOS / f"{codigo} - {nome}"
        pasta.mkdir(parents=True, exist_ok=True)
    if pasta is not None and renomear:
        if pasta.parent.name == "Publicados":
            falhar("Peça publicada não é renomeada.")
        if letra == "R":
            nova = pasta.parent / f"{codigo} - {renomear}"
        elif letra == "C":
            nova = pasta.parent / f"Carrossel_{codigo[1:]}_{renomear}"
        else:
            nova = pasta.parent / f"{codigo} - {renomear}"
        if nova.exists():
            falhar(f"Já existe {nova.name}.")
        pasta.rename(nova)
        pasta = nova

    estado_arq = (pasta / f"_peca_{codigo}.json") if pasta else None
    estado = {}
    if estado_arq and estado_arq.exists():
        try:
            estado = json.loads(ler(estado_arq))
        except ValueError:
            estado = {"aviso": "estado anterior ilegível, recomeçado"}

    mudou = False
    if pasta is not None and (fase or sets or gravar_brief or nome or renomear):
        estado.setdefault("codigo", codigo)
        estado.setdefault("trilha", letra)
        estado["pasta"] = str(pasta.relative_to(RAIZ)).replace("\\", "/")
        estado["nome"] = re.sub(r"^(R\d{3} - |Carrossel_\d{3}_|A\d+ - )", "", pasta.name)
        estado.setdefault("historico", [])
        if fase:
            estado["fase"] = fase
            estado["historico"].append({"fase": fase, "em": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})
        if gravar_brief:
            resultado = brief_qualquer(codigo)
            estado["brief"] = resultado.get("peca") or {"aviso": resultado.get("aviso", "")}
            if resultado.get("grade_em_volta"):
                estado["grade_em_volta"] = resultado["grade_em_volta"]
        for item in sets:
            if "=" not in item:
                falhar(f"--set espera chave=valor, recebi {item!r}")
            k, v = item.split("=", 1)
            atribuir(estado, k.strip(), valor_json(v.strip()))
        estado["atualizado_em"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        estado_arq.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        mudou = True

    inv = inventario(pasta) if pasta else {}
    saida = {
        "codigo": codigo,
        "trilha": letra,
        "pasta": str(pasta) if pasta else None,
        "publicada": bool(pasta and pasta.parent.name == "Publicados"),
        "fase_arquivos": fase_pelos_arquivos(pasta, inv) if pasta else "sem_pasta",
        "fase_registrada": estado.get("fase"),
        "arquivos": inv,
        "estado": estado if estado else None,
        "estado_gravado_agora": mudou,
    }
    if pasta and letra == "R":
        saida["roteiro_meta"] = meta_do_roteiro(pasta)
        saida["cor_legenda"] = cor_legenda(pasta)
    elif pasta and letra == "A":
        saida["roteiro_meta"] = meta_do_anuncio(pasta)
        saida["cor_legenda"] = cor_legenda(pasta)
    print(json.dumps(saida, ensure_ascii=False, indent=2))


TRABALHO_EDICAO = (Path(os.environ.get("REELS_EDITAR_HOME") or Path(os.environ.get("LOCALAPPDATA", Path.home() / ".cache")) / "reels-editar")) / "trabalho"


def referenciados_na_pasta(pasta: Path, arqs):
    """Nomes de arquivo que o JSON de edição ou os HTML da pasta usam (ficam sempre)."""
    nomes = {f.name for f in arqs}
    usados = set()
    for ed in pasta.glob("_edicao_*.json"):
        try:
            cfg = json.loads(ler(ed))
        except ValueError:
            continue

        def coletar(v):
            if isinstance(v, str):
                # o JSON pode guardar o caminho inteiro (com barras de Windows): vale o nome do arquivo
                nome = v.replace("\\", "/").split("/")[-1]
                if nome in nomes:
                    usados.add(nome)
            elif isinstance(v, dict):
                for x in v.values():
                    coletar(x)
            elif isinstance(v, list):
                for x in v:
                    coletar(x)
        coletar(cfg)
    for h in pasta.glob("*.html"):
        for ref in re.findall(r"""(?:src|href)=["']([^"']+)["']""", ler(h)):
            nome = ref.split("/")[-1].split("?")[0]
            if nome in nomes:
                usados.add(nome)
    return usados


def cmd_limpar(args):
    """Depois da aprovação: lista (e com --apagar remove) os arquivos de trabalho da edição.

    Ficam: o bruto, o vídeo final, o roteiro e os HTML, capa e telas, legenda, o _edicao_*.json
    (reedição), o estado, as fotos e tudo que o JSON de edição ou um HTML usa.
    Saem: versões anteriores, prévias, testes, prévias de capa, cópias de transcrição e,
    com --trabalho, a pasta de trabalho da edição no computador.
    """
    if not args:
        falhar("Uso: peca.py limpar R035 [--apagar] [--trabalho]")
    codigo = normalizar(args[0])
    apagar, trabalho = "--apagar" in args, "--trabalho" in args
    pasta = achar_pasta(codigo)
    if pasta is None:
        falhar(f"Pasta do {codigo} não encontrada.")
    arqs = [f for f in pasta.iterdir() if f.is_file()]
    usados = referenciados_na_pasta(pasta, arqs)
    fica, sai = [], []
    for f in arqs:
        n, low = f.name, f.name.lower()
        final = re.match(rf"{codigo}_editado.*\.mp4$", n, re.I) is not None
        bruto = (f.suffix.lower() in (".mp4", ".mov") and not n.startswith("_") and "editado" not in low
                 and not re.search(r"previa|teste", low))
        sempre = (n in usados or final or bruto or f.suffix.lower() == ".html" or n == "legenda.txt"
                  or n.startswith(("_peca_", "_edicao_", "_CAPA_", "_TELA", "CAPA_", "TELA_")))
        if sempre:
            fica.append(n)
        elif n.startswith("_") or re.search(r"_previa|_PREVIA|_teste", n):
            sai.append(n)
        else:
            fica.append(n)   # fotos e imagens do celular: nunca se mexe sem pedido
    tamanho = sum((pasta / n).stat().st_size for n in sai)
    pastas_trab = [TRABALHO_EDICAO / c for c in (codigo, codigo + "V", codigo + "H") if (TRABALHO_EDICAO / c).exists()]
    tam_trab = sum(f.stat().st_size for p in pastas_trab for f in p.rglob("*") if f.is_file())
    apagados = []
    if apagar:
        for n in sai:
            (pasta / n).unlink()
            apagados.append(n)
        if trabalho:
            for p in pastas_trab:
                shutil.rmtree(p, ignore_errors=True)
                apagados.append(str(p))
    print(json.dumps({
        "codigo": codigo,
        "pasta": str(pasta),
        "sai": sai,
        "fica": fica,
        "liberado_mb": round(tamanho / 1e6, 1),
        "trabalho_edicao": [str(p) for p in pastas_trab],
        "trabalho_mb": round(tam_trab / 1e6, 1),
        "apagado": apagar,
        "apagados": apagados,
        "aviso": None if apagar else "Nada foi apagado: rode de novo com --apagar (e --trabalho para a pasta de trabalho) depois do ok do Rodrigo.",
    }, ensure_ascii=False, indent=2))


def cmd_proximo(_args):
    saida = {
        "proximo_reel": f"R{maior_numero('R') + 1:03d}",
        "proximo_carrossel": f"C{maior_numero('C') + 1:03d}",
        "proximo_anuncio": f"A{maior_numero('A') + 1:02d}",
        "em_andamento": em_andamento(),
    }
    try:
        arq = arquivo_diretrizes()
        pecas = parse_diretrizes(ler(arq), ano_do_arquivo(arq))
        saida["diretrizes"] = str(arq)
        saida["sem_pasta_nas_diretrizes"] = [
            {k: p[k] for k in ("codigo", "dia", "hora", "formato", "titulo", "capa")}
            for p in pecas if achar_pasta(p["codigo"]) is None
        ]
    except SystemExit:
        saida["diretrizes"] = None
    print(json.dumps(saida, ensure_ascii=False, indent=2))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    comando, args = sys.argv[1], sys.argv[2:]
    if comando == "brief":
        cmd_brief(args)
    elif comando == "estado":
        cmd_estado(args)
    elif comando == "proximo":
        cmd_proximo(args)
    elif comando == "limpar":
        cmd_limpar(args)
    else:
        falhar(f"Comando desconhecido: {comando}. Use brief, estado, proximo ou limpar.")


if __name__ == "__main__":
    main()
