from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("kinetic_title")
class KineticTitle(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / f"kinetic_title_{self.element.text[:20]}.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        words = self.element.text.split() if self.element.text else []
        accent = self.element.accent_color
        bg = self.element.bg_color or "#1A1A2E"
        
        words_html = ""
        for i, word in enumerate(words):
            delay = i * 5
            words_html += f'''
                <span class="word" style="--delay: {delay};">{word}</span>
            ''' if i > 0 else f'<span class="word first" style="--delay: 0;">{word}</span>'

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kinetic Title</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: {bg};
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            font-family: 'Montserrat', sans-serif;
        }}
        .container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 16px;
        }}
        .word {{
            font-size: 72px;
            font-weight: 900;
            color: white;
            opacity: 0;
            transform: scale(0.8);
            display: inline-block;
            white-space: nowrap;
            text-shadow: 0 0 20px {accent}, 0 0 40px {accent};
            animation: wordIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
            animation-delay: calc(var(--delay) * 100ms);
        }}
        .word.first {{
            color: {accent};
        }}
        .word em {{
            font-style: normal;
            color: {accent};
        }}
        @keyframes wordIn {{
            0% {{
                opacity: 0;
                transform: scale(0.8) translateY(20px);
            }}
            100% {{
                opacity: 1;
                transform: scale(1) translateY(0);
            }}
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
        }}
        button {{
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            cursor: pointer;
            border-radius: 4px;
        }}
        button:hover {{
            background: rgba(255,255,255,0.3);
        }}
    </style>
</head>
<body>
    <div class="container">{words_html}</div>
    <div class="controls">
        <button onclick="togglePlay()">Play/Pause</button>
        <button onclick="restart()">Restart</button>
    </div>
    <script>
        let paused = false;
        function togglePlay() {{
            paused = !paused;
            document.body.style.animationPlayState = paused ? 'paused' : 'running';
        }}
        function restart() {{
            document.querySelectorAll('.word').forEach(w => {{
                w.style.animation = 'none';
                w.offsetHeight;
                w.style.animation = '';
            }});
        }}
    </script>
</body>
</html>'''
