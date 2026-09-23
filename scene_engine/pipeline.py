import json
from pathlib import Path
from typing import Optional
from .scene_types import Beat, VideoScript, SceneStyle, VisualElement
from .scene_builder import SceneBuilder
from .renderers.html_renderer import HTMLRenderer
from .renderers.video_renderer import VideoRenderer
from .compositor import Compositor
from .scene_audio import SceneAudio


class VoxPipeline:
    def __init__(
        self,
        project_dir: Path,
        width: int = 1920,
        height: int = 1080,
        fps: int = 24,
        style: SceneStyle = SceneStyle.VOX_EDITORIAL,
    ):
        self.project_dir = Path(project_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.style = style
        
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        self.scenes_dir = self.project_dir / "scenes"
        self.output_dir = self.project_dir / "output"
        self.temp_dir = self.project_dir / "_temp"
        
        for d in [self.scenes_dir, self.output_dir, self.temp_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.scene_builder = SceneBuilder(
            output_dir=self.scenes_dir,
            width=width,
            height=height,
            fps=fps,
            style=style,
        )
        self.html_renderer = HTMLRenderer(
            output_dir=self.temp_dir,
            width=width,
            height=height,
            fps=fps,
        )
        self.video_renderer = VideoRenderer(
            output_dir=self.temp_dir,
            width=width,
            height=height,
            fps=fps,
        )
        self.compositor = Compositor(output_dir=self.temp_dir)
        
        print(f"[VoxPipeline] Inicializado em: {self.project_dir}")

    def create_script_from_beats(self, beats: list[Beat]) -> VideoScript:
        metadata = {
            "style": self.style.value,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "total_duration": sum(b.duration for b in beats),
        }
        return VideoScript(
            metadata=metadata,
            beats=beats,
            style=self.style,
        )

    def render_preview(self, beats: list[Beat], output_name: str = "preview.html") -> Path:
        print(f"[VoxPipeline] Renderizando preview HTML...")
        return self.html_renderer.create_composition_html(beats, output_name, self.style)

    def render_video(
        self,
        beats: list[Beat],
        output_name: str = "video.mp4",
        audio_path: Optional[Path] = None,
        with_subtitles: bool = False,
        subtitles_path: Optional[Path] = None,
    ) -> Path:
        print(f"[VoxPipeline] Renderizando vídeo...")
        
        scene_data = self.scene_builder.create_scene_from_script(beats, "main_scene")
        self.scene_builder.export_scene_json(scene_data)
        
        preview_html = self.render_preview(beats, "main_scene.html")
        
        total_duration = sum(beat.duration for beat in beats)
        video_path = self.output_dir / output_name
        
        self.video_renderer.render_html_to_video(
            html_path=preview_html,
            output_path=video_path,
            duration=total_duration,
            fps=self.fps,
        )
        
        if audio_path and Path(audio_path).exists():
            final_path = self.output_dir / f"final_{output_name}"
            self.video_renderer.add_audio_to_video(
                video_path=video_path,
                audio_path=audio_path,
                output_path=final_path,
            )
            video_path = final_path
        
        if with_subtitles and subtitles_path and Path(subtitles_path).exists():
            final_path = self.output_dir / f"subtitled_{output_name}"
            self.compositor.add_subtitles(video_path, subtitles_path, final_path)
            video_path = final_path
        
        print(f"[VoxPipeline] ✓ Vídeo pronto: {video_path}")
        return video_path

    def generate_audio(self, beats: list[Beat], voice: str = "razo") -> Optional[Path]:
        print(f"[VoxPipeline] Gerando áudio...")
        self.scene_audio = SceneAudio(self.project_dir, engine="piper")
        
        audio_files = self.scene_audio.generate_for_beats(beats, voice)
        narration = self.scene_audio.concatenate_audio(audio_files, "narration.wav")
        
        if narration:
            print(f"[VoxPipeline] ✓ Narração pronta: {narration}")
        return narration

    def render_with_audio(
        self,
        beats: list[Beat],
        output_name: str = "video_com_audio.mp4",
        voice: str = "razo",
        audio_path: Optional[Path] = None,
    ) -> Path:
        if audio_path is None:
            audio_path = self.generate_audio(beats, voice)
        
        if audio_path is None:
            print("[VoxPipeline] ERRO: Áudio não disponível")
            return self.render_video(beats, output_name)
        
        return self.render_video(beats, output_name, audio_path=audio_path)

    def export_script(self, script: VideoScript, output_name: str = "script.json") -> Path:
        output_path = self.project_dir / output_name
        
        data = {
            "metadata": script.metadata,
            "style": script.style.value,
            "beats": [
                {
                    "id": b.id,
                    "type": b.type,
                    "duration": b.duration,
                    "script": b.script,
                    "visual": {
                        "type": b.visual.type,
                        "text": b.visual.text,
                        "images": b.visual.images,
                        "annotation": b.visual.annotation,
                        "speaker_name": b.visual.speaker_name,
                        "speaker_title": b.visual.speaker_title,
                        "quote_text": b.visual.quote_text,
                        "accent_color": b.visual.accent_color,
                    },
                }
                for b in script.beats
            ],
        }
        
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[VoxPipeline] Script exportado: {output_path}")
        return output_path

    def cleanup(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print("[VoxPipeline] Limpeza concluída")


def demo():
    project = VoxPipeline(Path("D:/dev-projetos/BlueBookStudio/scene_engine/test_project"))
    
    beats = [
        SceneBuilder.create_beat(
            beat_id=1,
            beat_type="hook",
            script="Você sabia que...",
            visual_type="kinetic_title",
            text="COMO O MUNDO FUNCIONA",
            duration=5.0,
        ),
        SceneBuilder.create_beat(
            beat_id=2,
            beat_type="context",
            script="A história começa aqui...",
            visual_type="parallax_image",
            images=["https://picsum.photos/1920/1080"],
            duration=8.0,
        ),
        SceneBuilder.create_beat(
            beat_id=3,
            beat_type="expert_quote",
            script="Segundo especialistas...",
            visual_type="lower_third",
            speaker_name="Dr. Rafael",
            speaker_title="Pesquisador",
            quote_text="A verdade está nos detalhes",
            duration=6.0,
        ),
    ]
    
    preview_path = project.render_preview(beats)
    print(f"Preview: {preview_path}")
    
    script = project.create_script_from_beats(beats)
    project.export_script(script)


if __name__ == "__main__":
    demo()
