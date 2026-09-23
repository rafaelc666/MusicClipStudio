"""Renderizador experimental orientado pelo contrato de cenas."""
from html import escape
import json
from pathlib import Path

BASE = Path(__file__).parent
TEMPLATE = BASE / "demo.html"
SCHEMA = BASE / "scene_schema.json"
GENERATED = BASE / "_generated_scene.html"


def load_scene(path: Path = SCHEMA) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _layer(scene: dict, layer_id: str) -> dict:
    return next((item for item in scene.get("layers", []) if item.get("id") == layer_id), {})


def scene_to_html(scene: dict, template: str) -> str:
    headline = _layer(scene, "headline").get("content", "O detalhe que muda a história")
    stat = _layer(scene, "stat-card")
    value = stat.get("value", 860)
    suffix = stat.get("suffix", "")
    label = stat.get("label", "dado em destaque")
    waveform = _layer(scene, "waveform")
    lower = _layer(scene, "lower-third")
    waveform_label = waveform.get("label", "padrão detectado")
    speaker_name = lower.get("speaker_name", "Arquivo Vox")
    speaker_title = lower.get("speaker_title", "Demonstração editorial")
    words = escape(str(headline)).split()
    headline_html = "<br>".join(words[:2])
    if len(words) > 2:
        headline_html += "<br><em>" + " ".join(words[2:]) + "</em>"
    replacements = {
        "O detalhe<br>que <em>muda</em><br>a história": headline_html,
        '<div class="label">descarga registrada</div>': f'<div class="label">{escape(str(label))}</div>',
        '<div class="lower-third" data-layer="lower-third"><strong>Arquivo Vox</strong><small>Demonstração editorial</small></div>': f'<div class="lower-third" data-layer="lower-third"><strong>{escape(str(speaker_name))}</strong><small>{escape(str(speaker_title))}</small></div>',
        'Math.round(860 * seconds)': f'Math.round({float(value)} * seconds)',
        '>0</div><div class="label">': f'>{escape(str(value))}{escape(str(suffix))}</div><div class="label">',
    }
    for old, new in replacements.items():
        template = template.replace(old, new)
    return template


def build_scene_html(scene_path: Path = SCHEMA, output_path: Path = GENERATED) -> Path:
    scene = load_scene(scene_path)
    html = scene_to_html(scene, TEMPLATE.read_text(encoding="utf-8"))
    output_path.write_text(html, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    print(build_scene_html())
