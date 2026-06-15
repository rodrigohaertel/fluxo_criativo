"""
Otimiza um arquivo MP4 para scrubbing perfeito controlado por scroll.

Re-encoda o vídeo com um keyframe em cada frame (keyint=1), o que permite
o navegador buscar qualquer frame instantaneamente quando o JS faz seek
via video.currentTime. Ideal para hero de página com vídeo controlado por scroll.

Uso:
    py -3 scripts/otimizar-video-scrub.py caminho/do/video.mp4
    python3 scripts/otimizar-video-scrub.py caminho/do/video.mp4

O arquivo otimizado é salvo no mesmo diretório com sufixo "-scrub.mp4".
Cross-platform. Roda em Windows, macOS e Linux sem precisar instalar
ffmpeg manualmente (usa o pacote imageio-ffmpeg como fallback).
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def garantir_imageio_ffmpeg():
    """Instala imageio-ffmpeg via pip se nao estiver disponivel."""
    try:
        import imageio_ffmpeg  # noqa: F401
        return
    except ImportError:
        pass
    print("Instalando imageio-ffmpeg (primeira vez)...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "imageio-ffmpeg"],
        check=True,
    )


def localizar_ffmpeg():
    """Retorna o caminho do executavel ffmpeg.
    Prioriza o ffmpeg do sistema (mais rapido). Cai pro bundled se nao achar.
    """
    sistema = shutil.which("ffmpeg")
    if sistema:
        return sistema
    garantir_imageio_ffmpeg()
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def otimizar(entrada: Path) -> Path:
    if not entrada.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {entrada}")
    if entrada.suffix.lower() not in (".mp4", ".mov", ".webm", ".mkv"):
        raise ValueError(f"Formato nao suportado: {entrada.suffix}")

    saida = entrada.with_name(entrada.stem + "-scrub.mp4")
    ffmpeg = localizar_ffmpeg()

    print(f"FFmpeg em uso: {ffmpeg}")
    print(f"Otimizando: {entrada.name}")
    print(f"Destino:    {saida.name}")
    print()

    cmd = [
        ffmpeg,
        "-y",
        "-i", str(entrada),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "22",
        "-g", "1",
        "-keyint_min", "1",
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        str(saida),
    ]

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise RuntimeError("FFmpeg falhou. Veja a saida acima.")

    tamanho_orig = entrada.stat().st_size / (1024 * 1024)
    tamanho_novo = saida.stat().st_size / (1024 * 1024)
    print()
    print(f"Pronto. {entrada.name}: {tamanho_orig:.1f}MB -> {saida.name}: {tamanho_novo:.1f}MB")
    print(f"Caminho final: {saida}")
    return saida


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    entrada = Path(sys.argv[1]).resolve()
    try:
        otimizar(entrada)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
