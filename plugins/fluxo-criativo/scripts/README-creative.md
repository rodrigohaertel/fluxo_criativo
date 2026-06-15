# Processo Otimizado de Criacao de Criativos

## Objetivo
Gerar carrosseis, imagens estaticas e stories com o minimo de tokens na IDE (Claude Code).

## Arquitetura

```
Claude Code (gera copy + JSON)  -->  generate-creative.py (faz tudo sozinho)
         1 interacao                      execucao autonoma
```

**Principio:** Claude gera o conteudo (copy + config JSON). O script Python faz todo o resto (IA, HTML, screenshot). Zero volta pra IDE depois que o JSON esta pronto.

## Fluxo em 3 Passos

### Passo 1: Gerar Copy (Claude Code)
```
/copy-anuncio
```
Responde as perguntas. Claude gera a copy + JSON de config automaticamente.

### Passo 2: Revisar Config (opcional)
Abrir o arquivo JSON em `entregas/{produto}/anuncios/` e conferir textos.

### Passo 3: Gerar Imagens (terminal, sem Claude)
```bash
# Ver roteamento antes de gastar creditos
py -3 scripts/generate-creative.py --config entregas/{produto}/anuncios/{arquivo}.json --dry-run

# Gerar tudo
py -3 scripts/generate-creative.py --config entregas/{produto}/anuncios/{arquivo}.json

# Usar Freepik em vez de OpenRouter
py -3 scripts/generate-creative.py --config entregas/{produto}/anuncios/{arquivo}.json --provider freepik

# Regenerar so o texto (manter backgrounds IA ja gerados)
py -3 scripts/generate-creative.py --config entregas/{produto}/anuncios/{arquivo}.json --skip-ai
```

## Estrutura do JSON de Config

```json
{
  "template": "carrossel-slide.html",
  "colors": {"bg": "#0f0f0f", "text": "#ffffff", "accent": "#fbbf24"},
  "slides": [
    {
      "output": "nome-do-arquivo.png",
      "layout": "layout-gancho",
      "theme": "theme-dark",
      "headline": "Texto com **destaque** em accent",
      "subtitle": "Subtitulo opcional",
      "ai_prompt": "Prompt em ingles para gerar o background via IA"
    }
  ]
}
```

### Layouts Disponiveis
- `layout-gancho`: headline grande (slide 1)
- `layout-conteudo`: headline + corpo
- `layout-dado`: numero em destaque
- `layout-checklist`: lista com checkboxes
- `layout-comparacao`: dois blocos lado a lado
- `layout-cta`: call to action final

### Temas
- Prontos: `theme-dark`, `theme-light`, `theme-blue`, `theme-green`, `theme-warm`, `theme-red-soft`, `theme-green-soft`
- Custom: `theme-custom` + campo `colors` no JSON

### Texto com Destaque
Usar `**palavra**` no headline para aplicar a cor accent.

## Router de Modelos (OpenRouter)

O script escolhe automaticamente o melhor modelo por prompt:

| Tipo de visual | Modelo | Custo |
|---|---|---|
| Fotos reais, retratos | Gemini 3 Pro Image | ~$0.13 |
| Cenas complexas, infograficos | GPT-5 Image Mini | ~$0.02 |
| Backgrounds, texturas, gradientes | Gemini 3.1 Flash | ~$0.07 |

## Providers

| Provider | Chave no .env | Forte em | Quando usar |
|---|---|---|---|
| **OpenRouter** | `OPENROUTER_API_KEY` | Imagens (Gemini, GPT) | Padrao. Router inteligente |
| **Replicate** | `REPLICATE_API_TOKEN` | Imagens (Flux) + Videos | Fotorrealismo (Flux) e video |
| **Freepik** | `FREEPIK_API_KEY` | Imagens | Alternativa simples |

Com `--provider auto` (padrao), o script tenta: OpenRouter > Replicate > Freepik.

## Modelos Replicate (Imagem)

| Chave | Modelo | Uso |
|---|---|---|
| `photo` | black-forest-labs/flux-1.1-pro | Fotorrealismo (padrao) |
| `photo-max` | black-forest-labs/flux-2-pro | Qualidade maxima |
| `fast` | google/imagen-4-fast | Rapido e barato |
| `quality` | google/imagen-4 | Qualidade Google |
| `artistic` | recraft-ai/recraft-v4 | Estilizado, artistico |

Para usar modelo especifico do Replicate:
```bash
py -3 scripts/generate-creative.py --config {arquivo}.json --provider replicate --force-model black-forest-labs/flux-2-pro
```

## Modelos Replicate (Video)

| Chave | Modelo | Uso |
|---|---|---|
| `video` | kwaivgi/kling-v2.5-turbo-pro | Text-to-video (padrao) |
| `video-quality` | google/veo-3 | Qualidade maxima |
| `video-fast` | wan-video/wan-2.7-t2v | Rapido |
| `i2v` | kwaivgi/kling-v2.6 | Image-to-video |
| `i2v-fast` | wan-video/wan-2.7-i2v | Image-to-video rapido |

Video via Python:
```python
from generate_creative import generate_video_replicate
generate_video_replicate(api_key, "prompt do video", Path("saida.mp4"))
# Com imagem de referencia:
generate_video_replicate(api_key, "prompt", Path("saida.mp4"), image_path="slide.png")
```

## Economia de Tokens

| Acao | Tokens gastos |
|---|---|
| `/copy-anuncio` (gera copy + JSON) | ~5.000 |
| `py -3 scripts/generate-creative.py` (terminal) | 0 |
| Ajustar texto no JSON (editor) | 0 |
| `--skip-ai` (regenerar com texto novo) | 0 |
| **Total por carrossel** | **~5.000** |

Sem esse processo, cada iteracao de imagem gastava ~3.000 tokens.
Com 5 iteracoes de debug, chegava a 20.000 tokens por carrossel.

## Compatibilidade

- **Windows**: Edge ou Chrome (headless screenshot)
- **Mac**: Chrome ou Edge
- **Linux**: Chrome, Chromium ou Edge
- **Imagens**: OpenRouter (5 modelos) ou Freepik
- **Produtos**: generico, funciona para qualquer produto do sistema
