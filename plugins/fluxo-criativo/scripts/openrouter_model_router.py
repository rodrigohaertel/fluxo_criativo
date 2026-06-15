# -*- coding: utf-8 -*-
"""
Router inteligente de modelos de imagem para OpenRouter.

Analisa o prompt e a direcao criativa de cada imagem e seleciona
o modelo com melhor custo-beneficio para aquele tipo de visual.

Modelos confirmados no OpenRouter (abril 2026):
  google/gemini-3.1-flash-image-preview   (rapido, barato, bom geral)
  google/gemini-3-pro-image-preview       (qualidade maxima Google)
  google/gemini-2.5-flash-image           (legado, barato)
  openai/gpt-5-image-mini                 (texto, composicoes, cenas complexas)
  openai/gpt-5-image                      (qualidade maxima OpenAI)

Uso como modulo:
    from openrouter_model_router import route_model, classify_prompt, MODELS

Uso standalone (teste):
    py -3 scripts/openrouter_model_router.py "photorealistic portrait of a woman"
    py -3 scripts/openrouter_model_router.py --all
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelSpec:
    model_id: str
    name: str
    strengths: list[str]
    cost_per_image_usd: float
    speed_tier: str  # "fast", "medium", "slow"
    notes: str


# Apenas modelos CONFIRMADOS funcionando no OpenRouter via chat/completions
MODELS: dict[str, ModelSpec] = {
    "gemini-3.1-flash": ModelSpec(
        model_id="google/gemini-3.1-flash-image-preview",
        name="Gemini 3.1 Flash Image",
        strengths=["abstract", "gradient", "texture", "mood", "atmospheric",
                    "geometric", "pattern", "clean", "minimal", "fast_proto"],
        cost_per_image_usd=0.067,
        speed_tier="fast",
        notes="Rapido e barato. Bom para backgrounds, texturas, gradientes e elementos abstratos.",
    ),
    "gemini-3-pro": ModelSpec(
        model_id="google/gemini-3-pro-image-preview",
        name="Gemini 3 Pro Image",
        strengths=["photorealistic", "portrait", "product", "studio",
                    "high_fidelity", "detail", "lighting"],
        cost_per_image_usd=0.134,
        speed_tier="medium",
        notes="Qualidade maxima Google. Melhor para fotos reais, retratos e cenas detalhadas.",
    ),
    "gpt-5-image-mini": ModelSpec(
        model_id="openai/gpt-5-image-mini",
        name="GPT-5 Image Mini",
        strengths=["text_render", "composed", "designed", "layout", "typography",
                    "mockup", "marketing", "ad_creative", "complex_scene",
                    "infographic", "icon", "chart"],
        cost_per_image_usd=0.02,
        speed_tier="fast",
        notes="Melhor para composicoes com multiplos elementos, infograficos e cenas complexas. "
              "Mais barato do catalogo.",
    ),
    "gpt-5-image": ModelSpec(
        model_id="openai/gpt-5-image",
        name="GPT-5 Image",
        strengths=["photorealistic", "text_render", "composed", "artistic",
                    "creative", "high_fidelity", "complex_scene"],
        cost_per_image_usd=0.08,
        speed_tier="medium",
        notes="Qualidade maxima OpenAI. Fotorrealismo + composicoes complexas + texto legivel.",
    ),
}


# Palavras-chave por categoria visual
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "photorealistic": [
        r"photorealistic", r"photo\b", r"portrait", r"headshot", r"real person",
        r"product shot", r"studio light", r"natural skin", r"editorial photo",
        r"shallow depth", r"bokeh", r"dslr", r"camera", r"realistic face",
        r"professional photo", r"candid", r"lifestyle photo", r"overhead view",
    ],
    "complex_scene": [
        r"mockup", r"marketing material", r"ad creative", r"advertisement",
        r"composed scene", r"multiple elements", r"product display",
        r"scene with text", r"branded", r"layout", r"designed",
        r"banner", r"social media ad", r"promotional",
        r"desk scene", r"workspace", r"environment", r"split composition",
    ],
    "infographic": [
        r"infographic", r"icon\b", r"icons\b", r"flat\b", r"chart\b", r"graph\b",
        r"diagram", r"checkbox", r"checklist", r"comparison", r"versus",
        r"side by side", r"split", r"data viz", r"bar chart", r"pie chart",
        r"dashboard", r"metric", r"indicator", r"visualization",
    ],
    "abstract_mood": [
        r"abstract", r"gradient", r"texture", r"mood", r"atmospheric",
        r"geometric", r"pattern", r"glass morphism", r"frosted glass",
        r"3d render", r"isometric", r"fluent design", r"particles",
        r"bokeh", r"light effects", r"cinematic", r"dark.*background",
        r"glowing", r"floating", r"streams", r"minimal.*dark",
    ],
    "artistic": [
        r"illustration", r"artistic", r"stylized", r"creative", r"collage",
        r"surreal", r"concept art", r"digital art", r"painting",
        r"watercolor", r"sketch",
    ],
}

# Categoria -> modelo preferido
CATEGORY_TO_MODEL: dict[str, str] = {
    "photorealistic": "gemini-3-pro",
    "complex_scene": "gpt-5-image-mini",
    "infographic": "gpt-5-image-mini",
    "abstract_mood": "gemini-3.1-flash",
    "artistic": "gpt-5-image-mini",
}

DEFAULT_MODEL = "gemini-3.1-flash"


def classify_prompt(prompt: str) -> dict[str, Any]:
    prompt_lower = prompt.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            matches = re.findall(kw, prompt_lower)
            score += len(matches)
        scores[category] = score

    total_matches = sum(scores.values())
    if total_matches == 0:
        return {
            "category": "general",
            "confidence": 0.3,
            "scores": scores,
            "model_key": DEFAULT_MODEL,
            "model_id": MODELS[DEFAULT_MODEL].model_id,
            "reasoning": "Nenhum padrao detectado. Usando modelo padrao.",
        }

    best_category = max(scores, key=lambda k: scores[k])
    best_score = scores[best_category]
    confidence = round(best_score / total_matches, 2) if total_matches > 0 else 0.3

    if confidence < 0.4:
        model_key = DEFAULT_MODEL
        reasoning = f"Classificacao mista ({best_category} {confidence:.0%}). Modelo padrao."
    else:
        model_key = CATEGORY_TO_MODEL.get(best_category, DEFAULT_MODEL)
        reasoning = f"{best_category} ({confidence:.0%}) -> {MODELS[model_key].name}"

    return {
        "category": best_category,
        "confidence": confidence,
        "scores": scores,
        "model_key": model_key,
        "model_id": MODELS[model_key].model_id,
        "reasoning": reasoning,
    }


def route_model(prompt: str, force_model: str = "") -> str:
    if force_model:
        for key, spec in MODELS.items():
            if force_model in (key, spec.model_id):
                return spec.model_id
        return force_model
    return classify_prompt(prompt)["model_id"]


def route_batch(jobs: list[dict[str, Any]], force_model: str = "") -> list[dict[str, Any]]:
    for job in jobs:
        if force_model:
            job["model_id"] = route_model("", force_model=force_model)
            job["category"] = "forced"
        else:
            result = classify_prompt(job.get("prompt", job.get("ai_prompt", "")))
            job["model_id"] = result["model_id"]
            job["category"] = result["category"]
    return jobs


TEST_PROMPTS = [
    "Photorealistic portrait of a Brazilian woman, small business owner, 30s, warm smile",
    "Dark moody financial background, abstract golden coins floating, bokeh light effects, cinematic",
    "Abstract dark background with blue and gold light streams, cinematic lighting",
    "Overhead view of a messy desk with spreadsheet printouts, calculator, dim moody lighting, photorealistic",
    "Abstract split composition, warm golden tones left, cool blue right, dark background, cinematic",
    "Clean abstract visualization of four ascending bar charts made of blue light, minimal",
    "Elegant minimal dark background with glowing geometric pattern repeating in a grid",
    "Instagram CTA slide design: soft blue gradient background with save and follow icons",
]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        for p in TEST_PROMPTS:
            r = classify_prompt(p)
            print(f"{p[:75]}...")
            print(f"  -> {r['category']} ({r['confidence']:.0%}) -> {r['model_id']}\n")
    elif len(sys.argv) > 1:
        p = " ".join(sys.argv[1:])
        r = classify_prompt(p)
        print(f"Categoria: {r['category']} ({r['confidence']:.0%})")
        print(f"Modelo: {r['model_id']}")
    else:
        print("Uso: py -3 scripts/openrouter_model_router.py \"prompt\"")
        print("      py -3 scripts/openrouter_model_router.py --all")
