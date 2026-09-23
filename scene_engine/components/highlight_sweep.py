from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("highlight_sweep")
class HighlightSweep(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "highlight_sweep.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        text = self.element.text or "Texto em destaque"
        accent = self.element.accent_color

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Highlight Sweep</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: #1A1A2E;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Montserrat', sans-serif;
        }}
        .highlight-container {{
            position: relative;
            display: inline-block;
        }}
        .highlight-bg {{
            position: absolute;
            top: 10%;
            left: 0;
            height: 80%;
            width: 0;
            background: {accent};
            opacity: 0.3;
            border-radius: 4px;
            z-index: -1;
            animation: sweep 1.5s ease-out forwards;
        }}
        .highlight-text {{
            font-size: 72px;
            font-weight: 900;
            color: white;
            text-transform: uppercase;
        }}
        @keyframes sweep {{
            0% {{ width: 0; }}
            100% {{ width: 100%; }}
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
    <div class="highlight-container">
        <div class="highlight-bg"></div>
        <div class="highlight-text">{text}</div>
    </div>
    <div class="controls">
        <button onclick="restart()">Restart</button>
    </div>
    <script>
        function restart() {{
            const bg = document.querySelector('.highlight-bg');
            bg.style.animation = 'none';
            bg.offsetHeight;
            bg.style.animation = '';
        }}
    </script>
</body>
</html>'''
