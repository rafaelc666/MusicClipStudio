"""
Analise do audio da musica: BPM, grade de batidas e curva de energia.

Este modulo responde tres perguntas que o resto do pipeline precisa:
  1. Quantos segundos tem a musica? (duracao real, nao a que o usuario digitou)
  2. Em que instantes estao as batidas? (para cortar no ritmo)
  3. Onde a musica cresce e onde ela e calma? (para escolher o efeito)

Usa `librosa`, que ja esta instalado no ambiente do projeto.

Importante: a analise NUNCA deve derrubar a geracao. Se o librosa faltar,
se o arquivo estiver corrompido ou se a deteccao de batida falhar, cada
funcao devolve um resultado degradado (duracao via ffprobe, grade
uniforme) em vez de levantar excecao. O clipe tem que sair mesmo assim.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


# Faixa plausivel de BPM. Fora disso quase sempre e' erro de deteccao:
# o algoritmo divide ou dobra o tempo (92 -> 184, 92 -> 46).
BPM_MIN = 50.0
BPM_MAX = 200.0

# Abaixo disso o trecho e' considerado silencio/inicio e nao deve ser
# usado para definir o ritmo global.
LIMIAR_SILENCIO = 0.01


def librosa_disponivel() -> bool:
    """True se o librosa pode ser importado."""
    try:
        import librosa  # noqa: F401
        return True
    except Exception:
        return False


@dataclass
class AnaliseAudio:
    """Resultado da analise de um arquivo de audio."""

    duracao: float = 0.0
    bpm: float = 0.0
    batidas: list[float] = field(default_factory=list)
    energia: list[float] = field(default_factory=list)
    energia_tempos: list[float] = field(default_factory=list)
    erro: str = ""
    analisado: bool = False

    @property
    def ok(self) -> bool:
        return self.analisado and not self.erro

    @property
    def tem_batidas(self) -> bool:
        return len(self.batidas) >= 4 and self.bpm > 0

    @property
    def segundos_por_batida(self) -> float:
        return 60.0 / self.bpm if self.bpm > 0 else 0.0

    def energia_em(self, t: float) -> float:
        """Energia normalizada (0..1) no instante `t`.

        Sem analise de energia, devolve 0.5 (neutro) para nao enviesar
        a escolha de efeito nem o padrao de alternancia.
        """
        if not self.energia or not self.energia_tempos:
            return 0.5
        try:
            i = min(range(len(self.energia_tempos)),
                    key=lambda k: abs(self.energia_tempos[k] - t))
            return float(self.energia[i])
        except (ValueError, TypeError):
            return 0.5

    def resumo(self) -> str:
        if self.erro and not self.analisado:
            return f"análise indisponível ({self.erro})"
        partes = [f"{self.duracao:.1f}s"]
        if self.bpm > 0:
            partes.append(f"{self.bpm:.0f} BPM")
        if self.batidas:
            partes.append(f"{len(self.batidas)} batidas")
        return " · ".join(partes)


# ════════════════════════════════════════════════════════════════
# Duracao (fallback robusto, sem depender do librosa)
# ════════════════════════════════════════════════════════════════

def duracao_audio(caminho: str) -> float:
    """Duracao em segundos, tentando soundfile e depois ffprobe.

    Preferimos soundfile (nao abre processo). O ffprobe cobre formatos
    que o soundfile recusa (alguns mp3/m4a problematicos).
    """
    if not caminho or not Path(caminho).exists():
        return 0.0

    # 1. soundfile
    try:
        import soundfile as sf
        info = sf.info(str(caminho))
        if info.duration and info.duration > 0:
            return float(info.duration)
    except Exception:
        pass

    # 2. ffprobe
    try:
        ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
        if ffprobe:
            proc = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries",
                 "format=duration", "-of", "json", str(caminho)],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=30,
            )
            if proc.returncode == 0:
                dados = json.loads(proc.stdout or "{}")
                dur = float(dados.get("format", {}).get("duration", 0) or 0)
                if dur > 0:
                    return dur
    except Exception:
        pass

    return 0.0


# ════════════════════════════════════════════════════════════════
# Analise principal
# ════════════════════════════════════════════════════════════════

def analisar(caminho: str, callback_log=None) -> AnaliseAudio:
    """Analisa BPM, batidas e energia da musica.

    Nunca levanta excecao: qualquer falha volta dentro de `AnaliseAudio.erro`.
    """
    if callback_log is None:
        callback_log = lambda _m: None

    if not caminho or not Path(caminho).exists():
        return AnaliseAudio(erro=f"arquivo não encontrado: {caminho}")

    resultado = AnaliseAudio()
    resultado.duracao = duracao_audio(caminho)

    if not librosa_disponivel():
        resultado.erro = "librosa não instalado"
        callback_log("[AUDIO] librosa ausente — ritmo por duração fixa")
        return resultado

    if np is None:
        resultado.erro = "numpy não instalado"
        return resultado

    try:
        import librosa

        callback_log("[AUDIO] Analisando ritmo da música...")

        # sr=22050 e' o suficiente para batida e energia, e bem mais
        # rapido que 44100 em musica longa. mono evita analisar 2 canais
        # para uma informacao que e' global.
        y, sr = librosa.load(str(caminho), sr=22050, mono=True)

        if y.size == 0:
            resultado.erro = "áudio vazio"
            return resultado

        if resultado.duracao <= 0:
            resultado.duracao = len(y) / sr

        # ── Batidas e BPM ──────────────────────────────────────
        tempo, batidas = librosa.beat.beat_track(y=y, sr=sr, units="time")
        bpm = _bpm_escalar(tempo)

        if bpm > 0:
            bpm = _normalizar_bpm(bpm, callback_log)

        resultado.bpm = bpm
        resultado.batidas = [float(b) for b in batidas]

        # ── Curva de energia (RMS) ─────────────────────────────
        # A janela de analise precisa ser MAIS LARGA que o hop.
        # Com frame_length curto (o padrao do librosa, 2048) e hop
        # tambem curto, cada frame cai no silencio entre batidas e a
        # curva fica cheia de zeros — inutil para decidir efeito.
        # frame_length=8192 (~0.37s) cobre uma batida inteira.
        hop = 2048
        frame_length = 8192

        rms = librosa.feature.rms(
            y=y, frame_length=frame_length, hop_length=hop,
        )[0]
        tempos = librosa.frames_to_time(
            np.arange(len(rms)), sr=sr, hop_length=hop
        )

        # Suaviza para o perfil de energia virar TENDENCIA e nao
        # refletir cada batida individual.
        if rms.size > 0:
            janela = max(1, int(len(rms) / max(resultado.duracao, 1.0)))
            if janela > 1:
                kernel = np.ones(janela) / janela
                rms = np.convolve(rms, kernel, mode="same")

        pico = float(np.percentile(rms, 95)) if rms.size else 0.0
        if pico <= 0:
            pico = float(rms.max()) if rms.size else 0.0

        if pico > 0:
            energia = (rms / pico).astype(float)
            energia = np.clip(energia, 0.0, 1.0).tolist()
        else:
            energia = [0.0] * len(rms)

        resultado.energia = energia
        resultado.energia_tempos = [float(t) for t in tempos]
        resultado.analisado = True

        callback_log(
            f"[AUDIO] {resultado.resumo()}"
        )
        if resultado.batidas:
            callback_log(
                f"   Batidas detectadas a cada "
                f"{resultado.segundos_por_batida:.2f}s em média"
            )

    except Exception as e:
        resultado.erro = f"{type(e).__name__}: {e}"
        callback_log(f"[AUDIO] Falha na análise: {resultado.erro}")

    return resultado


def _bpm_escalar(tempo) -> float:
    """O librosa as vezes devolve array de 1 elemento em vez de float."""
    try:
        if hasattr(tempo, "__len__"):
            return float(tempo[0]) if len(tempo) else 0.0
        return float(tempo)
    except (TypeError, ValueError, IndexError):
        return 0.0


def _normalizar_bpm(bpm: float, callback_log) -> float:
    """Traz o BPM para a faixa plausivel.

    O detector erra por dobro/metade com frequencia: uma musica de 92 BPM
    costuma voltar como 184 ou 46. Dobrar/dividir por 2 ate' entrar na
    faixa e' a correcao padrao e nao muda o significado musical (o grid
    de batidas fica equivalente).
    """
    original = bpm
    tentativas = 0

    while bpm > BPM_MAX and tentativas < 4:
        bpm /= 2.0
        tentativas += 1
    while bpm < BPM_MIN and tentativas < 8:
        bpm *= 2.0
        tentativas += 1

    if abs(bpm - original) > 0.5:
        callback_log(
            f"   BPM {original:.0f} ajustado para {bpm:.0f} "
            f"(fora da faixa {BPM_MIN:.0f}-{BPM_MAX:.0f})"
        )

    return bpm


def grid_de_batidas(analise: AnaliseAudio, duracao: float,
                    batidas_por_troca: int = 8) -> list[float]:
    """Instantes de troca de midia, alinhados a batida.

    Usa as batidas REAIS quando existem (respeita aceleracao e
    rallentando). Sem elas, gera um grid uniforme a partir do BPM.
    Sem BPM, cai num grid de 4s.

    Devolve instantes crescentes, comecando em 0 e terminando em
    `duracao` — assim o ultimo clipe sempre cobre ate' o fim.
    """
    if duracao <= 0:
        return []

    if batidas_por_troca < 1:
        batidas_por_troca = 1

    batidas = analise.batidas if analise.batidas else []

    # Grid uniforme quando nao ha batidas detectadas
    if len(batidas) < 4:
        passo = analise.segundos_por_batida * batidas_por_troca
        if passo <= 0:
            passo = 4.0
        instantes = []
        t = 0.0
        while t < duracao:
            instantes.append(t)
            t += passo
        instantes.append(duracao)
        return instantes

    # Alinha o inicio ao primeiro instante util (batida 0)
    instantes = [0.0]
    for i in range(batidas_por_troca, len(batidas), batidas_por_troca):
        t = batidas[i]
        if t >= duracao:
            break
        if t - instantes[-1] < 0.35:
            # Duas trocas quase no mesmo instante: a segunda e' ruido
            # de deteccao e produziria um clipe de 1 frame.
            continue
        instantes.append(t)

    if instantes[-1] < duracao:
        instantes.append(duracao)

    return instantes


def _auto_teste() -> None:
    """Checagens internas baratas. Rodar com `python -m ...`."""
    print("librosa disponivel?", librosa_disponivel())

    a = AnaliseAudio()
    a.bpm = 120.0
    a.analisado = True
    print("segundos por batida (120 BPM):", a.segundos_por_batida)
    assert abs(a.segundos_por_batida - 0.5) < 1e-9

    print("_normalizar_bpm(184) ->", _normalizar_bpm(184.0, lambda _m: None))
    print("_normalizar_bpm(23)  ->", _normalizar_bpm(23.0, lambda _m: None))

    g = grid_de_batidas(AnaliseAudio(), 10.0, 8)
    print("grid sem analise (10s):", [round(x, 2) for x in g])
    assert g[0] == 0.0 and abs(g[-1] - 10.0) < 1e-9

    g2 = grid_de_batidas(AnaliseAudio(), 0.0)
    assert g2 == []

    print("auto-teste: OK")


if __name__ == "__main__":
    _auto_teste()
