# Cartões animados da tela dividida (1000 × 580, fundo transparente, um PNG por quadro).
# Usados pelo editar_reel.py no campo "contadores", escolhidos pelo "tipo":
#   "troca": preço que cai. O preço antigo aparece, o novo é revelado na palavra falada, o antigo leva um risco
#            vermelho e entra o selo da diferença.
#   "conta": conta que monta. "R$ 8,00 × 400 kg" entra termo a termo e o resultado sobe na palavra falada.
# Os tempos das marcas ("meio", "troca", "resultado") chegam em segundos a partir do início do cartão.
from PIL import Image, ImageDraw, ImageFont

VERDE, VERDE_CLARO = (15, 92, 46, 255), (228, 243, 232, 255)
TINTA, CINZA, CINZA_CLARO = (10, 23, 18, 255), (91, 102, 96, 255), (196, 203, 199, 255)
VERMELHO, OURO, BRANCO = (179, 38, 26, 255), (200, 164, 77, 255), (255, 255, 255, 255)


def _fonte(fontes, nome, tam):
    return ImageFont.truetype(str(fontes / nome), max(8, int(round(tam))))


def _ease(p):  # desaceleração (ease-out cúbico), de 0 a 1
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def _pop(t, dur=0.3, exagero=0.12):  # escala que passa um pouco do tamanho e assenta
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
    while tam > 30 and med.textlength(txt, font=_fonte(fontes, nome, tam)) > larg:
        tam -= 2
    return tam


def _texto_escalado(im, cx, cy, txt, f, cor, escala, alfa=255):
    """Escreve o texto centrado em (cx, cy) numa camada e aplica escala e transparência."""
    if escala <= 0.01 or alfa <= 0: return
    med = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = med.textbbox((0, 0), txt, font=f, anchor="mm")
    w, h = int(r - l) + 20, int(b - t) + 20
    cam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(cam).text((w / 2, h / 2), txt, font=f, fill=cor[:3] + (alfa,), anchor="mm")
    if abs(escala - 1) > 0.005:
        cam = cam.resize((max(1, int(w * escala)), max(1, int(h * escala))), Image.LANCZOS)
    im.alpha_composite(cam, (int(cx - cam.width / 2), int(cy - cam.height / 2)))


def _base(dr, fontes, rotulo):
    dr.rounded_rectangle([25, 22, 975, 542], radius=30, fill=BRANCO)
    if rotulo:
        _espacado(dr, 500, 62, rotulo.upper(), _fonte(fontes, "Montserrat-ExtraBold.ttf", 30), 4.5, VERDE)


def _entrada(im, t):
    """Cartão inteiro entra em 0,25 s: cresce de 94% para 100% e aparece."""
    if t >= 0.25: return im
    p = _ease(t / 0.25)
    esc = 0.94 + 0.06 * p
    menor = im.resize((int(1000 * esc), int(580 * esc)), Image.LANCZOS)
    a = menor.getchannel("A").point(lambda v: int(v * p))
    menor.putalpha(a)
    out = Image.new("RGBA", (1000, 580), (0, 0, 0, 0))
    out.alpha_composite(menor, ((1000 - menor.width) // 2, (580 - menor.height) // 2))
    return out


def quadros_troca(pasta, c, marcas, fps, fontes):
    """Preço que cai: dois preços lado a lado, o novo revelado na palavra 'troca'."""
    dura = c["dura"]
    t_meio = marcas.get("meio", 0.0)        # quando a coluna da direita aparece (com o preço escondido)
    t_troca = marcas.get("troca", t_meio + 1.0)
    antes, depois = c["antes"], c["depois"]  # {"titulo": ..., "valor": "R$ 54,00"}
    tam_tit = min(_cabe(fontes, "Montserrat-ExtraBold.ttf", x["titulo"].upper() + "    ", 360, 30) for x in (antes, depois))
    f_tit = _fonte(fontes, "Montserrat-ExtraBold.ttf", tam_tit)  # título da coluna: até 30 px, cabendo em 360 px
    tam = min(_cabe(fontes, "Montserrat-Black.ttf", antes["valor"], 340, 100),
              _cabe(fontes, "Montserrat-Black.ttf", depois["valor"], 340, 100))
    f_preco = _fonte(fontes, "Montserrat-Black.ttf", tam)
    f_selo = _fonte(fontes, "Montserrat-Black.ttf", 36)
    XE, XD, YP = 262, 738, 285
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        _base(dr, fontes, c.get("rotulo"))
        rt = t - t_troca  # tempo desde a revelação
        # antes da coluna da direita entrar, o preço de sempre fica no centro e desliza para a esquerda com ela
        xe = XE if t_meio <= 0 else 500 + (XE - 500) * _ease((t - t_meio) / 0.35)
        # destaque verde atrás do preço novo
        if rt > 0:
            a = _ease(rt / 0.25)
            dr.rounded_rectangle([XD - 205, 148, XD + 205, 370], radius=22,
                                 fill=VERDE_CLARO[:3] + (int(255 * a),))
        # coluna da esquerda: o preço de sempre
        _espacado(dr, xe, 178, antes["titulo"].upper(), f_tit, 2.5, CINZA)
        cor_e = TINTA if rt <= 0 else tuple(int(TINTA[i] + (CINZA_CLARO[i] - TINTA[i]) * _ease(rt / 0.3)) for i in range(3)) + (255,)
        _texto_escalado(im, xe, YP, antes["valor"], f_preco, cor_e, 1.0)
        if rt > 0:  # risco vermelho, desenhado da esquerda para a direita
            larg = dr.textlength(antes["valor"], font=f_preco)
            x0, x1 = xe - larg / 2 - 12, xe + larg / 2 + 12
            xr = x0 + (x1 - x0) * _ease(rt / 0.28)
            dr.line([(x0, YP + 12), (xr, YP + 12 - (xr - x0) * 0.06)], fill=VERMELHO, width=11)
        # seta entre as colunas
        sa = _ease((t - t_meio) / 0.3)
        if sa > 0:
            dr.polygon([(486, YP - 20), (518, YP), (486, YP + 20)], fill=OURO[:3] + (int(255 * sa),))
        # coluna da direita: entra deslizando, com o preço escondido até a troca
        if t >= t_meio:
            p = _ease((t - t_meio) / 0.35)
            dx = int(60 * (1 - p)); alfa = int(255 * p)
            camada = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dc = ImageDraw.Draw(camada)
            _espacado(dc, XD, 178, depois["titulo"].upper(), f_tit, 2.5, VERDE if rt > 0 else CINZA)
            if rt <= 0:
                _texto_escalado(camada, XD, YP, "R$ ?", f_preco, CINZA_CLARO, 1.0)
            else:
                _texto_escalado(camada, XD, YP, "R$ ?", f_preco, CINZA_CLARO, 1.0, int(255 * (1 - _ease(rt / 0.12))))
                _texto_escalado(camada, XD, YP, depois["valor"], f_preco, VERDE, max(_pop(rt, 0.32, 0.14), 0.01))
            if alfa < 255:
                camada.putalpha(camada.getchannel("A").point(lambda v: v * alfa // 255))
            im.alpha_composite(camada, (dx, 0))
        # selo da diferença
        st = rt - 0.35
        if st > 0 and c.get("selo"):
            selo = c["selo"].upper()
            lw = dr.textlength(selo, font=f_selo)
            esc = _pop(st, 0.3, 0.1)
            cam = Image.new("RGBA", (int(lw + 80), 84), (0, 0, 0, 0)); dc = ImageDraw.Draw(cam)
            dc.rounded_rectangle([0, 0, lw + 80, 84], radius=42, fill=OURO)
            dc.text(((lw + 80) / 2, 42), selo, font=f_selo, fill=TINTA, anchor="mm")
            cam = cam.resize((max(1, int(cam.width * esc)), max(1, int(cam.height * esc))), Image.LANCZOS)
            im.alpha_composite(cam, (int(500 - cam.width / 2), int(452 - cam.height / 2)))
        elif c.get("legenda_baixo"):
            dr.text((500, 452), c["legenda_baixo"], font=_fonte(fontes, "Montserrat-Bold.ttf", 30), fill=CINZA, anchor="mm")
        _entrada(im, t).save(pasta / f"{q:04d}.png")
    return pasta


def quadros_conta(pasta, c, marcas, fps, fontes, numero_br):
    """Conta que monta: os termos entram um a um e o resultado sobe na palavra 'resultado'."""
    dura = c["dura"]
    t_res = marcas.get("resultado", 1.0)
    termos = c["termos"]                      # ex.: ["R$ 8,00", "400 kg"]
    linha = "  ×  ".join(termos)
    tam = _cabe(fontes, "Montserrat-Black.ttf", linha, 820, 92)
    f_termo = _fonte(fontes, "Montserrat-Black.ttf", tam)
    ate, casas, pre, suf = c["ate"], c.get("casas", 0), c.get("prefixo", ""), c.get("sufixo", "")
    final = pre + numero_br(ate, casas) + suf
    tam_r = _cabe(fontes, "Montserrat-Black.ttf", final, 820, 136)
    subida = c.get("subida", 0.9)
    med = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    larguras = [med.textlength(x, font=f_termo) for x in termos]
    lx = med.textlength("  ×  ", font=f_termo)
    total = sum(larguras) + lx * (len(termos) - 1)
    for q in range(int(round(dura * fps))):
        t = q / fps
        im = Image.new("RGBA", (1000, 580), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        _base(dr, fontes, c.get("rotulo"))
        x = 500 - total / 2
        for k, termo in enumerate(termos):  # cada termo entra 0,3 s depois do anterior
            p = _ease((t - 0.3 * k) / 0.3)
            if k:
                xm = x + lx / 2
                _texto_escalado(im, xm, 172, "×", f_termo, OURO, max(p, 0.01), int(255 * p))
                x += lx
            _texto_escalado(im, x + larguras[k] / 2 + 40 * (1 - p), 172, termo, f_termo, TINTA, 1.0, int(255 * p))
            x += larguras[k]
        rt = t - t_res
        if rt > -0.25:  # linha dourada da conta
            pl = _ease((rt + 0.25) / 0.25)
            dr.rounded_rectangle([200, 258, 200 + 600 * pl, 268], radius=5, fill=OURO)
        if rt > 0:
            pr = min(rt / subida, 1.0); e = _ease(pr)
            v = ate * e
            txt = final if pr >= 1 else pre + numero_br(v, casas) + suf
            pulso = 1.0
            if 0 <= rt - subida < 0.3: pulso = 1 + 0.06 * (1 - abs((rt - subida) / 0.15 - 1))
            _texto_escalado(im, 500, 362, txt, _fonte(fontes, "Montserrat-Black.ttf", tam_r * pulso), VERDE, 1.0)
            if c.get("detalhe") and rt > subida:
                a = int(255 * min((rt - subida) / 0.3, 1.0))
                dr.text((500, 470), c["detalhe"], font=_fonte(fontes, "Montserrat-Bold.ttf", 30), fill=CINZA[:3] + (a,), anchor="mm")
        _entrada(im, t).save(pasta / f"{q:04d}.png")
    return pasta
