# -*- coding: utf-8 -*-
"""Monta o HTML dos trends do dia a partir do JSON da curadoria.

Uso: py -3 scripts/trends-restaurantes-html.py [AAAA-MM-DD]
Sem data, usa o JSON mais recente em meus-produtos/linha-editorial/trends/.
Grava meus-produtos/linha-editorial/trends/AAAA-MM-DD.html (arquivo único, tema escuro).
"""
import json
import sys
from datetime import date
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "meus-produtos" / "linha-editorial" / "trends"
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def e(t):
    return escape(str(t or ""))


def num(v, casas=1):
    if v is None:
        return "n/d"
    s = f"{v:,.{casas}f}" if isinstance(v, float) else f"{v:,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def link(url, texto, cls=""):
    if not url:
        return e(texto)
    return f'<a href="{e(url)}" target="_blank" rel="noopener" class="{cls}">{e(texto)}</a>'


CSS = """
:root{--ink-0:#0b0b0d;--ink-1:#131316;--ink-2:#1b1b20;--ink-3:#26262d;--line:#2e2e36;
--text-hi:#f4f4f5;--text-mid:#c1c1c6;--text-dim:#8a8a92;--text-faint:#5a5a63;
--neon:#c4ff5e;--neon-dim:#a3d94a;--rust:#e8805f;--ochre:#e3b04b;--sky:#7dc8e8;
--display:'Space Grotesk',sans-serif;--body:'Inter',sans-serif;--mono:'JetBrains Mono',monospace;--r:14px}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--ink-0);color:var(--text-mid);font-family:var(--body);font-size:15.5px;line-height:1.65;-webkit-font-smoothing:antialiased;
background-image:radial-gradient(900px 500px at 85% -10%,rgba(196,255,94,.07),transparent 60%),radial-gradient(700px 400px at -10% 30%,rgba(125,200,232,.05),transparent 60%)}
a{color:var(--sky);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1120px;margin:0 auto;padding:48px 24px 80px}
.label{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--neon-dim)}
h1{font-family:var(--display);color:var(--text-hi);font-size:clamp(38px,6vw,64px);line-height:1.02;letter-spacing:-.02em;margin:14px 0 6px}
h1 em{font-style:normal;color:var(--neon)}
.dia{font-family:var(--display);font-size:20px;color:var(--text-mid)}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}
.stat{background:var(--ink-1);border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:120px}
.stat b{display:block;font-family:var(--display);font-size:22px;color:var(--text-hi);line-height:1.1}
.stat span{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--text-dim)}
.fraco{margin-top:22px;border:1px solid rgba(227,176,75,.35);background:rgba(227,176,75,.08);color:var(--ochre);border-radius:10px;padding:12px 16px}
.indice{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:40px 0 18px}
.ind{display:block;background:linear-gradient(180deg,var(--ink-2),var(--ink-1));border:1px solid var(--line);border-radius:var(--r);padding:18px;color:var(--text-mid);transition:.2s}
.ind:hover{border-color:var(--neon-dim);transform:translateY(-2px);text-decoration:none}
.ind .n{font-family:var(--mono);color:var(--neon);font-size:13px}
.ind h3{font-family:var(--display);color:var(--text-hi);font-size:17px;line-height:1.25;margin:8px 0 12px}
.pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;border-radius:99px;padding:4px 10px;border:1px solid var(--line);color:var(--text-dim)}
.pill.alta{color:var(--rust);border-color:rgba(232,128,95,.45);background:rgba(232,128,95,.08)}
.pill.media{color:var(--ochre);border-color:rgba(227,176,75,.4);background:rgba(227,176,75,.07)}
.pill.novo{color:var(--neon);border-color:rgba(196,255,94,.35);background:rgba(196,255,94,.06)}
.dot{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 10px currentColor}
.topico{margin-top:56px;background:var(--ink-1);border:1px solid var(--line);border-radius:20px;overflow:hidden}
.topo{padding:30px 32px 24px;border-bottom:1px solid var(--line);display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:start}
.big{font-family:var(--display);font-size:76px;line-height:.8;color:transparent;-webkit-text-stroke:1.5px var(--neon-dim)}
.topo h2{font-family:var(--display);color:var(--text-hi);font-size:clamp(24px,3.2vw,34px);line-height:1.12;letter-spacing:-.01em}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.validade{margin-top:12px;color:var(--text-dim);font-size:14px}
.validade b{color:var(--text-mid);font-weight:600}
.corpo{display:grid;grid-template-columns:1.15fr .85fr;gap:0}
.col{padding:26px 32px}.col+.col{border-left:1px solid var(--line);background:rgba(255,255,255,.012)}
.bloco+.bloco{margin-top:26px}
.bt{font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--text-dim);margin-bottom:8px}
.bloco p{color:var(--text-mid)}
.fontes{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px}
.fontes a{font-family:var(--mono);font-size:11.5px;border:1px solid var(--line);border-radius:6px;padding:3px 9px;color:var(--sky)}
.lacuna{background:linear-gradient(135deg,rgba(196,255,94,.10),rgba(196,255,94,.02));border:1px solid rgba(196,255,94,.3);border-radius:12px;padding:16px 18px}
.lacuna .bt{color:var(--neon)}.lacuna p{color:var(--text-hi)}
.fala{display:grid;grid-template-columns:1fr auto;gap:4px 12px;padding:11px 0;border-bottom:1px dashed var(--line)}
.fala:last-child{border-bottom:0}
.fala .quem{color:var(--text-hi);font-weight:600;font-size:14.5px}
.fala .quem small{color:var(--text-dim);font-weight:400;margin-left:6px}
.fala .nota{grid-column:1/-1;color:var(--text-dim);font-size:13px}
.fala .com{font-family:var(--mono);font-size:12px;color:var(--text-mid);text-align:right;white-space:nowrap}
.barra{grid-column:1/-1;height:6px;background:var(--ink-3);border-radius:99px;overflow:hidden;margin-top:2px}
.barra i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--neon-dim),var(--neon))}
.forca{font-family:var(--mono);font-size:11px;color:var(--neon)}
.noticia .quem{font-weight:500}.noticia .quem a{color:var(--text-hi)}
.obs{margin-top:10px;font-size:13.5px;color:var(--ochre)}
.voz{position:relative;background:var(--ink-2);border:1px solid var(--line);border-radius:4px 14px 14px 14px;padding:11px 14px;font-size:14.5px;color:var(--text-hi);margin-top:10px}
.voz small{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--text-dim);margin-top:6px}
.voz.outro{border-color:rgba(125,200,232,.3);background:rgba(125,200,232,.05)}
.vazio{color:var(--text-dim);font-style:italic;font-size:14px}
.gancho{margin:0 32px 26px;padding:24px 26px;border-radius:16px;background:var(--ink-0);border:1px solid var(--line);position:relative}
.gancho .bt{color:var(--neon)}
.gancho blockquote{font-family:var(--display);font-size:clamp(19px,2.3vw,24px);line-height:1.35;color:var(--text-hi);padding-right:120px}
.copiar{position:absolute;top:20px;right:20px;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;background:var(--neon);color:#111;border:0;border-radius:8px;padding:8px 12px;cursor:pointer;font-weight:700}
.copiar.ok{background:var(--sky)}
.rodape-t{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 32px 30px}
.chip{background:var(--ink-2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;font-size:14.5px}
.cuidado{background:rgba(227,176,75,.07);border-color:rgba(227,176,75,.35)}
.cuidado .bt{color:var(--ochre)}
.radar{margin-top:56px}
.radar h2,.saude h2{font-family:var(--display);color:var(--text-hi);font-size:24px;margin:8px 0 16px}
.radar ul{list-style:none;display:grid;gap:10px}
.radar li{background:var(--ink-1);border:1px solid var(--line);border-radius:12px;padding:13px 16px;display:flex;gap:14px;align-items:flex-start}
.radar li::before{content:"";flex:none;width:8px;height:8px;border-radius:50%;background:var(--sky);margin-top:9px;box-shadow:0 0 8px var(--sky)}
.radar li span{flex:1}.radar li a{font-family:var(--mono);font-size:11px;white-space:nowrap;margin-top:3px}
.saude{margin-top:48px;padding-top:24px;border-top:1px solid var(--line);font-size:13.5px;color:var(--text-dim)}
.saude h2{font-size:16px}.saude p+p{margin-top:6px}.saude b{color:var(--text-mid)}
@media (max-width:860px){.indice{grid-template-columns:1fr}.corpo{grid-template-columns:1fr}.col+.col{border-left:0;border-top:1px solid var(--line)}
.rodape-t{grid-template-columns:1fr}.topo{grid-template-columns:1fr;gap:10px}.big{font-size:54px}}
@media (max-width:560px){.wrap{padding:32px 16px 60px}.topo,.col{padding:22px 18px}.gancho,.rodape-t{margin-left:18px;margin-right:18px}
.gancho blockquote{padding-right:0}.copiar{position:static;margin-top:14px}}
@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}.copiar{display:none}.topico{break-inside:avoid-page}}
"""

JS = """
document.querySelectorAll('.copiar').forEach(b=>b.addEventListener('click',()=>{
  const t=b.parentElement.querySelector('blockquote').innerText.trim();
  const ok=()=>{b.textContent='Copiado';b.classList.add('ok');setTimeout(()=>{b.textContent='Copiar gancho';b.classList.remove('ok')},1800)};
  if(navigator.clipboard){navigator.clipboard.writeText(t).then(ok).catch(()=>{})}
}));
"""


def classe_temp(t):
    return "alta" if (t or "").lower().startswith("alta") else "media"


def quem_fala(itens, nota):
    maxf = max([i.get("forca") or 0 for i in itens if i.get("tipo") == "instagram"] + [1])
    linhas = []
    for i in itens:
        if i.get("tipo") == "instagram":
            f = i.get("forca")
            larg = min(100, (f or 0) / max(maxf, 1) * 100)
            forca = f'<span class="forca">{num(f)}x o normal</span>' if f else '<span class="forca">sem histórico</span>'
            nota_i = f'<div class="nota">{e(i.get("nota"))}</div>' if i.get("nota") else ""
            linhas.append(
                f'<div class="fala"><div class="quem">{link(i.get("link"), "@" + i.get("perfil", ""))}'
                f'<small>{e(i.get("formato"))}</small></div>'
                f'<div class="com">{num(i.get("comentarios"))} coment.</div>{nota_i}'
                f'<div class="barra"><i style="width:{larg:.0f}%"></i></div><div>{forca}</div></div>')
        else:
            linhas.append(
                f'<div class="fala noticia"><div class="quem">{link(i.get("link"), i.get("titulo"))}</div>'
                f'<div class="com">notícia</div><div class="nota">{e(i.get("veiculo"))}</div></div>')
    obs = f'<p class="obs">{e(nota)}</p>' if nota else ""
    return "".join(linhas) + obs


def vozes(lista, vazio):
    if not lista:
        return f'<p class="vazio">{e(vazio or "Sem comentários coletados sobre esse assunto.")}</p>'
    out = []
    for v in lista:
        lado = (v.get("lado") or "dono").lower()
        cls = "voz" if lado == "dono" else "voz outro"
        out.append(f'<div class="{cls}">“{e(v.get("texto"))}”<small>{e(lado)}</small></div>')
    return "".join(out)


def topico(i, t):
    n = f"{i:02d}"
    temp = classe_temp(t.get("temperatura"))
    status = t.get("status") or "novo"
    st_cls = "novo" if status.lower().startswith("novo") else ""
    fontes = "".join(link(f.get("link"), f.get("nome")) for f in t.get("fontes") or [])
    cuidado = (f'<div class="chip cuidado"><div class="bt">Cuidado</div>{e(t.get("cuidado"))}</div>'
               if t.get("cuidado") else "")
    return f"""
<section class="topico" id="t{i}">
  <div class="topo">
    <div class="big">{n}</div>
    <div>
      <h2>{e(t.get("titulo"))}</h2>
      <div class="meta"><span class="pill {temp}"><span class="dot"></span>Temperatura {e(t.get("temperatura"))}</span>
      <span class="pill {st_cls}">{e(status)}</span></div>
      <p class="validade"><b>Validade:</b> {e(t.get("validade"))}</p>
    </div>
  </div>
  <div class="corpo">
    <div class="col">
      <div class="bloco"><div class="bt">O que aconteceu</div><p>{e(t.get("o_que_aconteceu"))}</p>
        <div class="fontes">{fontes}</div></div>
      <div class="bloco"><div class="bt">Por que mexe no caixa</div><p>{e(t.get("caixa"))}</p></div>
      <div class="bloco lacuna"><div class="bt">O que ninguém está dizendo</div><p>{e(t.get("lacuna"))}</p></div>
    </div>
    <div class="col">
      <div class="bloco"><div class="bt">Quem está falando</div>{quem_fala(t.get("quem_fala") or [], t.get("nota_quem_fala"))}</div>
      <div class="bloco"><div class="bt">O que estão dizendo nos comentários</div>{vozes(t.get("vozes"), t.get("vozes_vazio"))}</div>
    </div>
  </div>
  <div class="gancho"><div class="bt">Gancho pronto</div><blockquote>{e(t.get("gancho"))}</blockquote>
    <button class="copiar" type="button">Copiar gancho</button></div>
  <div class="rodape-t">
    <div class="chip"><div class="bt">Formato</div>{e(t.get("formato"))}<br><span style="color:var(--text-dim);font-size:13.5px">{e(t.get("ja_falou"))}</span></div>
    {cuidado}
  </div>
</section>"""


def montar(d):
    dt = date.fromisoformat(d["data"])
    dia = f"{DIAS[dt.weekday()]}, {dt.day:02d} de {MESES[dt.month - 1]} de {dt.year}"
    c = d.get("coleta") or {}
    stats = "".join(f'<div class="stat"><b>{v}</b><span>{r}</span></div>' for v, r in [
        (num(c.get("perfis")), "perfis lidos"), (num(c.get("posts_janela")), "posts em 48h"),
        (num(c.get("noticias")), "notícias"), (e(c.get("hora")), "hora da coleta"),
        ("US$ " + num(c.get("custo_usd"), 2) if c.get("custo_usd") is not None else "n/d", "custo do Apify")])
    tops = d.get("topicos") or []
    indice = "".join(
        f'<a class="ind" href="#t{i}"><span class="n">{i:02d}</span><h3>{e(t.get("titulo"))}</h3>'
        f'<span class="pill {classe_temp(t.get("temperatura"))}"><span class="dot"></span>{e(t.get("temperatura"))}</span></a>'
        for i, t in enumerate(tops, 1))
    fraco = f'<div class="fraco">{e(d.get("dia_fraco"))}</div>' if d.get("dia_fraco") else ""
    radar = "".join(f'<li><span>{e(r.get("texto"))}</span>{link(r.get("link"), "abrir")}</li>' for r in d.get("radar") or [])
    s = d.get("saude") or {}
    sem = ", ".join("@" + p for p in s.get("sem_post") or []) or "nenhum"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trends do dia {dt.strftime('%d/%m')}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main class="wrap">
<header>
  <div class="label">Radar do dono · Linha Editorial · @rodrigohaertel</div>
  <h1>O que os donos estão <em>discutindo</em> hoje</h1>
  <div class="dia">{e(dia)}</div>
  <div class="stats">{stats}</div>{fraco}
</header>
<nav class="indice">{indice}</nav>
{"".join(topico(i, t) for i, t in enumerate(tops, 1))}
<section class="radar"><div class="label">Ficou de fora, mas vale olhar</div><h2>No radar</h2><ul>{radar}</ul></section>
<footer class="saude"><div class="label">Bastidor</div><h2>Saúde da coleta</h2>
<p><b>Sem post nas últimas 48h:</b> {e(sem)}</p><p><b>Alertas:</b> {e(s.get("alertas") or "Nenhum.")}</p>
<p>Força = comentários do post ÷ mediana de comentários daquele perfil nos últimos 45 dias.</p></footer>
</main><script>{JS}</script></body></html>"""


def main():
    if len(sys.argv) > 1:
        origem = PASTA / f"{sys.argv[1]}.json"
    else:
        cands = sorted(p for p in PASTA.glob("????-??-??.json"))
        if not cands:
            raise SystemExit("Nenhum JSON de trends encontrado.")
        origem = cands[-1]
    d = json.loads(origem.read_text(encoding="utf-8"))
    destino = origem.with_suffix(".html")
    destino.write_text(montar(d), encoding="utf-8")
    print(f"HTML salvo em {destino}")


if __name__ == "__main__":
    main()
