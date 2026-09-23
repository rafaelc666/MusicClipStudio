from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("subtitle_burn")
class SubtitleBurn(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "subtitle_burn.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        script = self.element.script or "Texto de exemplo"
        accent = self.element.accent_color
        words = script.split()
        
        words_html = ""
        for i, word in enumerate(words):
            words_html += f'<span class="word" data-index="{i}">{word}</span> '

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subtitle Burn</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: #1A1A2E;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            padding-bottom: 60px;
            font-family: 'Montserrat', sans-serif;
        }}
        .subtitle-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 8px;
            padding: 20px 40px;
            background: rgba(0,0,0,0.6);
            border-radius: 8px;
        }}
        .word {{
            font-size: 36px;
            font-weight: 900;
            color: white;
            text-shadow: 
                2px 2px 0 black,
                -2px -2px 0 black,
                2px -2px 0 black,
                -2px 2px 0 black;
            transition: color 0.15s ease, text-shadow 0.15s ease;
            display: inline-block;
        }}
        .word.active {{
            color: {accent};
            text-shadow: 
                0 0 20px {accent},
                0 0 40px {accent},
                2px 2px 0 black,
                -2px -2px 0 black;
        }}
        .word.past {{
            color: rgba(255,255,255,0.6);
            text-shadow: 2px 2px 0 black;
        }}
        .controls {{
            position: fixed;
            top: 20px;
            right: 20px;
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
    </style>
</head>
<body>
    <div class="subtitle-container">{words_html}</div>
    <div class="controls">
        <button onclick="startAnimation()">Play</button>
        <button onclick="pauseAnimation()">Pause</button>
        <button onclick="resetAnimation()">Reset</button>
    </div>
    <script>
        const words = document.querySelectorAll('.word');
        let currentIndex = 0;
        let animationId = null;
        let isPlaying = false;
        
        function highlightWord(index) {{
            words.forEach((word, i) => {{
                word.classList.remove('active', 'past');
                if (i < index) word.classList.add('past');
                if (i === index) word.classList.add('active');
            }});
        }}
        
        function animate() {{
            if (currentIndex < words.length) {{
                highlightWord(currentIndex);
                currentIndex++;
                animationId = setTimeout(animate, 300);
            }} else {{
                isPlaying = false;
            }}
        }}
        
        function startAnimation() {{
            if (!isPlaying && currentIndex < words.length) {{
                isPlaying = true;
                animate();
            }}
        }}
        
        function pauseAnimation() {{
            isPlaying = false;
            clearTimeout(animationId);
        }}
        
        function resetAnimation() {{
            pauseAnimation();
            currentIndex = 0;
            words.forEach(word => word.classList.remove('active', 'past'));
        }}
        
        // Auto-start
        startAnimation();
    </script>
</body>
</html>'''
