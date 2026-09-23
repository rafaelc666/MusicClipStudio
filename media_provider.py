"""Media provider module for fetching images and videos from free APIs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import requests


@dataclass
class MediaAsset:
    """Represents a media asset (image or video) fetched from a provider."""
    url: str
    thumb: Optional[str] = None
    width: int = 0
    height: int = 0
    duration: Optional[float] = None  # For videos
    source: str = ""  # Provider name (e.g., "pexels", "pixabay")


class MediaProviderBase(ABC):
    """Abstract base class for media providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def search_images(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for images related to the query."""
        pass

    @abstractmethod
    def search_videos(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for videos related to the query."""
        pass


class PexelsProvider(MediaProviderBase):
    """Pexels API provider (placeholder implementation)."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.pexels.com/v1"

    def search_images(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for images on Pexels."""
        # Placeholder: return empty list for now
        # In a real implementation, we would make an API call to Pexels
        print(f"[Pexels] Searching for images: {query} (limit={limit})")
        return []

    def search_videos(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for videos on Pexels."""
        # Placeholder: return empty list for now
        print(f"[Pexels] Searching for videos: {query} (limit={limit})")
        return []


class PixabayProvider(MediaProviderBase):
    """Pixabay API provider (placeholder implementation)."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://pixabay.com/api/"

    def search_images(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for images on Pixabay."""
        print(f"[Pixabay] Searching for images: {query} (limit={limit})")
        return []

    def search_videos(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for videos on Pixabay."""
        print(f"[Pixabay] Searching for videos: {query} (limit={limit})")
        return []


class UnsplashProvider(MediaProviderBase):
    """Unsplash API provider (placeholder implementation)."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.unsplash.com/"

    def search_images(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for images on Unsplash."""
        print(f"[Unsplash] Searching for images: {query} (limit={limit})")
        return []

    def search_videos(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Search for videos on Unsplash (Unsplash doesn't have videos, so return empty)."""
        print(f"[Unsplash] Searching for videos: {query} (limit={limit})")
        return []


class MockProvider(MediaProviderBase):
    """Mock provider for testing - returns placeholder assets."""
    
    def __init__(self):
        super().__init__(api_key="mock")
    
    def search_images(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Return mock image assets."""
        return [
            MediaAsset(
                url=f"mock://image/{query}/{i}",
                width=1280,
                height=720,
                source="mock"
            )
            for i in range(min(limit, 5))
        ]
    
    def search_videos(self, query: str, limit: int = 10) -> List[MediaAsset]:
        """Return mock video assets."""
        return [
            MediaAsset(
                url=f"mock://video/{query}/{i}",
                width=1280,
                height=720,
                duration=5.0,
                source="mock"
            )
            for i in range(min(limit, 3))
        ]


# Example usage and testing
if __name__ == "__main__":
    # Test with dummy API keys
    pexels = PexelsProvider(api_key="dummy")
    images = pexels.search_images("beach", limit=5)
    print(f"Found {len(images)} images from Pexels")
    
    pixabay = PixabayProvider(api_key="dummy")
    videos = pixabay.search_videos("beach", limit=5)
    print(f"Found {len(videos)} videos from Pixabay")
    
    unsplash = UnsplashProvider(api_key="dummy")
    images = unsplash.search_images("beach", limit=5)
    print(f"Found {len(images)} images from Unsplash")
    
    # Test mock provider
    mock = MockProvider()
    mock_images = mock.search_images("test", limit=3)
    print(f"Found {len(mock_images)} mock images")