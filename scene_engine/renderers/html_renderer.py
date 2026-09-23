import json
from pathlib import Path
from typing import Optional
from ..scene_types import FPS, WIDTH, HEIGHT, Beat, VisualElement, SceneStyle


# Efeitos de imagem aceitos. São os MESMOS ids que o frontend oferece na
# etapa 05 — se alguém inventar um nome novo aqui sem mexer lá (ou vice-versa),
# a imagem cai em ken_burns em vez de ficar sem animação nenhuma.
EFEITOS_IMAGEM: tuple[str, ...] = (
    "ken_burns", "zoom_in", "zoom_out", "pan_left", "pan_right", "static",
)


def _classe_efeito(animation: Optional[str]) -> str:
    """Converte o efeito escolhido na classe CSS `.fx-*`.

    Desconhecido/vazio → ken_burns (o padrão histórico do motor).
    """
    nome = (animation or "").strip().lower()
    return f"fx-{nome}" if nome in EFEITOS_IMAGEM else "fx-ken_burns"


# Extensões que indicam que a "imagem" do beat é na verdade um VÍDEO.
# Metade dos resultados do stock é vídeo (verificado: 5 de 10 numa busca
# genérica) e o `url_full` vem como .mp4 — sem este tratamento o composer
# escrevia background-image: url('*.mp4'), que não desenha nada.
_EXT_VIDEO = (".mp4", ".webm", ".mov", ".m4v", ".ogv")


def _eh_video(url: Optional[str]) -> bool:
    """Diz se a URL aponta para um vídeo (não para uma imagem)."""
    if not url:
        return False
    u = url.split("?", 1)[0].lower()
    return u.endswith(_EXT_VIDEO) or "/video-files/" in u


class HTMLRenderer:
    def __init__(
        self,
        output_dir: Path,
        width: int = WIDTH,
        height: int = HEIGHT,
        fps: int = FPS,
    ):
        self.output_dir = Path(output_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_beat(self, beat: Beat, style: SceneStyle = SceneStyle.VOX_EDITORIAL) -> Path:
        visual = beat.visual
        component_type = visual.type
        
        from components.base import ComponentRegistry
        
        component_class = ComponentRegistry.get(component_type)
        if not component_class:
            raise ValueError(f"Componente '{component_type}' não encontrado")
        
        component = component_class(
            element=visual,
            output_dir=self.output_dir,
            width=self.width,
            height=self.height,
            fps=self.fps,
        )
        
        return component.render()

    def render_full_scene(self, beats: list[Beat], scene_id: str = "scene") -> list[Path]:
        paths = []
        for i, beat in enumerate(beats):
            try:
                path = self.render_beat(beat)
                paths.append(path)
                print(f"[HTMLRenderer] Beat {i+1}/{len(beats)}: {path.name}")
            except Exception as e:
                print(f"[HTMLRenderer] Erro no beat {i+1}: {e}")
        return paths

    def create_composition_html(
        self,
        beats: list[Beat],
        output_name: str = "composition.html",
        style: SceneStyle = SceneStyle.VOX_EDITORIAL,
        scene_id: str = "scene",
        # ⚠️ NOVO (23/09/2026) — REGRA DO PRODUTO: "o vídeo tem o tamanho do
        # áudio". Quando a soma dos beats é MENOR que a música, o último
        # beat se estende até a duração total (a imagem fica até o fim, o
        # vídeo em loop continua). Sem isso, o fim do clipe ficava PRETO.
        duracao_total: Optional[float] = None,
    ) -> Path:
        output_path = self.output_dir / output_name
        colors = self._get_style_colors(style)
        total_duration = sum(b.duration for b in beats)
        
        beats_html = ""
        for i, beat in enumerate(beats):
            visual = beat.visual
            start = sum(b.duration for b in beats[:i])
            end = start + beat.duration
            # ⚠️ REGRA (23/09/2026): último beat cobre até o fim da música —
            # sem isso, beats acabando antes do áudio deixavam o fim PRETO.
            # (1 imagem fica a música toda; 1 vídeo roda em loop até o fim.)
            if duracao_total and duracao_total > total_duration and i == len(beats) - 1:
                end = float(duracao_total)
            beat_class = f"beat beat-{i} beat-{visual.type.replace('_', '-')}"
            
            if visual.type == "kinetic_title":
                words = (visual.text or "").split()
                words_html = " ".join(f'<span class="word">{w}</span>' for w in words)
                beats_html += f'''
                <div class="{beat_class}" data-start="{start}" data-end="{end}">
                    <div class="beat-content">{words_html}</div>
                </div>'''
            elif visual.type == "parallax_image":
                img = visual.images[0] if visual.images else "background.jpg"
                # Efeito escolhido para ESTA imagem na etapa 05.
                fx = _classe_efeito(visual.animation)
                # ⚠️ VÍDEO: metade do stock é vídeo. Sem este ramo o mp4
                # virava background-image e o beat saía em branco.
                #
                # REGRA DE CORTE (21/09/2026) — escolhida pelo usuário:
                # "fundo com blur, só na divergência".
                #
                # São DUAS camadas:
                #   .parallax-fill  -> cover + blur + escurecida (o "fundo")
                #   .parallax-main  -> contain (a mídia inteira, sem corte)
                #
                # O "só na divergência" sai de graça do CSS: quando a
                # orientação da mídia bate com a do quadro, `contain` e
                # `cover` dão o mesmo resultado, a camada do meio cobre o
                # fundo inteiro e o blur nunca aparece. Quando diverge,
                # sobram faixas e elas são preenchidas pelo desfoque.
                if _eh_video(img):
                    fundo = (
                        f'<video class="parallax-fill-video" src="{img}" '
                        f'autoplay loop muted playsinline preload="auto"></video>'
                    )
                    principal = (
                        f'<video class="parallax-main-video" src="{img}" '
                        f'autoplay loop muted playsinline preload="auto"></video>'
                    )
                else:
                    fundo = (
                        f'<div class="parallax-fill" '
                        f'style="background-image: url(\'{img}\')"></div>'
                    )
                    principal = (
                        f'<div class="parallax-main" '
                        f'style="background-image: url(\'{img}\')"></div>'
                    )
                beats_html += f'''
                <div class="{beat_class}" data-start="{start}" data-end="{end}">
                    <div class="parallax-bg {fx}">{fundo}{principal}</div>
                </div>'''
            elif visual.type == "lower_third":
                beats_html += f'''
                <div class="{beat_class}" data-start="{start}" data-end="{end}">
                    <div class="lower-third">
                        <div class="bar"></div>
                        <div class="name">{visual.speaker_name or "Vox"}</div>
                        <div class="title">{visual.speaker_title or "Narrador"}</div>
                        {f'<div class="quote">"{visual.quote_text}"</div>' if visual.quote_text else ''}
                    </div>
                </div>'''
            elif visual.type == "annotated_map":
                ann = visual.annotation or {}
                beats_html += f'''
                <div class="{beat_class}" data-start="{start}" data-end="{end}">
                    <div class="map-container">
                        <svg class="map"><circle cx="50" cy="50" r="40" fill="none" stroke="{colors['secondary']}" stroke-width="0.5"/></svg>
                        <div class="annotation" style="left:{ann.get('x', 0.5)*100}%;top:{ann.get('y', 0.5)*100}%">
                            <div class="pulse"></div>
                            <div class="label">{ann.get('label', 'Local')}</div>
                        </div>
                    </div>
                </div>'''
            elif visual.type == "highlight_sweep":
                accent = visual.accent_color or colors['accent']
                beats_html += f'''
                <div class="{beat_class}" data-start="{start}" data-end="{end}">
                    <div class="highlight-container">
                        <div class="highlight-bg" style="background:{accent}"></div>
                        <div class="highlight-text">{visual.text or "DESTAQUE"}</div>
                    </div>
                </div>'''
            elif visual.type == "subtitle_burn":
                words = (visual.text or beat.script or "").split()
                words_html = " ".join(f'<span class="sub-word">{w}</span>' for w in words)
                beats_html += f'''
                <div class="{beat_class}" data-start="{start}" data-end="{end}">
                    <div class="subtitle-container">{words_html}</div>
                </div>'''

        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scene Composition - {scene_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;900&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: {colors['primary']};
            --bg-secondary: {colors['secondary']};
            --accent: {colors['accent']};
            --text-primary: {colors['text']};
            --text-secondary: {colors['text_secondary']};
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {self.width}px;
            height: {self.height}px;
            background: var(--bg-primary);
            overflow: hidden;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Container principal */
        .scene {{
            position: relative;
            width: 100%;
            height: 100%;
        }}
        
        /* Beat em posição absoluta, transição simples */
        .beat {{
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            visibility: hidden;
            opacity: 0;
        }}
        .beat.visible {{
            visibility: visible;
            opacity: 1;
        }}
        
        /* TÍTULO CINÉTICO */
        .beat-kinetic .beat-content {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 16px;
            padding: 40px;
            max-width: 90%;
        }}
        .beat-kinetic .word {{
            font-family: 'Montserrat', sans-serif;
            font-size: 72px;
            font-weight: 900;
            color: var(--text-primary);
            text-shadow: 0 0 20px var(--accent);
        }}
        .beat-kinetic .word:first-child {{
            color: var(--accent);
        }}

        /* IMAGEM DE FUNDO — ⚠️ CORRIGIDO (21/09/2026)
           A div .parallax-bg era escrita no HTML mas NÃO EXISTIA nenhuma
           regra de CSS para ela aqui: sem position/size, o background-image
           não tinha área para desenhar e a imagem simplesmente não
           aparecia no vídeo. O clipe saía com o fundo sólido do corpo. */
        /* ⚠️ REGRA DE CORTE (21/09/2026) — decidida com o usuário:
           "fundo com blur, só na divergência".

           Antes era `cover` puro: a mídia preenchia o quadro e o excesso
           era cortado pelo centro. Numa foto 16:9 para saída 9/16 isso
           descartava ~69% da largura — metade da cena ia fora.

           Agora são duas camadas:
             .parallax-fill -> cover + blur + escurecida  (o fundo)
             .parallax-main -> contain                    (a mídia inteira)

           O "só na divergência" sai de graça do CSS: quando a orientação
           da mídia bate com a do quadro, `contain` e `cover` dão o mesmo
           resultado, a camada da frente cobre o fundo inteiro e o blur
           nunca aparece. Quando diverge, sobram faixas — e elas são
           preenchidas pelo desfoque da própria imagem.

           O `inset: 0` (antes -6%) é de propósito: com `contain` o
           -6% faria a mídia crescer 12% e vazar do quadro. A folga para
           os efeitos de pan/zoom vem do próprio `scale` da animação. */
        .parallax-bg {{
            position: absolute;
            inset: 0;
            overflow: hidden;
            will-change: transform;
        }}

        /* FUNDO: só aparece quando sobra faixa. O scale(1.25) empurra as
           bordas translúcidas do blur para fora do quadro. */
        .parallax-fill {{
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            filter: blur(28px) brightness(0.55);
            transform: scale(1.25);
        }}

        /* MÍDIA: entra inteira, sem corte e sem distorção. */
        .parallax-main {{
            position: absolute;
            inset: 0;
            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;
        }}

        /* A mesma dupla para vídeo de banco (Pexels/Coverr). */
        .parallax-fill-video {{
            position: absolute;
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            display: block;
            filter: blur(28px) brightness(0.55);
            transform: scale(1.25);
        }}
        .parallax-main-video {{
            position: absolute;
            width: 100%;
            height: 100%;
            object-fit: contain;
            object-position: center;
            display: block;
        }}

        /* EFEITO POR IMAGEM — o id vem do seletor da etapa 05 */
        .fx-ken_burns {{ animation: fxKenBurns 12s ease-in-out infinite; }}
        .fx-zoom_in   {{ animation: fxZoomIn 12s ease-in-out infinite; }}
        .fx-zoom_out  {{ animation: fxZoomOut 12s ease-in-out infinite; }}
        .fx-pan_left  {{ animation: fxPanLeft 12s ease-in-out infinite; }}
        .fx-pan_right {{ animation: fxPanRight 12s ease-in-out infinite; }}
        .fx-static    {{ animation: none; }}

        @keyframes fxKenBurns {{
            0%   {{ transform: scale(1.04) translate(-1.5%, -1.5%); }}
            50%  {{ transform: scale(1.18) translate(1.5%, 1.5%); }}
            100% {{ transform: scale(1.04) translate(-1.5%, -1.5%); }}
        }}
        @keyframes fxZoomIn {{
            0%   {{ transform: scale(1.02); }}
            100% {{ transform: scale(1.22); }}
        }}
        @keyframes fxZoomOut {{
            0%   {{ transform: scale(1.22); }}
            100% {{ transform: scale(1.02); }}
        }}
        @keyframes fxPanLeft {{
            0%   {{ transform: scale(1.14) translateX(4%); }}
            100% {{ transform: scale(1.14) translateX(-4%); }}
        }}
        @keyframes fxPanRight {{
            0%   {{ transform: scale(1.14) translateX(-4%); }}
            100% {{ transform: scale(1.14) translateX(4%); }}
        }}

        /* HIGHLIGHT SWEEP */
        .beat-highlight .highlight-container {{
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .beat-highlight .highlight-bg {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            padding: 20px 60px;
            background: var(--accent);
            opacity: 0.25;
            border-radius: 8px;
        }}
        .beat-highlight .highlight-text {{
            font-family: 'Montserrat', sans-serif;
            font-size: 96px;
            font-weight: 900;
            color: var(--text-primary);
            text-transform: uppercase;
            position: relative;
            text-align: center;
        }}
        
        /* SUBTITLE BURN */
        .beat-subtitle .subtitle-container {{
            position: absolute;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            padding: 20px 40px;
            border-radius: 8px;
            max-width: 85%;
        }}
        .beat-subtitle .sub-word {{
            font-family: 'Montserrat', sans-serif;
            font-size: 36px;
            font-weight: 700;
            color: var(--text-primary);
            text-shadow: 2px 2px 0 black;
            margin: 0 8px;
        }}
        
        /* LOWER THIRD */
        .beat-lower .lower-third {{
            position: absolute;
            bottom: 80px;
            left: 60px;
        }}
        .beat-lower .bar {{
            height: 4px;
            width: 120px;
            background: var(--accent);
            box-shadow: 0 0 10px var(--accent);
            margin-bottom: 12px;
        }}
        .beat-lower .name {{
            font-family: 'Montserrat', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .beat-lower .title {{
            font-size: 18px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        .beat-lower .quote {{
            margin-top: 16px;
            padding-left: 16px;
            border-left: 3px solid var(--accent);
            font-family: Georgia, serif;
            font-size: 20px;
            color: var(--text-primary);
            font-style: italic;
        }}
        
        /* GRAIN — REMOVIDO (21/09/2026). Era o maior gargalo do render.
           O `.grain` usava feTurbulence fractalNoise (4 octaves) cobrindo
           o quadro inteiro. Ruído fractal SVG é rasterizado a cada paint:
           medido 695 ms/frame com ele e 116 ms/frame sem — ~580 ms por
           frame, 83% do tempo total, para um efeito de OPACIDADE 0.04
           (praticamente invisível).
           Se quiser granulação de volta, usar um tile de ruído pré-gerado
           (bitmap pequeno) em vez de feTurbulence ao vivo. */
        
        .controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            z-index: 10000;
        }}
        button {{
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            cursor: pointer;
            border-radius: 4px;
        }}
        button:hover {{ background: rgba(255,255,255,0.3); }}
    </style>
</head>
<body>
    <div class="scene">
        {beats_html}
    </div>
    <div class="controls">
        <button onclick="togglePlay()">Play/Pause</button>
        <button onclick="restart()">Restart</button>
    </div>
    <script>
        let totalDuration = {duracao_total if duracao_total and duracao_total > total_duration else total_duration};
        let currentTime = 0;
        let paused = false;
        let animationId = null;
        
        function updateBeats() {{
            if (paused) return;
            currentTime += 0.016;
            document.querySelectorAll('.beat').forEach(beat => {{
                let start = parseFloat(beat.dataset.start);
                let end = parseFloat(beat.dataset.end);
                if (currentTime >= start && currentTime < end) {{
                    beat.classList.add('visible');
                }} else {{
                    beat.classList.remove('visible');
                }}
            }});
            if (currentTime < totalDuration) {{
                animationId = requestAnimationFrame(updateBeats);
            }}
        }}
        
        function togglePlay() {{
            paused = !paused;
            if (!paused) updateBeats();
        }}
        
        function restart() {{
            currentTime = 0;
            paused = false;
            document.querySelectorAll('.beat').forEach(b => {{
                b.classList.remove('visible');
            }});
            // Mostrar primeiro beat imediatamente
            const firstBeat = document.querySelector('.beat');
            if (firstBeat && parseFloat(firstBeat.dataset.start) === 0) {{
                firstBeat.classList.add('visible');
            }}
            updateBeats();
        }}
        
        // Iniciar
        restart();
    </script>
</body>
</html>'''

        output_path.write_text(html, encoding="utf-8")
        print(f"[HTMLRenderer] Composição salva: {output_path}")
        return output_path

    def _get_style_colors(self, style: SceneStyle) -> dict:
        styles = {
            SceneStyle.VOX_EDITORIAL: {
                "primary": "#1A1A2E",
                "secondary": "#16213E",
                "accent": "#FFCC00",
                "text": "#FFFFFF",
                "text_secondary": "#B8B8D1",
            },
            SceneStyle.DANMAKU_DOC: {
                "primary": "#0D0D0D",
                "secondary": "#1A1A1A",
                "accent": "#FB7299",
                "text": "#FFFFFF",
                "text_secondary": "#888888",
            },
            SceneStyle.DATA_CARNIVAL: {
                "primary": "#0A0A0F",
                "secondary": "#151520",
                "accent": "#FFD700",
                "text": "#FFFFFF",
                "text_secondary": "#B8B8D1",
            },
            SceneStyle.NEON_MINIMAL: {
                "primary": "#050508",
                "secondary": "#0A0A12",
                "accent": "#00F0FF",
                "text": "#E8E8F0",
                "text_secondary": "#6B6B80",
            },
        }
        return styles.get(style, styles[SceneStyle.VOX_EDITORIAL])
