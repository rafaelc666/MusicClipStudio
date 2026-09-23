"""Render experimental da demo HTML para um MP4 curto.

Este arquivo e um prototipo isolado; nao substitui o motor oficial ainda.
"""
from pathlib import Path
import shutil
import subprocess
import sys

from playwright.sync_api import sync_playwright
from scene_renderer import build_scene_html

BASE = Path(__file__).parent
HTML = BASE / "demo.html"
FRAMES = BASE / "_frames"
OUTPUT = BASE / "vox_demo.mp4"
FPS = 30
DURATION = 8
WIDTH = 1280
HEIGHT = 720


def main():
    if not HTML.exists():
        raise FileNotFoundError(HTML)
    generated_html = build_scene_html()
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
        page.goto(generated_html.as_uri())
        page.wait_for_timeout(300)
        page.evaluate("document.getElementById('stage').classList.add('paused')")
        for frame in range(FPS * DURATION):
            timestamp = frame / FPS
            page.evaluate("(t) => { started = performance.now() - t * 1000; }", timestamp)
            page.screenshot(path=str(FRAMES / f"frame_{frame:05d}.png"))
        browser.close()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg nao encontrado no PATH")
    command = [
        ffmpeg, "-y", "-framerate", str(FPS),
        "-i", str(FRAMES / "frame_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        str(OUTPUT),
    ]
    subprocess.run(command, check=True)
    print(f"Render concluido: {OUTPUT}")
    print(f"Frames: {len(list(FRAMES.glob('*.png')))}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Erro no render: {error}", file=sys.stderr)
        raise
