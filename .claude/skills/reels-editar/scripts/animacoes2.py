# Efeitos de motion construídos em 21/10/2026 para o A52 (Dono 14%), no mesmo padrão do animacoes.py:
# um PNG por quadro, fundo transparente. Quatro deles são cartões da tela dividida (1000 × 580) e um é
# tela cheia (1080 × 1920), desenhado por cima do vídeo.
#
#   "distancia": tela cheia. "VENDER MAIS" e "TER RESULTADO" entram juntos e se afastam, com uma linha
#                dourada medindo o vão. Esquema do conceito, sobre o take andando.
#   "destaque":  recorte real de uma página (PNG) com um marca-texto varrendo o trecho marcado e uma
#                aproximação lenta no trecho. Crédito embaixo.
#   "grade":     grade de 10 × 10 (100 restaurantes) que se preenche por grupos coloridos; na palavra
#                marcada, um grupo pulsa e um número grande sobe ao lado. Modo "acende": tudo apagado e
#                só N quadrados acendem.
#   "regua":     régua de porcentagem com marcador que desliza de A para B, valores em reais nas pontas,
#                trecho entre eles que acende em dourado e selo com a diferença.
#
# Os tempos das marcas chegam em segundos a partir do início do cartão (como no animacoes.py).
from PIL import Image, ImageDraw, ImageFont, ImageFilter

VERDE, VERDE_CLARO = (15, 92, 46, 255), (228, 243, 232, 255)
TINTA, CINZA, CINZA_CLARO = (10, 23, 18, 255), (91, 102, 96, 255), (196, 203, 199, 255)
VERMELHO, OURO, BRANCO = (179, 38, 26, 255), (200, 164, 77, 255), (255, 255, 255, 255)
AMARELO = (242, 193, 78, 255)
ESMERALDA = (15, 46, 35, 255)
PALIDO = (236, 239, 237, 255)


def _fonte(fontes, nome, tam):
    return ImageFont.truetype(str(fontes / nome), max(8, int(round(tam))))


def _ease(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def _ease_io(p):  # suave nas duas pontas
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def _pop(t, dur=0.3, exagero=0.12):
    if t <= 0: return 0.0
    if t >= dur: return 1.0
    p = t / dur
    return _ease(p) + exagero * (1 - abs(2 * p - 1)) if p > 0.5 else _ease(p) * (1 + exagero)


def _espacado(dr, cx, y, txt, f, esp, cor):
    lw = sum(dr.textlength(ch, font=f) for ch in txt) + esp * (len(txt) - 1)
    x = cx - lw / 2
    for ch in txt:
        dr.text((x, y), ch, font=f, fill=cor); x += dr.textlength(ch, font=f) + esp


def _cabe(fontes, nome, txt, larg, tam):
    med = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while tam > 24 and med.textlength(txt, font=_fonte(fontes, nome, tam)) > larg:
        tam -= 2
    return tam


def _texto_escalado(im, cx, cy, txt, f, cor, escala, alfa=255):
    if escala <= 0.01 or alfa <= 0: return
    med = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = med.textbbox((0, 0), txt, font=f, anchor="mm")
    w, h = int(r - l) + 20, int(b - t) + 20
    cam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(cam).text((w / 2, h / 2), txt, font=f, fill=cor[:3] + (alfa,), anchor="mm")
    if abs(escala - 1) > 0.005:
        cam = cam.resize((max(1, int(w * escala)), max(1, int(h * escala))), Image.LANCZOS)
    im.alpha_composite(cam, (int(cx - cam.width / 2), int(cy - cam.height / 2)))


def _base(dr, fontes, rotulo, tam_rot=30):
    dr.rounded_rectangle([25, 22, 975, 542], radius=30, fill=BRANCO)
    if rotulo:
        f = _fonte(fontes, "Montserrat-ExtraBold.ttf", _cabe(fontes, "Montserrat-ExtraBold.ttf", rotulo.upper(), 880, tam_rot))
        _espacado(dr, 500, 62, rotulo.upper(), f, 3.5, VERDE)


def _entrada(im, t, tam=(1000, 580)):
    if t >= 0.25: return im
    p = _ease(t / 0.25)
    esc = 0.94 + 0.06 * p
    menor = im.resize((int(tam[0] * esc), int(tam[1] * esc)), Image.LANCZOS)
    menor.putalpha(menor.getchannel("A").point(lambda v: int(v * p)))
    out = Image.new("RGBA", tam, (0, 0, 0, 0))
    out.alpha_composite(menor, ((tam[0] - menor.width) // 2, (tam[1] - menor.height) // 2))
    return out


def _selo(im, cx, cy, texto, f, esc):
    if esc <= 0.01: return
    med = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lw = med.textlength(texto, font=f)
    cam = Image.new("RGBA", (int(lw + 80), 84), (0, 0, 0, 0)); dc = ImageDraw.Draw(cam)
    dc.rounded_rectangle([0, 0, lw + 80, 84], radius=42, fill=OURO)
    dc.text(((lw + 80) / 2, 42), texto, font=f, fill=TINTA, anchor="mm")
    cam = cam.resize((max(1, int(cam.width * esc)), max(1, int(cam.height * esc))), Image.LANCZOS)
    im.alpha_composite(cam, (int(cx - cam.width / 2), int(cy - cam.height / 2)))


# ----------------------------------------------------------------------------------------------------
# 1. A distância (tela cheia 1080 × 1920)
# ----------------------------------------------------------------------------------------------------
def quadros_distancia(pasta, c, marcas, fps, fontes):
    """c: dura, esquerda ("VENDER MAIS"), direita ("TER RESULTADO"), rotulo ("A DISTÂNCIA"), y (centro, padrão 1150).
    marcas: "abre" (quando começam a se afastar), "some" (quando o conjunto sai)."""
    dura = c["dura"]; y = c.get("y", 1150)
    t_abre = marcas.get("abre", 0.5); t_some = marcas.get("some", dura - 0.5)
    f_chip = _fonte(fontes, "Montserrat-Black.ttf", c.get("tamanho", 58))
    f_rot = _fonte(fontes, "Montserrat-ExtraBold.ttf", 30)
    med = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    esq, dir_ = c.get("esquerda", "VENDER MAIS").upper(), c.get("direita", "TER RESULTADO").upper()
    le, ld = med.textlength(esq, font=f_chip), med.textlength(dir_, font=f_chip)
    PAD, ALT = c.get("pad", 36), c.get("alt", 110)

    def chip(txt, lw):
        cam = Image.new("RGBA", (int(lw + 2 * PAD), ALT), (0, 0, 0, 0)); dc = ImageDraw.Draw(cam)
        dc.rounded_rectangle([0, 0, lw + 2 * PAD, ALT], radius=26, fill=ESMERALDA[:3] + (235,))
        dc.text(((lw + 2 * PAD) / 2, ALT / 2 + 2), txt, font=f_chip, fill=BRANCO, anchor="mm")
        return cam
    ce, cd = chip(esq, le), chip(dir_, ld)
    # posições: juntos no centro (quase encostados) e depois afastados até as bordas
    gap0, gap1 = 18, 1080 - 60 - ce.width - cd.width  # vão inicial e final entre os chips
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        ent = _ease(t / 0.35)
        if t >= t_some: ent = 1 - _ease((t - t_some) / 0.3)
        if ent <= 0: im.save(pasta / f"{q:04d}.png"); continue
        p = _ease_io((t - t_abre) / max(dura - t_abre - 0.8, 0.5)) if t > t_abre else 0.0
        gap = gap0 + (gap1 - gap0) * p
        total = ce.width + cd.width + gap
        xe = 540 - total / 2; xd = xe + ce.width + gap
        a = int(255 * ent)
        # linha dourada medindo o vão, com as pontinhas
        if gap > 60:
            x0, x1 = xe + ce.width + 14, xd - 14
            dr.line([(x0, y), (x1, y)], fill=OURO[:3] + (a,), width=6)
            for xx in (x0, x1): dr.line([(xx, y - 18), (xx, y + 18)], fill=OURO[:3] + (a,), width=6)
            if c.get("rotulo") and p > 0.35:
                ar = int(a * _ease((p - 0.35) / 0.3))
                _espacado(dr, (x0 + x1) / 2, y - 64, c["rotulo"].upper(), f_rot, 4, OURO[:3] + (ar,))
        for cam, x in ((ce, xe), (cd, xd)):
            camA = cam.copy()
            if a < 255: camA.putalpha(camA.getchannel("A").point(lambda v: v * a // 255))
            im.alpha_composite(camA, (int(x), int(y - ALT / 2)))
        im.save(pasta / f"{q:04d}.png")
    return pasta


# ----------------------------------------------------------------------------------------------------
# 2. Marca-texto na notícia (tela dividida)
# ----------------------------------------------------------------------------------------------------
def quadros_destaque(pasta, c, marcas, fps, fontes):
    """c: dura, imagem (PNG do recorte da página), caixa [x0, y0, x1, y1] do trecho a marcar (em pixels da imagem),
    linhas (quantas linhas o trecho ocupa), credito. marcas: "marca" (quando o marca-texto começa)."""
    dura = c["dura"]; t_marca = marcas.get("marca", 0.6)
    img = Image.open(c["imagem"]).convert("RGBA")
    x0, y0, x1, y1 = c["caixa"]; n_lin = max(1, int(c.get("linhas", 3)))
    AREA = (45, 42, 955, 480)  # onde a imagem aparece dentro do cartão
    aw, ah = AREA[2] - AREA[0], AREA[3] - AREA[1]
    f_cred = _fonte(fontes, "Montserrat-Bold.ttf", 26)
    esc0 = max(aw / img.width, ah / img.height)  # preenche a área
    cx_al, cy_al = (x0 + x1) / 2, (y0 + y1) / 2  # a aproximação mira o trecho
    # "seguir" (A52): a câmera do cartão aproxima até o trecho ficar legível no celular e acompanha a ponta do
    # marca-texto, linha por linha, com movimento suavizado. Sem "seguir", aproximação lenta de 16% no trecho.
    seguir, zf = c.get("seguir", False), c.get("zoom_final", 1.16)
    alt0 = (y1 - y0) / n_lin
    caixas0 = c.get("trechos") or [(x0, y0 + k * alt0, x1, y0 + (k + 1) * alt0) for k in range(n_lin)]
    larguras = [bx1 - bx0 for bx0, _, bx1, _ in caixas0]; total_l = sum(larguras)
    def ponta(pm):  # onde está a ponta do marca-texto (x, y), varrendo em velocidade constante
        alvo = pm * total_l
        for (bx0, by0, bx1, by1), lw in zip(caixas0, larguras):
            if alvo <= lw: return bx0 + alvo, (by0 + by1) / 2
            alvo -= lw
        bx0, by0, bx1, by1 = caixas0[-1]; return bx1, (by0 + by1) / 2
    cx_s, cy_s = img.width / 2, img.height / 2
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        _base(dr, fontes, None)
        if seguir:
            zoom = 1.0 + (zf - 1.0) * _ease_io(min(t / (t_marca + 0.5), 1.0))
            esc = esc0 * zoom; jw_ = aw / esc
            # enquadra a linha inteira que está sendo marcada (seguir a ponta cortava o começo e o fim das linhas)
            ty = (caixas0[0][1] + caixas0[-1][3]) / 2
            if t < t_marca:
                tx = (caixas0[0][0] + caixas0[0][2]) / 2
            else:
                alvo = min((t - t_marca) / c.get("varre", 1.4), 1.0) * total_l
                k_l = 0
                while k_l < len(larguras) - 1 and alvo > larguras[k_l]:
                    alvo -= larguras[k_l]; k_l += 1
                tx = (caixas0[k_l][0] + caixas0[k_l][2]) / 2
            k_s = 1 - 0.82 ** (30 / fps)  # suavização (constante de ~0,2 s)
            cx_s += (tx - cx_s) * k_s; cy_s += (ty - cy_s) * k_s
            cx, cy = cx_s, cy_s
        else:
            zoom = 1.0 + 0.16 * _ease_io(t / dura)  # aproximação lenta durante o cartão inteiro
            esc = esc0 * zoom
            # centro da janela: começa no centro da imagem e vai para o trecho
            pz = _ease_io(t / dura)
            cx = img.width / 2 + (cx_al - img.width / 2) * pz
            cy = img.height / 2 + (cy_al - img.height / 2) * pz
        # recorte da imagem que cabe na área, nessa escala
        jw, jh = aw / esc, ah / esc
        jx = min(max(cx - jw / 2, 0), img.width - jw); jy = min(max(cy - jh / 2, 0), img.height - jh)
        rec = img.crop((int(jx), int(jy), int(jx + jw), int(jy + jh))).resize((aw, ah), Image.LANCZOS)
        # marca-texto: varre linha por linha do trecho, no espaço da imagem, desenhado sobre o recorte
        if t > t_marca:
            pm = min((t - t_marca) / c.get("varre", 1.4), 1.0)
            cam = Image.new("RGBA", (aw, ah), (0, 0, 0, 0)); dm = ImageDraw.Draw(cam)
            alt_l = (y1 - y0) / n_lin
            caixas = c.get("trechos") or [(x0, y0 + k * alt_l, x1, y0 + (k + 1) * alt_l) for k in range(n_lin)]
            for k, (bx0, by0, bx1, by1) in enumerate(caixas):
                p_l = min(max(pm * len(caixas) - k, 0.0), 1.0)
                if p_l <= 0: continue
                lx0, lx1 = bx0, bx0 + (bx1 - bx0) * p_l
                ly0, ly1 = by0, by1
                dm.rounded_rectangle([(lx0 - jx) * esc, (ly0 - jy) * esc + 2, (lx1 - jx) * esc, (ly1 - jy) * esc - 2],
                                     radius=6, fill=AMARELO[:3] + (120,))
            rec = Image.alpha_composite(rec, cam)
        mask = Image.new("L", (aw, ah), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, aw, ah], radius=18, fill=255)
        im.paste(rec, (AREA[0], AREA[1]), mask)
        if c.get("credito"):
            dr.text((500, 512), c["credito"], font=f_cred, fill=CINZA, anchor="mm")
        _entrada(im, t).save(pasta / f"{q:04d}.png")
    return pasta


# ----------------------------------------------------------------------------------------------------
# 3. Grade de 100 (tela dividida)
# ----------------------------------------------------------------------------------------------------
def quadros_grade(pasta, c, marcas, fps, fontes, numero_br=None):
    """c: dura, rotulo, grupos [{"n": 40, "cor": "verde", "nome": "LUCRO"}, ...] (preenchem em ordem),
    destaque {"grupos": [1, 2], "numero": 59, "rotulo": "SEM LUCRO", "detalhe": "..."} (na marca "destaque"),
    modo "preenche" (padrão) ou "acende" (tudo pálido e só os grupos acendem).
    marcas: "preenche" (começa a preencher), "destaque"."""
    dura = c["dura"]; modo = c.get("modo", "preenche")
    t_pre = marcas.get("preenche", 0.3); t_des = marcas.get("destaque", None)
    cores = {"verde": VERDE, "cinza": (150, 158, 153, 255), "vermelho": VERMELHO, "ouro": OURO, "tinta": TINTA}
    grupos = c["grupos"]
    ordem = []  # célula -> (grupo, cor)
    for gi, g in enumerate(grupos):
        ordem += [(gi, cores[g["cor"]])] * int(g["n"])
    ordem = ordem[:100]
    CEL, GAP, GX, GY = 34, 7, 60, 112  # grade de 10 × 10 à esquerda
    f_rot = _fonte(fontes, "Montserrat-ExtraBold.ttf", 30)
    f_leg = _fonte(fontes, "Montserrat-ExtraBold.ttf", 28)
    f_num = _fonte(fontes, "Montserrat-Black.ttf", 150)
    f_det = _fonte(fontes, "Montserrat-Bold.ttf", 26)
    f_rot2 = _fonte(fontes, "Montserrat-ExtraBold.ttf", 26)
    vel = c.get("velocidade", 1.6)  # segundos para preencher as 100
    des = c.get("destaque")
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        _base(dr, fontes, c.get("rotulo"))
        n_vis = 100 if modo == "acende" else int(100 * _ease((t - t_pre) / vel)) if t > t_pre else 0
        if modo == "acende":
            n_acesas = int(min(max((t - t_pre) / c.get("passo", 0.18), 0), len(ordem)))
        pulso = 1.0
        if t_des is not None and t > t_des:
            rt = t - t_des
            pulso = 1 + 0.10 * abs(__import__("math").sin(min(rt, 1.2) * 3.1416 * 2.5)) * (1 if rt < 1.2 else 0)
        for i in range(100):
            r, col = divmod(i, 10)
            cx = GX + col * (CEL + GAP) + CEL / 2; cy = GY + r * (CEL + GAP) + CEL / 2
            if modo == "acende":
                aceso = i < n_acesas
                cor = ordem[i][1] if aceso else PALIDO
                esc = _pop(t - t_pre - i * c.get("passo", 0.18), 0.25, 0.3) if aceso else 1.0
                esc = max(esc, 0.6) if aceso else 1.0
            else:
                if i >= n_vis:
                    cor, esc = PALIDO, 1.0
                else:
                    gi, cor = ordem[i] if i < len(ordem) else (None, PALIDO)
                    esc = 1.0
                    if des and t_des is not None and t > t_des and gi in des.get("grupos", []):
                        esc = pulso
            s = CEL * esc
            dr.rounded_rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], radius=7, fill=cor)
        # legenda dos grupos à direita (entra quando o grupo começa a ser preenchido / acender)
        yl = 120
        for gi, g in enumerate(grupos):
            inicio_g = sum(int(x["n"]) for x in grupos[:gi])
            if modo == "acende": vis = n_acesas > inicio_g
            else: vis = n_vis > inicio_g
            if not vis: continue
            cor = cores[g["cor"]]
            dr.rounded_rectangle([560, yl, 560 + 26, yl + 26], radius=6, fill=cor)
            dr.text((600, yl + 13), f"{g['n']}  {g['nome'].upper()}", font=f_leg, fill=TINTA, anchor="lm")
            yl += 46
        # número grande do destaque
        if des and t_des is not None and t > t_des:
            rt = t - t_des
            pr = min(rt / 0.8, 1.0); e = _ease(pr)
            v = int(round(des["numero"] * e))
            if des.get("rotulo"):
                _espacado(dr, 770, yl + 14, des["rotulo"].upper(), f_rot2, 3, cores.get(des.get("cor", "vermelho"), VERMELHO))
            _texto_escalado(im, 770, yl + 150, str(v), f_num, cores.get(des.get("cor", "vermelho"), VERMELHO),
                            1.06 if 0 <= rt - 0.8 < 0.3 else 1.0)
            if des.get("detalhe") and rt > 0.8:
                a = int(255 * min((rt - 0.8) / 0.3, 1.0))
                dr.text((500, 512), des["detalhe"], font=f_det, fill=CINZA[:3] + (a,), anchor="mm")
        elif c.get("detalhe"):
            dr.text((500, 512), c["detalhe"], font=f_det, fill=CINZA, anchor="mm")
        _entrada(im, t).save(pasta / f"{q:04d}.png")
    return pasta


# ----------------------------------------------------------------------------------------------------
# 4. Régua de porcentagem (tela dividida)
# ----------------------------------------------------------------------------------------------------
def quadros_regua(pasta, c, marcas, fps, fontes, numero_br=None):
    """c: dura, rotulo, minimo, maximo, passo (ticks), de, ate, valor_de ("R$ 8.000"), valor_ate ("R$ 22.400"),
    selo ("R$ 14.400 A MAIS POR MÊS"), detalhe. marcas: "desliza" (marcador vai de 'de' a 'ate'), "selo"."""
    dura = c["dura"]
    t_des = marcas.get("desliza", 0.8); t_selo = marcas.get("selo", t_des + 1.6)
    mn, mx, passo = c.get("minimo", 0), c.get("maximo", 20), c.get("passo", 5)
    de, ate = c["de"], c["ate"]
    X0, X1, Y = 110, 890, 300
    px = lambda v: X0 + (X1 - X0) * (v - mn) / (mx - mn)
    f_tick = _fonte(fontes, "Montserrat-Bold.ttf", 26)
    f_val = _fonte(fontes, "Montserrat-Black.ttf", 40)
    f_pct = _fonte(fontes, "Montserrat-Black.ttf", 44)
    f_selo = _fonte(fontes, "Montserrat-Black.ttf", 36)
    f_det = _fonte(fontes, "Montserrat-Bold.ttf", 24)
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        _base(dr, fontes, c.get("rotulo"))
        # trilho e ticks
        dr.rounded_rectangle([X0, Y - 7, X1, Y + 7], radius=7, fill=(228, 240, 231, 255))
        v = mn
        while v <= mx + 1e-9:
            x = px(v)
            dr.line([(x, Y + 14), (x, Y + 30)], fill=CINZA_CLARO, width=3)
            dr.text((x, Y + 52), f"{int(v)}%", font=f_tick, fill=CINZA, anchor="mm")
            v += passo
        # posição do marcador
        pd = _ease_io((t - t_des) / c.get("tempo_desliza", 1.1)) if t > t_des else 0.0
        pos = de + (ate - de) * pd
        # trecho dourado entre 'de' e a posição atual (acende forte no selo)
        forte = t > t_selo
        cor_tr = OURO if forte else (OURO[0], OURO[1], OURO[2], 110)
        if pos > de + 0.05:
            dr.rounded_rectangle([px(de), Y - 7, px(pos), Y + 7], radius=7, fill=cor_tr)
        # valores nas pontas
        _texto_escalado(im, px(de), Y - 70, f"{de}%", f_pct, CINZA if pd > 0.5 else TINTA, 1.0)
        dr.text((px(de), Y - 118), c.get("valor_de", ""), font=f_val, fill=CINZA if pd > 0.5 else TINTA, anchor="mm")
        if pd >= 0.999:
            rt = t - t_des - c.get("tempo_desliza", 1.1)
            _texto_escalado(im, px(ate), Y - 70, f"{ate}%", f_pct, VERDE, max(_pop(rt, 0.3, 0.14), 0.01))
            a = int(255 * _ease(rt / 0.3))
            dr.text((px(ate), Y - 118), c.get("valor_ate", ""), font=f_val, fill=VERDE[:3] + (a,), anchor="mm")
        # marcador (triângulo) na posição
        x = px(pos)
        dr.polygon([(x - 22, Y - 34), (x + 22, Y - 34), (x, Y - 8)], fill=VERDE if pd >= 0.999 else TINTA)
        # selo com a diferença
        if forte and c.get("selo"):
            _selo(im, 500, 440, c["selo"].upper(), f_selo, _pop(t - t_selo, 0.3, 0.1))
        if c.get("detalhe") and forte and t - t_selo > 0.3:
            a = int(255 * min((t - t_selo - 0.3) / 0.3, 1.0))
            dr.text((500, 512), c["detalhe"], font=f_det, fill=CINZA[:3] + (a,), anchor="mm")
        _entrada(im, t).save(pasta / f"{q:04d}.png")
    return pasta


# ----------------------------------------------------------------------------------------------------
# cartão estático simples (CTA), um PNG só
# ----------------------------------------------------------------------------------------------------
def cartao_estatico(caminho, linhas, fontes, rotulo=None, destaque_ultima=True):
    im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    _base(dr, fontes, rotulo)
    n = len(linhas); y = 290 - (n - 1) * 60
    for k, l in enumerate(linhas):
        ult = destaque_ultima and k == n - 1
        f = _fonte(fontes, "Montserrat-Black.ttf", _cabe(fontes, "Montserrat-Black.ttf", l.upper(), 880, 76 if ult else 64))
        dr.text((500, y), l.upper(), font=f, fill=VERDE if ult else TINTA, anchor="mm"); y += 120
    im.save(caminho)
    return caminho
