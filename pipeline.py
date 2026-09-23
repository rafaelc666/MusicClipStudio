"""
Pipeline de alto nível para geração de clipes musicais v2.

Combina:
  1. Criação de beats (letras/descrição → beats)
  2. Agente de direção (decisões visuais)
  3. Geração de áudio (ACE-Step)
  4. Geração de legendas
  5. Montagem (scene_engine)
  6. Finalização
"""

import sys
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import ClipConfig, load_config
from MusicClipStudio.schema import (
    MusicClipProject, MusicBeat,
    letras_para_beats, descricao_para_beats,
    project_from_lyrics,
)
from MusicClipStudio.engine import MusicClipEngine, ClipProgress
from MusicClipStudio.audio import gerar_trilha
from MusicClipStudio.legendas import gerar_srt_letras
from MusicClipStudio.agent import ClipAgent, AgentPlan, AgentMood
from MusicClipStudio.database import StockDatabase


@dataclass
class ClipJob:
    """Trabalho de geração de clipe."""
    id: str = ""
    lyrics: str = ""
    description: str = ""
    music_prompt: str = ""
    title: str = ""
    artist: str = ""
    images: list[str] = field(default_factory=list)
    beats: list[MusicBeat] = field(default_factory=list)
    duracao: int = 30
    formato: str = "9/16"
    saida: str = ""
    status: str = "pendente"
    progresso: float = 0.0
    mensagem: str = ""
    agente: Optional[dict] = None
    arquivo_video: str = ""
    arquivo_audio: str = ""
    arquivo_legenda: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"clip_{int(time.time())}_{uuid.uuid4().hex[:6]}"


class MusicClipPipeline:
    """Pipeline completo de geração de clipes musicais v2."""

    def __init__(self, config: Optional[ClipConfig] = None):
        self.config = config or load_config()
        self.engine = MusicClipEngine(self.config)
        self.agent = ClipAgent(self.config)
        self._jobs: dict[str, ClipJob] = {}

    def criar_job(
        self,
        lyrics: str = "",
        description: str = "",
        music_prompt: str = "",
        title: str = "",
        artist: str = "",
        images: Optional[list[str]] = None,
        duracao: int = 30,
        formato: str = "9/16",
        use_agent: bool = True,
    ) -> ClipJob:
        """Cria um trabalho de geração de clipe."""
        job = ClipJob(
            lyrics=lyrics,
            description=description,
            music_prompt=music_prompt,
            title=title,
            artist=artist,
            images=images or [],
            duracao=duracao,
            formato=formato,
        )

        # Criar beats
        if lyrics.strip() or description.strip():
            job.beats = letras_para_beats(
                lyrics,
                duration_estimada=duracao / max(len(letras_para_beats(lyrics or description)), 1) if (lyrics or description) else 5.0,
            ) or descricao_para_beats(description, duration_estimada=5.0)

        # Executar agente
        if use_agent and (lyrics or description):
            plan = self.agent.analisar(lyrics=lyrics, description=description, music_prompt=music_prompt)
            job.agente = {
                "mood": plan.mood.value,
                "style": plan.style.value,
                "colors": plan.color_palette,
                "global_effects": plan.global_effects,
                "decisions": [
                    {
                        "beat_id": d.beat_id,
                        "component_type": d.component_type,
                        "effect": d.effect,
                        "accent_color": d.accent_color,
                        "photo_query": d.photo_query,
                    }
                    for d in plan.beats
                ],
            }

        self._jobs[job.id] = job
        return job

    def executar(self, job: ClipJob) -> Optional[Path]:
        """Executa o trabalho de geração."""
        job.status = "executando"
        job.progresso = 0.0

        def on_progress(event: str, data: dict):
            job.progresso = data.get("progresso", 0) * 100
            job.mensagem = data.get("mensagem", "")

        self.engine.on_progress(on_progress)

        try:
            # Gerar áudio se houver prompt musical
            audio_path = None
            if job.music_prompt or job.lyrics:
                prompt = job.music_prompt or job.lyrics[:100]
                job.arquivo_audio = str(self.config.output_path / f"audio_{job.id}.wav")
                audio_path = gerar_trilha(prompt, job.duracao)

            # Gerar clipe
            resultado = self.engine.generate(
                lyrics=job.lyrics,
                description=job.description,
                title=job.title,
                artist=job.artist,
                music_prompt=job.music_prompt,
                images=job.images if job.images else None,
                format=job.formato,
                duration_beat=5.0,
                output=job.saida,
            )

            if resultado:
                job.status = "concluido"
                job.arquivo_video = str(resultado)
                job.progresso = 100.0
            else:
                job.status = "erro"
                job.mensagem = "Falha na geração"
            return resultado

        except Exception as e:
            job.status = "erro"
            job.mensagem = str(e)
            return None

    def executar_rapido(
        self,
        lyrics: str = "",
        description: str = "",
        music_prompt: str = "",
        title: str = "",
        images: Optional[list[str]] = None,
        duracao: int = 30,
        formato: str = "9/16",
    ) -> Optional[Path]:
        """Criar e executar clipe de uma vez."""
        job = self.criar_job(
            lyrics=lyrics,
            description=description,
            music_prompt=music_prompt,
            title=title,
            images=images,
            duracao=duracao,
            formato=formato,
        )
        return self.executar(job)

    def gerar_com_agente(
        self,
        descricao: str,
        music_prompt: str = "",
        title: str = "",
        formato: str = "9/16",
    ) -> Optional[Path]:
        """
        Gera clipe com descrição + agente de IA.

        O agente analisa a descrição e decide toda a direção visual.
        """
        plan = self.agent.analisar(description=descricao, music_prompt=music_prompt)

        # Gerar query de imagens do agente
        if self.config.stock_api_key:
            db = StockDatabase(self.config)
            imagens = db.selecionar_imagens_banco(n_imagens=4, query=descricao)
        else:
            imagens = []

        job = self.criar_job(
            description=descricao,
            music_prompt=music_prompt,
            title=title or descricao[:50],
            images=imagens,
            duracao=30,
            formato=formato,
            use_agent=False,  # Agente já foi executado
        )

        # Aplicar decisões do agente aos beats
        for d in plan.beats:
            job.beats.append(
                MusicBeat(
                    id=d.beat_id,
                    type="verse",
                    duration=5.0,
                    script=d.style_note or d.photo_query,
                    visual=MusicVisualElement(
                        type=d.component_type,
                        accent_color=d.accent_color,
                        bg_color=d.bg_color,
                        animation=d.animation,
                    ),
                )
            )

        return self.executar(job)

    def listar_jobs(self) -> dict[str, ClipJob]:
        return dict(self._jobs)

    def get_job(self, job_id: str) -> Optional[ClipJob]:
        return self._jobs.get(job_id)

    def executar_bateria(self, jobs: list[ClipJob]) -> dict:
        """Executa múltiplos clipes em sequência."""
        resultados = {}
        for job in jobs:
            resultados[job.id] = self.executar(job)
        return resultados