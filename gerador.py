"""
Geração de clipe musical - integra GUI com moviepy/efeitos.
"""

import sys
import urllib.request
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from moviepy import (
    ImageClip, VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip
)
import numpy as np
from PIL import Image

from MusicClipStudio.config import get_config, ClipConfig


FORMATOS_RESOLUCAO = {
    "9/16": (1080, 1920),
    "16/9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "3/4": (810, 1080),
    "4/3": (1080, 810),
}


def gerar_clipe(
    midia_selecionada: list,
    output_path: str,
    duracao_total: int = 30,
    fps: int = 30,
    formato: str = "9/16",
    efeito: str = "zoom_in",
    transicao: str = "fade",
    duracao_por_imagem: float = 5.0,
    audio_path: Optional[str] = None,
    legendas: Optional[list] = None,
    salvar_srt: bool = True,
    config_ritmo=None,
    descricao: str = "",
    callback_log: Optional[Callable] = None,
    callback_prog: Optional[Callable] = None,
) -> str:
    """Gera o clipe musical.

    `legendas` e' uma lista de `SegmentoLegenda` (ja revisada pelo usuario
    na etapa 2). Se vier preenchida, as legendas sao queimadas nos frames
    do video antes do encode. Se vier vazia/None, o video sai sem legenda
    e nada muda no caminho antigo.

    `config_ritmo` e' um `planejador.ConfigRitmo`. Quando informado, a
    duracao de cada clipe e' CALCULADA a partir da musica (frases da
    letra, ou grade de batidas, ou fallback uniforme) em vez de ser a
    divisao cega `duracao_total / n_midias`. A lista final de midias
    passa a ser a que o plano escolheu — inclusive reciclando quando
    faltam midias.

    `descricao` e' a descricao livre da musica ("tribal com tambores,
    violao classico"). Ela nao muda o calculo dos slots; serve para a
    busca de midia. Aqui ela so e' registrada no log para rastreio.
    """
    if callback_log is None:
        callback_log = print
    if callback_prog is None:
        callback_prog = lambda x: None

    largura, altura = FORMATOS_RESOLUCAO.get(formato, (1080, 1920))

    callback_log("[CLIP] Iniciando geracao do clipe...")
    callback_log(f"   Formato: {formato} ({largura}x{altura})")
    callback_log(f"   Duracao: {duracao_total}s | FPS: {fps}")
    callback_log(f"   Efeito: {efeito} | Transicao: {transicao}")
    callback_log(f"   Itens: {len(midia_selecionada)}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="clipe_"))

    try:
        # ── Analise da musica + calculo do plano ───────────────
        # Feito ANTES do download: se faltar midia, o usuario descobre
        # agora, nao depois de baixar 200 arquivos.
        analise = None
        plano = None
        if config_ritmo is not None:
            analise = _analisar_audio(audio_path, callback_log)
            plano = _calcular_plano(
                duracao_total, midia_selecionada, config_ritmo,
                legendas, analise, callback_log,
            )
            if plano is not None and getattr(plano, "midias", None):
                midia_selecionada = plano.midias
                callback_log(
                    f"[PLANO] {len(midia_selecionada)} clipe(s) definidos "
                    f"a partir da música"
                )
        if descricao:
            callback_log(f"[PLANO] Descrição da música: {descricao}")

        callback_log("[DOWNLOAD] Baixando midia...")
        callback_prog(5)
        clip_paths = _baixar_midia(midia_selecionada, temp_dir, callback_log)

        if not clip_paths:
            callback_log("[ERROR] Nenhuma midia valida encontrada")
            return ""

        callback_log(f"[OK] {len(clip_paths)} arquivo(s) baixado(s)")
        callback_prog(25)

        # O plano fala de midias; o download pode ter descartado algumas
        # (URL quebrada). Alinha os dois antes de montar, senao o efeito
        # calculado para um slot cairia em outro.
        if plano is not None:
            clip_paths, plano = _alinhar_plano(clip_paths, plano, callback_log)

        callback_log("[CLIP] Criando clips...")
        callback_prog(30)
        clips = _criar_clips(
            clip_paths, largura, altura, duracao_por_imagem,
            efeito, fps, callback_log, callback_prog, plano=plano,
        )

        if not clips:
            callback_log("[ERROR] Nenhum clip valido criado")
            return ""

        callback_log(f"[OK] {len(clips)} clip(s) criado(s)")
        callback_prog(60)

        if plano is not None:
            # Cada clipe com a duracao do SEU slot (vinda da musica),
            # nao uma media global. E' isto que faz o corte cair no fim
            # da frase em vez de cortar uma palavra no meio.
            clips_ajustados = _ajustar_duracoes(clips, plano, callback_log)
        else:
            duracao_por_clip = duracao_total / max(len(clips), 1)
            callback_log(f"[TIME] {duracao_por_clip:.1f}s por clip")

            clips_ajustados = []
            for clip in clips:
                if clip.duration < duracao_por_clip:
                    clip = clip.with_duration(duracao_por_clip)
                elif clip.duration > duracao_por_clip:
                    clip = clip.subclipped(0, duracao_por_clip)
                clips_ajustados.append(clip)

        callback_log("[CONCAT] Concatenando clips...")
        callback_prog(70)
        if len(clips_ajustados) > 1:
            video_final = concatenate_videoclips(clips_ajustados, method="compose")
        else:
            video_final = clips_ajustados[0]

        if audio_path and Path(audio_path).exists():
            callback_log("[AUDIO] Adicionando audio...")
            audio = AudioFileClip(audio_path)
            if audio.duration > video_final.duration:
                video_final = video_final.with_duration(audio.duration)
            else:
                video_final = video_final.subclipped(0, audio.duration)
            video_final = video_final.with_audio(audio)

        # ── Legendas ────────────────────────────────────────────
        # Queimadas DEPOIS do audio, para o clip ja ter a duracao
        # definitiva (senao o SRT poderia ter tempos alem do video).
        srt_path = ""
        if legendas:
            try:
                from MusicClipStudio.renderizador_legendas import (
                    aplicar_legendas, segmentos_para_srt,
                )

                # Tempos que passam do fim do video sao cortados: legenda
                # orfa faria o moviepy pedir frames inexistentes.
                dur_video = video_final.duration
                validas = [
                    s for s in legendas
                    if getattr(s, "inicio", 0) < dur_video
                    and getattr(s, "texto", "").strip()
                ]
                descartadas = len(legendas) - len(validas)
                if descartadas:
                    callback_log(
                        f"   [WARN] {descartadas} legenda(s) fora da duracao "
                        f"do video ({dur_video:.1f}s) foram ignoradas"
                    )

                if validas:
                    callback_log("[LEGENDA] Queimando legendas no video...")
                    callback_prog(85)
                    video_final = aplicar_legendas(
                        video_final, validas, callback_log=callback_log
                    )

                    if salvar_srt:
                        srt_path = str(
                            Path(output_path).with_suffix(".srt")
                        )
                        try:
                            segmentos_para_srt(validas, srt_path)
                            callback_log(f"   [OK] SRT salvo: {srt_path}")
                        except Exception as e:
                            callback_log(f"   [WARN] Nao salvou SRT: {e}")
                            srt_path = ""
            except Exception as e:
                # Legenda e' acessorio: falhar aqui nao pode perder o
                # video inteiro que ja levou minutos para ser montado.
                callback_log(f"   [WARN] Falha ao aplicar legendas: {e}")
                import traceback
                traceback.print_exc()

        callback_prog(90)
        callback_log(f"[RENDER] Renderizando: {output_path}")
        video_final.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            threads=4,
            ffmpeg_params=[
                "-crf", "18",
                "-profile:v", "high",
                "-level", "4.1",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
            ],
            logger=None,
        )

        callback_prog(100)
        callback_log(f"[OK] Clipe gerado: {output_path}")
        if legendas:
            callback_log(f"   Legendas queimadas: {len(legendas)}")
            if srt_path:
                callback_log(f"   Arquivo de legenda: {srt_path}")
        return output_path

    except Exception as e:
        callback_log(f"[ERROR] Erro na geracao: {e}")
        import traceback
        traceback.print_exc()
        return ""

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ════════════════════════════════════════════════════════════════
# Ponte com o planejador
# ════════════════════════════════════════════════════════════════

def _analisar_audio(audio_path: Optional[str], callback_log: Callable):
    """Analisa a musica (BPM, batidas, energia). Nunca levanta.

    Sem audio nao ha musica para seguir; devolve None e o plano cai no
    modo uniforme, que e' o comportamento antigo.
    """
    if not audio_path or not Path(audio_path).exists():
        callback_log("   [PLANO] Sem áudio: cálculo pela duração informada")
        return None

    try:
        from MusicClipStudio.analise_audio import analisar

        callback_log("[ANALISE] Lendo batida e energia da música...")
        analise = analisar(audio_path, callback_log=lambda m: callback_log(f"   {m}"))
        if analise.ok:
            callback_log(f"   {analise.resumo()}")
        else:
            callback_log(f"   [WARN] Análise incompleta: {analise.erro}")
        return analise
    except Exception as e:
        # Analise e' enfeite: o clipe tem que sair mesmo sem ela.
        callback_log(f"   [WARN] Não foi possível analisar o áudio: {e}")
        return None


def _calcular_plano(duracao, midias, config_ritmo, legendas, analise,
                    callback_log: Callable):
    """Chama o planejador. Nunca levanta — devolve None se falhar."""
    try:
        from MusicClipStudio.planejador import calcular_plano

        # As legendas revisadas sao os segmentos de frase: e' delas que
        # saem os tempos de corte. Sem elas o plano usa batida/uniforme.
        segmentos = [
            s for s in (legendas or [])
            if float(getattr(s, "fim", 0) or 0) > float(getattr(s, "inicio", 0) or 0)
        ]
        if not segmentos and legendas:
            callback_log("   [PLANO] Legendas sem tempos válidos; usando batida")

        return calcular_plano(
            duracao=float(duracao or 0.0),
            midias=midias,
            config=config_ritmo,
            segmentos=segmentos,
            analise=analise,
            callback_log=callback_log,
        )
    except Exception as e:
        callback_log(f"   [WARN] Falha no cálculo do plano: {e}")
        import traceback
        traceback.print_exc()
        return None


def _alinhar_plano(clip_paths: list, plano, callback_log: Callable):
    """Casa o plano com os arquivos que o download realmente entregou.

    O download descarta URL quebrada e deduplica por URL. Se ele devolver
    menos itens que o plano, alinhamos pela posicao para o efeito/duration
    calculado para um slot nao cair em outro clipe.
    """
    n_plano = len(getattr(plano, "slots", []))
    n_real = len(clip_paths)

    if n_real == n_plano:
        return clip_paths, plano

    callback_log(
        f"   [PLANO] Ajuste: {n_plano} slot(s) calculados, "
        f"{n_real} arquivo(s) baixados"
    )

    if n_real < n_plano:
        # Faltou midia: corta os slots sobrando do fim e renumera.
        plano.slots = list(plano.slots[:n_real])
        if getattr(plano, "efeitos", None):
            plano.efeitos = list(plano.efeitos[:n_real])
        for i, s in enumerate(plano.slots, 1):
            s.indice = i
        plano.avisos.append(
            f"{n_plano - n_real} clipe(s) caíram: mídia indisponível no download"
        )
    else:
        # Sobrou midia baixada: gera slots uniformes para elas, para nao
        # jogar arquivo fora silenciosamente.
        try:
            from MusicClipStudio.planejador import Slot

            extra = plano.slots[-1] if plano.slots else None
            passo = (extra.duracao if extra else 5.0) or 5.0
            fim = extra.fim if extra else 0.0
            novos = []
            for i in range(n_plano + 1, n_real + 1):
                novos.append(Slot(
                    indice=i, inicio=fim, fim=fim + passo, origem="extra",
                ))
                fim += passo
            plano.slots.extend(novos)
            efeito_extra = (
                plano.efeitos[-1] if getattr(plano, "efeitos", None) else "zoom_in"
            )
            plano.efeitos = list(
                getattr(plano, "efeitos", [])
            ) + [efeito_extra] * len(novos)
        except Exception:
            plano.slots = list(plano.slots[:n_real])
            plano.efeitos = list(getattr(plano, "efeitos", []))[:n_real]

    return clip_paths, plano


def _ajustar_duracoes(clips: list, plano, callback_log: Callable) -> list:
    """Aplica a duracao de CADA slot ao clipe correspondente.

    Substitui a antiga divisao cega `duracao_total / n_clips`, em que
    todo clipe recebia o mesmo tempo e o corte caia no meio da palavra.
    """
    dur_total = 0.0
    ajustados = []

    for i, clip in enumerate(clips):
        dur_slot = None
        if i < len(getattr(plano, "slots", [])):
            dur_slot = plano.slots[i].duracao

        if not dur_slot or dur_slot <= 0:
            dur_slot = clip.duration or 5.0

        if clip.duration < dur_slot:
            clip = clip.with_duration(dur_slot)
        elif clip.duration > dur_slot:
            clip = clip.subclipped(0, dur_slot)

        dur_total += dur_slot
        ajustados.append(clip)

    callback_log(
        f"[TIME] {len(ajustados)} clipe(s) com duração da música "
        f"(média {dur_total / max(len(ajustados), 1):.1f}s, "
        f"total {dur_total:.1f}s)"
    )
    return ajustados


def _baixar_midia(midia: list, temp_dir: Path, callback_log: Callable) -> list:
    """Baixa mídia com streaming (chunks) e dedup.
    Aceita tanto objetos MediaAsset quanto dicts com keys 'path' e 'type' (já baixados).
    """
    paths = []
    seen_urls = set()

    for i, item in enumerate(midia):
        try:
            # Se já é dict com path e type (vindo do _download_mock_assets), usar direto
            if isinstance(item, dict):
                if "path" in item and "type" in item:
                    paths.append({"path": item["path"], "type": item["type"]})
                    callback_log(f"   [OK] Usando mídia local: {Path(item['path']).name}")
                continue

            # Caso contrário, trata como objeto MediaAsset
            url = item.video_url if item.media_type == "video" and item.video_url else (item.download_url or item.url)
            if not url:
                continue

            # Dedup
            base_url = url.split("?")[0]
            if base_url in seen_urls:
                continue
            seen_urls.add(base_url)

            if Path(url).exists():
                paths.append({"path": url, "type": item.media_type})
                continue

            if not url.startswith("http"):
                continue

            ext = ".mp4" if item.media_type == "video" else ".jpg"
            filename = f"midia_{i}{ext}"
            filepath = temp_dir / filename

            search_info = f" [{item.search_term}]" if hasattr(item, 'search_term') and item.search_term else ""
            callback_log(f"   [DOWNLOAD] [{i+1}] {item.source}{search_info}: {item.description[:35]}...")

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            # Streaming download (chunks)
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(filepath, "wb") as f:
                    while True:
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)

            size_mb = filepath.stat().st_size / (1024 * 1024)
            callback_log(f"   [OK] {filename} ({size_mb:.1f}MB)")
            paths.append({"path": str(filepath), "type": item.media_type})

        except Exception as e:
            callback_log(f"   [WARN] Erro item {i}: {e}")
            continue

    return paths


def _criar_clips(
    clip_paths: list,
    largura: int,
    altura: int,
    duracao_por_imagem: float,
    efeito: str,
    fps: int,
    callback_log: Callable,
    callback_prog: Callable,
    plano=None,
) -> list:
    """Cria clips. Efeitos SÓ em imagens, vídeos passam direto.

    Com `plano`, cada clipe usa o efeito e a duracao do SEU slot —
    video toca direto, imagem recebe movimento conforme a energia do
    trecho. Sem `plano`, mantem o efeito unico escolhido na tela.
    """
    clips = []
    total = len(clip_paths)
    original_clips = []  # Para fechar depois

    efeitos = list(getattr(plano, "efeitos", None) or []) if plano else []
    slots = list(getattr(plano, "slots", None) or []) if plano else []

    for idx, item in enumerate(clip_paths):
        try:
            path = item["path"]
            tipo = item["type"]
            progresso = 30 + int(30 * idx / max(total, 1))
            callback_prog(progresso)

            # Efeito e duracao deste clipe especificamente. O plano manda;
            # o que veio da tela e' so o fallback.
            efeito_clipe = efeitos[idx] if idx < len(efeitos) else efeito
            dur_clipe = (
                slots[idx].duracao if idx < len(slots) else duracao_por_imagem
            )

            if tipo == "video" and Path(path).suffix.lower() in [".mp4", ".webm", ".avi", ".mov"]:
                callback_log(f"   [VIDEO] [{idx+1}/{total}] Video: {Path(path).name}")
                clip = VideoFileClip(path)
                original_clips.append(clip)
                clip = clip.resized(new_size=(largura, altura))
                clips.append(clip)

            elif Path(path).suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]:
                callback_log(
                    f"   [IMAGE] [{idx+1}/{total}] Imagem: {Path(path).name} "
                    f"(+{efeito_clipe}, {dur_clipe:.1f}s)"
                )
                img = Image.open(path)
                img = img.convert("RGB")

                scale = max(largura / img.width, altura / img.height)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.BILINEAR)

                left = (img.width - largura) // 2
                top = (img.height - altura) // 2
                img = img.crop((left, top, left + largura, top + altura))

                frame = np.array(img)
                clip = _criar_clip_com_efeito(frame, dur_clipe, efeito_clipe, fps)
                clips.append(clip)

        except Exception as e:
            callback_log(f"   [WARN] Erro processando {item['path']}: {e}")
            continue

    return clips


def _criar_clip_com_efeito(frame: np.ndarray, duration: float, efeito: str, fps: int):
    """Cria clip de imagem com efeito aplicado."""

    def make_frame(t):
        p = t / max(duration, 0.001)

        if efeito == "corte":
            return frame

        elif efeito == "zoom_in":
            zoom = 1.0 + 0.15 * p
            return _aplicar_zoom(frame, zoom)

        elif efeito == "zoom_out":
            zoom = 1.15 - 0.15 * p
            return _aplicar_zoom(frame, zoom)

        elif efeito == "zoom_in_out":
            wave = 0.5 - 0.5 * np.cos(2 * np.pi * p)
            zoom = 1.0 + 0.1 * wave
            return _aplicar_zoom(frame, zoom)

        elif efeito == "zoom_diagonal":
            zoom = 1.0 + 0.12 * p
            dx = int(10 * p)
            dy = int(10 * p)
            return _aplicar_zoom_pan(frame, zoom, dx, dy)

        elif efeito == "pan_left":
            dx = int(50 * p)
            return _aplicar_pan(frame, dx, 0)

        elif efeito == "pan_right":
            dx = int(-50 * p)
            return _aplicar_pan(frame, dx, 0)

        elif efeito == "pan_up":
            dy = int(50 * p)
            return _aplicar_pan(frame, 0, dy)

        elif efeito == "pan_down":
            dy = int(-50 * p)
            return _aplicar_pan(frame, 0, dy)

        elif efeito == "dolly_zoom":
            zoom = 1.0 + 0.2 * p
            return _aplicar_zoom(frame, zoom)

        elif efeito == "shake":
            dx = int(5 * np.sin(p * 10))
            dy = int(3 * np.cos(p * 8))
            return _aplicar_pan(frame, dx, dy)

        elif efeito == "parallax":
            dx = int(30 * p)
            return _aplicar_pan(frame, dx, 0)

        elif efeito == "orbital":
            angle = p * 2 * np.pi
            dx = int(20 * np.cos(angle))
            dy = int(20 * np.sin(angle))
            return _aplicar_pan(frame, dx, dy)

        elif efeito == "blur_reveal":
            if p < 0.3:
                from PIL import ImageFilter
                blur_radius = int(15 * (1 - p / 0.3))
                img = Image.fromarray(frame)
                if blur_radius > 0:
                    img = img.filter(ImageFilter.GaussianBlur(blur_radius))
                return np.array(img)
            return frame

        elif efeito == "fade_in":
            alpha = min(1.0, p * 2)
            return (frame * alpha).astype(np.uint8)

        elif efeito == "fade_out":
            alpha = max(0.0, 1.0 - (p - 0.7) * 3.33) if p > 0.7 else 1.0
            return (frame * alpha).astype(np.uint8)

        return frame

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)


def _aplicar_zoom(frame: np.ndarray, zoom: float) -> np.ndarray:
    h, w = frame.shape[:2]
    new_h, new_w = int(h * zoom), int(w * zoom)
    img = Image.fromarray(frame)
    img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    img = img.crop((left, top, left + w, top + h))
    return np.array(img)


def _aplicar_zoom_pan(frame: np.ndarray, zoom: float, dx: int, dy: int) -> np.ndarray:
    h, w = frame.shape[:2]
    new_h, new_w = int(h * zoom), int(w * zoom)
    img = Image.fromarray(frame)
    img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    left = (new_w - w) // 2 + dx
    top = (new_h - h) // 2 + dy
    left = max(0, min(left, new_w - w))
    top = max(0, min(top, new_h - h))
    img = img.crop((left, top, left + w, top + h))
    return np.array(img)


def _aplicar_pan(frame: np.ndarray, dx: int, dy: int) -> np.ndarray:
    h, w = frame.shape[:2]
    margin = 100
    new_w = w + margin * 2
    new_h = h + margin * 2
    big = np.zeros((new_h, new_w, 3), dtype=np.uint8)
    big[margin:margin+h, margin:margin+w] = frame
    left = margin - dx
    top = margin - dy
    left = max(0, min(left, new_w - w))
    top = max(0, min(top, new_h - h))
    return big[top:top+h, left:left+w]
