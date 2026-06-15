#!/usr/bin/env python3
"""
gerar-sprites-bonecos.py

Gera 7 sprite sheets placeholder pros bonecos da Sala dos Agentes.
Layout RPG Maker (96x128 px, 4 frames horizontais x 4 direcoes verticais):

    Linha 0 (y=0):   facing DOWN   (frente)
    Linha 1 (y=32):  facing LEFT
    Linha 2 (y=64):  facing RIGHT
    Linha 3 (y=96):  facing UP     (costas)

    Coluna 0: walk-1 (perna direita a frente)
    Coluna 1: idle / stand
    Coluna 2: walk-2 (perna esquerda a frente)
    Coluna 3: idle / stand (mesmo do col 1)

Cada frame e 24x32 px. Boneco simples, com:
  - cabeca/cabelo
  - tronco (cor da categoria)
  - bracos
  - pernas
  - sombra

Salva em painel/sala-assets/bonecos/{cat}.png
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "painel" / "sala-assets" / "bonecos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FRAME_W, FRAME_H = 24, 32
COLS, ROWS = 4, 4
SHEET_W, SHEET_H = FRAME_W * COLS, FRAME_H * ROWS

# Personagens
CHARS = [
    {"id": "prod",  "shirt": (196, 255,  94), "hair": ( 70,  70,  70)},
    {"id": "copy",  "shirt": (255, 255, 255), "hair": ( 40,  40,  40)},
    {"id": "pag",   "shirt": (158, 201,  71), "hair": (110,  60,  30)},
    {"id": "ad",    "shirt": (212, 162,  74), "hair": ( 30,  20,  10)},
    {"id": "vid",   "shirt": (217, 119,  87), "hair": ( 80,  40,  30)},
    {"id": "sales", "shirt": (207, 207, 203), "hair": (140,  90,  50)},
    {"id": "data",  "shirt": (122, 168, 201), "hair": ( 60,  60,  90)},
]

SKIN = (245, 214, 179)
PANTS = (60, 60, 70)
BOOTS = (30, 30, 30)
SHADOW = (0, 0, 0, 80)


def draw_shadow(draw, x, y):
    # Elipse achatada sob os pes
    draw.ellipse((x + 4, y + 28, x + 19, y + 31), fill=SHADOW)


def draw_down(draw, x, y, c, leg_offset=0):
    """Boneco de frente. leg_offset: -1 (perna dir frente), 0 (parado), +1 (perna esq frente)."""
    s = c["shirt"]
    h = c["hair"]
    draw_shadow(draw, x, y)
    # cabelo (topo)
    draw.rectangle((x + 8, y + 2, x + 15, y + 10), fill=h)
    # rosto
    draw.rectangle((x + 9, y + 6, x + 14, y + 12), fill=SKIN)
    # olhos (2 pixels pretos)
    draw.point((x + 10, y + 9), fill=(20, 20, 20))
    draw.point((x + 13, y + 9), fill=(20, 20, 20))
    # tronco (camisa)
    draw.rectangle((x + 7, y + 13, x + 16, y + 22), fill=s)
    # bracos (laterais do tronco)
    draw.rectangle((x + 5, y + 14, x + 6, y + 21), fill=s)
    draw.rectangle((x + 17, y + 14, x + 18, y + 21), fill=s)
    # maos
    draw.rectangle((x + 5, y + 21, x + 6, y + 22), fill=SKIN)
    draw.rectangle((x + 17, y + 21, x + 18, y + 22), fill=SKIN)
    # pernas
    if leg_offset == 0:
        draw.rectangle((x + 8, y + 23, x + 11, y + 28), fill=PANTS)
        draw.rectangle((x + 12, y + 23, x + 15, y + 28), fill=PANTS)
        draw.rectangle((x + 8, y + 28, x + 11, y + 30), fill=BOOTS)
        draw.rectangle((x + 12, y + 28, x + 15, y + 30), fill=BOOTS)
    elif leg_offset == -1:
        # perna direita (do espectador = boneco esquerda) a frente
        draw.rectangle((x + 8, y + 23, x + 11, y + 27), fill=PANTS)
        draw.rectangle((x + 12, y + 24, x + 15, y + 28), fill=PANTS)
        draw.rectangle((x + 8, y + 27, x + 11, y + 29), fill=BOOTS)
        draw.rectangle((x + 12, y + 28, x + 15, y + 30), fill=BOOTS)
    else:  # +1
        draw.rectangle((x + 8, y + 24, x + 11, y + 28), fill=PANTS)
        draw.rectangle((x + 12, y + 23, x + 15, y + 27), fill=PANTS)
        draw.rectangle((x + 8, y + 28, x + 11, y + 30), fill=BOOTS)
        draw.rectangle((x + 12, y + 27, x + 15, y + 29), fill=BOOTS)


def draw_up(draw, x, y, c, leg_offset=0):
    """Costas: cabelo na frente, sem rosto."""
    s = c["shirt"]
    h = c["hair"]
    draw_shadow(draw, x, y)
    # cabeca toda de cabelo
    draw.rectangle((x + 8, y + 2, x + 15, y + 12), fill=h)
    # nuca (pequeno detalhe de pele entre cabelo e camisa)
    draw.rectangle((x + 10, y + 12, x + 13, y + 13), fill=SKIN)
    # tronco (camisa de costas)
    draw.rectangle((x + 7, y + 13, x + 16, y + 22), fill=s)
    # bracos
    draw.rectangle((x + 5, y + 14, x + 6, y + 21), fill=s)
    draw.rectangle((x + 17, y + 14, x + 18, y + 21), fill=s)
    draw.rectangle((x + 5, y + 21, x + 6, y + 22), fill=SKIN)
    draw.rectangle((x + 17, y + 21, x + 18, y + 22), fill=SKIN)
    # pernas (mesmo padrao do down)
    if leg_offset == 0:
        draw.rectangle((x + 8, y + 23, x + 11, y + 28), fill=PANTS)
        draw.rectangle((x + 12, y + 23, x + 15, y + 28), fill=PANTS)
        draw.rectangle((x + 8, y + 28, x + 11, y + 30), fill=BOOTS)
        draw.rectangle((x + 12, y + 28, x + 15, y + 30), fill=BOOTS)
    elif leg_offset == -1:
        draw.rectangle((x + 8, y + 23, x + 11, y + 27), fill=PANTS)
        draw.rectangle((x + 12, y + 24, x + 15, y + 28), fill=PANTS)
        draw.rectangle((x + 8, y + 27, x + 11, y + 29), fill=BOOTS)
        draw.rectangle((x + 12, y + 28, x + 15, y + 30), fill=BOOTS)
    else:
        draw.rectangle((x + 8, y + 24, x + 11, y + 28), fill=PANTS)
        draw.rectangle((x + 12, y + 23, x + 15, y + 27), fill=PANTS)
        draw.rectangle((x + 8, y + 28, x + 11, y + 30), fill=BOOTS)
        draw.rectangle((x + 12, y + 27, x + 15, y + 29), fill=BOOTS)


def draw_side_right(draw, x, y, c, leg_offset=0):
    """Perfil olhando pra direita."""
    s = c["shirt"]
    h = c["hair"]
    draw_shadow(draw, x, y)
    # cabeca (perfil): cabelo cobre topo + atras
    draw.rectangle((x + 9, y + 2, x + 14, y + 11), fill=h)
    # rosto perfil (olho a direita)
    draw.rectangle((x + 12, y + 6, x + 15, y + 12), fill=SKIN)
    draw.rectangle((x + 11, y + 8, x + 12, y + 11), fill=SKIN)  # bochecha
    draw.point((x + 14, y + 9), fill=(20, 20, 20))  # olho
    # tronco
    draw.rectangle((x + 9, y + 13, x + 14, y + 22), fill=s)
    # braco da frente (em movimento se walking)
    if leg_offset == -1:
        # braco pra tras
        draw.rectangle((x + 8, y + 14, x + 9, y + 21), fill=s)
        draw.rectangle((x + 14, y + 16, x + 16, y + 21), fill=s)  # braco frente avancado
    elif leg_offset == 1:
        draw.rectangle((x + 7, y + 16, x + 9, y + 21), fill=s)  # braco tras avancado
        draw.rectangle((x + 14, y + 14, x + 15, y + 21), fill=s)
    else:
        draw.rectangle((x + 8, y + 14, x + 9, y + 21), fill=s)
        draw.rectangle((x + 14, y + 14, x + 15, y + 21), fill=s)
    # mao (so a da frente fica visivel)
    draw.point((x + 15, y + 21), fill=SKIN)
    # pernas (perfil)
    if leg_offset == 0:
        draw.rectangle((x + 10, y + 23, x + 12, y + 28), fill=PANTS)
        draw.rectangle((x + 12, y + 23, x + 14, y + 28), fill=PANTS)
        draw.rectangle((x + 10, y + 28, x + 14, y + 30), fill=BOOTS)
    elif leg_offset == -1:
        # perna esq da frente, dir atras
        draw.rectangle((x + 10, y + 23, x + 12, y + 27), fill=PANTS)
        draw.rectangle((x + 13, y + 24, x + 14, y + 29), fill=PANTS)
        draw.rectangle((x + 9, y + 27, x + 12, y + 29), fill=BOOTS)
        draw.rectangle((x + 13, y + 29, x + 15, y + 30), fill=BOOTS)
    else:
        draw.rectangle((x + 10, y + 24, x + 12, y + 29), fill=PANTS)
        draw.rectangle((x + 13, y + 23, x + 14, y + 27), fill=PANTS)
        draw.rectangle((x + 9, y + 29, x + 12, y + 30), fill=BOOTS)
        draw.rectangle((x + 13, y + 27, x + 15, y + 29), fill=BOOTS)


def draw_side_left(draw, x, y, c, leg_offset=0):
    """Espelha o side_right horizontalmente."""
    # Cria um sub-canvas com side_right e flipa
    tmp = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    tmp_draw = ImageDraw.Draw(tmp)
    draw_side_right(tmp_draw, 0, 0, c, leg_offset)
    flipped = tmp.transpose(Image.FLIP_LEFT_RIGHT)
    # cola no destino
    img = draw._image  # acesso ao Image atraves do Draw
    img.paste(flipped, (x, y), flipped)


def gerar_personagem(c):
    img = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Linha 0: facing DOWN
    draw_down(draw, 0 * FRAME_W, 0, c, leg_offset=-1)  # walk-1
    draw_down(draw, 1 * FRAME_W, 0, c, leg_offset=0)   # idle
    draw_down(draw, 2 * FRAME_W, 0, c, leg_offset=+1)  # walk-2
    draw_down(draw, 3 * FRAME_W, 0, c, leg_offset=0)   # idle (mesmo do col 1)

    # Linha 1: facing LEFT
    draw_side_left(draw, 0 * FRAME_W, 1 * FRAME_H, c, leg_offset=-1)
    draw_side_left(draw, 1 * FRAME_W, 1 * FRAME_H, c, leg_offset=0)
    draw_side_left(draw, 2 * FRAME_W, 1 * FRAME_H, c, leg_offset=+1)
    draw_side_left(draw, 3 * FRAME_W, 1 * FRAME_H, c, leg_offset=0)

    # Linha 2: facing RIGHT
    draw_side_right(draw, 0 * FRAME_W, 2 * FRAME_H, c, leg_offset=-1)
    draw_side_right(draw, 1 * FRAME_W, 2 * FRAME_H, c, leg_offset=0)
    draw_side_right(draw, 2 * FRAME_W, 2 * FRAME_H, c, leg_offset=+1)
    draw_side_right(draw, 3 * FRAME_W, 2 * FRAME_H, c, leg_offset=0)

    # Linha 3: facing UP
    draw_up(draw, 0 * FRAME_W, 3 * FRAME_H, c, leg_offset=-1)
    draw_up(draw, 1 * FRAME_W, 3 * FRAME_H, c, leg_offset=0)
    draw_up(draw, 2 * FRAME_W, 3 * FRAME_H, c, leg_offset=+1)
    draw_up(draw, 3 * FRAME_W, 3 * FRAME_H, c, leg_offset=0)

    out = OUT_DIR / f"{c['id']}.png"
    img.save(out, "PNG")
    return out


def main():
    print(f"Gerando {len(CHARS)} sprites em {OUT_DIR}...")
    for c in CHARS:
        out = gerar_personagem(c)
        print(f"  - {out.name}")
    print("Pronto.")


if __name__ == "__main__":
    main()
