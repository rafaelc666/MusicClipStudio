import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional
from ..scene_types import FPS, WIDTH, HEIGHT


class VideoRenderer:
    # Escala de captura: 0.5 = metade da resolução final.
    # O Chromium renderiza e screenshotta em resolução reduzida;
    # o FFmpeg faz o upscale para a resolução final (lanczos).
    # Reduz o custo de screenshot ~4x com perda visual mínima em clips 24fps.
    CAPTURE_SCALE = 0.5

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

        # Resolução de captura (metade da final, arredondada)
        self.capture_width = max(1, int(self.width * self.CAPTURE_SCALE))
        self.capture_height = max(1, int(self.height * self.CAPTURE_SCALE))

        self._check_ffmpeg()
        self._check_playwright()

    def _check_ffmpeg(self):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg não encontrado. Instale o FFmpeg para renderizar vídeos.")
        print("[VideoRenderer] FFmpeg OK")

    def _check_playwright(self):
        try:
            from playwright.sync_api import sync_playwright
            print("[VideoRenderer] Playwright OK")
        except ImportError:
            print("[VideoRenderer] AVISO: Playwright não instalado. Execute: pip install playwright && playwright install chromium")

    def render_html_to_images(
        self,
        html_path: Path,
        output_dir: Path,
        duration: float = 8.0,
        fps: int = None,
    ) -> Path:
        if fps is None:
            fps = self.fps
            
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        total_frames = int(duration * fps)
        
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    viewport={"width": self.capture_width, "height": self.capture_height},
                    device_scale_factor=1,
                )

                page.goto(html_path.as_uri())
                page.wait_for_timeout(500)

                # ⚠️ CORRIGIDO (21/09/2026) — esperava só 500 ms e já saía
                # fotografando. Para fotos do Pexels (cache miss, 3–10 MB)
                # e vídeos (streaming) isso é cedo demais: a captura saía
                # com a área da imagem/vídeo AINDA preta e o clipe ficava
                # com tudo escuro, só com a legenda por cima.
                # Agora: espera rede ficar ociosa (pega background-image
                # que NÃO é <img>), <video> com readyState>=3 e <img>
                # completas. Tem timeout duro de 20 s por elemento para
                # uma URL quebrada não travar o job.
                try:
                    # 1) rede ociosa — cobre background-image das fotos e
                    #    confirma que os downloads de vídeos/images concluíram.
                    #    networkidle é suficiente: se a rede ficou ociosa, os
                    #    arquivos já estão no disco do Chromium.
                    page.wait_for_load_state("networkidle", timeout=20000)
                    # 2) verifica rápido se os <video>/<img> explícitos estão
                    #    com o atributo complete/readyState — mas com timeout
                    #    curto (2s), pois vídeos 4K podem nunca atingir pronto
                    #    antes do primeiro frame ser pego (não é erro).
                    page.wait_for_function(
                        """() => {
                          const imgs = [...document.querySelectorAll('img')];
                          const vids = [...document.querySelectorAll('video')];
                          const imgsOk = imgs.every(i => i.complete && i.naturalWidth > 0);
                          const vidsOk = vids.every(v => v.readyState >= 3);
                          return imgsOk && vidsOk;
                        }""",
                        timeout=2000,
                    )
                except Exception as _e:
                    # não é fatal: se falhar, segue com o que estiver
                    print(f"[VideoRenderer] AVISO: mídias podem não ter "
                          f"carregado totalmente ({_e})")
                # segundo respiro para o primeiro frame do <video> pintar
                page.wait_for_timeout(300)

                for frame_num in range(total_frames):
                    timestamp = frame_num / fps
                    # ⚠️ CORRIGIDO (21/09/2026) — o JS anima via
                    # requestAnimationFrame acumulando currentTime em
                    # tempo-de-relógio. Cada screenshot leva ~150–300 ms
                    # (PNG 1080×1920), então 72 frames × ~250 ms = ~18 s
                    # de wall time para uma composição de 3 s. Resultado:
                    # o JS atinge totalDuration, para de agendar frames e
                    # esconde TODOS os beats — frames 18+ saíam com 99%
                    # cor de fundo, só o frame 0 tinha conteúdo. O mesmo
                    # valia para qualquer composição > ~2 s.
                    #
                    # Correção: pausar o RAF e DIRIGIR currentTime e
                    # `.visible` por frame, determinístico.
                    page.evaluate(
                        """(t) => {
                          paused = true;
                          currentTime = t;
                          document.querySelectorAll('.beat').forEach(b => {
                            const s = parseFloat(b.dataset.start);
                            const e = parseFloat(b.dataset.end);
                            b.classList.toggle('visible', t >= s && t < e);
                          });
                        }""",
                        timestamp,
                    )
                    page.screenshot(
                        path=str(output_dir / f"frame_{frame_num:05d}.jpg"),
                        type="jpeg",
                        quality=95,
                        omit_background=False,
                    )

                    if frame_num % 24 == 0:
                        print(f"[VideoRenderer] Frame {frame_num}/{total_frames}")

                browser.close()

        except ImportError:
            print("[VideoRenderer] ERRO: Playwright necessário para renderizar HTML")
            return output_dir

        print(f"[VideoRenderer] Frames salvos em: {output_dir}")
        return output_dir

    def images_to_video(
        self,
        frames_dir: Path,
        output_path: Path,
        fps: int = None,
        crf: int = 20,
    ) -> Path:
        if fps is None:
            fps = self.fps

        output_path = Path(output_path)

        # Se a resolução de captura for menor que a final, faz upscale via FFmpeg
        scale_filter = ""
        if (self.capture_width, self.capture_height) != (self.width, self.height):
            scale_filter = f"scale={self.width}:{self.height}:flags=lanczos"

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%05d.jpg"),
        ]
        if scale_filter:
            ffmpeg_cmd.extend(["-vf", scale_filter])
        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", str(crf),
            "-preset", "medium",
            str(output_path),
        ])

        print(f"[VideoRenderer] Executando FFmpeg {'com upscale para '+str(self.width)+'x'+str(self.height) if scale_filter else ''}...")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[VideoRenderer] FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg falhou: {result.stderr}")

        print(f"[VideoRenderer] Vídeo salvo: {output_path}")
        return output_path

    def render_html_to_video(
        self,
        html_path: Path,
        output_path: Path,
        duration: float = 8.0,
        fps: int = None,
        crf: int = 20,
        cleanup_frames: bool = False,
    ) -> Path:
        """Renderiza HTML → frames → MP4.

        NOTA (19/09/2026) — por que `cleanup_frames=False` por padrão:

        A limpeza dos frames apagava a pasta inteira (`shutil.rmtree`) logo
        após o FFmpeg terminar. O vídeo JÁ ESTAVA salvo, mas o ambiente tem
        um guard de exclusão em massa (limite ~50 arquivos/turno) que
        **matava o processo no meio da limpeza**. Resultado: o job nunca
        marcava `done` e a UI travava em 50% para sempre, mesmo com o clipe
        pronto no disco.

        Apagar frame é faxina, não parte do render — não faz sentido
        arriscar o clipe por causa disso. Então: o padrão agora é NÃO
        apagar, e a limpeza fica disponível via `_limpar_frames()` para ser
        chamada num momento seguro (ex.: por um utilitário, ou entre jobs).

        ⚠️ CORRIGIDO (21/09/2026) — frames de jobs ANTERIORES vazavam
        para dentro do clipe novo.

        Como a pasta era FIXA (`_temp_frames`) e nunca era limpa, o FFmpeg
        (`-i frame_%05d.png`) lia a sequência contígua do disco: os 72
        frames deste job + os ~1300 frames sobrando do job anterior. O clipe
        saía com cenas de OUTRO vídeo coladas no fim.

        Achado num job real: beat de 1,5 s → MP4 de 49 s. Os frames
        00000–00071 eram deste job; o 00072 estava datado de 12 min antes.

        Agora cada render escreve na sua própria pasta
        (`_temp_frames_<id>`), derivada do nome do HTML — que já é único por
        job (`clip_<timestamp>.html`). Sobrando lixo antigo ou não, ele
        nunca entra no vídeo.
        """
        if fps is None:
            fps = self.fps

        # pasta ÚNICA por render — impede mistura com frames de outros jobs
        # Caminho rápido (1 screenshot por beat + zoompan). Se não se
        # aplicar — beat com vídeo, Playwright ausente, zoompan falhando —
        # cai no caminho por frame, que continua funcionando.
        try:
            return self.render_html_to_video_rapido(
                html_path, output_path, duration, fps, crf
            )
        except Exception as e:
            print(f"[VideoRenderer] caminho rápido indisponível ({e}) "
                  f"— usando 1 screenshot por frame")

        frames_dir = self.output_dir / f"_temp_frames_{html_path.stem}"

        self.render_html_to_images(html_path, frames_dir, duration, fps)
        
        output_path = self.images_to_video(frames_dir, output_path, fps, crf)
        
        if cleanup_frames:
            self._limpar_frames(frames_dir)
        
        return output_path

    # ── CAMINHO RÁPIDO: 1 screenshot por beat + zoompan do FFmpeg ────
    #
    # ⚠️ 21/09/2026. O caminho por frame custa ~425 ms/frame com fotos
    # (31 min para um clipe de 3 min) e ~1 s/frame com vídeo (~70 min).
    # Praticamente todo esse tempo é rasterizar e codificar a MESMA cena
    # milhares de vezes, sendo que a única coisa que muda é o zoom/pan.
    #
    # O FFmpeg faz zoom/pan nativamente (filtro zoompan), quase de graça.
    # Então: um screenshot por beat e o zoompan gera o movimento. Um
    # clipe de 20 beats cai de 4320 screenshots para 20.
    #
    # Só se aplica a beat de IMAGEM — beat com <video> precisa dos frames
    # reais (o vídeo está se movendo por conta própria) e continua no
    # caminho por frame.

    def render_html_to_video_rapido(
        self,
        html_path: Path,
        output_path: Path,
        duration: float = 8.0,
        fps: int = None,
        crf: int = 20,
    ) -> Path:
        """HTML -> 1 imagem por beat -> zoompan -> MP4."""
        if fps is None:
            fps = self.fps
        output_path = Path(output_path)
        pasta = self.output_dir / f"_temp_zoompan_{Path(html_path).stem}"
        pasta.mkdir(parents=True, exist_ok=True)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Playwright necessário")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": self.width, "height": self.height},
                device_scale_factor=1,
            )
            page.goto(Path(html_path).as_uri())
            page.wait_for_timeout(500)
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(300)

            beats = page.evaluate(
                """() => [...document.querySelectorAll('.beat')].map((b, i) => ({
                    i,
                    start: parseFloat(b.dataset.start),
                    end: parseFloat(b.dataset.end),
                    fx: ((b.querySelector('.parallax-bg') || {}).className || '')
                          .split(' ').find(c => c.indexOf('fx-') === 0) || '',
                    temVideo: !!b.querySelector('video'),
                }))"""
            )

            # ⚠️ Uma sessão só para tudo. Abrir o Chromium custa caro
            # (cold start de dezenas de segundos neste ambiente): numa
            # primeira versão eu subia o browser duas vezes — uma para
            # ler os beats e outra para fotografar — e o caminho rápido
            # ficou MAIS LENTO que o de por frame (68 s vs 31 s).
            if not beats:
                browser.close()
                raise RuntimeError("nenhum beat para renderizar")
            if any(b["temVideo"] for b in beats):
                browser.close()
                raise RuntimeError("beat com vídeo — caminho rápido não se aplica")

            # 1 screenshot por beat, sem animação: o movimento vem do zoompan
            for b in beats:
                page.evaluate(
                    """(idx) => {
                        document.querySelectorAll('.beat').forEach((el, i) => {
                            el.classList.toggle('visible', i === idx);
                        });
                        document.querySelectorAll('.parallax-bg')
                            .forEach(e => { e.style.animation = 'none'; });
                    }""",
                    b["i"],
                )
                page.screenshot(
                    path=str(pasta / f"beat_{b['i']:03d}.jpg"),
                    type="jpeg", quality=95,
                )
            browser.close()

        # um segmento por beat via zoompan
        segmentos = []
        for b in beats:
            dur = max(0.0, float(b["end"]) - float(b["start"]))
            if dur <= 0:
                continue
            n = max(1, int(round(dur * fps)))
            z, cx, cy = self._expr_zoompan(b["fx"], n)
            img = pasta / f"beat_{b['i']:03d}.jpg"
            seg = pasta / f"seg_{b['i']:03d}.mp4"
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(img),
                "-vf",
                (f"zoompan=z='{z}':x='{cx}':y='{cy}'"
                 f":d={n}:s={self.width}x{self.height}:fps={fps}"
                 f",format=yuv420p"),
                # ⚠️ -frames:v, NÃO -t. Com `-loop 1` a entrada é um
                # stream infinito do mesmo frame, e o zoompan gera `d`
                # frames de saída PARA CADA frame de entrada. Usando -t
                # ele processava muito mais do que os n necessários e o
                # caminho rápido ficava mais lento que o de por frame
                # (55 s vs 31 s). Parando em n frames, sai exato.
                "-frames:v", str(n),
                "-c:v", "libx264", "-crf", str(crf),
                "-preset", "medium", "-pix_fmt", "yuv420p",
                str(seg),
            ]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"zoompan falhou: {r.stderr[:300]}")
            segmentos.append(seg)

        if not segmentos:
            raise RuntimeError("nenhum segmento gerado")

        if len(segmentos) == 1:
            shutil.copyfile(segmentos[0], output_path)
        else:
            lista = pasta / "lista.txt"
            lista.write_text(
                "\n".join(f"file '{s.as_posix()}'" for s in segmentos),
                encoding="utf-8",
            )
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                   "-i", str(lista), "-c", "copy", str(output_path)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"concat falhou: {r.stderr[:300]}")

        print(f"[VideoRenderer] Caminho rápido: {len(beats)} beat(s), "
              f"{len(segmentos)} segmento(s)")
        return output_path

    @staticmethod
    def _expr_zoompan(fx: str, n: int):
        """Expressões z/x/y do filtro zoompan para um efeito."""
        cx = "iw/2-(iw/zoom/2)"
        cy = "ih/2-(ih/zoom/2)"
        if fx == "fx-zoom_in":
            z = f"1.02+0.20*on/{n}"
        elif fx == "fx-zoom_out":
            z = f"1.22-0.20*on/{n}"
        elif fx == "fx-ken_burns":
            z = f"1.04+0.14*on/{n}"
        elif fx == "fx-pan_left":
            z, cx = "1.14", f"(iw-iw/zoom)*(1-on/{n})"
        elif fx == "fx-pan_right":
            z, cx = "1.14", f"(iw-iw/zoom)*(on/{n})"
        else:
            z = "1"
        return z, cx, cy

    @staticmethod
    def _limpar_frames(frames_dir: Path) -> None:
        """Limpeza dos frames temporários — best-effort, nunca fatal.

        CORRIGIDO (19/09/2026): antes era `shutil.rmtree(frames_dir)`, que
        apaga a pasta inteira de uma vez. Um clipe de 72 frames estoura o
        guard de exclusão em massa do ambiente (limite 50 arquivos/turno) e
        o processo **morre no meio do render** — o vídeo já estava salvo,
        mas o job nunca marcava `done` e a UI travava em 50%.

        Agora: tentamos remover arquivo a arquivo, tolerando falha. Se o
        ambiente bloquear (guard de segurança), paramos na hora e seguimos
        — o render NUNCA é interrompido por causa de limpeza. Os frames
        ficam como lixo temporário e podem ser removidos depois, à parte.
        """
        if not frames_dir.exists():
            return
        removidos, bloqueado = 0, False
        try:
            for arq in sorted(frames_dir.glob("*")):
                try:
                    arq.unlink()
                    removidos += 1
                except (OSError, PermissionError):
                    bloqueado = True
                    break
            if not bloqueado:
                try:
                    frames_dir.rmdir()
                except OSError:
                    pass
        except Exception:
            bloqueado = True

        if bloqueado:
            resto = len(list(frames_dir.glob("*"))) if frames_dir.exists() else 0
            print(f"[VideoRenderer] {removidos} frames removidos; "
                  f"{resto} mantidos (limpeza bloqueada pelo ambiente — não é erro)")
        else:
            print(f"[VideoRenderer] {removidos} frames temporários removidos")

    def add_audio_to_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        audio_volume: float = 1.0,
    ) -> Path:
        output_path = Path(output_path)
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-filter:a", f"volume={audio_volume}",
            "-shortest",
            str(output_path),
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[VideoRenderer] FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg falhou: {result.stderr}")
        
        print(f"[VideoRenderer] Áudio adicionado: {output_path}")
        return output_path
