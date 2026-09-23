from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

FPS = 24
WIDTH = 1920
HEIGHT = 1080


class SceneStyle(Enum):
    VOX_EDITORIAL = "vox_editorial"
    DANMAKU_DOC = "danmaku_doc"
    DATA_CARNIVAL = "data_carnival"
    NEON_MINIMAL = "neon_minimal"


@dataclass
class VisualElement:
    type: str
    text: Optional[str] = None
    images: list[str] = field(default_factory=list)
    annotation: Optional[dict] = None
    speaker_name: Optional[str] = None
    speaker_title: Optional[str] = None
    quote_text: Optional[str] = None
    speaker_image: Optional[str] = None
    bg_color: Optional[str] = None
    accent_color: str = "#FFCC00"
    animation: str = "fade_in"
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100


@dataclass
class Beat:
    id: int
    type: str
    duration: float
    script: str
    visual: VisualElement
    danmaku: Optional[list[dict]] = None


@dataclass
class LayerConfig:
    name: str
    z_index: int
    opacity: float = 1.0
    blend_mode: str = "normal"
    width: int = WIDTH
    height: int = HEIGHT


@dataclass
class Scene:
    scene_id: str
    duration: float
    profile: SceneStyle
    layers: list[dict] = field(default_factory=list)
    beats: list[Beat] = field(default_factory=list)
    fps: int = FPS
    width: int = WIDTH
    height: int = HEIGHT


@dataclass
class VideoScript:
    metadata: dict
    beats: list[Beat]
    style: SceneStyle = SceneStyle.VOX_EDITORIAL
