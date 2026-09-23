# Scene Engine — Sistema de Vídeos Vox

Sistema de renderização de vídeos estilo documentários Vox (YouTube) usando Python + HTML + FFmpeg.

## Estrutura

```
scene_engine/
├── __init__.py
├── scene_types.py          # Tipos e constantes
├── scene_builder.py        # Construtor de cenas
├── compositor.py           # Composição FFmpeg
├── pipeline.py             # Orquestrador principal
├── components/
│   ├── __init__.py
│   ├── base.py             # Classe base dos componentes
│   ├── kinetic_title.py    # Título com palavras animadas
│   ├── parallax_image.py   # Imagem com Ken Burns
│   ├── annotated_map.py    # Mapa com anotações
│   ├── lower_third.py      # Identificação do apresentador
│   ├── subtitle_burn.py    # Legendas karaoke
│   ├── highlight_sweep.py  # Highlight amarelo
│   ├── callout_line.py     # Linha tracejada
│   └── grain_overlay.py    # Textura de filme
├── renderers/
│   ├── __init__.py
│   ├── html_renderer.py     # Renderiza HTML animado
│   └── video_renderer.py   # Converte HTML → MP4
├── templates/
│   └── vox_editorial.html  # Template base
└── assets/
    ├── backgrounds/
    └── textures/
```

## Componentes Disponíveis

| Componente | Tipo | Descrição |
|------------|------|-----------|
| KineticTitle | `kinetic_title` | Título com palavras animadas uma a uma |
| ParallaxImage | `parallax_image` | Imagem com efeito Ken Burns |
| AnnotatedMap | `annotated_map` | Mapa SVG com pontos e labels |
| LowerThird | `lower_third` | Identificação do apresentador |
| SubtitleBurn | `subtitle_burn` | Legendas estilo karaokê |
| HighlightSweep | `highlight_sweep` | Retângulo amarelo que desliza |
| CalloutLine | `callout_line` | Linha tracejada animada |
| GrainOverlay | `grain_overlay` | Textura de filme sutil |

## Uso Rápido

```python
from pathlib import Path
from scene_engine import VoxPipeline, SceneBuilder

# Criar projeto
project = VoxPipeline(Path("meu_video"))

# Criar beats
beats = [
    SceneBuilder.create_beat(
        beat_id=1,
        beat_type="hook",
        script="Você sabia que...",
        visual_type="kinetic_title",
        text="COMO O MUNDO FUNCIONA",
        duration=5.0,
    ),
    SceneBuilder.create_beat(
        beat_id=2,
        beat_type="context",
        script="A história começa...",
        visual_type="parallax_image",
        images=["minha_imagem.jpg"],
        duration=8.0,
    ),
    SceneBuilder.create_beat(
        beat_id=3,
        beat_type="expert_quote",
        script="Segundo especialistas...",
        visual_type="lower_third",
        speaker_name="Dr. Silva",
        speaker_title="Pesquisador USP",
        duration=6.0,
    ),
]

# Renderizar preview HTML
preview = project.render_preview(beats)
print(f"Preview: {preview}")

# Renderizar vídeo (requer Playwright + FFmpeg)
video = project.render_video(beats, "video_final.mp4")
print(f"Vídeo: {video}")
```

## Pré-requisitos

```bash
pip install playwright
playwright install chromium
ffmpeg  # No PATH do sistema
```

## Estilos Disponíveis

- `SceneStyle.VOX_EDITORIAL` — Estilo Vox padrão (fundo escuro, amarelo #FFCC00)
- `SceneStyle.DANMAKU_DOC` — Estilo Danmaku (escuro + rosa #FB7299)
- `SceneStyle.DATA_CARNIVAL` — Estilo Carnaval de Dados (multicor vibrante)
- `SceneStyle.NEON_MINIMAL` — Estilo Neon Minimal (escuro + ciano #00F0FF)

## Fluxo

```
Roteiro (beats)
    ↓
HTML Renderer → preview HTML animado
    ↓
Video Renderer → frames (Playwright) → MP4 (FFmpeg)
    ↓
Compositor → adicionar áudio + legendas
    ↓
Vídeo final
```
