"""Lyrics parsing module for extracting themes and structure from song lyrics."""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class ThemeScore:
    """Represents a theme and its relevance score."""
    theme: str
    relevance: float  # 0.0 to 1.0


@dataclass
class LyricsAnalysis:
    """Analysis result of song lyrics."""
    title: str
    artist: str
    line_texts: List[str]
    themes: List[ThemeScore]


class LyricsParser:
    """Parses song lyrics to extract themes, structure, and key elements."""

    def __init__(self):
        # Common stop words to ignore in theme extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
            'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
            'this', 'that', 'these', 'those', 'am', 'pm', 'love', 'like', 'know'
        }

    def parse(self, lyrics_text: str, title: str = "Unknown", artist: str = "Unknown") -> LyricsAnalysis:
        """
        Parse lyrics text and extract analysis.
        
        Args:
            lyrics_text: The raw lyrics text
            title: Song title (optional)
            artist: Artist name (optional)
            
        Returns:
            LyricsAnalysis object containing parsed information
        """
        # Clean and split into lines
        lines = [line.strip() for line in lyrics_text.split('\n') if line.strip()]
        
        # Extract themes from lines
        themes = self._extract_themes(lines)
        
        return LyricsAnalysis(
            title=title,
            artist=artist,
            line_texts=lines,
            themes=themes
        )

    def _extract_themes(self, lines: List[str]) -> List[ThemeScore]:
        """Extract themes from lyric lines with relevance scores."""
        # Simple word frequency-based theme extraction
        word_freq = {}
        
        for line in lines:
            # Convert to lowercase and split into words
            words = re.findall(r'\b[a-z]+\b', line.lower())
            for word in words:
                if word not in self.stop_words and len(word) > 2:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Normalize frequencies to scores (0.0 to 1.0)
        if not word_freq:
            return []
            
        max_freq = max(word_freq.values())
        themes = []
        
        for word, freq in word_freq.items():
            # Only keep words with significant frequency
            if freq >= 2:  # Appear at least twice
                relevance = freq / max_freq
                themes.append(ThemeScore(theme=word, relevance=relevance))
        
        # Sort by relevance descending and limit to top themes
        themes.sort(key=lambda x: x.relevance, reverse=True)
        return themes[:10]  # Top 10 themes


# Example usage and testing
if __name__ == "__main__":
    # Test with sample lyrics
    sample_lyrics = """
    Verão chegando, o sol está brilhando
    Praia lotada, gente se divertindo
    Cerveja gelada, pé na areia
    Vamos curtir o dia inteiro
    
    Refrão:
    Esse é o nosso verão, nosso tempo de amar
    Dançando na beira-mar, sem parar de celebrar
    """
    
    parser = LyricsParser()
    analysis = parser.parse(sample_lyrics, title="Verão", artist="Artista Exemplo")
    
    print(f"Title: {analysis.title}")
    print(f"Artist: {analysis.artist}")
    print(f"Lines ({len(analysis.line_texts)}):")
    for i, line in enumerate(analysis.line_texts[:3]):  # Show first 3 lines
        print(f"  {i+1}. {line}")
    print(f"Themes ({len(analysis.themes)}):")
    for theme in analysis.themes:
        print(f"  {theme.theme}: {theme.relevance:.2f}")