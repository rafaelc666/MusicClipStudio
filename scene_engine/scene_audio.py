from pathlib import Path
from typing import Optional
from .scene_types import Beat


class SceneAudio:
    def __init__(self, project_dir: Path, engine: str = "piper"):
        self.project_dir = Path(project_dir)
        self.audio_dir = self.project_dir / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.engine = engine
        self._init_engine()

    def _init_engine(self):
        try:
            from core.narration import NarrationEngine
            self.narration_engine = NarrationEngine.get_engine(self.engine)
            print(f"[SceneAudio] Engine TTS: {self.engine}")
        except ImportError:
            print("[SceneAudio] AVISO: core.narration não disponível")
            self.narration_engine = None

    def generate_for_beats(self, beats: list[Beat], voice: str = "razo") -> list[Path]:
        audio_files = []
        
        for i, beat in enumerate(beats):
            if not beat.script:
                continue
                
            output_path = self.audio_dir / f"beat_{i:03d}.wav"
            
            if self.narration_engine:
                try:
                    result = self.narration_engine.generate(
                        text=beat.script,
                        output=output_path,
                        mode="single",
                        speaker=voice,
                    )
                    audio_files.append(result.audio_path)
                    print(f"[SceneAudio] Beat {i+1}: {output_path.name} ({result.duration:.1f}s)")
                except Exception as e:
                    print(f"[SceneAudio] Erro no beat {i+1}: {e}")
                    audio_files.append(None)
            else:
                audio_files.append(None)
        
        return audio_files

    def concatenate_audio(self, audio_files: list[Path], output_name: str = "narration.wav") -> Optional[Path]:
        valid_files = [f for f in audio_files if f and f.exists()]
        
        if not valid_files:
            print("[SceneAudio] Nenhum arquivo de áudio válido")
            return None
        
        output_path = self.audio_dir / output_name
        
        if len(valid_files) == 1:
            import shutil
            shutil.copy2(valid_files[0], output_path)
            return output_path
        
        return self._concat_with_ffmpeg(valid_files, output_path)

    def _concat_with_ffmpeg(self, files: list[Path], output: Path) -> Path:
        import subprocess
        
        concat_file = self.project_dir / "_concat_audio.txt"
        with open(concat_file, "w") as f:
            for file in files:
                f.write(f"file '{file.resolve()}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        concat_file.unlink()
        
        if result.returncode != 0:
            print(f"[SceneAudio] Erro: {result.stderr}")
            return None
        
        print(f"[SceneAudio] Áudio concatenado: {output}")
        return output

    def add_bed_music(
        self,
        narration_path: Path,
        bed_path: Path,
        output_path: Path,
        bed_volume: float = -20.0,
    ) -> Path:
        import subprocess
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(narration_path),
            "-i", str(bed_path),
            "-filter_complex",
            f"[1:a]volume={bed_volume}dB[bed];[0:a][bed]amix=inputs=2:duration=first:dropout_transition=2",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[SceneAudio] Erro: {result.stderr}")
            return narration_path
        
        print(f"[SceneAudio] Música de fundo adicionada: {output_path}")
        return output_path

    def get_duration(self, audio_path: Path) -> float:
        import subprocess
        
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            return float(result.stdout.strip())
        except:
            return 0.0
