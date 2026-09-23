"""Prompt generation module for converting lyric analysis to media search prompts."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class MediaCategory(Enum):
    """Categories of media to search for."""
    IMAGE = "image"
    VIDEO = "video"
    ANY = "any"


@dataclass
class PromptConfig:
    """Configuration for prompt generation."""
    max_themes: int = 5
    max_words_per_prompt: int = 6
    include_artist: bool = False
    include_title: bool = True


@dataclass
class MediaPrompt:
    """A prompt for searching media (image or video)."""
    query: str
    category: MediaCategory = MediaCategory.ANY
    weight: float = 1.0  # Importance weight for selection


class PromptGenerator:
    """Generates media search prompts from lyric analysis."""

    def __init__(self, config: Optional[PromptConfig] = None):
        self.config = config or PromptConfig()

    def generate(self, analysis: 'LyricsAnalysis', categories: List[MediaCategory] = None) -> List[MediaPrompt]:
        """
        Generate media prompts from lyric analysis.
        
        Args:
            analysis: LyricsAnalysis object from lyrics parser
            categories: List of media categories to generate prompts for (default: [ANY])
            
        Returns:
            List of MediaPrompt objects
        """
        if categories is None:
            categories = [MediaCategory.ANY]
        
        prompts = []
        
        # Generate prompts from themes
        theme_prompts = self._generate_theme_prompts(analysis.themes)
        prompts.extend(theme_prompts)
        
        # Optionally add title and artist as prompts
        if self.config.include_title and analysis.title != "Unknown":
            title_prompts = self._create_prompts_from_text(analysis.title, categories)
            prompts.extend(title_prompts)
            
        if self.config.include_artist and analysis.artist != "Unknown":
            artist_prompts = self._create_prompts_from_text(analysis.artist, categories)
            prompts.extend(artist_prompts)
        
        # Remove duplicates and sort by weight (descending)
        unique_prompts = self._deduplicate_prompts(prompts)
        unique_prompts.sort(key=lambda p: p.weight, reverse=True)
        
        # Limit total prompts based on config (optional)
        return unique_prompts

    def _generate_theme_prompts(self, themes: List['ThemeScore']) -> List[MediaPrompt]:
        """Generate prompts from the top themes in the analysis."""
        prompts = []
        # Take top themes based on config
        top_themes = themes[:self.config.max_themes]
        
        for theme in top_themes:
            # Only generate if relevance is above a threshold
            if theme.relevance > 0.3:  # Arbitrary threshold
                # Create a prompt from the theme word
                prompt_text = theme.theme
                # For each category, create a prompt
                for category in [MediaCategory.ANY]:  # For now, we'll just do ANY, can be extended
                    prompts.append(MediaPrompt(
                        query=prompt_text,
                        category=category,
                        weight=theme.relevance
                    ))
        return prompts

    def _create_prompts_from_text(self, text: str, categories: List[MediaCategory]) -> List[MediaPrompt]:
        """Create prompts from a given text (title or artist)."""
        prompts = []
        # Simple approach: use the text as is, but limit words
        words = text.split()
        if len(words) > self.config.max_words_per_prompt:
            # Take the first N words
            prompt_text = ' '.join(words[:self.config.max_words_per_prompt])
        else:
            prompt_text = text
        
        for category in categories:
            prompts.append(MediaPrompt(
                query=prompt_text,
                category=category,
                weight=0.8  # Default weight for title/artist
            ))
        return prompts

    def _deduplicate_prompts(self, prompts: List[MediaPrompt]) -> List[MediaPrompt]:
        """Remove duplicate prompts (same query and category)."""
        seen = set()
        unique = []
        for prompt in prompts:
            key = (prompt.query.lower(), prompt.category.value)
            if key not in seen:
                seen.add(key)
                unique.append(prompt)
        return unique


# Example usage and testing
if __name__ == "__main__":
    # Import LyricsAnalysis and ThemeScore from lyrics_parser (for testing)
    from lyrics_parser import ThemeScore, LyricsAnalysis
    
    # Create a sample analysis
    sample_themes = [
        ThemeScore(theme="verão", relevance=0.9),
        ThemeScore(theme="praia", relevance=0.8),
        ThemeScore(theme="sol", relevance=0.7),
        ThemeScore(theme="cerveja", relevance=0.6),
        ThemeScore(theme="diversão", relevance=0.5),
    ]
    sample_analysis = LyricsAnalysis(
        title="Verão Bom",
        artist="Artista do Verão",
        line_texts=["Verão chegando, o sol está brilhando", "Praia lotada, gente se divertindo"],
        themes=sample_themes
    )
    
    # Generate prompts
    generator = PromptGenerator(PromptConfig(max_themes=3, max_words_per_prompt=4))
    prompts = generator.generate(sample_analysis, categories=[MediaCategory.IMAGE, MediaCategory.VIDEO])
    
    print(f"Generated {len(prompts)} prompts:")
    for i, prompt in enumerate(prompts):
        print(f"{i+1}. [{prompt.category.value}] '{prompt.query}' (weight: {prompt.weight:.2f})")