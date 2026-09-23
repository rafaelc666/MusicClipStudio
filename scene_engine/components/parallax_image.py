from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("parallax_image")
class ParallaxImage(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "parallax_image.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        images = self.element.images or ["background.jpg"]
        accent = self.element.accent_color
        
        images_html = ""
        for i, img in enumerate(images):
            images_html += f'<img src="{img}" alt="" class="slide" style="--slide-index: {i}">'

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parallax Image</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: #1A1A2E;
            overflow: hidden;
            position: relative;
        }}
        .slides {{
            position: absolute;
            inset: 0;
        }}
        .slide {{
            position: absolute;
            inset: -5%;
            background-size: cover;
            background-position: center;
            opacity: 0;
            transform: scale(1.05);
            animation: kenBurns 12s ease-in-out infinite;
            animation-delay: calc(var(--slide-index) * 12s);
        }}
        .slide:first-child {{
            opacity: 1;
            animation-delay: 0s;
        }}
        .overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(
                to top,
                rgba(10, 10, 20, 0.8) 0%,
                transparent 50%
            );
        }}
        @keyframes kenBurns {{
            0% {{
                opacity: 1;
                transform: scale(1.05) translate(-2%, -2%);
            }}
            50% {{
                opacity: 1;
                transform: scale(1.15) translate(2%, 2%);
            }}
            100% {{
                opacity: 0;
                transform: scale(1.05) translate(-2%, -2%);
            }}
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
    <div class="slides">{images_html}</div>
    <div class="overlay"></div>
    <div class="controls">
        <button onclick="togglePlay()">Play/Pause</button>
    </div>
    <script>
        let paused = false;
        function togglePlay() {{
            paused = !paused;
            document.querySelectorAll('.slide').forEach(s => {{
                s.style.animationPlayState = paused ? 'paused' : 'running';
            }});
        }}
    </script>
</body>
</html>'''
