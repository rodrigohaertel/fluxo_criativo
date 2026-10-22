# Transcreve fala por fala: corta o áudio nos silêncios e transcreve cada trecho separado.
# Transcrever o vídeo inteiro de uma vez deixa o Whisper "fundir" duas tentativas da mesma frase
# (no R026, "a referência que eu utilizo" dita duas vezes virou uma frase só, com o "32%" esticado por 5 s).
# Uso: py -3 transcrever_por_fala.py audio16k.wav palavras.json ["texto do roteiro para orientar a grafia"]
import json, os, re, subprocess, sys, time, wave
from pathlib import Path

def _registrar_dlls_cuda():
    try:
        import nvidia
    except ImportError:
        return
    for base in nvidia.__path__:
        for pasta in Path(base).glob("*/bin"):
            os.add_dll_directory(str(pasta))
            os.environ["PATH"] = str(pasta) + os.pathsep + os.environ.get("PATH", "")

_registrar_dlls_cuda()
import numpy as np
from faster_whisper import WhisperModel

audio, saida = sys.argv[1], sys.argv[2]
prompt = sys.argv[3] if len(sys.argv) > 3 else None
SILENCIO_MIN = 0.6  # pausa que separa uma fala da outra
t0 = time.time()

wf = wave.open(audio)
dados = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
dur = len(dados) / 16000
# limiar do silêncio relativo ao ruído do lugar: 12 dB acima do fundo (em sala silenciosa fica perto de -40 dB;
# em salão de restaurante, com ruído, -40 dB não acha pausa nenhuma, como no A52)
q = dados[: len(dados) // 160 * 160].reshape(-1, 160)
nivel = 20 * np.log10(np.sqrt((q ** 2).mean(1)) + 1e-9)
LIMIAR = max(-40.0, float(np.percentile(nivel[nivel > -90], 10)) + 12) if (nivel > -90).any() else -40.0
txt = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", f"silencedetect=noise={LIMIAR:.1f}dB:d={SILENCIO_MIN}",
                      "-f", "null", "-"], capture_output=True, text=True, errors="ignore").stderr
ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", txt)]
fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", txt)]
falas, cur = [], 0.0
for a, b in zip(ini, fim + [dur]):
    if a - cur > 0.15:
        falas.append((max(cur - 0.1, 0), min(a + 0.1, dur)))
    cur = b
if dur - cur > 0.15:
    falas.append((max(cur - 0.1, 0), dur))

try:
    modelo, disp = WhisperModel("large-v3-turbo", device="cuda", compute_type="int8_float32"), "placa de vídeo"
except Exception:
    modelo, disp = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8"), "processador"

palavras = []
for a, b in falas:
    trecho = dados[int(a * 16000):int(b * 16000)]
    if len(trecho) < 1600:
        continue
    segs, _ = modelo.transcribe(trecho, language="pt", word_timestamps=True, initial_prompt=prompt,
                                vad_filter=False, condition_on_previous_text=False)
    for s in segs:
        for w in s.words:
            palavras.append({"w": w.word.strip(), "s": round(a + w.start, 3), "e": round(a + w.end, 3),
                             "p": round(w.probability, 3), "fala": len(palavras) and None})
for w in palavras:
    w.pop("fala", None)
json.dump(palavras, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"limiar do silêncio {LIMIAR:.1f} dB; {len(palavras)} palavras em {len(falas)} falas, {time.time() - t0:.1f}s ({disp})")
