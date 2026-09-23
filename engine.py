"""
Engine principal do Gerador de Clipes Musicais v2.

Pipeline usando o novo motor (scene_engine):
  1. Recebe letras/descrição + imagens e a música pronta do usuário
  2. Cria beats visuais a partir do conteúdo
  3. Renderiza via HTMLRenderer → Playwright → VideoRenderer
  4. Adiciona áudio e legendas ao vídeo final

Integrações:
  - scene_engine.renderers.HTMLRenderer (componentes visuais)
  - scene_engine.renderers.VideoRenderer (HTML → vídeo e áudio)
  - scene_engine.compositor.Compositor (legendas)
"""

import os
import sys
import time
import subprocess
import json
import threading
import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import ClipConfig, get_config
from MusicClipStudio.schema import MusicClipProject, MusicBeat, letras_para_beats, descricao_para_beats, project_from_lyrics
from MusicClipStudio.legendas import gerar_srt_letras


# Dimensões (largura, altura) por formato de clipe.
# Fonte ÚNICA da verdade — usada em generate() e no fallback moviepy.
# Nunca escrever `{formato: {...}}` inline: isso cria um dict com chave
# literal em vez de fazer lookup (bug corrigido em 19/09/2026).
_DIMS = {
    "9/16": (1080, 1920),
    "16/9": (1920, 1080),
    "3/4":  (1080, 1440),
    "4/3":  (1440, 1080),
    "1/1":  (1080, 1080),
}


@dataclass
class ClipProgress:
    progresso: float = 0.0
    etapa: str = "inativo"
    mensagem: str = ""
    clip_id: int = 0
    total_clips: int = 0

    @property
    def percentual(self) -> float:
        return self.progresso * 100


class MusicClipEngine:
    """Motor de geração de clipes musicais v2 (scene_engine)."""

    def __init__(self, config: Optional[ClipConfig] = None):
        self.config = config or get_config()
        self._callbacks: list[callable] = []
        self._gerando = False
        self._cancelar = False
        self._active_projects: dict[str, MusicClipProject] = {}

    def _notify(self, event: str, data: dict):
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                pass

    def on_progress(self, callback: callable):
        self._callbacks.append(callback)

    def _progress(self, pct: float, etapa: str, mensagem: str = ""):
        self._notify("progress", {"progresso": pct / 100.0, "etapa": etapa, "mensagem": mensagem})

    def criar_beats(
        self,
        lyrics: str = "",
        description: str = "",
        duration_beat: float = 5.0,
    ) -> list[MusicBeat]:
        """Cria beats a partir de letras ou descrição."""
        if lyrics.strip():
            return letras_para_beats(lyrics, duration_estimada=duration_beat)
        elif description.strip():
            return descricao_para_beats(description, duration_estimada=duration_beat)
        return []

    def gerar_projeto(
        self,
        lyrics: str = "",
        description: str = "",
        title: str = "",
        artist: str = "",
        music_prompt: str = "",
        images: list[str] = None,
        efeitos: list[str] = None,
        format: str = "9/16",
        duration_beat: float = 5.0,
    ) -> MusicClipProject:
        """
        Cria projeto de clipe com beats.

        Se lyrics fornecido → beats a partir de letras
        Se description fornecido → beats a partir de descrição
        Se images → distribui entre beats como parallax_image

        `efeitos` tem um efeito por imagem, na mesma ordem de `images`
        (ken_burns, zoom_in, zoom_out, pan_left, pan_right, static). Sem
        `efeitos`, todas as cenas usam ken_burns.
        """
        project = project_from_lyrics(
            lyrics=lyrics,
            title=title,
            artist=artist,
            music_prompt=music_prompt,
            description=description,
            format=format,
            duration_beat=duration_beat,
        )

        # Dimensões por formato.
        #
        # CORRIGIDO (19/09/2026): aqui estava
        #     {format: {"9/16": 1080, ...}}.get(format, 1080)
        # O `{format: ...}` cria um dict com a CHAVE LITERAL "format" cujo
        # valor é o dict de dimensões — não um lookup. Aí o `.get(format)`
        # encontrava essa chave externa e devolvia o DICIONÁRIO INTEIRO.
        # Resultado: project.width virava dict, e o Playwright quebrava com
        # "viewport.width: expected integer, got object" na hora de renderizar.
        # Só passava despercebido porque ninguém chegava até a renderização.
        _w, _h = _DIMS.get(format, (1080, 1920))
        if format not in _DIMS:
            print(f"[AVISO] formato '{format}' desconhecido — usando 9/16 (1080x1920)")
        project.width = int(_w)
        project.height = int(_h)

        if images:
            # ⚠️ CORRIGIDO (21/09/2026): o efeito era fixo "ken_burns" para
            # todas as cenas — a escolha por imagem feita na etapa 05 não
            # chegava a lugar nenhum. Agora cada beat recebe o efeito da
            # imagem que caiu nele.
            n = len(project.beats)
            for i, beat in enumerate(project.beats):
                beat.visual.type = "parallax_image"
                beat.visual.images = [images[i % len(images)]]
                beat.visual.animation = (
                    efeitos[i % len(efeitos)] if efeitos else "ken_burns"
                )

        project.created_at = datetime.datetime.now().isoformat()
        self._active_projects[project.project_id] = project

        return project

    def render_html(
        self,
        project: MusicClipProject,
    ) -> Path:
        """
        Renderiza projeto como HTML usando scene_engine.

        1. Cria beats no formato scene_engine.Beat
        2. Usa HTMLRenderer para gerar composição
        3. Retorna caminho do HTML
        """
        from MusicClipStudio.scene_engine.renderers.html_renderer import HTMLRenderer
        from MusicClipStudio.scene_engine.scene_types import Beat, VisualElement, SceneStyle

        # Converter beats para formato scene_engine
        scene_beats = []
        for mb in project.beats:
            visual = VisualElement(
                type=mb.visual.type,
                text=mb.visual.text,
                images=mb.visual.images,
                accent_color=mb.visual.accent_color,
                bg_color=mb.visual.bg_color,
                animation=mb.visual.animation,
                speaker_name=mb.visual.speaker_name,
                speaker_title=mb.visual.speaker_title,
            )
            scene_beats.append(Beat(
                id=mb.id,
                type=mb.type,
                duration=mb.duration,
                script=mb.script,
                visual=visual,
            ))

        # Renderizar HTML
        temp_dir = Path(self.config.base_dir) / "gerador_clipes_musicais" / "output" / "_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        renderer = HTMLRenderer(
            output_dir=temp_dir,
            width=project.width,
            height=project.height,
            fps=project.fps,
        )

        html_path = renderer.create_composition_html(
            beats=scene_beats,
            output_name=f"{project.project_id}.html",
            style=SceneStyle.VOX_EDITORIAL,
            scene_id=project.project_id,
            # ⚠️ REGRA (23/09/2026): o vídeo tem o tamanho do ÁUDIO — os
            # beats se estendem para cobrir a música inteira (o fim não
            # fica mais preto quando os beats acabam primeiro).
            duracao_total=self._duracao_do_clipe(project, audio_path),
        )

        self._progress(30, "html", f"HTML renderizado: {html_path}")
        return html_path

    def generate(
        self,
        lyrics: str = "",
        description: str = "",
        title: str = "",
        artist: str = "",
        music_prompt: str = "",
        images: Optional[list[str]] = None,
        efeitos: Optional[list[str]] = None,
        format: str = "9/16",
        duration_beat: float = 5.0,
        output: Optional[str] = None,
        audio_path: Optional[str] = None,
        legenda_estilo: Optional[dict] = None,
        legendas: Optional[list[dict]] = None,
    ) -> Optional[Path]:
        """
        Pipeline completo de geração de clipe musical v2.

        Args:
            lyrics: Letra da música (principal)
            description: Descrição do clipe (alternativa à letra)
            title: Título do clipe
            artist: Nome do artista
            music_prompt: Prompt para trilha musical
            images: Lista de imagens (uma por cena, na ordem do clipe)
            efeitos: Um efeito por imagem, na mesma ordem (ken_burns,
                zoom_in, zoom_out, pan_left, pan_right, static)
            format: Formato de vídeo
            duration_beat: Duração de cada beat
            output: Caminho de saída
            audio_path: MÚSICA PRONTA enviada pelo usuário (caminho do arquivo).
            legenda_estilo: estilo da legenda queimada (cor, corContorno,
                fonte, tamanho, contorno, posicao, negrito). None = padrão.

        Returns:
            Path do vídeo gerado ou None
        """
        self._gerando = True
        self._cancelar = False
        self._progress(0, "início", "Iniciando geração de clipe musical v2...")

        try:
            # 1. Criar projeto e beats
            self._progress(5, "projeto", "Criando beats visuais...")
            project = self.gerar_projeto(
                lyrics=lyrics,
                description=description,
                title=title,
                artist=artist,
                music_prompt=music_prompt,
                images=images,
                efeitos=efeitos,
                format=format,
                duration_beat=duration_beat,
            )

            if not project.beats:
                self._progress(100, "erro", "Nenhum beat gerado. Forneça letras ou descrição.")
                return None

            # 2. Trilha musical
            #
            # ARQUITETURA DO PRODUTO: a música é sempre enviada pronta pelo
            # usuário. Este motor nunca deve chamar geradores de música por IA.
            # Sem arquivo de áudio, ainda é possível gerar uma prévia muda.
            self._progress(10, "áudio", "Preparando trilha sonora...")
            if audio_path:
                if not Path(audio_path).exists():
                    self._progress(100, "erro", f"Áudio não encontrado: {audio_path}")
                    return None
                self._progress(25, "áudio", f"Trilha do usuário: {Path(audio_path).name}")
            else:
                self._progress(25, "áudio", "Sem trilha — gerando prévia muda.")

            # 3. Renderizar HTML → vídeo (scene_engine pipeline)
            self._progress(30, "render", "Renderizando cena HTML...")
            html_path = self.render_html(project)

            # 4. HTML → Vídeo via Playwright
            try:
                from MusicClipStudio.scene_engine.renderers.video_renderer import VideoRenderer
                from MusicClipStudio.scene_engine.compositor import Compositor
                has_scene_engine = True
            except ImportError:
                has_scene_engine = False
                print("[Engine] AVISO: scene_engine não disponível, fallback para moviepy")

            if has_scene_engine:

                self._progress(50, "render", "Convertendo HTML para vídeo...")
                video_renderer = VideoRenderer(
                    output_dir=Path(self.config.base_dir) / "gerador_clipes_musicais" / "output" / "_temp",
                    width=project.width,
                    height=project.height,
                    fps=project.fps,
                )

                if output is None:
                    output = str(project.output_path or self.config.output_path / f"{project.project_id}.mp4")

                video_path = video_renderer.render_html_to_video(
                    html_path=html_path,
                    output_path=output,
                    duration=self._duracao_do_clipe(project, audio_path),
                    fps=project.fps,
                )

                self._progress(75, "render", f"Vídeo base pronto: {video_path}")

            else:
                self._progress(50, "render", "Fallback: gerando vídeo com moviepy...")
                import numpy as np
                from moviepy import ImageClip, AudioFileClip

                if output is None:
                    output = str(self.config.output_path / f"{project.project_id or 'clip'}.mp4")

                # CORRIGIDO (19/09/2026): mesmo bug do dict invertido que existia
                # no generate(). `{project.format: {...}}.get(project.format)` batia
                # na chave literal e devolvia o dict inteiro em vez da tupla.
                w, h = _DIMS.get(project.format, (1080, 1920))
                img = np.zeros((h, w, 3), dtype=np.uint8)
                img[:, :] = [20, 20, 30]
                dur = self._duracao_do_clipe(project, audio_path)
                clip = ImageClip(img).set_duration(dur).resize((w, h))
                if audio_path and Path(audio_path).exists():
                    clip = clip.set_audio(AudioFileClip(audio_path))
                clip.write_videofile(output, fps=30, codec="libx264", audio_codec="aac", preset="medium")
                video_path = Path(output)
                self._progress(75, "render", f"Vídeo base pronto: {video_path}")

            # 5. Adicionar áudio
            # No fallback MoviePy, o áudio já foi inserido ao criar o clip.
            # VideoRenderer só existe no caminho scene_engine, portanto não
            # pode ser usado fora dele.
            if has_scene_engine and audio_path and Path(audio_path).exists():
                self._progress(80, "áudio", "Combinando áudio...")
                final_path = str(Path(output).with_name(Path(output).stem + "_final.mp4"))
                video_renderer.add_audio_to_video(
                    video_path=Path(video_path),
                    audio_path=Path(audio_path),
                    output_path=Path(final_path),
                )
                video_path = Path(final_path)
                self._progress(85, "áudio", "Áudio combinado")

            # 6. Legendas de letras
            # A queima de legendas depende do Compositor do scene_engine. No
            # fallback, preservamos o MP4 válido em vez de falhar no final.
            if lyrics and self.config.lyrics_active and has_scene_engine:
                self._progress(88, "legendas", "Gerando legendas...")
                srt_path = Path(output).with_suffix(".srt")
                if legendas:
                    # ⚠️ NOVO (22/09/2026): tempos REAIS da transcrição do
                    # Whisper (etapa 03) — sincronia de verdade com o áudio.
                    self._srt_de_legendas(legendas, str(srt_path))
                else:
                    gerar_srt_letras(lyrics, str(srt_path), self._duracao_do_clipe(project, audio_path))

                final_com_legenda = str(Path(output).with_name(Path(output).stem + "_legendado.mp4"))
                from MusicClipStudio.scene_engine.compositor import Compositor
                compositor = Compositor(output_dir=self.config.output_path)
                compositor.add_subtitles(
                    video_path=Path(video_path),
                    subtitles_path=srt_path,
                    output_path=Path(final_com_legenda),
                    estilo=legenda_estilo,
                )
                video_path = Path(final_com_legenda)
                self._progress(92, "legendas", "Legendas adicionadas")
            elif lyrics and self.config.lyrics_active:
                self._progress(92, "legendas", "Fallback sem legendas — MP4 preservado")

            # Limpeza dos intermediários desta geração — sobra apenas o vídeo
            # final (video_path). Antes, a base sem áudio e o _final.mp4 sem
            # legenda ficavam acumulados em output/clipes/ (pareciam "2 vídeos
            # na pasta"). Em caso de ERRO nada é apagado (facilita diagnóstico).
            finais = {Path(video_path).resolve()}
            for inter in (
                Path(output),
                Path(output).with_name(Path(output).stem + "_final.mp4"),
            ):
                try:
                    if inter.exists() and inter.resolve() not in finais:
                        inter.unlink()
                        print(f"[Engine] Intermediário removido: {inter.name}")
                except OSError:
                    pass

            self._progress(100, "concluído", f"Clip gerado: {video_path}")
            return video_path

        except Exception as e:
            self._progress(100, "erro", f"Erro: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self._gerando = False

    @staticmethod
    def _srt_de_legendas(legendas: list[dict], saida: str) -> None:
        """Escreve SRT a partir de legendas com tempos reais (Whisper).

        Cada item: {inicio: float, fim: float, texto: str} em segundos.
        Ordena por início e descarta itens sem tempo útil.
        """
        def _fmt(seg: float) -> str:
            h = int(seg // 3600)
            m = int((seg % 3600) // 60)
            s = int(seg % 60)
            ms = int(round((seg - int(seg)) * 1000))
            if ms >= 1000:
                ms = 999
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        itens = sorted(
            [l for l in legendas if float(l.get("fim", 0)) > float(l.get("inicio", 0))],
            key=lambda l: float(l.get("inicio", 0)),
        )
        blocos = []
        for i, l in enumerate(itens, start=1):
            ini = _fmt(float(l["inicio"]))
            fim = _fmt(float(l["fim"]))
            blocos.append(f"{i}\n{ini} --> {fim}\n{l['texto'].strip()}\n")
        Path(saida).write_text("\n".join(blocos), encoding="utf-8")
        print(f"[Engine] SRT com tempos reais: {len(blocos)} linhas -> {saida}")

    @staticmethod
    def _duracao_do_clipe(project, audio_path: Optional[str] = None) -> float:
        """Duração do clipe, em segundos.

        Regra do produto: **a música manda.** Se o usuário enviou a faixa
        pronta, o vídeo acompanha a duração dela — não os beats estimados.
        Sem música, cai na soma dos beats (ou 30s como piso).
        """
        if audio_path and Path(audio_path).exists():
            try:
                from moviepy import AudioFileClip
                with AudioFileClip(str(audio_path)) as af:
                    if af.duration and af.duration > 0:
                        return float(af.duration)
            except Exception:
                pass
        total = sum(getattr(b, "duration", 0) for b in getattr(project, "beats", []))
        return float(total) if total > 0 else 30.0

    def cancelar(self):
        self._cancelar = True
        self._gerando = False