# Gera uma camada-guia PNG 1080x1920 com a zona segura do Instagram Reels.
# Uso: importar como camada por cima no CapCut enquanto edita, posicionar
# texto e numeros dentro do retangulo verde, e APAGAR a camada antes de exportar.

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# margens inseguras (pixels) na tela de 1080x1920
top = 150      # barra de status, audio, icones
bottom = 380   # legenda do post, @, nome do audio, botao (area mais critica)
left = 60
right = 120    # coluna de botoes (curtir, comentar, enviar, salvar)

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

red = (220, 40, 40, 95)       # bandas proibidas, translucido
green = (40, 200, 120, 235)   # contorno da area segura

# bandas inseguras
d.rectangle([0, 0, W, top], fill=red)
d.rectangle([0, H - bottom, W, H], fill=red)
d.rectangle([0, 0, left, H], fill=red)
d.rectangle([W - right, 0, W, H], fill=red)

# contorno da area segura (linha verde grossa)
safe = [left, top, W - right, H - bottom]
for i in range(7):
    d.rectangle([safe[0] + i, safe[1] + i, safe[2] - i, safe[3] - i], outline=green)

# fontes
try:
    f_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 48)
    f_med = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
except Exception:
    f_big = ImageFont.load_default()
    f_med = f_big


def centro(cx, cy, texto, fonte, cor):
    bbox = d.textbbox((0, 0), texto, font=fonte)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw / 2, cy - th / 2), texto, font=fonte, fill=cor)


branco = (255, 255, 255, 235)
centro(W / 2, H / 2 - 20, "ZONA SEGURA", f_big, branco)
centro(W / 2, H / 2 + 35, "texto e números aqui dentro", f_med, (235, 235, 235, 215))

centro(W / 2, top / 2, "EVITE: topo (barra e áudio)", f_med, branco)
centro(W / 2, H - bottom / 2, "EVITE: legenda, @ e botão do post", f_med, branco)
centro(W - right / 2, top + 60, "botões", f_med, branco)

out = ("C:/Users/rodri/OneDrive/Documentos/Claude/Projects/fluxo-criativo/"
       "meus-produtos/linha-editorial/entregas/reels/_GUIA_zona-segura_1080x1920.png")
img.save(out)
print("salvo:", out)
