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
from pathlib import Path
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
    """A distância v2 (22/10, pedido do Rodrigo no A52: os chips que se afastavam não diziam nada).
    Painel translúcido no peito com um gráfico: a linha de VENDAS sobe, a linha de LUCRO fica parada e o vão
    entre as duas acende em dourado com o rótulo A DISTÂNCIA. c: dura, esquerda (rótulo da linha que sobe,
    "VENDER MAIS"), direita (rótulo da linha parada, "TER RESULTADO"), rotulo ("A DISTÂNCIA"), y (topo do painel).
    marcas: "abre" (as linhas começam a se separar), "some" (o painel sai)."""
    dura = c["dura"]; y0 = c.get("y", 1030)
    t_abre = marcas.get("abre", 0.3); t_some = marcas.get("some", dura - 0.35)
    f_lin = _fonte(fontes, "Montserrat-Black.ttf", 40)
    f_lin2 = _fonte(fontes, "Montserrat-Black.ttf", 38)
    f_rot = _fonte(fontes, "Montserrat-ExtraBold.ttf", 32)
    sobe_txt, parado_txt = c.get("esquerda", "VENDER MAIS").upper(), c.get("direita", "TER RESULTADO").upper()
    PX0, PX1, PY1 = 50, 1030, y0 + 360              # painel (acaba acima da legenda, que começa em ~1450)
    X0, X1 = 110, 600                                  # gráfico
    YB, YT, YP = y0 + 300, y0 + 110, y0 + 265          # base, topo da linha que sobe, fim da linha parada
    VERDE_VIVO, CINZA_LUZ = (94, 224, 154, 255), (205, 212, 208, 255)
    n_pts = 60
    def curva_sobe(u):  # sobe acelerando
        return YB - (YB - YT) * (u ** 1.6)
    def curva_parada(u):
        return YB - (YB - YP) * u
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        a_ent = _ease(t / 0.3)
        if t >= t_some: a_ent = 1 - _ease((t - t_some) / 0.3)
        if a_ent <= 0: im.save(pasta / f"{q:04d}.png"); continue
        cam = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); dr = ImageDraw.Draw(cam)
        dr.rounded_rectangle([PX0, y0, PX1, PY1], radius=34, fill=(10, 30, 23, 246))
        dr.rounded_rectangle([PX0, y0, PX1, PY1], radius=34, outline=(200, 164, 77, 120), width=2)
        # quanto do gráfico já foi desenhado
        p = _ease_io((t - t_abre) / max(t_some - t_abre - 0.5, 0.8)) if t > t_abre else 0.0
        us = [i / n_pts * p for i in range(n_pts + 1)]
        xs = [X0 + (X1 - X0) * u for u in us]
        sobe = [(x, curva_sobe(u)) for x, u in zip(xs, us)]
        parada = [(x, curva_parada(u)) for x, u in zip(xs, us)]
        # o vão entre as linhas, em dourado translúcido
        if p > 0.15:  # numa camada à parte, misturada por cima (desenhar direto troca o alfa e fura o painel)
            vao = Image.new("RGBA", cam.size, (0, 0, 0, 0))
            ImageDraw.Draw(vao).polygon(sobe + parada[::-1], fill=(200, 164, 77, int(80 * min((p - 0.15) / 0.3, 1))))
            cam.alpha_composite(vao); dr = ImageDraw.Draw(cam)
        # eixo de base
        dr.line([(X0, YB + 18), (X1 + 10, YB + 18)], fill=(255, 255, 255, 60), width=2)
        if len(sobe) > 1:
            dr.line(parada, fill=CINZA_LUZ, width=9, joint="curve")
            dr.line(sobe, fill=VERDE_VIVO, width=11, joint="curve")
            for pts, cor in ((parada, CINZA_LUZ), (sobe, VERDE_VIVO)):
                x, y = pts[-1]; dr.ellipse([x - 12, y - 12, x + 12, y + 12], fill=cor)
        # rótulos nas pontas, entram com o desenho
        if p > 0.35:
            ar = int(255 * min((p - 0.35) / 0.25, 1))
            xs_, ys_ = sobe[-1]; xp_, yp_ = parada[-1]
            dr.text((xs_ + 34, ys_), sobe_txt, font=f_lin, fill=VERDE_VIVO[:3] + (ar,), anchor="lm")
            dr.text((xp_ + 34, yp_), parado_txt, font=f_lin2, fill=CINZA_LUZ[:3] + (ar,), anchor="lm")
        # a medida do vão e o nome do conceito
        if p > 0.7:
            ab = int(255 * min((p - 0.7) / 0.2, 1))
            xm = sobe[-1][0] - 4; ya, yb = sobe[-1][1] + 18, parada[-1][1] - 18
            if yb - ya > 30:
                dr.line([(xm, ya), (xm, yb)], fill=OURO[:3] + (ab,), width=5)
                for yy in (ya, yb): dr.line([(xm - 14, yy), (xm + 14, yy)], fill=OURO[:3] + (ab,), width=5)
            _espacado(dr, (PX0 + PX1) / 2, y0 + 34, c.get("rotulo", "A DISTÂNCIA").upper(), f_rot, 5, OURO[:3] + (ab,))
        if a_ent < 1: cam.putalpha(cam.getchannel("A").point(lambda v: int(v * a_ent)))
        im.alpha_composite(cam)
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
        if c.get("parado"):
            zoom, esc, cx, cy = 1.0, esc0, img.width / 2, img.height / 2
        elif seguir:
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
    cores = {"verde": VERDE, "cinza": (150, 158, 153, 255), "vermelho": VERMELHO, "ouro": OURO, "tinta": TINTA,
             "claro": (214, 219, 216, 255)}
    grupos = c["grupos"]
    ordem = []  # célula -> (grupo, cor)
    for gi, g in enumerate(grupos):
        ordem += [(gi, cores[g["cor"]])] * int(g["n"])
    ordem = ordem[:100]
    CEL, GAP, GX, GY = 31, 6, 64, 102  # grade de 10 × 10 à esquerda (termina em y 466, acima do rodapé)
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
        if t_des is not None and t > t_des and c.get("pulsar", False):
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
            if not vis or g.get("legenda") is False: continue
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
# 3b. Rosca (tela dividida): 100 dividido em fatias coloridas, uma fatia em destaque
# ----------------------------------------------------------------------------------------------------
def quadros_rosca(pasta, c, marcas, fps, fontes, numero_br=None):
    """Rosca de 100 (22/10, A52): outra forma gráfica para não repetir a grade de 100.
    c: dura, rotulo, fatias [{"n": 38, "cor": "cinza", "nome": "NÃO MEXERAM"}, ...] (desenham em ordem, no
    sentido horário), destaque {"fatia": 3, "numero": 6, "rotulo": "EM CADA 100"} (a fatia sai do anel e o
    número entra no centro), detalhe (rodapé).
    marcas: "preenche" (o anel começa a se completar), "destaque"."""
    import math
    dura = c["dura"]
    t_pre = marcas.get("preenche", 0.3); t_des = marcas.get("destaque", None)
    cores = {"verde": VERDE, "cinza": (150, 158, 153, 255), "vermelho": VERMELHO, "ouro": OURO,
             "dourado_claro": (226, 201, 132, 255), "tinta": TINTA, "claro": (214, 219, 216, 255)}
    fatias = c["fatias"]; total = sum(f["n"] for f in fatias)
    des = c.get("destaque") or {}
    k_des = des.get("fatia", len(fatias) - 1)
    f_leg = _fonte(fontes, "Montserrat-ExtraBold.ttf", 28)
    f_num = _fonte(fontes, "Montserrat-Black.ttf", 104)
    f_cen = _fonte(fontes, "Montserrat-ExtraBold.ttf", 17)  # cabe dentro do anel
    f_det = _fonte(fontes, "Montserrat-Bold.ttf", 25)
    CX, CY, R, ESP = 285, 300, 175, 62   # centro, raio externo e espessura do anel
    SS = 2                                # desenha em dobro e reduz (bordas lisas)
    vel = c.get("velocidade", 1.5)
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        _base(dr, fontes, c.get("rotulo"))
        prog = _ease((t - t_pre) / vel) if t > t_pre else 0.0  # quanto do anel já foi desenhado
        dest = _ease((t - t_des) / 0.35) if (t_des is not None and t > t_des) else 0.0
        lay = Image.new("RGBA", (2 * (R + 40) * SS, 2 * (R + 40) * SS), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        oc = (R + 40) * SS
        # trilho pálido do anel inteiro
        dl.ellipse([oc - R * SS, oc - R * SS, oc + R * SS, oc + R * SS], fill=PALIDO)
        ang0 = -90.0; feito = prog * total
        for k, f in enumerate(fatias):
            n_vis = min(max(feito, 0), f["n"]); feito -= f["n"]
            if n_vis <= 0: ang0 += 360 * f["n"] / total; continue
            a1 = ang0 + 360 * n_vis / total
            desloc = 16 * dest if k == k_des else 0  # a fatia em destaque sai do anel
            meio = math.radians((ang0 + ang0 + 360 * f["n"] / total) / 2)
            dx, dy = math.cos(meio) * desloc * SS, math.sin(meio) * desloc * SS
            rr = (R + (6 * dest if k == k_des else 0)) * SS
            dl.pieslice([oc - rr + dx, oc - rr + dy, oc + rr + dx, oc + rr + dy], ang0, a1, fill=cores[f["cor"]])
            ang0 += 360 * f["n"] / total
        ri = (R - ESP) * SS
        dl.ellipse([oc - ri, oc - ri, oc + ri, oc + ri], fill=BRANCO)
        # finos separadores brancos entre as fatias
        ang = -90.0
        for f in fatias:
            a = math.radians(ang)
            dl.line([(oc + math.cos(a) * ri, oc + math.sin(a) * ri), (oc + math.cos(a) * (R + 24) * SS, oc + math.sin(a) * (R + 24) * SS)],
                    fill=BRANCO, width=4 * SS)
            ang += 360 * f["n"] / total
        lay = lay.resize((lay.width // SS, lay.height // SS), Image.LANCZOS)
        im.alpha_composite(lay, (CX - (R + 40), CY - (R + 40)))
        dr = ImageDraw.Draw(im)
        # número no centro
        if dest > 0:
            cor_n = cores.get(des.get("cor", fatias[k_des]["cor"]), VERDE)
            v = int(round(des.get("numero", fatias[k_des]["n"]) * dest))
            _texto_escalado(im, CX, CY - 10, str(v), f_num, cor_n, 1.06 if 0.35 < t - t_des < 0.6 else 1.0)
            if des.get("rotulo"):
                _espacado(dr, CX, CY + 46, des["rotulo"].upper(), f_cen, 1.5, cor_n)
        # legenda à direita: cada fatia entra quando começa a ser desenhada
        yl = 132; acum = 0
        for k, f in enumerate(fatias):
            if prog * total <= acum: break
            acum += f["n"]
            forte = (k == k_des and dest > 0)
            cor = cores[f["cor"]]
            dr.rounded_rectangle([560, yl, 588, yl + 28], radius=7, fill=cor)
            dr.text((604, yl + 14), f"{f['n']}  {f['nome'].upper()}", font=f_leg,
                    fill=(cor if forte else TINTA), anchor="lm")
            if forte:
                dr.rounded_rectangle([548, yl - 12, 975 - 18, yl + 40], radius=14, outline=cor, width=3)
            yl += 62
        if c.get("detalhe") and prog > 0.9:
            a = int(255 * min((prog - 0.9) / 0.1, 1.0))
            dr.text((500, 512), c["detalhe"], font=f_det, fill=CINZA[:3] + (a,), anchor="mm")
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
# 5. Placar (tela dividida, 1000 × 640): jogo de veredito do R033 (29/10)
# ----------------------------------------------------------------------------------------------------
OURO_CLARO, OURO_ESCURO, VERDE_FUNDO = (250, 242, 222, 255), (112, 86, 26, 255), (234, 246, 238, 255)
P_W, P_H = 1000, 640
P_ARENA = (500, 100, 880, 116)            # centro x, centro y, largura, altura do cartão da decisão
P_COL = {"dinheiro": 265, "bonito": 735}  # centro de cada coluna
P_CAB_Y, P_CHIP_Y, P_CHIP_H, P_CHIP_GAP, P_CHIP_W = 198, 296, 60, 12, 420


def _placar_cartao(fontes, texto, w, h, estilo):
    """Cartão da decisão, desenhado grande; vira a ficha da coluna encolhendo."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    fundo, tinta, borda = {"ouro": (OURO, TINTA, OURO_ESCURO)}.get(estilo, (PALIDO, TINTA, CINZA_CLARO))
    dr.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 4, fill=fundo, outline=borda, width=4)
    f = _fonte(fontes, "Montserrat-Black.ttf", _cabe(fontes, "Montserrat-Black.ttf", texto, w - 80, int(h * 0.45)))
    dr.text((w / 2, h / 2), texto, font=f, fill=tinta, anchor="mm")
    return im


def _placar_ficha(fontes, texto, lado, estilo):
    im = Image.new("RGBA", (P_CHIP_W, P_CHIP_H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    if estilo == "ouro": fundo, tinta = OURO, TINTA
    elif lado == "dinheiro": fundo, tinta = VERDE_FUNDO, VERDE
    else: fundo, tinta = OURO_CLARO, OURO_ESCURO
    dr.rounded_rectangle([0, 0, P_CHIP_W - 1, P_CHIP_H - 1], radius=16, fill=fundo)
    f = _fonte(fontes, "Montserrat-ExtraBold.ttf", _cabe(fontes, "Montserrat-ExtraBold.ttf", texto, P_CHIP_W - 40, 28))
    dr.text((P_CHIP_W / 2, P_CHIP_H / 2), texto, font=f, fill=tinta, anchor="mm")
    return im


def _colar(im, peca, cx, cy, escala=1.0, alfa=1.0):
    if escala <= 0.01 or alfa <= 0.01: return
    if abs(escala - 1) > 0.005:
        peca = peca.resize((max(1, int(peca.width * escala)), max(1, int(peca.height * escala))), Image.LANCZOS)
    if alfa < 0.999:
        peca = peca.copy(); peca.putalpha(peca.getchannel("A").point(lambda v: int(v * alfa)))
    im.alpha_composite(peca, (int(cx - peca.width / 2), int(cy - peca.height / 2)))


def _placar_carimbo(fontes, texto, cor):
    f = _fonte(fontes, "Montserrat-Black.ttf", 46)
    lw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(texto, font=f)
    w, h = int(lw + 70), 92
    cam = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(cam)
    dc.rounded_rectangle([3, 3, w - 4, h - 4], radius=16, fill=BRANCO, outline=cor, width=7)
    dc.text((w / 2, h / 2), texto, font=f, fill=cor, anchor="mm")
    return cam.rotate(-5, resample=Image.BICUBIC, expand=True)


def quadros_placar(pasta, c, marcas, fps, fontes):
    """Placar de duas colunas, DÁ DINHEIRO (verde, esquerda) e FICA BONITO (dourado, direita). Um contador por
    decisão; o placar inteiro é redesenhado em cada um a partir das decisões anteriores.
    c: dura, item (texto do cartão), lado ("dinheiro", "bonito" ou "meio"), estilo ("ouro" para o cartão da
    promessa), anteriores [{"item": ..., "lado": ..., "estilo": ...}], carimbo ("NENHUM DOS DOIS"),
    carimbo_troca ("DEPENDE DA CONTA"), entrada (o placar inteiro entra com fade; padrão: só sem anteriores).
    marcas: "desliza" (o cartão vai para a coluna), "selo" (carimbo), "troca" (o carimbo muda),
    "destaque" (desempate: a coluna que ganhou acende, a outra apaga e o placar aparece grande no meio)."""
    dura = c["dura"]; lado = c.get("lado", "meio"); estilo = c.get("estilo")
    t_des = marcas.get("desliza"); t_selo = marcas.get("selo"); t_troca = marcas.get("troca")
    t_dest = marcas.get("destaque")
    ant = c.get("anteriores", [])
    entrada = c.get("entrada", not ant)
    ROT = {"dinheiro": c.get("rotulo_esquerda", "DÁ DINHEIRO"), "bonito": c.get("rotulo_direita", "FICA BONITO")}
    pontos = {k: sum(1 for a in ant if a["lado"] == k) for k in ("dinheiro", "bonito")}
    f_cab = _fonte(fontes, "Montserrat-Black.ttf", 34)
    f_pts = _fonte(fontes, "Montserrat-Black.ttf", 52)
    f_placar = _fonte(fontes, "Montserrat-Black.ttf", 110)
    fichas = [(_placar_ficha(fontes, a["item"].upper(), a["lado"], a.get("estilo")), a["lado"]) for a in ant if a["lado"] in P_COL]
    cartao = _placar_cartao(fontes, c["item"].upper(), P_ARENA[2], P_ARENA[3], estilo)
    ficha_nova = _placar_ficha(fontes, c["item"].upper(), lado, estilo) if lado in P_COL else None
    slot_y = lambda n: P_CHIP_Y + n * (P_CHIP_H + P_CHIP_GAP) + P_CHIP_H / 2
    VOO = 0.45
    car = {}
    if t_selo is not None and c.get("carimbo"): car["selo"] = _placar_carimbo(fontes, c["carimbo"].upper(), CINZA)
    if t_troca is not None and c.get("carimbo_troca"): car["troca"] = _placar_carimbo(fontes, c["carimbo_troca"].upper(), VERDE)
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (P_W, P_H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        dr.rounded_rectangle([25, 22, P_W - 25, P_H - 22], radius=30, fill=BRANCO)
        chegou = t_des is not None and ficha_nova is not None and t >= t_des + VOO
        pts = dict(pontos)
        if chegou: pts[lado] += 1
        # as duas colunas: cabeçalho com o número e as fichas já decididas
        pisca = t_selo is not None and 0 <= t - t_selo < 0.6 and int((t - t_selo) / 0.15) % 2 == 0
        for k, cx in P_COL.items():
            cor_f, cor_t = (VERDE, BRANCO) if k == "dinheiro" else (OURO, TINTA)
            esc = 1.0
            if chegou and k == lado: esc = max(_pop(t - t_des - VOO, 0.3, 0.08), 0.9)
            w, h = 440 * esc, 82 * esc
            fundo = cor_f if not pisca else (cor_f[0], cor_f[1], cor_f[2], 120)
            dr.rounded_rectangle([cx - w / 2, P_CAB_Y - h / 2 + 22, cx + w / 2, P_CAB_Y + h / 2 + 22], radius=20, fill=fundo)
            dr.text((cx - w / 2 + 26, P_CAB_Y + 22), ROT[k], font=f_cab, fill=cor_t, anchor="lm")
            ep = _pop(t - t_des - VOO, 0.35, 0.3) if chegou and k == lado else 1.0
            _texto_escalado(im, cx + w / 2 - 44, P_CAB_Y + 22, str(pts[k]), f_pts, cor_t, max(ep, 0.6))
        n_col = {"dinheiro": 0, "bonito": 0}
        for ficha, ld in fichas:
            _colar(im, ficha, P_COL[ld], slot_y(n_col[ld])); n_col[ld] += 1
        # o cartão da decisão: entra no meio, voa para a coluna no veredito
        if ficha_nova is not None and t_des is not None and t >= t_des:
            p = _ease_io((t - t_des) / VOO)
            x0, y0, w0 = P_ARENA[0], P_ARENA[1], P_ARENA[2]
            x1, y1, w1 = P_COL[lado], slot_y(n_col[lado]), P_CHIP_W
            if p < 1:
                _colar(im, cartao, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p, (w0 + (w1 - w0) * p) / w0)
            else:
                _colar(im, ficha_nova, x1, y1, 1.0)
        else:
            _colar(im, cartao, P_ARENA[0], P_ARENA[1], max(_pop(t, 0.35, 0.1), 0.01))
        # carimbo por cima do cartão que fica no meio
        if "selo" in car and t >= t_selo:
            atual = car["troca"] if "troca" in car and t >= t_troca else car["selo"]
            t_ref = t_troca if "troca" in car and t >= t_troca else t_selo
            _colar(im, atual, 500, 562, max(_pop(t - t_ref, 0.25, 0.25), 0.01))  # no espaço livre embaixo das colunas
        # desempate: a coluna que ganhou acende, a outra apaga, o placar aparece grande no meio
        if t_dest is not None and t >= t_dest:
            p = _ease((t - t_dest) / 0.4)
            perde = "bonito" if pts["dinheiro"] >= pts["bonito"] else "dinheiro"
            cx = P_COL[perde]
            veu = Image.new("RGBA", (460, 440), (255, 255, 255, int(170 * p)))
            im.alpha_composite(veu, (int(cx - 230), P_CAB_Y - 30))
            if t >= t_des + VOO if t_des is not None else True:
                cobre = Image.new("RGBA", (P_ARENA[2] + 20, P_ARENA[3] + 20), (255, 255, 255, int(255 * p)))
                im.alpha_composite(cobre, (P_ARENA[0] - P_ARENA[2] // 2 - 10, P_ARENA[1] - P_ARENA[3] // 2 - 10))
                _texto_escalado(im, P_ARENA[0], P_ARENA[1], f"{pts['dinheiro']} x {pts['bonito']}", f_placar, VERDE,
                                max(_pop(t - t_dest, 0.35, 0.15), 0.01))
        (_entrada(im, t, (P_W, P_H)) if entrada else im).save(pasta / f"{q:04d}.png")
    return pasta


# ----------------------------------------------------------------------------------------------------
# 6. Veredito (tela cheia 1080 × 1920, por cima do vídeo): versão do R033 aprovada pelo Rodrigo em 29/10,
#    no lugar do placar em tela dividida. Ele grava de longe; as laterais guardam a contagem e o meio de baixo
#    mostra a decisão (ícone + título), que voa para o lado do veredito.
# ----------------------------------------------------------------------------------------------------
EMOJI = Path(r"C:\Windows\Fonts\seguiemj.ttf")
V_LADO = {"dinheiro": 180, "bonito": 900}       # centro de cada lateral
V_ETQ_Y, V_NUM_Y, V_MINI_Y = 636, 760, 865      # etiqueta, número, primeira linha de mini ícones
V_MINI, V_MINI_GAP = 84, 12
V_CARD = (540, 1445, 560, 340)                  # centro x, centro y, largura, altura do cartão do meio
V_COR = {"dinheiro": (VERDE, BRANCO), "bonito": (OURO, TINTA)}


def _icone(txt, tam):
    """Emoji colorido do Windows; sem a fonte, devolve None e o cartão fica só com o título."""
    if not EMOJI.exists(): return None
    txt = txt.replace("️", "")  # o seletor de variação desenha alguns ícones tortos ou miúdos
    f = ImageFont.truetype(str(EMOJI), 109)  # tamanho nativo do bitmap da fonte; depois redimensiona
    im = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((75, 75), txt, font=f, embedded_color=True, anchor="mm")
    caixa = im.getbbox()
    if not caixa: return None
    im = im.crop(caixa)
    esc = tam / max(im.size)
    return im.resize((max(1, int(im.width * esc)), max(1, int(im.height * esc))), Image.LANCZOS)


def _foto(caminho, w, h, raio):
    """Foto (real ou gerada) recortada para preencher w × h, com cantos redondos."""
    im = Image.open(caminho).convert("RGBA")
    esc = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * esc)), max(h, int(im.height * esc))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((x, y, x + w, y + h))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=raio, fill=255)
    im.putalpha(m)
    return im


def _v_cartao(fontes, c):
    w, h = V_CARD[2], V_CARD[3]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    ouro = c.get("estilo") == "ouro"
    dr.rounded_rectangle([0, 0, w - 1, h - 1], radius=36, fill=OURO if ouro else BRANCO,
                         outline=OURO_ESCURO if ouro else CINZA_CLARO, width=5)
    titulo = c["item"].upper()
    if c.get("grande"):  # cartão sem ícone: o número em destaque ("14%") e o título embaixo
        f = _fonte(fontes, "Montserrat-Black.ttf", 150)
        dr.text((w / 2, (h - 60) / 2), c["grande"], font=f, fill=TINTA, anchor="mm")
    elif c.get("imagem"):  # foto no lugar do ícone (foto real ou gerada), ocupando a parte de cima do cartão
        im.alpha_composite(_foto(c["imagem"], w - 24, h - 88, 26), (12, 12))
    else:
        ic = _icone(c.get("icone", ""), 150) if c.get("icone") else None
        if ic: im.alpha_composite(ic, (int(w / 2 - ic.width / 2), int((h - 60) / 2 - ic.height / 2)))
    f = _fonte(fontes, "Montserrat-Black.ttf", _cabe(fontes, "Montserrat-Black.ttf", titulo, w - 60, 44))
    dr.text((w / 2, h - 40), titulo, font=f, fill=TINTA, anchor="mm")
    return im


def _v_mini(fontes, c, lado):
    s = V_MINI
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    ouro = c.get("estilo") == "ouro"
    dr.rounded_rectangle([0, 0, s - 1, s - 1], radius=20, fill=OURO if ouro else BRANCO,
                         outline=V_COR[lado][0], width=4)
    if c.get("grande"):
        f = _fonte(fontes, "Montserrat-Black.ttf", _cabe(fontes, "Montserrat-Black.ttf", c["grande"], s - 14, 36))
        dr.text((s / 2, s / 2), c["grande"], font=f, fill=TINTA, anchor="mm")
    elif c.get("imagem"):
        im.alpha_composite(_foto(c["imagem"], s - 10, s - 10, 16), (5, 5))
    else:
        ic = _icone(c.get("icone", ""), s - 26) if c.get("icone") else None
        if ic: im.alpha_composite(ic, (int(s / 2 - ic.width / 2), int(s / 2 - ic.height / 2)))
    return im


def _v_slot(lado, n):
    col, lin = n % 2, n // 2
    return V_LADO[lado] + (col - 0.5) * (V_MINI + V_MINI_GAP), V_MINI_Y + lin * (V_MINI + V_MINI_GAP) + V_MINI / 2


def quadros_veredito(pasta, c, marcas, fps, fontes):
    """Tela cheia por cima do vídeo. Laterais fixas: DÁ DINHEIRO (verde, esquerda) e FICA BONITO (dourado, direita),
    cada uma com a etiqueta, o número e os mini ícones das decisões já julgadas. No meio de baixo, o cartão da
    decisão (ícone + título) entra com salto e voa para a lateral do veredito.
    c: dura, item (título; sem item = só apresenta as laterais), icone (emoji), imagem (caminho de uma foto) ou
    grande ("14%"), lado
    ("dinheiro", "bonito" ou "meio"), estilo ("ouro"), anteriores [{"item", "icone"/"grande", "lado", "estilo"}],
    carimbo / carimbo_troca (cartão que fica no meio), entrada (as laterais entram com animação).
    marcas: "desliza" (voa para a lateral), "abre" (sem item: a lateral direita aparece), "selo", "troca",
    "destaque" (desempate: o lado que perdeu apaga e o placar aparece grande no lugar do cartão)."""
    dura = c["dura"]; lado = c.get("lado", "meio"); ant = c.get("anteriores", [])
    t_des = marcas.get("desliza"); t_abre = marcas.get("abre"); t_selo = marcas.get("selo")
    t_troca = marcas.get("troca"); t_dest = marcas.get("destaque")
    entrada = c.get("entrada", False)
    ROT = {"dinheiro": c.get("rotulo_esquerda", "DÁ DINHEIRO"), "bonito": c.get("rotulo_direita", "FICA BONITO")}
    f_etq = _fonte(fontes, "Montserrat-Black.ttf", 34)
    f_num = _fonte(fontes, "Montserrat-Black.ttf", 112)
    f_placar = _fonte(fontes, "Montserrat-Black.ttf", 150)
    minis = [(_v_mini(fontes, a, a["lado"]), a["lado"]) for a in ant if a["lado"] in V_LADO]
    pontos = {k: sum(1 for a in ant if a["lado"] == k) for k in V_LADO}
    tem_item = bool(c.get("item"))
    cartao = _v_cartao(fontes, c) if tem_item else None
    mini_nova = _v_mini(fontes, c, lado) if tem_item and lado in V_LADO else None
    car = {}
    if t_selo is not None and c.get("carimbo"): car["selo"] = _placar_carimbo(fontes, c["carimbo"].upper(), CINZA)
    if t_troca is not None and c.get("carimbo_troca"): car["troca"] = _placar_carimbo(fontes, c["carimbo_troca"].upper(), VERDE)
    VOO = 0.5
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        chegou = t_des is not None and mini_nova is not None and t >= t_des + VOO
        pts = dict(pontos)
        if chegou: pts[lado] += 1
        pisca = t_selo is not None and 0 <= t - t_selo < 0.6 and int((t - t_selo) / 0.15) % 2 == 0
        perde = None
        if t_dest is not None and t >= t_dest:
            perde = "bonito" if pts["dinheiro"] >= pts["bonito"] else "dinheiro"
        for k, cx in V_LADO.items():
            # aparecimento das laterais: entrada = as duas sobem juntas; sem item, a direita espera a marca "abre"
            inicio = 0.0 if (k == "dinheiro" or t_abre is None) else t_abre
            ap = _pop(t - inicio, 0.35, 0.12) if (entrada or not tem_item) else 1.0
            if ap <= 0.01: continue
            camada = Image.new("RGBA", (300, 560), (0, 0, 0, 0)); dc = ImageDraw.Draw(camada)
            cor_f, cor_t = V_COR[k]
            fundo = cor_f if not pisca else cor_f[:3] + (110,)
            dc.rounded_rectangle([0, 0, 299, 74], radius=24, fill=fundo)
            dc.text((150, 38), ROT[k], font=f_etq, fill=cor_t, anchor="mm")
            ep = 1.0
            if chegou and k == lado: ep = max(_pop(t - t_des - VOO, 0.35, 0.3), 0.6)
            num = Image.new("RGBA", (300, 150), (0, 0, 0, 0))
            ImageDraw.Draw(num).text((150, 75), str(pts[k]), font=f_num, fill=BRANCO, anchor="mm",
                                     stroke_width=7, stroke_fill=TINTA)
            _colar(camada, num, 150, 124 + 74 / 2 - 37 + 50, ep)
            n = 0
            for mi, ld in minis:
                if ld != k: continue
                x, y = _v_slot(k, n); n += 1
                _colar(camada, mi, x - cx + 150, y - V_ETQ_Y + 37 + 0)
            if chegou and k == lado:
                x, y = _v_slot(k, n)
                _colar(camada, mini_nova, x - cx + 150, y - V_ETQ_Y + 37, max(_pop(t - t_des - VOO, 0.25, 0.2), 0.5))
            alfa = 1.0
            if perde == k: alfa = 1 - 0.65 * _ease((t - t_dest) / 0.4)
            _colar(im, camada, cx, V_ETQ_Y - 37 + 280, ap, alfa)
        if tem_item:
            if mini_nova is not None and t_des is not None and t >= t_des:
                p = _ease_io((t - t_des) / VOO)
                if p < 1:
                    x1, y1 = _v_slot(lado, pontos[lado])
                    esc = 1 + (V_MINI / V_CARD[2] - 1) * p
                    _colar(im, cartao, V_CARD[0] + (x1 - V_CARD[0]) * p, V_CARD[1] + (y1 - V_CARD[1]) * p, esc)
            else:
                _colar(im, cartao, V_CARD[0], V_CARD[1], max(_pop(t, 0.35, 0.12), 0.01))
            if "selo" in car and t >= t_selo:
                atual = car["troca"] if "troca" in car and t >= t_troca else car["selo"]
                t_ref = t_troca if "troca" in car and t >= t_troca else t_selo
                _colar(im, atual, V_CARD[0], V_CARD[1] - 30, max(_pop(t - t_ref, 0.25, 0.25), 0.01))
        if perde is not None:
            caixa = Image.new("RGBA", (620, 220), (0, 0, 0, 0)); dk = ImageDraw.Draw(caixa)
            dk.rounded_rectangle([0, 0, 619, 219], radius=40, fill=BRANCO)
            dk.text((310, 112), f"{pts['dinheiro']} x {pts['bonito']}", font=f_placar, fill=VERDE, anchor="mm")
            _colar(im, caixa, V_CARD[0], V_CARD[1], max(_pop(t - t_dest, 0.35, 0.15), 0.01))
        im.save(pasta / f"{q:04d}.png", compress_level=1)
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
