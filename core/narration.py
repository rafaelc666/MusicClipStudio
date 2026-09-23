"""
NarrationEngine: Abstração unificada para síntese de voz (TTS).

Suporta:
- single: Piper ou Kokoro (rápido, sem alucinação, voz robótica aceitável)
- multi: XTTS v2 (multi-personagens, roteiro "Nome: fala")

Engines que requerem subprocess (XTTS) são isolados para evitar conflitos de dependência.
"""

import json
import subprocess
import sys
import tempfile
import urllib.request
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal, Union

import numpy as np
import soundfile as sf
import torch
import torchaudio
from pydantic import BaseModel, Field, validator
from tqdm import tqdm

# Tipos
NarrationMode = Literal["single", "clone", "multi"]
NarrationModeEnum = NarrationMode  # alias para compatibilidade com subprocess workers


class NarrationConfig(BaseModel):
    """Configuração de narração para um projeto."""
    mode: NarrationMode = "single"
    engine: str = "piper"  # piper, kokoro, xtts
    voice_ref: Optional[Union[str, Path]] = None  # Arquivo de referência para clone/multi
    text: Optional[str] = None  # Texto direto
    text_file: Optional[Union[str, Path]] = None  # Arquivo de texto
    output: Union[str, Path] = "output.wav"
    language: Optional[str] = None  # pt_BR, en_US, etc.
    speaker: Optional[str] = None  # Nome do personagem para multi

    @validator("voice_ref", pre=True, always=True)
    def resolve_voice_ref(cls, v):
        if v is None:
            return None
        return Path(v) if isinstance(v, str) else v

    @validator("text_file", pre=True, always=True)
    def resolve_text_file(cls, v):
        if v is None:
            return None
        return Path(v) if isinstance(v, str) else v


@dataclass
class NarrationResult:
    """Resultado de uma síntese de voz."""
    audio_path: Path
    duration: float
    sample_rate: int
    success: bool
    error: Optional[str] = None


class NarrationEngine(ABC):
    """Interface base para engines de TTS."""

    @classmethod
    def get_engine(cls, name: str) -> "NarrationEngine":
        """Factory: retorna engine por nome."""
        engines = {
            "piper": PiperEngine,
            "kokoro": KokoroEngine,
            "xtts": XTTSEngine,
        }
        if name not in engines:
            raise ValueError(f"Engine desconhecido: {name}. Opções: {list(engines.keys())}")
        return engines[name]()

    @abstractmethod
    def generate(
        self,
        text: str,
        voice_ref: Optional[Path] = None,
        output: Optional[Path] = None,
        mode: NarrationMode = "single",
        **kwargs,
    ) -> NarrationResult:
        """Gera áudio a partir de texto.

        Args:
            text: Texto a ser sintetizado
            voice_ref: Arquivo de referência para clonagem (clone/multi)
            output: Caminho de saída (opcional, retorna Path temporário se None)
            mode: Modo de síntese
            kwargs: Parâmetros específicos do engine

        Returns:
            NarrationResult com caminho do áudio e metadados
        """
        pass

    def _write_wav(self, audio: np.ndarray, sample_rate: int, output: Union[str, Path]) -> Path:
        """Escreve áudio em WAV."""
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output), audio, sample_rate)
        return output


# URLs dos modelos Piper (huggingface)
PIPER_MODELS = {
    "pt_BR-faber": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
    },
    # Razo: voz masculina técnica pt-BR, fine-tune Piper/VITS, RTF < 0.1, CPU-only.
    # ATENÇÃO: URLs abaixo retornaram 404 no teste (repo comunitário, nome de
    # arquivo real não confirmado). Voz padrão continua "faber" até isso ser checado.
    "pt_BR-razo": {
        "model": "https://huggingface.co/Lucasllfs/Razo-piper-voice/resolve/main/razo.onnx",
        "config": "https://huggingface.co/Lucasllfs/Razo-piper-voice/resolve/main/razo.onnx.json",
    },
    "en_US-amy": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
    },
    "en_US-lessac": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    },
}

# URLs dos modelos Kokoro - usamos HuggingFace com autenticação opcional
# Se não houver token, o usuário deve colocar o modelo manualmente em models/kokoro/
KOKORO_MODELS = {
    "pt_BR-faber": {
        "url": "https://huggingface.co/thewh1teagle/kokoro-onnx/resolve/main/models/kokoro-v1.0-pt_BR-faber.onnx",
        "requires_token": True,
    },
    "en_US-af": {
        "url": "https://huggingface.co/thewh1teagle/kokoro-onnx/resolve/main/models/kokoro-v1.0-en_US-af.onnx",
        "requires_token": True,
    },
    "en_US-am": {
        "url": "https://huggingface.co/thewh1teagle/kokoro-onnx/resolve/main/models/kokoro-v1.0-en_US-am.onnx",
        "requires_token": True,
    },
}


def download_model(url: str, dest: Path) -> None:
    """Baixa modelo com barra de progresso."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    class TqdmUpTo(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)

    with TqdmUpTo(unit='B', unit_scale=True, unit_divisor=1024, miniters=1,
                  desc=dest.name) as t:
        urllib.request.urlretrieve(url, str(dest), reporthook=t.update_to)


def _default_progress_path() -> Path:
    """Caminho padrão do arquivo de progresso, lido pelo monitor externo (monitor_narracao.py)."""
    base = Path(__file__).parent.parent
    path = base / "producao" / "logs" / "narration_progress.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_progress(
    path: Union[str, Path],
    status: str,
    current: int,
    total: int,
    message: str = "",
    done: bool = False,
) -> None:
    """Escreve o estado atual da geração em JSON para o monitor externo ler.

    Best-effort: qualquer falha aqui é silenciosa e nunca deve derrubar a geração de áudio.
    """
    try:
        import time as _time

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        if status == "iniciando" or "start_time" not in data:
            data["start_time"] = _time.time()

        data.update({
            "status": status,       # iniciando | gerando | tentando_novamente | erro_trecho | concluido | concluido_com_avisos | erro
            "current": current,     # trecho atual
            "total": total,         # total de trechos
            "message": message,
            "done": done,
            "updated_at": _time.time(),
        })
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class PiperEngine(NarrationEngine):
    """Engine Piper TTS (leve, rápido, sem alucinação)."""

    def __init__(self, models_dir: Optional[Path] = None):
        try:
            from piper import PiperVoice
            self.PiperVoice = PiperVoice
            # Caminho absoluto baseado no local deste arquivo (core/narration.py)
            # -> <raiz>/models/piper. Evita problemas quando o Python roda
            # de outro CWD (ex: GUI aberta pelo launcher).
            if models_dir is None:
                _base = Path(__file__).resolve().parent.parent  # raiz do projeto
                models_dir = _base / "models" / "piper"
            self.models_dir = Path(models_dir)
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self._voice_cache = {}
        except ImportError:
            raise ImportError("Piper TTS não instalado. Instale com: pip install piper-tts")

    def _ensure_model(self, voice_key: str) -> Path:
        """Verifica/baixa modelo Piper se necessário."""
        if voice_key in self._voice_cache:
            return self._voice_cache[voice_key]

        if voice_key not in PIPER_MODELS:
            raise ValueError(f"Voz não suportada: {voice_key}. Disponíveis: {list(PIPER_MODELS.keys())}")

        model_info = PIPER_MODELS[voice_key]
        model_path = self.models_dir / f"{voice_key}.onnx"
        config_path = self.models_dir / f"{voice_key}.onnx.json"

        if not model_path.exists():
            print(f"Baixando modelo Piper: {voice_key}...")
            download_model(model_info["model"], model_path)
        if not config_path.exists():
            download_model(model_info["config"], config_path)

        # Carrega voz
        voice = self.PiperVoice.load(str(model_path), str(config_path))
        self._voice_cache[voice_key] = voice
        return voice

    def generate(
        self,
        text: str,
        voice_ref: Optional[Path] = None,
        output: Optional[Path] = None,
        mode: NarrationMode = "single",
        language: str = "pt_BR",
        speaker: str = "faber",
        max_chars: int = 300,
        silence_ms: int = 250,
        progress_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> NarrationResult:
        """Gera áudio com Piper, quebrando o texto em trechos menores.

        Isso evita falhas em narrações longas (15-20min), permite retry isolado
        por trecho, e escreve progresso em JSON para o monitor_narracao.py acompanhar
        em tempo real (current/total/status/mensagem).
        """
        if mode != "single":
            raise ValueError("Piper só suporta modo 'single'")

        output = output or Path(tempfile.mktemp(suffix=".wav"))
        progress_file = Path(progress_path) if progress_path else _default_progress_path()

        try:
            voice_key = f"{language}-{speaker}"
            voice = self._ensure_model(voice_key)

            chunks = split_long_text(text, max_chars=max_chars)
            total = len(chunks)

            sample_rate = None
            audio_parts: list = []
            errors: list = []

            _write_progress(progress_file, "iniciando", 0, total, "Preparando geração...")

            for i, chunk in enumerate(chunks, start=1):
                chunk_audio = None
                last_error = None

                for attempt in (1, 2):
                    try:
                        audio_chunks = list(voice.synthesize(chunk))
                        if not audio_chunks:
                            raise ValueError("Nenhum áudio gerado para este trecho")
                        chunk_audio = np.concatenate(
                            [c.audio_float_array for c in audio_chunks]
                        )
                        sample_rate = audio_chunks[0].sample_rate
                        break
                    except Exception as e:
                        last_error = str(e)
                        if attempt == 1:
                            _write_progress(
                                progress_file, "tentando_novamente", i, total,
                                f"Trecho {i}/{total} falhou, tentando de novo...",
                            )

                if chunk_audio is None:
                    errors.append(f"Trecho {i}: {last_error}")
                    _write_progress(
                        progress_file, "erro_trecho", i, total,
                        f"Trecho {i}/{total} pulado após 2 tentativas ({last_error})",
                    )
                    continue

                audio_parts.append(chunk_audio)
                if sample_rate and silence_ms > 0 and i < total:
                    silence = np.zeros(
                        int(sample_rate * silence_ms / 1000), dtype=chunk_audio.dtype
                    )
                    audio_parts.append(silence)

                _write_progress(
                    progress_file, "gerando", i, total, f"Trecho {i}/{total} concluído"
                )

            if not audio_parts:
                raise ValueError("Nenhum trecho de áudio foi gerado com sucesso")

            full_audio = np.concatenate(audio_parts)
            written = self._write_wav(full_audio, sample_rate, output)

            status_final = "concluido_com_avisos" if errors else "concluido"
            _write_progress(
                progress_file, status_final, total, total,
                "Áudio finalizado" + (f" ({len(errors)} trecho(s) com problema)" if errors else ""),
                done=True,
            )

            return NarrationResult(
                audio_path=written,
                duration=len(full_audio) / sample_rate,
                sample_rate=sample_rate,
                success=True,
                error="; ".join(errors) if errors else None,
            )
        except Exception as e:
            _write_progress(progress_file, "erro", 0, 0, str(e), done=True)
            return NarrationResult(
                audio_path=output,
                duration=0,
                sample_rate=0,
                success=False,
                error=str(e),
            )


class KokoroEngine(NarrationEngine):
    """Engine Kokoro TTS (leve, rápido, sem alucinação)."""

    def __init__(self, models_dir: Optional[Path] = None):
        try:
            import kokoro_onnx
            self.kokoro_onnx = kokoro_onnx
            # Caminho absoluto (evita problema de CWD)
            if models_dir is None:
                _base = Path(__file__).resolve().parent.parent
                models_dir = _base / "models" / "kokoro"
            self.models_dir = Path(models_dir)
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self._model_cache = {}
        except ImportError:
            raise ImportError("Kokoro TTS não instalado. Instale com: pip install kokoro-onnx")

    def _ensure_model(self, voice_key: str) -> "kokoro_onnx.Kokoro":
        """Verifica/baixa modelo Kokoro se necessário."""
        if voice_key in self._model_cache:
            return self._model_cache[voice_key]

        if voice_key not in KOKORO_MODELS:
            raise ValueError(f"Voz não suportada: {voice_key}. Disponíveis: {list(KOKORO_MODELS.keys())}")

        model_path = self.models_dir / f"{voice_key}.onnx"
        model_info = KOKORO_MODELS[voice_key]

        if not model_path.exists():
            if model_info.get("requires_token", False):
                raise RuntimeError(
                    f"Modelo Kokoro '{voice_key}' requer token do HuggingFace. "
                    f"Configure HF_TOKEN ou coloque o arquivo manualmente em: {model_path}"
                )
            print(f"Baixando modelo Kokoro: {voice_key}...")
            download_model(model_info["url"], model_path)

        # Carrega modelo
        model = self.kokoro_onnx.Kokoro(str(model_path))
        self._model_cache[voice_key] = model
        return model

    def generate(
        self,
        text: str,
        voice_ref: Optional[Path] = None,
        output: Optional[Path] = None,
        mode: NarrationMode = "single",
        language: str = "pt_BR",
        speaker: str = "faber",
        **kwargs,
    ) -> NarrationResult:
        """Gera áudio com Kokoro."""
        if mode != "single":
            raise ValueError("Kokoro só suporta modo 'single'")

        output = output or Path(tempfile.mktemp(suffix=".wav"))

        try:
            voice_key = f"{language}-{speaker}"
            model = self._ensure_model(voice_key)

            # Sintetiza
            audio, sample_rate = model.create(text, voice=voice_key)
            written = self._write_wav(audio, sample_rate, output)

            return NarrationResult(
                audio_path=written,
                duration=len(audio) / sample_rate,
                sample_rate=sample_rate,
                success=True,
            )
        except Exception as e:
            return NarrationResult(
                audio_path=output,
                duration=0,
                sample_rate=0,
                success=False,
                error=str(e),
            )


class XTTSEngine(NarrationEngine):
    """Engine XTTS v2 (multi-personagens, roteiro 'Nome: fala')."""

    def generate(
        self,
        text: str,
        voice_ref: Optional[Path] = None,
        output: Optional[Path] = None,
        mode: NarrationMode = "multi",
        **kwargs,
    ) -> NarrationResult:
        """Gera áudio com XTTS via subprocess."""
        if mode != "multi":
            raise ValueError("XTTS só suporta modo 'multi'")

        if not voice_ref or not voice_ref.exists():
            raise ValueError(f"Arquivo de referência de voz não encontrado: {voice_ref}")

        output = output or Path(tempfile.mktemp(suffix=".wav"))

        try:
            # Chama script worker
            script = Path(__file__).parent.parent / "workers" / "xtts_worker.py"
            result = subprocess.run(
                [sys.executable, str(script), str(voice_ref), text, str(output)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return NarrationResult(
                    audio_path=output,
                    duration=0,
                    sample_rate=0,
                    success=False,
                    error=result.stderr,
                )

            # Extrair metadados
            info = sf.info(str(output))
            return NarrationResult(
                audio_path=output,
                duration=info.duration,
                sample_rate=int(info.samplerate),
                success=True,
            )
        except Exception as e:
            return NarrationResult(
                audio_path=output,
                duration=0,
                sample_rate=0,
                success=False,
                error=str(e),
            )


# Funções utilitárias

def split_long_text(text: str, max_chars: int = 200) -> list[str]:
    """Divide texto longo em frases menores sem cortar palavras."""
    import re
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    # Divide por pontuação de fim de frase
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def detect_best_engine(mode: NarrationMode) -> str:
    """Detecta melhor engine para o modo."""
    mapping = {
        "single": "piper",      # Piper é mais leve e rápido
        "multi": "xtts",
    }
    return mapping.get(mode, "piper")


# Factory de alto nível para uso simplificado
def create_narration(
    text: str,
    output: Union[str, Path],
    mode: NarrationMode = "single",
    engine: Optional[str] = None,
    voice_ref: Optional[Union[str, Path]] = None,
    **kwargs,
) -> NarrationResult:
    """Função de conveniência para gerar narração.

    Args:
        text: Texto a ser sintetizado
        output: Caminho de saída
        mode: Modo de síntese (single, clone, multi)
        engine: Engine específico (opcional, usa detect_best_engine se None)
        voice_ref: Arquivo de referência de voz (para clone/multi)
        kwargs: Parâmetros extras para o engine

    Returns:
        NarrationResult
    """
    engine_name = engine or detect_best_engine(mode)
    eng = NarrationEngine.get_engine(engine_name)
    return eng.generate(
        text=text,
        voice_ref=Path(voice_ref) if voice_ref else None,
        output=Path(output),
        mode=mode,
        **kwargs,
    )


if __name__ == "__main__":
    # Teste rápido
    engine = NarrationEngine.get_engine("piper")
    result = engine.generate("Olá mundo, este é um teste de síntese de voz.", output="test_piper.wav")
    print(f"Generated: {result.audio_path}, duration: {result.duration:.2f}s, success: {result.success}")