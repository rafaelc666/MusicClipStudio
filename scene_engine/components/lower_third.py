from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("lower_third")
class LowerThird(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "lower_third.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        name = self.element.speaker_name or "Arquivo Vox"
        title = self.element.speaker_title or "Demonstração"
        quote = self.element.quote_text or ""
        accent = self.element.accent_color

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lower Third</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: #1A1A2E;
            display: flex;
            align-items: flex-end;
            justify-content: flex-start;
            padding: 0 0 80px 60px;
            font-family: 'Inter', sans-serif;
        }}
        .content {{
            max-width: 70%;
        }}
        .bar {{
            height: 4px;
            background: {accent};
            width: 0;
            margin-bottom: 16px;
            box-shadow: 0 0 10px {accent};
            animation: barExpand 0.8s ease-out forwards;
        }}
        .text-content {{
            transform: translateY(30px);
            opacity: 0;
            animation: textIn 0.6s ease-out 0.4s forwards;
        }}
        .name {{
            font-family: 'Montserrat', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: white;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .speaker-title {{
            font-size: 18px;
            color: #B8B8D1;
            margin-top: 4px;
        }}
        .quote {{
            margin-top: 24px;
            padding-left: 20px;
            border-left: 3px solid {accent};
            font-family: Georgia, serif;
            font-size: 20px;
            color: white;
            font-style: italic;
            line-height: 1.5;
            transform: translateY(30px);
            opacity: 0;
            animation: textIn 0.6s ease-out 0.8s forwards;
        }}
        @keyframes barExpand {{
            0% {{ width: 0; }}
            100% {{ width: 120px; }}
        }}
        @keyframes textIn {{
            0% {{
                transform: translateY(30px);
                opacity: 0;
            }}
            100% {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
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
    <div class="content">
        <div class="bar"></div>
        <div class="text-content">
            <div class="name">{name}</div>
            <div class="speaker-title">{title}</div>
        </div>
        {f'<div class="quote">"{quote}"</div>' if quote else ''}
    </div>
    <div class="controls">
        <button onclick="restart()">Restart</button>
    </div>
    <script>
        function restart() {{
            document.querySelector('.bar').style.animation = 'none';
            document.querySelector('.bar').offsetHeight;
            document.querySelector('.bar').style.animation = '';
            
            document.querySelector('.text-content').style.animation = 'none';
            document.querySelector('.text-content').offsetHeight;
            document.querySelector('.text-content').style.animation = '';
            
            const quote = document.querySelector('.quote');
            if (quote) {{
                quote.style.animation = 'none';
                quote.offsetHeight;
                quote.style.animation = '';
            }}
        }}
    </script>
</body>
</html>'''
