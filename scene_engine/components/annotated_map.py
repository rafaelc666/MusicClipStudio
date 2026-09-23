from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("annotated_map")
class AnnotatedMap(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "annotated_map.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        annotation = self.element.annotation or {"x": 0.5, "y": 0.5, "label": "Local"}
        accent = self.element.accent_color
        
        x_pct = annotation.get("x", 0.5) * 100
        y_pct = annotation.get("y", 0.5) * 100
        label = annotation.get("label", "Local")
        value = annotation.get("value", "")

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Annotated Map</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: #16213E;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Inter', sans-serif;
        }}
        .map-container {{
            width: 80%;
            height: 80%;
            position: relative;
        }}
        .map-svg {{
            width: 100%;
            height: 100%;
            opacity: 0.3;
        }}
        .annotation {{
            position: absolute;
            left: {x_pct}%;
            top: {y_pct}%;
            transform: translate(-50%, -50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: annotationIn 1s ease-out forwards;
            opacity: 0;
        }}
        .pulse-dot {{
            width: 20px;
            height: 20px;
            background: {accent};
            border-radius: 50%;
            box-shadow: 0 0 20px {accent}, 0 0 40px {accent};
            animation: pulse 2s ease-in-out infinite;
        }}
        .ripple {{
            position: absolute;
            width: 40px;
            height: 40px;
            border: 2px solid {accent};
            border-radius: 50%;
            animation: ripple 2s ease-out infinite;
        }}
        .label-box {{
            background: rgba(26, 26, 46, 0.95);
            padding: 12px 20px;
            border-left: 4px solid {accent};
            margin-top: 15px;
            animation: labelIn 0.5s ease-out 0.5s forwards;
            opacity: 0;
        }}
        .label-title {{
            font-family: 'Montserrat', sans-serif;
            font-size: 24px;
            font-weight: 700;
            color: white;
        }}
        .label-value {{
            font-size: 18px;
            color: {accent};
            margin-top: 4px;
        }}
        @keyframes annotationIn {{
            0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0); }}
            100% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.2); }}
        }}
        @keyframes ripple {{
            0% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.6; }}
            100% {{ transform: translate(-50%, -50%) scale(3); opacity: 0; }}
        }}
        @keyframes labelIn {{
            0% {{ opacity: 0; transform: translateY(10px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
        }}
        button {{
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="map-container">
        <svg class="map-svg" viewBox="0 0 100 100">
            <rect x="0" y="0" width="100" height="100" fill="none" stroke="#B8B8D1" stroke-width="0.5"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="#B8B8D1" stroke-width="0.3"/>
            <line x1="0" y1="50" x2="100" y2="50" stroke="#B8B8D1" stroke-width="0.2"/>
            <line x1="50" y1="0" x2="50" y2="100" stroke="#B8B8D1" stroke-width="0.2"/>
        </svg>
        <div class="annotation">
            <div class="ripple"></div>
            <div class="pulse-dot"></div>
            <div class="label-box">
                <div class="label-title">{label}</div>
                {f'<div class="label-value">{value}</div>' if value else ''}
            </div>
        </div>
    </div>
    <div class="controls">
        <button onclick="togglePlay()">Play/Pause</button>
    </div>
    <script>
        let paused = false;
        function togglePlay() {{
            paused = !paused;
            document.body.style.animationPlayState = paused ? 'paused' : 'running';
            document.querySelectorAll('.annotation, .label-box').forEach(el => {{
                el.style.animationPlayState = paused ? 'paused' : 'running';
            }});
        }}
    </script>
</body>
</html>'''
