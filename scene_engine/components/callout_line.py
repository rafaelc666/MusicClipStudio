from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("callout_line")
class CalloutLine(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "callout_line.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        annotation = self.element.annotation or {}
        x1 = annotation.get("x1", 20)
        y1 = annotation.get("y1", 50)
        x2 = annotation.get("x2", 80)
        y2 = annotation.get("y2", 50)
        accent = self.element.accent_color
        
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Callout Line</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: #1A1A2E;
            position: relative;
            overflow: hidden;
        }}
        .callout-svg {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
        }}
        .callout-line {{
            stroke: {accent};
            stroke-width: 3;
            stroke-dasharray: {length * 10};
            stroke-dashoffset: {length * 10};
            animation: drawLine 1s ease-out forwards;
        }}
        .endpoint {{
            fill: {accent};
            transform: scale(0);
            animation: popIn 0.3s ease-out 0.8s forwards;
        }}
        @keyframes drawLine {{
            0% {{ stroke-dashoffset: {length * 10}; }}
            100% {{ stroke-dashoffset: 0; }}
        }}
        @keyframes popIn {{
            0% {{ transform: scale(0); }}
            70% {{ transform: scale(1.3); }}
            100% {{ transform: scale(1); }}
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
    <svg class="callout-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
        <line 
            class="callout-line" 
            x1="{x1}" 
            y1="{y1}" 
            x2="{x2}" 
            y2="{y2}"
            stroke-linecap="round"
        />
        <circle class="endpoint" cx="{x2}" cy="{y2}" r="2"/>
    </svg>
    <div class="controls">
        <button onclick="restart()">Restart</button>
    </div>
    <script>
        function restart() {{
            document.querySelector('.callout-line').style.animation = 'none';
            document.querySelector('.callout-line').offsetHeight;
            document.querySelector('.callout-line').style.animation = '';
            
            document.querySelector('.endpoint').style.animation = 'none';
            document.querySelector('.endpoint').offsetHeight;
            document.querySelector('.endpoint').style.animation = '';
        }}
    </script>
</body>
</html>'''
