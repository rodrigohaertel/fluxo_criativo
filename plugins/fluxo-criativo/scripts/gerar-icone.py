"""Gera os arquivos de ícone do Workshop IA para Mac (.icns) e Windows (.ico)."""
import os
import struct
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
BUILD  = os.path.join(ROOT, 'build')
ICONSET = os.path.join(BUILD, 'icon.iconset')

os.makedirs(ASSETS, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)
os.makedirs(ICONSET, exist_ok=True)

# ── Paleta (igual ao design system do app) ───────────────────────────────────
BG       = (11, 11, 11, 255)   # --ink-2
BORDER   = (38, 38, 38, 255)   # --line-2
NEON     = (196, 255, 94, 255) # --neon
TEXT     = (255, 255, 255, 255)

def draw_icon(size: int) -> Image.Image:
    img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r = int(size * 0.18)  # raio do arredondamento

    # Fundo arredondado
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=BG)

    # Borda sutil
    draw.rounded_rectangle([1, 1, size - 2, size - 2], radius=r, outline=BORDER, width=max(1, size // 80))

    # Ponto neon (canto superior esquerdo, como na UI)
    dot_r   = int(size * 0.06)
    dot_cx  = int(size * 0.22)
    dot_cy  = int(size * 0.22)
    draw.ellipse(
        [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
        fill=NEON
    )

    # "W" centralizado em branco
    font_size = int(size * 0.46)
    font = None
    for path in ['/System/Library/Fonts/Geneva.ttf', '/System/Library/Fonts/SFNSMono.ttf']:
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    letter = 'W'
    bbox   = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx     = (size - tw) // 2 - bbox[0]
    ty     = (size - th) // 2 - bbox[1] + int(size * 0.04)
    draw.text((tx, ty), letter, font=font, fill=TEXT)

    return img

# ── Gerar PNG master 1024×1024 ───────────────────────────────────────────────
master = draw_icon(1024)
master_path = os.path.join(BUILD, 'icon.png')
master.save(master_path, 'PNG')
print(f'PNG master: {master_path}')

# ── Gerar iconset para macOS ─────────────────────────────────────────────────
SIZES = [16, 32, 64, 128, 256, 512, 1024]
for s in SIZES:
    img = draw_icon(s)
    img.save(os.path.join(ICONSET, f'icon_{s}x{s}.png'))
    if s <= 512:
        img2x = draw_icon(s * 2)
        img2x.save(os.path.join(ICONSET, f'icon_{s}x{s}@2x.png'))

result = subprocess.run(
    ['iconutil', '-c', 'icns', ICONSET, '-o', os.path.join(BUILD, 'icon.icns')],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f'ICNS: {os.path.join(BUILD, "icon.icns")}')
else:
    print(f'Erro iconutil: {result.stderr}')

# ── Gerar ICO para Windows (multi-resolução, base 256×256) ───────────────────
ico_sizes = [16, 24, 32, 48, 64, 128, 256]
base256   = draw_icon(256).convert('RGBA')
ico_path  = os.path.join(ASSETS, 'icon.ico')
base256.save(
    ico_path, format='ICO',
    sizes=[(s, s) for s in ico_sizes]
)
print(f'ICO: {ico_path}')

# Limpar iconset temporário
shutil.rmtree(ICONSET)
print('Concluído.')
