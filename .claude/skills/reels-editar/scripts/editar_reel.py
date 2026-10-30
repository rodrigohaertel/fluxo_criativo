# Editor de Reels: bruto vertical -> Reel final.
# Cortes só nas pausas longas (com dissolvência curta), zoom suave contínuo ancorado no rosto,
# legenda Montserrat em maiúscula palavra por palavra, título + pílula nos 3 primeiros segundos
# e a capa no primeiro quadro (para a miniatura do WhatsApp).
# Uso: py -3 editar_reel.py _edicao_R0XX.json [--render]
# Sem --render, só monta o plano (cortes, zoom, título, legenda) e imprime o resumo.
import json, re, subprocess, sys, unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FERR = Path(__file__).resolve().parent
sys.path.insert(0, str(FERR))
from ambiente import FONTES, TRABALHO, ambiente, deep_filter
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
# arquivos intermediários: por padrão em %LOCALAPPDATA%/reels-editar/trabalho/{código}, preenchidos pelo preparar.py
TRAB = Path(cfg.get("trabalho") or TRABALHO / cfg["codigo"]); TRAB.mkdir(parents=True, exist_ok=True)
# modo palco: no lugar da tela dividida, fundo de marca cheio, cartão grande em cima, o rosto num círculo
# com borda dourada embaixo e uma etiqueta com o nome do momento (A PESQUISA, O NÚMERO...)
PALCO = cfg.get("modo_div") == "palco"
P_CARD_Y, P_CARD_W, P_D = cfg.get("palco_y", 360), 1040, cfg.get("palco_diametro", 420)
P_CY = cfg.get("palco_cy", P_CARD_Y + round(P_CARD_W * 0.58) + 32 + P_D // 2)  # centro do círculo
P_TELA_ALT = 720  # aula no palco (R029): a tela animada entra em 1080 × 720, de y P_CARD_Y para baixo
P_LEG_Y = cfg.get("palco_legenda_y", P_CY + P_D // 2 + 110)
cfg.setdefault("audio16k", str(TRAB / "audio16k.wav"))
cfg.setdefault("palavras", str(TRAB / "palavras.json"))
# bruto, capa, saída e cartões podem vir só com o nome do arquivo: valem a partir da pasta do Reel (onde fica o JSON)
PASTA = Path(sys.argv[1]).resolve().parent
na_pasta = lambda c: str(c if Path(c).is_absolute() else PASTA / c)
cfg.setdefault("capa", None)
for k in ("bruto", "capa", "saida"):
    if cfg[k]: cfg[k] = na_pasta(cfg[k])
for c in cfg.get("cartoes", []):
    c["arquivo"] = na_pasta(c["arquivo"])

D = 0.12            # duração da dissolvência em cada corte
PAUSA_MIN = cfg.get("pausa_min", 1.0)    # só corta pausa maior que isso (padrão dos Reels publicados: pausa típica 0,7 a 0,8 s)
PAUSA_FICA = cfg.get("pausa_fica", 0.8)  # quanto da pausa cortada permanece
FPS = 30
HORIZONTAL = cfg.get("formato") == "16:9"  # aula do YouTube; o padrão é Reel 9:16
W, H = (1920, 1080) if HORIZONTAL else (1080, 1920)
INICIO, FIM = cfg["inicio"], cfg["fim"]
FX0, FY0 = cfg["rosto"]  # centro do rosto em fração do quadro do bruto

# ---------- enquadramento: bruto em outra proporção ----------
# Aula gravada só com a câmera: câmera 4K em 16:9 vira o Reel 9:16 e o celular na vertical vira o YouTube 16:9.
# O quadro é recortado em volta do rosto antes do zoom (PRE); FX e FY passam a valer dentro do recorte.
_sonda = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height:stream_side_data=rotation", "-of", "json", cfg["bruto"]],
                                   capture_output=True, text=True).stdout)["streams"][0]
BW, BH = _sonda["width"], _sonda["height"]
if any(abs(int(d.get("rotation", 0))) == 90 for d in _sonda.get("side_data_list", [])):
    BW, BH = BH, BW  # celular gravado de pé

def regiao(aspecto, alt=1.0, rosto_y=0.42):
    """Recorte (x, y, w, h) do bruto na proporção pedida, com o rosto no centro e a rosto_y da altura."""
    h = min(BH * alt, BW / aspecto); w = h * aspecto
    x = min(max(FX0 * BW - w / 2, 0), BW - w); y = min(max(FY0 * BH - rosto_y * h, 0), BH - h)
    par = lambda v: int(v) // 2 * 2
    return par(x), par(y), par(w), par(h)

PRE, FX, FY = "", FX0, FY0
if abs(BW / BH - W / H) > 0.02:
    px, py, pw, ph = regiao(W / H, 1.0, 0.40)
    PRE = f"crop={pw}:{ph}:{px}:{py},"
    FX, FY = (FX0 * BW - px) / pw, (FY0 * BH - py) / ph
    print(f"bruto {BW}x{BH} recortado em {pw}x{ph} a partir de ({px}, {py}) para {W}x{H}")

# takes descartados (erros e regravações aprovados pelo Rodrigo): [início, fim] no tempo do bruto
TAKES_FORA = sorted(tuple(x) for x in cfg.get("remover", []))
fora_do_take = lambda w: any(a - 0.05 <= w["s"] and w["e"] <= b + 0.05 for a, b in TAKES_FORA)
palavras = [w for w in json.load(open(cfg["palavras"], encoding="utf-8"))
            if INICIO - 0.6 <= w["s"] < FIM and not fora_do_take(w)]

# ---------- pausas reais do áudio ----------
txt = subprocess.run(["ffmpeg", "-hide_banner", "-i", cfg["audio16k"], "-af",
                      "silencedetect=noise=-32dB:d=0.15", "-f", "null", "-"], capture_output=True, text=True).stderr
silencios = [(float(a), float(a) + float(d)) for a, d in
             zip(re.findall(r"silence_start: ([\d.]+)", txt), re.findall(r"silence_duration: ([\d.]+)", txt))]
silencios = [(a, b) for a, b in silencios if a > INICIO and b < FIM]

manter = cfg.get("pausas_manter", [])        # pausas dramáticas que não são cortadas
especiais = cfg.get("pausas_especiais", {})  # pausa -> quanto fica
remover = []
for a, b in silencios:
    if any(abs(a - m) < 0.15 for m in manter):
        continue
    fica = next((v for k, v in especiais.items() if abs(a - float(k)) < 0.15), PAUSA_FICA)
    if b - a >= PAUSA_MIN and (b - a) - fica >= cfg.get("corte_minimo", 0.4):
        remover.append((a + fica / 2, b - fica / 2))

# junta os cortes de pausa com os takes descartados (sem sobreposição)
juntos = []
for a, b in sorted(remover + list(TAKES_FORA)):
    if juntos and a <= juntos[-1][1] + 0.05: juntos[-1][1] = max(juntos[-1][1], b)
    else: juntos.append([a, b])
remover = [tuple(x) for x in juntos]
trechos, cur = [], INICIO
for a, b in remover:
    trechos.append((cur, a)); cur = b
trechos.append((cur, FIM))
offs, acc = [], 0.0
for i, (a, b) in enumerate(trechos):
    offs.append(acc); acc += (b - a) - D
DUR = acc + D

def mapa(t):
    for (a, b), o in zip(trechos, offs):
        if t < a: return o
        if t <= b: return o + (t - a)
    return DUR

def ajusta(w):
    s, e = w["s"], w["e"]
    for a, b in silencios:
        if a <= s < b: s = b
        if a < e <= b: e = a
        if s < a and e > b and a - s < 0.2: s = b
    s = max(s, INICIO)
    return s, max(e, s + 0.08)

itens = []
for w in palavras:
    s, e = ajusta(w)
    itens.append({"t": w["w"], "s": mapa(s), "e": mapa(e)})
juntados = []
for it in itens:
    t = it["t"]
    if juntados and (t in ("$", "%", "%,", "%.") or re.match(r"^[.,]\d", t) or t.startswith("-")):
        juntados[-1]["t"] += t; juntados[-1]["e"] = it["e"]; continue
    juntados.append(it)
itens = juntados
for troca in cfg.get("trocas", []):
    for it in itens:
        if it["t"].lower().strip(".,?!") == troca[0]:
            it["t"] = re.sub(re.escape(troca[0]), troca[1], it["t"], flags=re.I)

def com_separador(t):
    m = re.match(r"^(R\$)?(\d{4,})([.,%?!]*)$", t)
    if not m: return t
    if not m.group(1) and len(m.group(2)) == 4 and 1900 <= int(m.group(2)) <= 2100:
        return t  # ano fica sem ponto (2026)
    n = f"{int(m.group(2)):,}".replace(",", ".")
    return (m.group(1) or "") + n + m.group(3)
for it in itens:
    it["t"] = com_separador(it["t"])

# número por extenso e em algarismo casam igual ("quatro bilhões" no JSON acha "4 bilhões" na fala, e vice-versa)
NUMEROS = {w: str(k) for k, ws in enumerate(["zero", "um uma", "dois duas", "tres", "quatro", "cinco", "seis", "sete",
           "oito", "nove", "dez", "onze", "doze", "treze", "quatorze catorze", "quinze", "dezesseis", "dezessete",
           "dezoito", "dezenove", "vinte"]) for w in ws.split()}
NUMEROS.update({"trinta": "30", "quarenta": "40", "cinquenta": "50", "cem": "100"})

def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = re.sub(r"[^a-z0-9 ]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))
    return " ".join(NUMEROS.get(w, w) for w in t.split())

def acha(frase, depois=0.0):
    alvo = norm(frase).split()
    ws = [norm(i["t"]) for i in itens]
    for k in range(len(ws) - len(alvo) + 1):
        if ws[k:k + len(alvo)] == alvo and itens[k]["s"] >= depois:
            return itens[k]["s"], itens[k + len(alvo) - 1]["e"]
    raise SystemExit(f"Frase não encontrada na fala: {frase}")

# frases corrigidas pelo sentido: [como saiu na fala, como deve ficar na legenda], palavra por palavra
for errado, certo in cfg.get("trocas_frase", []):
    s0, _ = acha(errado)
    k0 = next(k for k, it in enumerate(itens) if abs(it["s"] - s0) < 1e-6)
    for k, palavra in enumerate(certo.split()):
        itens[k0 + k]["t"] = palavra

def acha_aprox(frase, depois=0.0):
    """Como acha(), mas aceita fala que fugiu um pouco do roteiro: primeiro trecho parecido (80%) depois de 'depois'."""
    try:
        return acha(frase, depois) + (1.0,)
    except SystemExit:
        pass
    from difflib import SequenceMatcher
    alvo = norm(frase); n = len(alvo.split())
    ws = [norm(i["t"]) for i in itens]
    melhor = (0.0, None)
    for k in range(len(ws) - n + 1):
        if itens[k]["s"] < depois: continue
        r = SequenceMatcher(None, alvo, " ".join(ws[k:k + n])).ratio()
        if r >= 0.8: melhor = (r, k); break
        if r > melhor[0]: melhor = (r, k)
    if melhor[0] < 0.6:
        raise SystemExit(f"Palavra da tela não encontrada na fala: {frase}")
    k = melhor[1]
    return itens[k]["s"], itens[k + n - 1]["e"], melhor[0]

# ---------- telas da aula gravada só com a câmera ----------
# "telas" no JSON (montada do roteiro, seção 1.1): cada troca de cena e cada clique ancorados numa palavra falada.
# Na cena "tela": vertical com a tela em cima e a câmera embaixo; horizontal com a tela cheia e a câmera no canto.
TELAS = cfg.get("telas", [])
AULA = bool(TELAS)
TELA_JAN, CLIQUES = [], []  # janelas com a tela e [tempo, número do clique], no tempo do vídeo final
if AULA:
    cena, ini, ult_t = "rosto", None, 0.0
    for marca in TELAS:
        s, _, conf = acha_aprox(marca["palavra"], ult_t - 0.01)
        ult_t = s
        if conf < 1.0:
            print(f"  âncora aproximada ({conf:.0%}): \"{marca['palavra']}\" em {s:.2f}s")
        t = max(s - 0.10, 0)  # a cena troca logo antes da palavra
        if marca.get("cena") == "tela" and cena != "tela":
            ini, cena = t, "tela"
        elif marca.get("cena") == "rosto" and cena == "tela":
            TELA_JAN.append([ini, t]); cena = "rosto"
        if "clique" in marca:
            CLIQUES.append([max(s - 0.15, 0), int(marca["clique"])])
    if cena == "tela":
        TELA_JAN.append([ini, DUR + 1])
    CLIQUES.sort()
    print("telas:", ", ".join(f"{a:.1f}-{b:.1f}s" for a, b in TELA_JAN))
    print("cliques:", ", ".join(f"{n} em {t:.1f}s" for t, n in CLIQUES))

# ---------- cenas do OBS ----------
# Aulas gravadas no OBS alternam só rosto e tela dividida (a aula em cima, creme). Na tela dividida
# não tem zoom (cortaria a aula) e a legenda sobe para entre a tela e a cabeça.
CENAS_DIV = []  # janelas de tela dividida no tempo do bruto
if cfg.get("cenas_obs"):
    cache = TRAB / "cenas_divididas.json"
    if not cache.exists():
        import numpy as np
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", cfg["bruto"], "-vf", "fps=2," + ("crop=1400:1000:40:40" if HORIZONTAL else "crop=1080:900:0:30") + ",scale=108:90",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.uint8).reshape(-1, 90, 108, 3).astype(float)
        fracao = (np.abs(x - cfg.get("cor_tela", [247, 242, 232])).sum(3) < 40).reshape(len(x), -1).mean(1)
        creme = fracao > 0.30
        idx = np.where(creme)[0]
        for a, b in zip(idx[:-1], idx[1:]):
            if 1 < b - a <= 8: creme[a:b] = True  # buraco de até 4 s no meio da tela dividida
        jan, ini = [], None
        for i in range(len(creme) + 1):
            v = creme[i] if i < len(creme) else False
            if v and ini is None: ini = i
            if not v and ini is not None:
                if (i - ini) / 2 >= 1.5: jan.append([ini / 2, i / 2])
                ini = None
        json.dump(jan, open(cache, "w"))
    CENAS_DIV = json.load(open(cache))
    print("tela dividida (bruto):", ", ".join(f"{a:.0f}-{b:.0f}s" for a, b in CENAS_DIV))
def div_out():  # janelas de tela no vídeo final (aula do OBS ou telas geradas do roteiro)
    if AULA: return [tuple(j) for j in TELA_JAN]
    return [(mapa(a), mapa(b)) for a, b in CENAS_DIV if mapa(b) - mapa(a) > 0.2]
def na_cena_div(t):
    return any(a - 0.01 <= t < b for a, b in div_out())

# ---------- zoom suave (pontos-chave com transição em curva S) ----------
chaves = [(0.0, 1.0), (cfg.get("titulo_ate", 3.0), 1.0)]
base = cfg.get("zoom_base", [1.06, 1.0])
for k, z in enumerate(cfg["zoom"]):
    s, _ = acha(z["de"], chaves[-1][0] - 1)
    _, e = acha(z["ate"], s)
    volta = base[k % 2]
    if z.get("empurra"):  # aproximação lenta ao longo da frase inteira
        chaves += [(max(s - 0.1, chaves[-1][0] + 0.2), chaves[-1][1]), (e, z["zoom"]), (e + 1.0, volta)]
    else:
        chaves += [(max(s - 0.45, chaves[-1][0] + 0.2), chaves[-1][1]), (s + 0.05, z["zoom"]),
                   (e + 0.1, z["zoom"]), (e + 1.1, volta)]
chaves.append((DUR + 1, chaves[-1][1]))

def expr_zoom(desloc):
    t = f"(it+{desloc:.3f})"
    partes = [f"{chaves[0][1]:.3f}"]
    for (t0, z0), (t1, z1) in zip(chaves, chaves[1:]):
        if abs(z1 - z0) < 1e-6: continue
        c = f"clip(({t}-{t0:.3f})/{t1 - t0:.3f},0,1)"
        partes.append(f"{z1 - z0:+.3f}*{c}*{c}*(3-2*{c})")
    z = "".join(partes)
    if div_out():  # na tela dividida o zoom fica em 1
        fora = "+".join(f"between({t},{a:.3f},{b:.3f})" for a, b in div_out())
        z = f"1+(({z})-1)*(1-min(1,{fora}))"
    return z

# ---------- título dos 3 primeiros segundos, no padrão da capa (PNG transparente) ----------
# Cartão menta com o selo verde espaçado e as linhas em preto (Inter 900), e a última linha
# em branco na tarja vermelha inclinada -2°, como nas capas da Linha Editorial.
def inter(peso, tam):
    f = ImageFont.truetype(str(FONTES / "Inter-Variable.ttf"), tam); f.set_variation_by_axes([peso, 0]); return f

def largura(dr, txt, f, esp, espaco=0):
    return sum(dr.textlength(c, font=f) for c in txt) + esp * (len(txt) - 1) + espaco * txt.count(" ")

def escreve(dr, x, y, txt, f, esp, cor, espaco=0):
    for c in txt:
        dr.text((x, y), c, font=f, fill=cor); x += dr.textlength(c, font=f) + esp + (espaco if c == " " else 0)

VERDE, MENTA, TINTA = (15, 92, 46, 255), (213, 236, 221, 248), (10, 23, 18, 255)
ALERTA, PAPEL = (179, 38, 26, 255), (255, 253, 246, 255)
def hexa(h, a=255): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
FUNDO = hexa(cfg["titulo_fundo"], 248) if "titulo_fundo" in cfg else MENTA  # cor de fundo da capa do Reel
COR_SELO = hexa(cfg["titulo_selo"]) if "titulo_selo" in cfg else VERDE
TT = cfg.get("titulo_tamanho", 78)
f_tag, f_tit = inter(800, round(TT * 0.40)), inter(900, TT)
esp_tag, esp_tit = TT * 0.40 * 0.22, TT * 0.01
ESP_PAL = TT * 0.16  # o Inter 900 tem espaço estreito: as palavras do título grudavam (R030)
linhas = [l.upper() for l in cfg["titulo"]]
pretas, vermelha = linhas[:-1], linhas[-1]
med = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
larg_cartao = max([largura(med, cfg["pilula"].upper(), f_tag, esp_tag)] +
                  [largura(med, l, f_tit, esp_tit, espaco=ESP_PAL) for l in pretas]) + 2 * round(TT * 0.6)
pad, passo = round(TT * 0.36), round(TT * 1.04)
alt_tag = round(TT * 0.40) + round(TT * 0.3)
alt_cartao = pad + alt_tag + passo * len(pretas) + round(TT * 0.95)

# tarja vermelha desenhada à parte e girada
lv = largura(med, vermelha, f_tit, esp_tit, espaco=ESP_PAL)
bx, bt, bb = round(TT * 0.38), round(TT * 0.18), round(TT * 0.22)
tarja = Image.new("RGBA", (round(lv + 2 * bx + 20), round(TT * 1.0 + bt + bb + 20)), (0, 0, 0, 0))
dt = ImageDraw.Draw(tarja)
dt.rounded_rectangle([10, 10, 10 + lv + 2 * bx, 10 + TT * 1.0 + bt + bb], radius=round(TT * 0.18), fill=ALERTA)
escreve(dt, 10 + bx, 10 + bt - round(TT * 0.06), vermelha, f_tit, esp_tit, PAPEL, espaco=ESP_PAL)
tarja = tarja.rotate(2, resample=Image.BICUBIC, expand=True)

alt_total = alt_cartao + tarja.height // 2
if HORIZONTAL:  # 16:9: o título vai onde o enquadramento deixar livre (titulo_x e titulo_y), longe das bordas
    y0 = max(60, min(cfg.get("titulo_y", 80), H - 60 - alt_total))
else:  # 9:16: entre y 300 (grid 4:5 e cabeçalho) e 1248 (zona segura do Reels)
    y0 = max(300, min(cfg.get("titulo_y", 900), 1240 - alt_total))
CX = cfg.get("titulo_x", W / 2)
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
x0 = CX - larg_cartao / 2
dr.rounded_rectangle([x0, y0, x0 + larg_cartao, y0 + alt_cartao], radius=round(TT * 0.3), fill=FUNDO)
y = y0 + pad
lt = largura(dr, cfg["pilula"].upper(), f_tag, esp_tag)
escreve(dr, CX - lt / 2, y, cfg["pilula"].upper(), f_tag, esp_tag, COR_SELO)
y += alt_tag
for l in pretas:
    w = largura(dr, l, f_tit, esp_tit, espaco=ESP_PAL)
    escreve(dr, CX - w / 2, y - round(TT * 0.1), l, f_tit, esp_tit, TINTA, espaco=ESP_PAL); y += passo
ov.alpha_composite(tarja, (round(CX - tarja.width / 2), round(y0 + alt_cartao - tarja.height / 2)))
ov.save(TRAB / "titulo.png")
if cfg.get("titulo_da_capa"):  # R030: o título dos 3 s é o mesmo bloco da capa (selo e quadro), tirado do _CAPA_*.html
    from telas import titulo_da_capa
    tc = cfg["titulo_da_capa"]
    titulo_da_capa(na_pasta(tc["html"]), TRAB / "titulo.png", tc.get("seletores", [".tag", ".quadro"]), tc.get("dy", 0))
print(f"título: y {y0} a {y0 + alt_total}")
if PALCO:
    import numpy as np
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - P_CARD_Y - 300) / H) ** 2)
    k = np.clip(dist / 0.75, 0, 1)[..., None]
    perto, longe = np.array(cfg.get("palco_cor_centro", (22, 62, 44))), np.array(cfg.get("palco_cor_borda", (8, 22, 16)))
    fundo = (perto * (1 - k) + longe * k).astype(np.uint8)
    mold = Image.fromarray(np.dstack([fundo, np.full((H, W), 255, np.uint8)]), "RGBA")
    dm = ImageDraw.Draw(mold)
    r = P_D // 2
    dm.ellipse([W / 2 - r - 9, P_CY - r - 9, W / 2 + r + 9, P_CY + r + 9], fill=(200, 164, 77, 255))  # borda dourada
    dm.ellipse([W / 2 - r, P_CY - r, W / 2 + r, P_CY + r], fill=(0, 0, 0, 0))  # o furo por onde o rosto aparece
    mold.save(TRAB / "palco_moldura.png")
    mk = np.full((P_TELA_ALT, W), 255, np.float32)  # bordas de cima e de baixo esfumadas (90 px)
    rampa = np.linspace(0, 255, 90, dtype=np.float32)[:, None]
    mk[:90] = rampa; mk[-90:] = rampa[::-1]
    Image.fromarray(mk.astype(np.uint8), "L").save(TRAB / "palco_tela_mascara.png")
    f_etq = inter(900, 44)
    for i, item in enumerate(cfg.get("cartoes", []) + cfg.get("contadores", [])):
        if not item.get("etiqueta"): continue
        txt = item["etiqueta"].upper(); le = largura(med, txt, f_etq, 1.5)
        et = Image.new("RGBA", (W, H), (0, 0, 0, 0)); de = ImageDraw.Draw(et)
        ye = P_CY + r - 34
        de.rounded_rectangle([W / 2 - le / 2 - 30, ye, W / 2 + le / 2 + 30, ye + 74], radius=14, fill=(200, 164, 77, 255))
        escreve(de, W / 2 - le / 2, ye + 9, txt, f_etq, 1.5, TINTA)
        et.save(TRAB / f"palco_etq_{i}.png")
    print(f"palco: cartão em y {P_CARD_Y}, círculo de {P_D} px centrado em y {P_CY}, legenda em y {P_LEG_Y}")
if cfg.get("tag_fixa"):  # tag que fica do fim do título até o fim do vídeo, no alto (acima dos cartões da tela dividida)
    f_fixa = inter(800, cfg.get("tag_tamanho", 27)); esp_fixa = cfg.get("tag_tamanho", 27) * 0.2
    txt_fixa = cfg["tag_fixa"].upper()
    lf = largura(med, txt_fixa, f_fixa, esp_fixa)
    alt_f, pad_f = round(cfg.get("tag_tamanho", 27) * 1.55), 26
    tg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(tg)
    yf = cfg.get("tag_y", 290)
    dg.rounded_rectangle([W / 2 - lf / 2 - pad_f, yf, W / 2 + lf / 2 + pad_f, yf + alt_f], radius=alt_f // 2, fill=FUNDO)
    escreve(dg, W / 2 - lf / 2, yf + (alt_f - cfg.get("tag_tamanho", 27) * 1.2) / 2, txt_fixa, f_fixa, esp_fixa, COR_SELO)
    tg.save(TRAB / "tag_fixa.png")
    print(f"tag fixa: y {yf} a {yf + alt_f}")

# ---------- legenda ASS ----------
def ts(t):
    t = max(t, 0); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
blocos, atual = [], []
for it in itens:
    atual.append(it)
    if re.search(r"[.,?!]$", it["t"]) or len(atual) >= 3 or sum(len(x["t"]) for x in atual) >= 15:
        blocos.append(atual); atual = []
if atual: blocos.append(atual)
limpa = lambda t: re.sub(r"(?<!\d)[.,]|[.,](?!\d)|[!?]", "", t).upper()  # tira pontuação, mas mantém 1.500 e 2,5

# janelas dos cartões de prova (calculadas antes, porque a legenda muda de lugar na tela dividida)
cartoes = cfg.get("cartoes", [])
tempos = []
for c in cartoes:
    s0, _ = acha(c["palavra"], tempos[-1][0] if tempos else 0)
    tempos.append([s0, s0 + c.get("dura", 3.0)])
for k in range(len(tempos) - 1):
    tempos[k][1] = min(tempos[k][1], tempos[k + 1][0])
# contadores (número que cresce): cartão animado na tela dividida, ancorado na palavra falada
# tipo "numero" (padrão), "troca" (preço que cai) ou "conta" (conta que monta), desenhados no animacoes.py;
# palavra_meio, palavra_troca e palavra_resultado marcam os passos da animação; "fim" ancora o fim numa palavra.
contadores = cfg.get("contadores", [])
tempos_cont = []
for c in contadores:
    s0, _ = acha(c["palavra"], tempos_cont[-1][0] if tempos_cont else 0)
    c["_marcas"] = {m: acha(c["palavra_" + m], s0)[0] - s0 for m in ("meio", "troca", "resultado", "marca", "preenche", "destaque", "desliza", "selo", "abre", "some") if c.get("palavra_" + m)}
    t1 = acha(c["fim"], s0)[1] + c.get("folga", 0.4) if c.get("fim") else s0 + c.get("dura", 3.0)
    tempos_cont.append([s0, t1])
# cartão que acaba a menos de 0,6 s do próximo fica até o próximo entrar (sem piscar o rosto cheio no meio)
TELA_CHEIA = [c.get("tipo") in ("distancia", "veredito") for c in contadores]  # efeito de tela cheia, por cima do vídeo
_seq = sorted(tempos + [tc for tc, cheia in zip(tempos_cont, TELA_CHEIA) if not cheia])
for a, b in zip(_seq, _seq[1:]):
    if b[0] - a[1] < 0.6: a[1] = b[0]
for c, (t0, t1) in zip(contadores, tempos_cont):
    c["dura"] = t1 - t0
DIVIDIDA = cfg.get("tela_dividida", True)
janelas = []  # cartões e contadores colados viram uma janela só de tela dividida
for t0, t1 in sorted(tempos + [tc for tc, cheia in zip(tempos_cont, TELA_CHEIA) if not cheia]):
    if janelas and t0 - janelas[-1][1] < 0.05: janelas[-1][1] = t1
    else: janelas.append([t0, t1])
na_divisao = lambda t: DIVIDIDA and any(j0 - 0.01 <= t < j1 for j0, j1 in janelas)

# cores da legenda: cada vídeo tem a sua cor de destaque; palavras-chave ficam coloridas o tempo todo
CORES = {"amarelo": "&H0000E6FF&", "verde": "&H0084DC3D&", "vermelho": "&H005A5AFF&", "laranja": "&H00248CFF&",
         "dourado": "&H005AC1E8&", "lilas": "&H00FFA8C8&", "rosa": "&H00B67AFF&", "ciano": "&H00E6E15C&"}  # cor em BGR
mudancas = sorted((acha(m["de"])[0], CORES[m["cor"]]) for m in cfg.get("cores_legenda", []))
COR_VIDEO = CORES[cfg.get("cor_legenda", "amarelo")]  # uma cor de destaque por vídeo, fixa do começo ao fim
def cor_em(t):
    cor = COR_VIDEO
    for t0, c in mudancas:
        if t >= t0 - 0.01: cor = c
    return cor
chave = set()
for frase in cfg.get("palavras_chave", []):
    s0, e0 = acha(frase)
    chave |= {id(it) for it in itens if s0 - 0.01 <= it["s"] <= e0}

CAIXA = cfg.get("legenda_estilo") == "caixa"
if CAIXA:
    from PIL import ImageFont as _IF
    from fontTools.ttLib import TTFont as _TT
    _os2 = _TT(str(FONTES / "Montserrat-ExtraBold.ttf"))["OS/2"]
    _EM = 62 * 1000 / (_os2.usWinAscent + _os2.usWinDescent)  # o libass mede o tamanho pela altura de linha do Windows
    _F_LEG = _IF.truetype(str(FONTES / "Montserrat-ExtraBold.ttf"), round(_EM))
    _larg = lambda s: _F_LEG.getlength(s) + len(s)  # Spacing 1 do estilo
    def _ret(x0, y0, x1, y1, r):  # retângulo de cantos redondos em desenho ASS
        return (f"m {x0 + r:.0f} {y0:.0f} l {x1 - r:.0f} {y0:.0f} b {x1:.0f} {y0:.0f} {x1:.0f} {y0:.0f} {x1:.0f} {y0 + r:.0f} "
                f"l {x1:.0f} {y1 - r:.0f} b {x1:.0f} {y1:.0f} {x1:.0f} {y1:.0f} {x1 - r:.0f} {y1:.0f} l {x0 + r:.0f} {y1:.0f} "
                f"b {x0:.0f} {y1:.0f} {x0:.0f} {y1:.0f} {x0:.0f} {y1 - r:.0f} l {x0:.0f} {y0 + r:.0f} b {x0:.0f} {y0:.0f} {x0:.0f} {y0:.0f} {x0 + r:.0f} {y0:.0f}")
    def caixa_eventos(bl, wi, chave, cor, a, b, yb):
        """yb = base do texto. Camada 0: caixa; 1: pílula da palavra dita; 2: texto."""
        pal = [limpa(x["t"]) for x in bl]
        esp = _larg(" ")
        tw = sum(_larg(p) for p in pal) + esp * (len(pal) - 1)
        x0 = W / 2 - tw / 2
        topo, base = yb - 50, yb - 14  # do topo da maiúscula até a linha de base
        out = [f"Dialogue: 0,{ts(a)},{ts(b)},Leg,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H12170A&\\1a&H26&}}"
               + _ret(x0 - 30, topo - 14, x0 + tw + 30, base + 14, 26) + "{\\p0}"]
        px = x0 + sum(_larg(p) + esp for p in pal[:wi])
        out.append(f"Dialogue: 1,{ts(a)},{ts(b)},Leg,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{cor}\\1a&H00&}}"
                   + _ret(px - 12, topo - 4, px + _larg(pal[wi]) + 12, base + 4, 16) + "{\\p0}")
        txt = []
        for k, (x, p_) in enumerate(zip(bl, pal)):
            if k == wi: txt.append(r"{\c&H12170A&}" + p_ + r"{\c&HFFFFFF&}")
            elif id(x) in chave: txt.append(r"{\c" + cor + "}" + p_ + r"{\c&HFFFFFF&}")
            else: txt.append(p_)
        out.append(f"Dialogue: 2,{ts(a)},{ts(b)},Leg,,0,0,0,,{{\\an1\\pos({x0:.0f},{yb})\\bord0\\shad0}}" + " ".join(txt))
        return out

BORDAS_DIV = sorted({x for j in janelas for x in j} | {x for j in div_out() for x in j}) if (janelas or CENAS_DIV) else []
ev = []
for bi, bl in enumerate(blocos):
    prox = blocos[bi + 1][0]["s"] if bi + 1 < len(blocos) else bl[-1]["e"] + 0.4
    cor = cor_em(bl[0]["s"])
    for wi, w in enumerate(bl):
        ini = w["s"] if wi else bl[0]["s"]
        fim = bl[wi + 1]["s"] if wi + 1 < len(bl) else (prox if prox - bl[-1]["e"] < 0.35 else bl[-1]["e"] + 0.15)
        partes_l = []
        for k, x in enumerate(bl):
            if k == wi:
                partes_l.append(r"{\c" + cor + r"\fscx108\fscy108}" + limpa(x["t"]) + r"{\c&HFFFFFF&\fscx100\fscy100}")
            elif id(x) in chave:
                partes_l.append(r"{\c" + cor + "}" + limpa(x["t"]) + r"{\c&HFFFFFF&}")
            else:
                partes_l.append(limpa(x["t"]))
        # a legenda troca de lugar no instante em que a tela dividida entra ou sai, mesmo no meio de um bloco
        # (no R028 o bloco que começava antes do cartão ficava embaixo, em cima do rosto)
        cortes_pos = [ini] + sorted(b for b in BORDAS_DIV if ini + 0.02 < b < fim - 0.02) + [fim]
        if CAIXA:  # legenda em caixa (R029): fundo verde-escuro arredondado e a palavra dita numa pílula da cor do vídeo
            for a_pos, b_pos in zip(cortes_pos, cortes_pos[1:]):
                if na_divisao(a_pos + 0.01): yb = 962 + 40
                elif na_cena_div(a_pos + 0.01) and not PALCO: yb = cfg.get("legenda_div_y", 1000 if HORIZONTAL else 1130)  # no palco a legenda fica sempre embaixo
                else: yb = H - (H - cfg.get("legenda_base_y", 1516))
                ev.extend(caixa_eventos(bl, wi, chave, cor, a_pos, b_pos, yb))
            continue
        for a_pos, b_pos in zip(cortes_pos, cortes_pos[1:]):
            if na_divisao(a_pos + 0.01) and PALCO: pos = r"{\an5\pos(540,%d)}" % P_LEG_Y  # palco: abaixo da etiqueta
            elif na_divisao(a_pos + 0.01): pos = r"{\an5\pos(540,962)}"  # tela dividida com cartão: legenda na linha da divisão
            elif na_cena_div(a_pos + 0.01): pos = r"{\an2\pos(%d,%d)}" % (W // 2, cfg.get("legenda_div_y", 1000 if HORIZONTAL else 1130))  # tela dividida do OBS
            else: pos = ""
            ev.append(f"Dialogue: 0,{ts(a_pos)},{ts(b_pos)},Leg,,0,0,0,,{pos}" + " ".join(partes_l))
leg_y = cfg.get("legenda_base_y", 1000 if HORIZONTAL else 1516)
(TRAB / "legenda.ass").write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,Montserrat ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,4,3,2,60,60,{H - leg_y},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n", encoding="utf-8")

def ts_srt(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
(TRAB / "legenda.srt").write_text("\n".join(
    f"{k}\n{ts_srt(bl[0]['s'] + 1 / FPS)} --> {ts_srt(bl[-1]['e'] + 1 / FPS)}\n{' '.join(limpa(x['t']) for x in bl)}\n"
    for k, bl in enumerate(blocos, 1)), encoding="utf-8")

# ---------- redução de respiração ----------
# Nos intervalos entre palavras o volume desce (padrão -12 dB) com rampas de 50 ms, sem encostar nas palavras.
# Em sala silenciosa nada cobre a respiração, e o compressor a traz para a frente (R024).
RESP_DB = cfg.get("respiracao_db", 0)  # o áudio D (IA) já abaixa a respiração; use -12 só se ainda aparecer
janelas_resp = []
if cfg.get("respiracao") == "voz":
    # microfone perto da boca (R030): a inspiração antes da frase passa pela IA (-30 a -45 dB) e aparece depois do ganho.
    # Respiração = trecho sem tom de voz (autocorrelação baixa), fora das palavras, com pico abaixo de -28 dB e 80 ms ou mais.
    import wave
    import numpy as np
    RESP_DB = RESP_DB or -20
    fonte = TRAB / "audio_d.wav"
    if fonte.exists():  # o áudio já limpo pela IA (de uma render anterior) mostra só o que sobrou
        _raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(fonte), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                              capture_output=True).stdout
    else:
        _w = wave.open(cfg["audio16k"]); _raw = _w.readframes(_w.getnframes())
    amostras = np.frombuffer(_raw, np.int16).astype(float) / 32768
    dentro = lambda t: any(w["s"] + 0.03 <= t <= w["e"] - 0.03 for w in palavras)
    trecho = []
    for i in range(int(INICIO * 16000), min(len(amostras), int(FIM * 16000)) - 480, 160):
        q = amostras[i:i + 480]; t = i / 16000 + 0.015
        db = 20 * np.log10(np.sqrt((q ** 2).mean()) + 1e-9)
        ac = np.correlate(q, q, "full")[479:]; ac = ac / (ac[0] + 1e-12)
        if -55 < db < -10 and ac[40:320].max() < 0.5 and not dentro(t):
            trecho.append((t, db)); continue
        if len(trecho) >= 8 and max(d for _, d in trecho) < -28:
            janelas_resp.append((trecho[0][0] - 0.03, trecho[-1][0] + 0.03))
        trecho = []
elif RESP_DB < 0:
    import wave
    import numpy as np
    wf = wave.open(cfg["audio16k"])
    amostras = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(float) / 32768
    def nivel(t):  # dB de um trecho de 10 ms
        q = amostras[int(t * 16000):int(t * 16000) + 160]
        return 20 * np.log10(np.sqrt((q ** 2).mean()) + 1e-9) if len(q) else -99
    FALA_DB = -24  # acima disso é fala, nunca abaixa
    tempos_pal = [ajusta(w) for w in palavras]
    for (s1, e1), (s2, e2) in zip(tempos_pal, tempos_pal[1:]):
        a0, b0 = e1 + 0.08, s2 - 0.06
        while a0 < b0 and nivel(a0 - 0.03) > FALA_DB: a0 += 0.01  # o Whisper às vezes encurta a palavra
        while b0 > a0 and nivel(b0 + 0.02) > FALA_DB: b0 -= 0.01
        if b0 - a0 >= 0.12 and max(nivel(t) for t in np.arange(a0, b0, 0.01)) <= FALA_DB:
            janelas_resp.append((a0, b0))
def expr_resp():
    g = 10 ** (RESP_DB / 20)
    termos = "+".join(f"clip((t-{a0:.3f})/0.05,0,1)*clip(({b0:.3f}-t)/0.05,0,1)" for a0, b0 in janelas_resp)
    return f"1-{1 - g:.4f}*({termos})" if termos else "1"
print(f"respiração: {len(janelas_resp)} intervalos abaixados em {RESP_DB} dB")

# ---------- cor (padrão C: balanço de branco e exposição pelo rosto + acabamento Instagram) ----------
FILTRO_COR = ""
if cfg.get("cor", "C") != "nenhuma":
    sys.path.insert(0, str(FERR))
    from cor import filtro_cor
    quadros = []
    rosto_jan, cur_r = [], INICIO  # trechos só de rosto (a tela creme da aula não pode virar referência de branco)
    for a, b in sorted(CENAS_DIV):
        if a > cur_r: rosto_jan.append((cur_r, min(a, FIM)))
        cur_r = max(cur_r, b)
    if cur_r < FIM: rosto_jan.append((cur_r, FIM))
    tot = sum(b - a for a, b in rosto_jan)
    def tempo_rosto(frac):
        alvo = frac * tot
        for a, b in rosto_jan:
            if alvo <= b - a: return a + alvo
            alvo -= b - a
        return rosto_jan[-1][1] - 1
    for k, frac in enumerate((0.2, 0.4, 0.6, 0.8)):
        q = TRAB / f"cor_{k}.png"
        t = tempo_rosto(frac)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", cfg["bruto"], "-frames:v", "1",
                        "-vf", f"{PRE}scale={W}:{H}", str(q)], check=True)
        quadros.append(str(q))
    cx, cy = FX * W, FY * H
    rosto_caixa = tuple(int(v) for v in cfg.get("rosto_caixa", (cx - 70, cy - 200, cx + 70, cy - 20)))
    FILTRO_COR, info_cor = filtro_cor(quadros, rosto_caixa, acabamento=cfg.get("cor", "C") == "C",
                                      esfriar=cfg.get("cor_esfriar", 0.0),
                                      exposicao=cfg.get("cor_exposicao", not cfg.get("cenas_obs")))
    FILTRO_COR = "," + FILTRO_COR
    print("cor:", {k: (v if v is None or isinstance(v, list) else float(v)) for k, v in info_cor.items()})

# ---------- filtro ----------
p = []
def sondar(arq):
    st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                    "-of", "json", arq], capture_output=True, text=True).stdout)["streams"][0]
    return st["width"], st["height"]
CAM2 = na_pasta(cfg["camera_bruto"]) if PALCO and cfg.get("camera_bruto") else None
# câmera da cena "tela" da aula: vertical, metade de baixo (1080 × 960) com o plano aberto;
# horizontal, quadradinho no canto inferior direito, fora da zona útil da tela (x 385 a 1535)
CANTO = cfg.get("camera_canto", [360, 296])
CANTO_XY = (W - 24 - CANTO[0], H - 24 - CANTO[1])
if AULA:
    if HORIZONTAL:
        CAM_W, CAM_H = CANTO
        cx_, cy_, cw_, ch_ = regiao(CAM_W / CAM_H, cfg.get("camera_altura", 0.75), cfg.get("camera_rosto_y", 0.42))  # canto pequeno: um pouco mais perto
    else:
        CAM_W, CAM_H = 1080, 960
        cx_, cy_, cw_, ch_ = regiao(CAM_W / CAM_H, cfg.get("camera_altura", 1.0), cfg.get("camera_rosto_y", 0.40))  # rosto alto no bruto: subir (R029, 0,6)
        if PALCO:  # aula no palco: o rosto num círculo embaixo da tela, com folga em volta da cabeça
            CAM_W = CAM_H = P_D
            cx_, cy_, cw_, ch_ = regiao(1.0, cfg.get("palco_lado", 1000) / BH, cfg.get("camera_rosto_y", 0.55))
            if CAM2:  # câmera do círculo vinda do bruto horizontal (plano aberto): o vertical do OBS é um recorte
                # ampliado do rosto e a cabeça não cabia inteira no círculo (R029 v3)
                c2w, c2h = sondar(CAM2)
                lado2 = min(cfg.get("camera_lado", 700), c2h)
                rx, ry = cfg.get("camera_rosto", [0.5, 0.45])
                cx_ = int(min(max(rx * c2w - lado2 / 2, 0), c2w - lado2)) // 2 * 2
                cy_ = int(min(max(ry * c2h - cfg.get("camera_rosto_y", 0.5) * lado2, 0), c2h - lado2)) // 2 * 2
                cw_ = ch_ = int(lado2) // 2 * 2
    CAM = f"crop={cw_}:{ch_}:{cx_}:{cy_},scale={CAM_W}:{CAM_H}"
for i, ((a, b), o) in enumerate(zip(trechos, offs)):
    corte = f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps={FPS}"
    if AULA and CAM2:
        d2 = cfg.get("camera_desloc", 0.0)
        p.append(f"[c2_{i}]trim={a + d2:.3f}:{b + d2:.3f},setpts=PTS-STARTPTS,fps={FPS},{CAM}{FILTRO_COR},setsar=1,format=yuv420p[k{i}]")
        corte += ","
    elif AULA:
        p.append(f"{corte},split[r{i}][q{i}]"); corte = f"[r{i}]"
        p.append(f"[q{i}]{CAM}{FILTRO_COR},setsar=1,format=yuv420p[k{i}]")
    else:
        corte += ","
    p.append(f"{corte}{PRE}zoompan=z='{expr_zoom(o)}':x='{FX}*(iw-iw/zoom)':y='{FY}*(ih-ih/zoom)':d=1:s={W}x{H}:fps={FPS}{FILTRO_COR},"
             f"setsar=1,format=yuv420p[v{i}]")
    p.append(f"[1:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}]")
uv, ua, uk = "[v0]", "[a0]", "[k0]"
for i in range(1, len(trechos)):
    p.append(f"{uv}[v{i}]xfade=transition=fade:duration={D}:offset={offs[i]:.3f}[xv{i}]")
    p.append(f"{ua}[a{i}]acrossfade=d={D}:c1=tri:c2=tri[xa{i}]")
    uv, ua = f"[xv{i}]", f"[xa{i}]"
    if AULA:
        p.append(f"{uk}[k{i}]xfade=transition=fade:duration={D}:offset={offs[i]:.3f}[xk{i}]")
        uk = f"[xk{i}]"
cartoes = cfg.get("cartoes", [])
if AULA:
    from telas import tem_motion as _tm
    tem_motion_tela = _tm(na_pasta(cfg["tela_html"]))
    # a trilha das telas (tela_trilha.mp4, um PNG por clique com dissolvência) entra só nas janelas de tela
    it = 4 + len(cartoes)
    p.append(f"[{it}:v]setsar=1,format=yuv420p[tl]")
    if HORIZONTAL:
        p.append(f"[{it + 1}:v]format=gray,scale={CAM_W}:{CAM_H}[msk]")
        p.append(f"{uk}format=yuva420p[k_a];[k_a][msk]alphamerge[k_m]")
        if tem_motion_tela:
            p.append(f"movie=camera_anel.png:loop=0,setpts=N/({FPS}*TB),format=rgba[anel]")
            p.append("[tl][anel]overlay=0:0:shortest=1[tla]")
            p.append(f"[tla][k_m]overlay={CANTO_XY[0]}:{CANTO_XY[1]}:eof_action=pass[comp]")
        else:
            p.append(f"[tl][k_m]overlay={CANTO_XY[0]}:{CANTO_XY[1]}:eof_action=pass[comp]")
    else:
        if PALCO:  # fundo da marca com o furo do círculo, o rosto por trás do furo e a tela animada por cima, de bordas esfumadas
            p.append(f"{uk}pad=1080:1920:{(1080 - P_D) // 2}:{P_CY - P_D // 2}:color=0x0A1712[pf]")
            p.append(f"movie=palco_moldura.png:loop=0,setpts=N/({FPS}*TB),format=rgba[pmold]")
            p.append("[pf][pmold]overlay=0:0:shortest=1[pb]")
            p.append(f"movie=palco_tela_mascara.png:loop=0,setpts=N/({FPS}*TB),format=gray[pmk]")
            p.append("[tl]format=yuva420p[tla];[tla][pmk]alphamerge[tlm]")
            p.append(f"[pb][tlm]overlay=0:{P_CARD_Y}:eof_action=pass,format=yuv420p[comp]")
        else:
            p.append(f"[tl]{uk}vstack[comp]")
    jt = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in TELA_JAN)
    p.append(f"{uv}[comp]overlay=0:0:eof_action=pass:enable='{jt}'[va]")
    uv = "[va]"
ta = cfg.get("titulo_ate", 3.0)
_ent = "" if cfg.get("titulo_sem_entrada") else "fade=t=in:st=0:d=0.2:alpha=1,"  # capa com o mesmo título: sem piscar no início
p.append(f"[2:v]format=rgba,{_ent}fade=t=out:st={ta - 0.3}:d=0.3:alpha=1[tit]")
ult = "[vt]"
p.append(f"{uv}[tit]overlay=0:0:eof_action=pass[vt]")
FUNDO_DIV = cfg.get("fundo_divisao", "0x0A1712")
if FUNDO_DIV == "vidro": FUNDO_DIV = "0x0A1712"  # o vidro é desenhado por cima; o pad usa o verde-escuro
IDX_CONT = 4 + len(cartoes) + (1 + (1 if HORIZONTAL else 0) if AULA else 0)  # entradas dos contadores no ffmpeg
VT = "[vt]"  # efeitos de tela cheia (a distância do A52) vão por cima do vídeo inteiro, antes da tela dividida
for k, (c, (t0, t1)) in enumerate(zip(contadores, tempos_cont)):
    if TELA_CHEIA[k]:
        p.append(f"[{IDX_CONT + k}:v]format=rgba,setpts=PTS-STARTPTS+{t0:.3f}/TB[n{k}]")
        p.append(f"{VT}[n{k}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[vtc{k}]")
        VT = f"[vtc{k}]"
        print(f"efeito de tela cheia {k + 1} ({c.get('tipo')}): {t0:.2f}s a {t1:.2f}s")
if DIVIDIDA and (cartoes or any(not x for x in TELA_CHEIA)):
    # tela dividida: notícia na metade de cima, vídeo deslocado para baixo com o rosto inteiro
    VIDRO = cfg.get("fundo_divisao") == "vidro" and not PALCO  # metade de cima: o próprio vídeo desfocado com véu verde-escuro
    p.append(f"{VT}split=3[vfull][vdiv][vgl]" if VIDRO else f"{VT}split[vfull][vdiv]")
    DIV_ALT = int(cfg.get("div_altura", 960))
    if PALCO:
        lado = int(cfg.get("palco_lado", 760))
        px0 = int(min(max(FX * 1080 - lado / 2, 0), 1080 - lado))
        py0 = int(min(max(FY * 1920 - 0.42 * lado, 0), 1920 - lado))
        p.append(f"[vdiv]crop={lado}:{lado}:{px0}:{py0},scale={P_D}:{P_D},"
                 f"pad=1080:1920:{(1080 - P_D) // 2}:{P_CY - P_D // 2}:color=0x0A1712[vrost]")
        p.append(f"movie=palco_moldura.png:loop=0,setpts=N/({FPS}*TB),format=rgba[pmold]")
        p.append("[vrost][pmold]overlay=0:0:shortest=1[vbase0]")
    elif DIV_ALT <= 960:
        corte_y = int(cfg.get("div_topo", min(max(FY * 1920 - 0.3 * 960, 0), 960)))
        p.append(f"[vdiv]crop=1080:960:0:{corte_y},pad=1080:1920:0:960:color={FUNDO_DIV}[vbase0]")
    else:
        # rosto muito de perto (R028): a câmera da tela dividida mostra um pedaço maior do quadro, reduzido
        # para caber na metade de baixo, com o mesmo trecho desfocado preenchendo as laterais
        corte_y = int(cfg.get("div_topo", min(max(FY * 1920 - 0.42 * DIV_ALT, 0), 1920 - DIV_ALT)))
        larg_red = int(round(1080 * 960 / DIV_ALT / 2) * 2)
        p.append(f"[vdiv]crop=1080:{DIV_ALT}:0:{corte_y},split[dv1][dv2]")
        p.append(f"[dv1]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,boxblur=24:2,eq=brightness=-0.08[dvfundo]")
        p.append(f"[dv2]scale={larg_red}:960[dvrosto]")
        p.append(f"[dvfundo][dvrosto]overlay=x={(1080 - larg_red) // 2}:y=0,pad=1080:1920:0:960:color={FUNDO_DIV}[vbase0]")
    if VIDRO:
        p.append("[vgl]crop=1080:960:0:0,scale=216:192,boxblur=6:2,scale=1080:960,eq=brightness=-0.10:saturation=0.75,"
                 "drawbox=x=0:y=0:w=1080:h=960:color=0x0A1712@0.50:t=fill,"
                 "drawbox=x=0:y=900:w=1080:h=60:color=0x0A1712@0.35:t=fill[vglass]")
        p.append("[vbase0][vglass]overlay=0:0[vbase]")
    else:
        p.append("[vbase0]null[vbase]")
    ult = "[vbase]"
    for k, (c, (t0, t1)) in enumerate(zip(cartoes, tempos)):
        larg = c.get("largura", 1000)
        if PALCO: larg = P_CARD_W
        p.append(f"[{4 + k}:v]format=rgba,scale={larg}:-1[c{k}]")
        y_c = f"{P_CARD_Y}+({round(P_CARD_W * 0.58)}-h)/2" if PALCO else "300+(640-h)/2"
        p.append(f"{ult}[c{k}]overlay=x={(1080 - larg) // 2}:y='{y_c}':shortest=1:enable='between(t,{t0:.3f},{t1:.3f})'[vc{k}]")
        ult = f"[vc{k}]"
        print(f"cartão {k + 1}: {t0:.2f}s a {t1:.2f}s  ({Path(c['arquivo']).name})")
    for k, (c, (t0, t1)) in enumerate(zip(contadores, tempos_cont)):
        if TELA_CHEIA[k]: continue
        esc = f",scale={P_CARD_W}:-1" if PALCO else ""
        p.append(f"[{IDX_CONT + k}:v]format=rgba{esc},setpts=PTS-STARTPTS+{t0:.3f}/TB[n{k}]")
        x_n, y_n = (f"{(1080 - P_CARD_W) // 2}", f"{P_CARD_Y}+({round(P_CARD_W * 0.58)}-h)/2") if PALCO else ("40", "300+(640-h)/2")
        p.append(f"{ult}[n{k}]overlay=x={x_n}:y='{y_n}':eof_action=repeat:enable='between(t,{t0:.3f},{t1:.3f})'[vn{k}]")
        ult = f"[vn{k}]"
        print(f"contador {k + 1} ({c.get('tipo', 'numero')}): {t0:.2f}s a {t1:.2f}s  ({c.get('rotulo', '')})")
    if PALCO:
        itens_p = list(zip(cartoes, tempos)) + list(zip(contadores, tempos_cont))
        for i, (c, (t0, t1)) in enumerate(itens_p):
            if not c.get("etiqueta") or (i >= len(cartoes) and TELA_CHEIA[i - len(cartoes)]): continue
            p.append(f"movie=palco_etq_{i}.png:loop=0,setpts=N/({FPS}*TB),format=rgba[pe{i}]")
            p.append(f"{ult}[pe{i}]overlay=0:0:shortest=1:enable='between(t,{t0:.3f},{t1:.3f})'[vpe{i}]")
            ult = f"[vpe{i}]"
    cond = "+".join(f"between(t,{j0:.3f},{j1:.3f})" for j0, j1 in janelas)
    p.append(f"[vfull]{ult}overlay=0:0:shortest=1:enable='{cond}'[vsplit]")
    ult = "[vsplit]"
else:
    ult = VT
    for k, (c, (t0, t1)) in enumerate(zip(cartoes, tempos)):
        seco_antes = k > 0 and abs(tempos[k - 1][1] - t0) < 0.05
        seco_depois = k + 1 < len(tempos) and abs(tempos[k + 1][0] - t1) < 0.05
        fades = ("" if seco_antes else f",fade=t=in:st={t0:.3f}:d=0.2:alpha=1") + \
                ("" if seco_depois else f",fade=t=out:st={t1 - 0.2:.3f}:d=0.2:alpha=1")
        larg = c.get("largura", 1000)
        p.append(f"[{4 + k}:v]format=rgba,scale={larg}:-1{fades}[c{k}]")
        p.append(f"{ult}[c{k}]overlay=x={(1080 - larg) // 2}:y={c.get('y', 500)}:shortest=1:enable='between(t,{t0:.3f},{t1:.3f})'[vc{k}]")
        ult = f"[vc{k}]"
        print(f"cartão {k + 1}: {t0:.2f}s a {t1:.2f}s  ({Path(c['arquivo']).name})")
    for k, (c, (t0, t1)) in enumerate(zip(contadores, tempos_cont)):
        if TELA_CHEIA[k]: continue
        p.append(f"[{IDX_CONT + k}:v]format=rgba,setpts=PTS-STARTPTS+{t0:.3f}/TB[n{k}]")
        p.append(f"{ult}[n{k}]overlay=x=40:y={c.get('y', 500)}:eof_action=repeat:enable='between(t,{t0:.3f},{t1:.3f})'[vn{k}]")
        ult = f"[vn{k}]"
if cfg.get("tag_fixa"):
    _ta = cfg.get("titulo_ate", 3.0)
    p.append(f"movie=tag_fixa.png:loop=0,setpts=N/({FPS}*TB),format=rgba,fade=t=in:st={_ta:.2f}:d=0.3:alpha=1[tagf]")
    p.append(f"{ult}[tagf]overlay=0:0:shortest=1:enable='gte(t,{_ta:.2f})'[vtag]")
    ult = "[vtag]"
p.append(f"{ult}subtitles=legenda.ass:fontsdir='{FONTES.as_posix().replace(':', '\\:')}'[vm]")
p.append(f"[3:v]scale={W}:{H},setsar=1,fps={FPS},format=yuv420p,trim=end_frame=1,setpts=PTS-STARTPTS[cv]")
p.append(f"anullsrc=r=48000:cl=mono,atrim=end={1 / FPS:.4f}[sil]")
p.append(f"{ua}afade=t=out:st={DUR - 0.6:.3f}:d=0.6[afim]")
if cfg.get("capa"):
    p.append(f"[cv][sil][vm][afim]concat=n=2:v=1:a=1[vout][aout]")
else:  # anúncio: o primeiro quadro é o gancho, não a capa (a miniatura do anúncio se escolhe na Meta)
    p.append("[cv]nullsink"); p.append("[sil]anullsink"); p.append("[vm]null[vout]"); p.append("[afim]anull[aout]")
if CAM2:  # o bruto horizontal entra como a última entrada do ffmpeg (ver o render)
    i_cam2 = 4 + len(cartoes) + 1 + len(contadores)
    p.insert(0, f"[{i_cam2}:v]split={len(trechos)}" + "".join(f"[c2_{i}]" for i in range(len(trechos))))
(TRAB / "filtro.txt").write_text(";\n".join(p), encoding="utf-8")

print(f"{len(trechos)} trechos ({len(trechos) - 1} cortes), duração {DUR + 1 / FPS:.2f}s")
for (a, b), o in zip(trechos, offs):
    print(f"  {a:6.2f}-{b:6.2f} -> {o:6.2f}  " + " ".join(w["w"] for w in palavras if a - 0.05 <= ajusta(w)[0] < b)[:70])
print("zoom:", ", ".join(f"{t:.2f}={z:.2f}" for t, z in chaves))
# plano salvo para o conferir.py escolher os quadros de conferência (tempos já no vídeo final, sem o quadro da capa)
json.dump({"duracao": DUR + 1 / FPS, "fps": FPS, "titulo_ate": cfg.get("titulo_ate", 3.0), "zoom": chaves[:-1],
           "cartoes": sorted(tempos + tempos_cont), "cortes": offs[1:], "saida": cfg["saida"], "formato": "16:9" if HORIZONTAL else "9:16",
           "telas": TELA_JAN, "cliques": CLIQUES, "falas": [[i["t"], round(i["s"], 3)] for i in itens]},
          open(TRAB / "plano.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- trilha das telas (aula gravada só com a câmera) ----------
def trilha_telas():
    """Exporta as telas do HTML (um PNG por clique) e monta tela_trilha.mp4 com a duração do vídeo final:
    cada clique entra na sua palavra com dissolvência de 0,3 s, como a transição da própria tela."""
    from telas import exportar, total_cliques, tem_motion
    html_tela = Path(na_pasta(cfg["tela_html"]))
    if tem_motion(html_tela):
        return trilha_motion(html_tela)
    pasta = TRAB / "telas"
    total = exportar(html_tela, pasta)
    marcas = [list(c) for c in CLIQUES] or [[0.0, 1]]
    falta = [n for _, n in marcas if not 1 <= n <= total]
    if falta:
        raise SystemExit(f"A tela tem {total} cliques; o roteiro pede {falta}.")
    marcas[0][0] = 0.0  # antes do primeiro clique a tela já mostra o primeiro
    XF = 0.3
    for k in range(1, len(marcas)):  # cliques colados: dá tempo da dissolvência
        marcas[k][0] = max(marcas[k][0], marcas[k - 1][0] + XF + 0.05)
    imgs = []
    for _, n in marcas:
        if HORIZONTAL:  # moldura atrás da câmera do canto, desenhada na própria tela
            im = Image.open(pasta / f"tela_{n:02d}.png").convert("RGBA")
            dr = ImageDraw.Draw(im)
            x, y = CANTO_XY
            dr.rounded_rectangle([x - 6, y - 6, x + CANTO[0] + 5, y + CANTO[1] + 5], radius=26, fill=(15, 92, 46, 255))
            arq = TRAB / f"tela_h_{n:02d}.png"; im.convert("RGB").save(arq); imgs.append(arq)
        else:
            imgs.append(pasta / f"tela_v_{n:02d}.png")
    if HORIZONTAL:
        msk = Image.new("L", tuple(CANTO), 0)
        ImageDraw.Draw(msk).rounded_rectangle([0, 0, CANTO[0] - 1, CANTO[1] - 1], radius=20, fill=255)
        msk.save(TRAB / "camera_mascara.png")
    fim = DUR + 1
    cmd, f = ["ffmpeg", "-v", "error", "-y"], []
    for k, ((t0, _), arq) in enumerate(zip(marcas, imgs)):
        t1 = marcas[k + 1][0] if k + 1 < len(marcas) else fim
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{t1 - t0 + XF:.3f}", "-i", str(arq)]
        f.append(f"[{k}:v]setsar=1,format=yuv420p[i{k}]")
    ult = "[i0]"
    for k in range(1, len(marcas)):
        f.append(f"{ult}[i{k}]xfade=transition=fade:duration={XF}:offset={marcas[k][0]:.3f}[x{k}]"); ult = f"[x{k}]"
    (TRAB / "filtro_telas.txt").write_text(";\n".join(f) + f";\n{ult}trim=duration={fim:.3f}[out]", encoding="utf-8")
    saida = TRAB / "tela_trilha.mp4"
    subprocess.run(cmd + ["-filter_complex_script", str(TRAB / "filtro_telas.txt"), "-map", "[out]", "-r", str(FPS),
                          "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", str(saida)], check=True)
    print(f"trilha das telas: {len(marcas)} cliques, {fim:.1f}s")
    return saida

def trilha_motion(html_tela):
    """Tela animada (cena(p, t, T) no HTML, R029): grava cada clique quadro a quadro enquanto a tela está visível
    e segura o último quadro até o próximo clique. Sem dissolvência: as transições moram na própria tela."""
    from telas import gravar_motion
    marcas = [list(c) for c in CLIQUES] or [[0.0, 1]]
    lead = marcas[0][0]  # antes do primeiro clique a tela não aparece: segura o primeiro quadro (no R029 v1 a
    # animação do clique 1 rodava no tempo 0 e a tela entrava travada no R$ 0,00)
    fim = DUR + 1
    segs = []
    for k, (t0, n) in enumerate(marcas):
        t1 = marcas[k + 1][0] if k + 1 < len(marcas) else fim
        visivel = max((b for a, b in TELA_JAN if a <= t0 + 0.6 and b > t0), default=t0 + 0.1)  # até onde a tela aparece
        segs.append((n, t0, max(0.1, min(t1, visivel + 0.3) - t0), t1 - t0))
    pasta = TRAB / "motion"
    print(f"motion: gravando {sum(s[2] for s in segs):.0f} s de tela animada ({len(segs)} cliques)")
    if HORIZONTAL:  # câmera do canto num círculo com anel dourado, como o palco do vertical (R029)
        x, y = CANTO_XY; anel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(anel).ellipse([x - 8, y - 8, x + CANTO[0] + 7, y + CANTO[1] + 7], fill=(226, 190, 98, 255))
        anel.save(TRAB / "camera_anel.png")
        msk = Image.new("L", tuple(CANTO), 0)
        ImageDraw.Draw(msk).ellipse([0, 0, CANTO[0] - 1, CANTO[1] - 1], fill=255)
        msk.save(TRAB / "camera_mascara.png")
    gravar_motion(html_tela, pasta, [s[:3] for s in segs], FPS, vertical=not HORIZONTAL, falas=[[i["t"], i["s"]] for i in itens], cliques=CLIQUES)
    cmd, f = ["ffmpeg", "-v", "error", "-y"], []
    for k, (_, _, grav, total) in enumerate(segs):
        cmd += ["-framerate", str(FPS), "-i", str(pasta / f"seg_{k:02d}" / "q_%04d.jpg")]
        ant = f"tpad=start_mode=clone:start_duration={lead:.3f}," if k == 0 and lead > 0 else ""
        total += lead if k == 0 else 0
        esc = (f"crop=iw:ih*{P_TELA_ALT / 960:.4f}:0:ih*{(1 - P_TELA_ALT / 960) / 2:.4f},scale=1080:{P_TELA_ALT}" if PALCO
               else "scale=1920:1080" if HORIZONTAL else "scale=1080:960")
        f.append(f"[{k}:v]{esc},setsar=1,format=yuv420p,{ant}tpad=stop_mode=clone:stop_duration={max(total - grav, 0) + 1:.3f},"
                 f"trim=duration={total:.3f},setpts=PTS-STARTPTS[s{k}]")
    f.append("".join(f"[s{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1[out]")
    (TRAB / "filtro_telas.txt").write_text(";\n".join(f), encoding="utf-8")
    saida = TRAB / "tela_trilha.mp4"
    subprocess.run(cmd + ["-filter_complex_script", str(TRAB / "filtro_telas.txt"), "-map", "[out]", "-r", str(FPS),
                          "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", str(saida)], check=True)
    print(f"trilha das telas (motion): {len(segs)} cliques, {fim:.1f}s")
    return saida

# ---------- contador: número que cresce (cartão animado, 1000 × 580 com fundo transparente) ----------
def numero_br(v, casas):
    t = f"{v:,.{casas}f}"
    return t.replace(",", "X").replace(".", ",").replace("X", ".")

def quadros_contador(k, c):
    """Grava um PNG por quadro: o número sobe do 'de' ao 'ate' com desaceleração, pulsa no fim e o detalhe aparece."""
    pasta = TRAB / f"contador_{k}"; pasta.mkdir(exist_ok=True)
    for velho in pasta.glob("*.png"): velho.unlink()
    tipo = c.get("tipo", "numero")
    if tipo != "numero":  # preço que cai e conta que monta
        import animacoes
        if tipo == "troca": animacoes.quadros_troca(pasta, c, c.get("_marcas", {}), FPS, FONTES)
        elif tipo in ("destaque", "grade", "regua", "distancia", "rosca", "placar", "veredito"):  # efeitos de 21/10 (A52), placar e veredito (R033)
            import animacoes2
            import inspect
            fn = getattr(animacoes2, "quadros_" + tipo)
            args = [pasta, c, c.get("_marcas", {}), FPS, FONTES]
            if len(inspect.signature(fn).parameters) > 5: args.append(numero_br)  # só a grade e a régua usam
            fn(*args)
        else: animacoes.quadros_conta(pasta, c, c.get("_marcas", {}), FPS, FONTES, numero_br)
        print(f"contador {k + 1} ({tipo}): {int(round(c['dura'] * FPS))} quadros")
        return pasta
    dura, subida = c.get("dura", 3.0), c.get("subida", 1.4)
    de, ate, casas = c.get("de", 0), c["ate"], c.get("casas", 0)
    pre, suf = c.get("prefixo", ""), c.get("sufixo", "")
    cor_num = {"verde": (15, 92, 46, 255), "vermelho": (179, 38, 26, 255), "tinta": (10, 23, 18, 255)}[c.get("cor", "verde")]
    mont = lambda nome, tam: ImageFont.truetype(str(FONTES / nome), tam)
    f_rot, f_det = mont("Montserrat-ExtraBold.ttf", 32), mont("Montserrat-Bold.ttf", 32)
    final = c.get("texto_final") or pre + numero_br(ate, casas) + suf  # texto_final: como o número para (ex.: R$ 4 BILHÕES)
    tam = 180  # o número final tem que caber em 860 px; o tamanho fica fixo durante a contagem
    while tam > 80 and ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(final, font=mont("Montserrat-Black.ttf", tam)) > 860:
        tam -= 4
    for q in range(int(round(dura * FPS))):
        t = q / FPS
        pr = min(t / subida, 1.0); e = 1 - (1 - pr) ** 3
        v = ate if pr >= 1 else de + (ate - de) * e
        pulso = 1.0
        if 0 <= t - subida < 0.3: pulso = 1 + 0.06 * (1 - abs((t - subida) / 0.15 - 1))  # pulso de 0,3 s no fim
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        dr.rounded_rectangle([25, 22, 975, 542], radius=30, fill=(255, 255, 255, 255))
        if c.get("rotulo"):
            rot = c["rotulo"].upper(); esp = 4.5
            lw = sum(dr.textlength(ch, font=f_rot) for ch in rot) + esp * (len(rot) - 1); x = 500 - lw / 2
            for ch in rot:
                dr.text((x, 70), ch, font=f_rot, fill=(15, 92, 46, 255)); x += dr.textlength(ch, font=f_rot) + esp
        f_num = mont("Montserrat-Black.ttf", round(tam * pulso))
        txt = final if pr >= 1 else pre + numero_br(v, casas) + suf
        dr.text((500, 262), txt, font=f_num, fill=cor_num, anchor="mm")
        largura_barra = 640 * e  # barra de progresso embaixo do número
        dr.rounded_rectangle([180, 372, 820, 384], radius=6, fill=(228, 240, 231, 255))
        if largura_barra > 12:
            dr.rounded_rectangle([180, 372, 180 + largura_barra, 384], radius=6, fill=(200, 164, 77, 255))
        if c.get("detalhe") and t > subida:
            a = int(255 * min((t - subida) / 0.3, 1.0))
            dr.text((500, 450), c["detalhe"], font=f_det, fill=(91, 102, 96, a), anchor="mm")
        im.save(pasta / f"{q:04d}.png")
    print(f"contador {k + 1}: {int(round(dura * FPS))} quadros, {final}")
    return pasta

# ---------- render ----------
if "--render" in sys.argv:
    import time
    t_ini = time.time()
    if cfg.get("audio_limpo"):
        audio_base = cfg["audio_limpo"]
    else:  # padrão D, igual ao CapCut: reduzir ruído + aprimorar voz (75%); a normalização a -14 LUFS vem no fim
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cfg["bruto"], "-vn", "-ac", "1", "-ar", "48000",
                        "-c:a", "pcm_s16le", "audio_bruto.wav"], cwd=TRAB, check=True)
        (TRAB / "df").mkdir(exist_ok=True)
        subprocess.run([deep_filter(), "-D", "-o", "df", "audio_bruto.wav"], cwd=TRAB, check=True,
                       capture_output=True)
        subprocess.run(ambiente()["voz"] + [str(FERR / "aprimorar_voz.py"), "df/audio_bruto.wav", "audio_ia.wav",
                        str(cfg.get("aprimorar_voz", 75))], cwd=TRAB, check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "audio_ia.wav", "-af", "highpass=f=70",
                        "-c:a", "pcm_s24le", "audio_d.wav"], cwd=TRAB, check=True)
        audio_base = str(TRAB / "audio_d.wav")
        print("áudio D pronto (reduzir ruído + aprimorar voz)")
    audio_in = audio_base
    if janelas_resp:
        (TRAB / "respiracao.txt").write_text(f"asetnsamples=n=240:p=0,volume='{expr_resp()}':eval=frame", encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", audio_base, "-filter_script:a", "respiracao.txt",
                        "-c:a", "pcm_s24le", "audio_resp.wav"], cwd=TRAB, check=True)
        audio_in = str(TRAB / "audio_resp.wav")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", cfg["bruto"], "-i", audio_in,
           "-loop", "1", "-t", str(ta), "-framerate", str(FPS), "-i", "titulo.png",
           "-loop", "1", "-t", "0.1", "-framerate", str(FPS), "-i", cfg["capa"] or "titulo.png"]
    for c in cartoes:
        cmd += ["-loop", "1", "-t", f"{DUR + 1:.2f}", "-framerate", str(FPS), "-i", c["arquivo"]]
    if AULA:
        cmd += ["-i", str(trilha_telas())]
        if HORIZONTAL:
            cmd += ["-loop", "1", "-t", f"{DUR + 1:.2f}", "-framerate", str(FPS), "-i", str(TRAB / "camera_mascara.png")]
    for k, c in enumerate(contadores):
        cmd += ["-framerate", str(FPS), "-i", str(quadros_contador(k, c) / "%04d.png")]
    if CAM2:
        cmd += ["-i", CAM2]
    cmd += ["-filter_complex_script", "filtro.txt", "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264",
            "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
            # nível 4.2 fixo: sem ele o x264 marcava nível 6.2 (vídeo 8K) e o decodificador por hardware do
            # computador mostrava manchas e brilhos que não existem no arquivo (R029 e R030)
            "-profile:v", "high", "-level:v", "4.2", "-maxrate", "40M", "-bufsize", "60M",
            "-c:a", "pcm_s24le", "montado.mkv"]
    subprocess.run(cmd, cwd=TRAB, check=True)
    # volume final linear: ganho fixo até -14 LUFS e limitador de pico em -1,5 dB.
    # (o loudnorm cai no modo dinâmico quando falta folga de pico e levanta pausas e respiração)
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", "montado.mkv", "-vn", "-af", "ebur128", "-f", "null", "-"],
                         cwd=TRAB, capture_output=True, text=True, errors="ignore").stderr
    integrado = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", med)[-1])
    ganho = -14.0 - integrado
    # o limitador segura parte do ganho (mais em vídeo longo): mede o resultado e corrige até 2 vezes
    for _ in range(3):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "montado.mkv", "-c:v", "copy", "-af",
                        f"volume={ganho:.2f}dB,alimiter=limit=0.841:attack=2:release=60:level=false,aresample=48000",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", cfg["saida"]], cwd=TRAB, check=True)
        med = subprocess.run(["ffmpeg", "-hide_banner", "-i", cfg["saida"], "-vn", "-af", "ebur128", "-f", "null", "-"],
                             capture_output=True, text=True, errors="ignore").stderr
        final = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", med)[-1])
        if abs(final + 14.0) <= 0.3: break
        ganho += -14.0 - final
    print(f"volume final {final:.1f} LUFS")
    print(f"render pronto em {time.time() - t_ini:.0f}s: {cfg['saida']}")
