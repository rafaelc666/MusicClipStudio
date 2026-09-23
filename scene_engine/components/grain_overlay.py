from pathlib import Path
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement
from .base import BaseComponent, ComponentRegistry


@ComponentRegistry.register("grain_overlay")
class GrainOverlay(BaseComponent):
    def render(self) -> Path:
        output_path = self.output_dir / "grain_overlay.html"
        html = self._generate_html()
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _generate_html(self) -> str:
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grain Overlay</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%);
            position: relative;
            overflow: hidden;
        }}
        .grain {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            opacity: 0.04;
            pointer-events: none;
            z-index: 9999;
            mix-blend-mode: overlay;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            animation: grainShift 0.5s steps(10) infinite;
        }}
        @keyframes grainShift {{
            0%, 100% {{ transform: translate(0, 0); }}
            10% {{ transform: translate(-5%, -10%); }}
            20% {{ transform: translate(-15%, 5%); }}
            30% {{ transform: translate(7%, -25%); }}
            40% {{ transform: translate(-5%, 25%); }}
            50% {{ transform: translate(-15%, 10%); }}
            60% {{ transform: translate(15%, 0%); }}
            70% {{ transform: translate(0%, 15%); }}
            80% {{ transform: translate(3%, 35%); }}
            90% {{ transform: translate(-10%, 10%); }}
        }}
        .demo-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-family: Arial, sans-serif;
            font-size: 24px;
            text-align: center;
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
    <div class="demo-text">
        Grain Overlay Demo<br>
        <small style="opacity: 0.6;">Textura de filme sutil (4% opacity)</small>
    </div>
    <div class="grain"></div>
    <div class="controls">
        <button onclick="toggleGrain()">Toggle Grain</button>
        <button onclick="changeOpacity()">Change Opacity</button>
    </div>
    <script>
        let grainEnabled = true;
        let opacities = [0.04, 0.02, 0.06, 0.08];
        let opacityIndex = 0;
        
        function toggleGrain() {{
            grainEnabled = !grainEnabled;
            document.querySelector('.grain').style.opacity = grainEnabled ? '0.04' : '0';
        }}
        
        function changeOpacity() {{
            opacityIndex = (opacityIndex + 1) % opacities.length;
            document.querySelector('.grain').style.opacity = opacities[opacityIndex];
        }}
    </script>
</body>
</html>'''
