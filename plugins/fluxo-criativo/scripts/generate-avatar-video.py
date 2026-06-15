# -*- coding: utf-8 -*-
"""
Gera video de avatar falante via Replicate (Kling Avatar V2).

Envia foto + audio e recebe video com lip sync.

Uso:
  py -3 scripts/generate-avatar-video.py --foto minha-foto.jpg --audio roteiro.mp3
  py -3 scripts/generate-avatar-video.py --foto minha-foto.jpg --audio roteiro.mp3 --output meu-video.mp4
  py -3 scripts/generate-avatar-video.py --foto minha-foto.jpg --audio roteiro.mp3 --model kwaivgi/kling-avatar-v2

Requisitos:
  - REPLICATE_API_TOKEN no .env
  - Foto: frente, rosto visivel, boa iluminacao (jpg/png)
  - Audio: gravacao lendo o roteiro (mp3/wav/m4a)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_creative import load_env_file, generate_avatar_video_replicate
import os


def main() -> int:
    load_env_file(ROOT / ".env")

    ap = argparse.ArgumentParser(description="Gera video avatar falante (foto + audio)")
    ap.add_argument("--foto", required=True, help="Caminho da foto do expert (jpg/png)")
    ap.add_argument("--audio", required=True, help="Caminho do audio gravado (mp3/wav/m4a)")
    ap.add_argument("--output", default="", help="Caminho do video de saida (padrao: meus-produtos/{ativo}/entregas/videos/)")
    ap.add_argument("--model", default="kwaivgi/kling-avatar-v2", help="Modelo Replicate")
    args = ap.parse_args()

    api_key = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not api_key:
        print("REPLICATE_API_TOKEN nao encontrada no .env", file=sys.stderr)
        print("Obtenha em: https://replicate.com/account/api-tokens")
        return 1

    foto = Path(args.foto)
    if not foto.exists():
        # Tentar caminho relativo ao ROOT
        foto = ROOT / args.foto
    if not foto.exists():
        print(f"Foto nao encontrada: {args.foto}", file=sys.stderr)
        return 1

    audio = Path(args.audio)
    if not audio.exists():
        audio = ROOT / args.audio
    if not audio.exists():
        print(f"Audio nao encontrado: {args.audio}", file=sys.stderr)
        return 1

    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = ROOT / args.output
    else:
        # Salvar na pasta de videos do produto ativo
        ativo_file = ROOT / "meus-produtos" / ".ativo"
        if ativo_file.exists():
            slug = ativo_file.read_text(encoding="utf-8").strip()
        else:
            slug = "geral"
        output_dir = ROOT / "meus-produtos" / slug / "entregas" / "videos"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"avatar-{foto.stem}.mp4"

    print(f"Foto:   {foto}")
    print(f"Audio:  {audio}")
    print(f"Modelo: {args.model}")
    print(f"Saida:  {output}")
    print()

    ok = generate_avatar_video_replicate(api_key, str(foto), str(audio), output, args.model)

    if ok:
        print(f"\nVideo salvo em: {output}")
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"Tamanho: {size_mb:.1f} MB")
        return 0
    else:
        print("\nFalha na geracao do video.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
