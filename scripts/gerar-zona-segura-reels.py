# Gera uma camada-guia PNG 1080x1920 com a zona segura do Instagram Reels.
# Uso: importar como camada por cima no CapCut enquanto edita, posicionar
# texto e numeros dentro do retangulo verde, e APAGAR a camada antes de exportar.
#
# ATUALIZADO EM SETEMBRO/2026 com as margens oficiais da Meta para Reels:
#   topo 14%, base 35%, laterais 6% (em 1080x1920 = 269px, 672px, 65px).
# A versao anterior reservava so 150px no topo e 380px na base, o que deixava
# quase 300px de risco na parte de baixo (legenda, audio, botoes e CTA).
#
# Excecao proposital: a lateral DIREITA usa 130px em vez dos 65px oficiais,
# porque a coluna de botoes do Reel organico (curtir, comentar, enviar, salvar,
# perfil) ocupa mais do que os 6% previstos para anuncio.

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# margens inseguras (pixels) na tela de 1080x1920
top = 269       # 14% - barra de status, nome da conta, foto de perfil
bottom = 672    # 35% - legenda, @, audio, curtir/comentar/salvar e o CTA do anuncio
left = 65       # 6%
right = 130     # 12% - coluna de botoes do Reel organico (mais larga que os 6% do anuncio)

safe_w = W - left - right
safe_h = H - top - bottom

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
    f_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 52)
    f_med = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
    f_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
except Exception:
    f_big = ImageFont.load_default()
    f_med = f_big
    f_small = f_big


def centro(cx, cy, texto, fonte, cor):
    bbox = d.textbbox((0, 0), texto, font=fonte)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw / 2, cy - th / 2), texto, font=fonte, fill=cor)


branco = (255, 255, 255, 235)
cinza = (235, 235, 235, 215)

# miolo: identificacao da area util
# cor verde (a mesma do contorno) para o texto aparecer tanto na previa
# quanto por cima de video claro ou escuro no CapCut
verde_txt = (16, 150, 90, 230)
meio_y = top + safe_h / 2
centro(W / 2, meio_y - 45, "ZONA SEGURA", f_big, verde_txt)
centro(W / 2, meio_y + 15, "texto e números aqui dentro", f_med, verde_txt)
centro(W / 2, meio_y + 65, f"{safe_w} x {safe_h} px", f_small, verde_txt)

# faixas proibidas, com o numero para conferencia
centro(W / 2, top / 2 - 20, "EVITE: topo", f_med, branco)
centro(W / 2, top / 2 + 20, f"269 px (14%) · barra, perfil", f_small, cinza)

centro(W / 2, H - bottom / 2 - 30, "EVITE: base", f_med, branco)
centro(W / 2, H - bottom / 2 + 10, "672 px (35%)", f_small, cinza)
centro(W / 2, H - bottom / 2 + 45, "legenda, @, áudio, botões e CTA", f_small, cinza)

centro(W - right / 2, top + 120, "botões", f_small, branco)

# rodape com a referencia
centro(W / 2, H - 40, "Meta Reels 2026 · topo 14% · base 35% · laterais 6%", f_small, cinza)

out = ("C:/Users/rodri/OneDrive/Documentos/Claude/Projects/fluxo-criativo/"
       "meus-produtos/linha-editorial/entregas/reels/_GUIA_zona-segura_1080x1920.png")
img.save(out)
print("salvo:", out)
print(f"area util: {safe_w} x {safe_h} px  (topo {top}, base {bottom}, esq {left}, dir {right})")
