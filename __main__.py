"""Entry point para: python -m MusicClipStudio"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.cli import main

if __name__ == "__main__":
    main()