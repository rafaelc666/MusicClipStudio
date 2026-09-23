"""Semantic video engine for selecting media based on prompts."""

from dataclasses import dataclass
from typing import List, Optional
from MusicClipStudio.media_provider import MediaProviderBase, MediaAsset
from MusicClipStudio.prompt_generator import MediaPrompt, MediaCategory


@dataclass
class SemanticVideoEngineConfig:
    """Configuration for the semantic video engine."""
    max_assets: int = 30
    parallel_search: bool = True
    # Weights for different media types (if needed)
    image_weight: float = 1.0
    video_weight: float = 1.0


class SemanticVideoEngine:
    """Engine that selects media assets based on generated prompts using various providers."""

    def __init__(self, providers: List[MediaProviderBase], config: Optional[SemanticVideoEngineConfig] = None):
        """
        Initialize the semantic video engine.
        
        Args:
            providers: List of media provider instances (e.g., PexelsProvider, PixabayProvider)
            config: Configuration for the engine
        """
        self.providers = providers
        self.config = config or SemanticVideoEngineConfig()

    def select_media(self, prompts: List[MediaPrompt]) -> List[MediaAsset]:
        """
        Select media assets based on a list of prompts.
        
        Args:
            prompts: List of MediaPrompt objects
            
        Returns:
            List of MediaAsset objects selected from the providers
        """
        # We'll collect assets from all providers for each prompt
        assets: List[MediaAsset] = []
        
        for prompt in prompts:
            # For each provider, search for images and/or videos based on the prompt category
            for provider in self.providers:
                if prompt.category in [MediaCategory.IMAGE, MediaCategory.ANY]:
                    images = provider.search_images(prompt.query, limit=5)
                    for img in images:
                        img.source = provider.__class__.__name__.replace('Provider', '').lower()
                        assets.append(img)
                
                if prompt.category in [MediaCategory.VIDEO, MediaCategory.ANY]:
                    videos = provider.search_videos(prompt.query, limit=5)
                    for vid in videos:
                        vid.source = provider.__class__.__name__.replace('Provider', '').lower()
                        assets.append(vid)
        
        # Remove duplicates (based on URL) and limit to max_assets
        unique_assets = []
        seen_urls = set()
        for asset in assets:
            if asset.url not in seen_urls:
                seen_urls.add(asset.url)
                unique_assets.append(asset)
        
        # Sort by weight? We don't have a weight on assets, but we could use the prompt weight.
        # For simplicity, we'll just take the first max_assets.
        if len(unique_assets) > self.config.max_assets:
            unique_assets = unique_assets[:self.config.max_assets]
        
        return unique_assets


# Example usage and testing
if __name__ == "__main__":
    # Import the provider classes
    from MusicClipStudio.media_provider import PexelsProvider, PixabayProvider, UnsplashProvider
    
    # Create dummy providers
    providers = [
        PexelsProvider(api_key="dummy"),
        PixabayProvider(api_key="dummy"),
        UnsplashProvider(api_key="dummy")
    ]
    
    engine = SemanticVideoEngine(providers, SemanticVideoEngineConfig(max_assets=10))
    
    # Create some dummy prompts
    prompts = [
        MediaPrompt(query="beach", category=MediaCategory.IMAGE, weight=1.0),
        MediaPrompt(query="ocean", category=MediaCategory.VIDEO, weight=0.8),
    ]
    
    assets = engine.select_media(prompts)
    print(f"Selected {len(assets)} assets:")
    for asset in assets:
        print(f"  - [{asset.source}] {asset.url} ({asset.width}x{asset.height})")