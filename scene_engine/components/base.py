from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ..scene_types import FPS, WIDTH, HEIGHT, VisualElement


class BaseComponent(ABC):
    def __init__(
        self,
        element: VisualElement,
        output_dir: Path,
        width: int = WIDTH,
        height: int = HEIGHT,
        fps: int = FPS,
    ):
        self.element = element
        self.output_dir = Path(output_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def render(self) -> Path:
        pass

    def get_layer_html(self) -> str:
        return ""


class ComponentRegistry:
    _components: dict[str, type[BaseComponent]] = {}

    @classmethod
    def register(cls, component_type: str):
        def decorator(component_class: type[BaseComponent]):
            cls._components[component_type] = component_class
            return component_class
        return decorator

    @classmethod
    def get(cls, component_type: str) -> Optional[type[BaseComponent]]:
        return cls._components.get(component_type)

    @classmethod
    def list_types(cls) -> list[str]:
        return list(cls._components.keys())
