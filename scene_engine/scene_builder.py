from pathlib import Path
from .scene_types import Beat, VisualElement, SceneStyle, FPS, WIDTH, HEIGHT


class SceneBuilder:
    def __init__(
        self,
        output_dir: Path,
        width: int = WIDTH,
        height: int = HEIGHT,
        fps: int = FPS,
        style: SceneStyle = SceneStyle.VOX_EDITORIAL,
    ):
        self.output_dir = Path(output_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.style = style
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_scene_from_script(self, beats: list[Beat], scene_id: str = "scene") -> dict:
        total_duration = sum(beat.duration for beat in beats)
        
        layers = []
        current_time = 0.0
        
        for i, beat in enumerate(beats):
            layer = {
                "id": f"layer_{i}",
                "beat_id": beat.id,
                "type": beat.type,
                "start_time": current_time,
                "duration": beat.duration,
                "visual": {
                    "type": beat.visual.type,
                    "data": self._extract_visual_data(beat.visual),
                },
            }
            layers.append(layer)
            current_time += beat.duration
        
        return {
            "scene_id": scene_id,
            "duration": total_duration,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "profile": self.style.value,
            "layers": layers,
            "total_frames": int(total_duration * self.fps),
        }

    def _extract_visual_data(self, visual: VisualElement) -> dict:
        data = {
            "type": visual.type,
            "accent_color": visual.accent_color,
        }
        
        if visual.text:
            data["text"] = visual.text
        if visual.images:
            data["images"] = visual.images
        if visual.annotation:
            data["annotation"] = visual.annotation
        if visual.speaker_name:
            data["speaker_name"] = visual.speaker_name
        if visual.speaker_title:
            data["speaker_title"] = visual.speaker_title
        if visual.quote_text:
            data["quote_text"] = visual.quote_text
        
        return data

    def get_layer_config(self, beat_type: str) -> dict:
        configs = {
            "hook": {"z_index": 10, "opacity": 1.0, "priority": "high"},
            "context": {"z_index": 5, "opacity": 1.0, "priority": "medium"},
            "data_reveal": {"z_index": 20, "opacity": 1.0, "priority": "high"},
            "expert_quote": {"z_index": 15, "opacity": 1.0, "priority": "medium"},
            "conclusion": {"z_index": 10, "opacity": 1.0, "priority": "high"},
            "transition": {"z_index": 1, "opacity": 0.5, "priority": "low"},
        }
        return configs.get(beat_type, {"z_index": 5, "opacity": 1.0, "priority": "medium"})

    def export_scene_json(self, scene_data: dict, output_path: Path = None) -> Path:
        if output_path is None:
            output_path = self.output_dir / f"{scene_data['scene_id']}_schema.json"
        
        import json
        output_path.write_text(json.dumps(scene_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[SceneBuilder] Schema exportado: {output_path}")
        return output_path

    @staticmethod
    def create_beat(
        beat_id: int,
        beat_type: str,
        script: str,
        visual_type: str,
        duration: float = 5.0,
        **visual_kwargs,
    ) -> Beat:
        visual = VisualElement(
            type=visual_type,
            text=visual_kwargs.get("text"),
            images=visual_kwargs.get("images", []),
            annotation=visual_kwargs.get("annotation"),
            speaker_name=visual_kwargs.get("speaker_name"),
            speaker_title=visual_kwargs.get("speaker_title"),
            quote_text=visual_kwargs.get("quote_text"),
            accent_color=visual_kwargs.get("accent_color", "#FFCC00"),
            animation=visual_kwargs.get("animation", "fade_in"),
        )
        
        return Beat(
            id=beat_id,
            type=beat_type,
            duration=duration,
            script=script,
            visual=visual,
        )
