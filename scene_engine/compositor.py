import subprocess
import shutil
from pathlib import Path
from typing import Optional


class Compositor:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg não encontrado")
        print("[Compositor] FFmpeg OK")

    def composite_layers(
        self,
        layers: list[Path],
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
        duration: float = None,
    ) -> Path:
        if not layers:
            raise ValueError("Nenhuma camada fornecida")
        
        output_path = Path(output_path)
        
        if len(layers) == 1:
            return self._copy_video(layers[0], output_path)
        
        filter_complex = self._build_filter(layers)
        
        inputs = []
        for layer in layers:
            inputs.extend(["-i", str(layer)])
        
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", f"[out]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            str(output_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Compositor] Erro: {result.stderr}")
            raise RuntimeError(f"FFmpeg falhou")
        
        print(f"[Compositor] Composição salva: {output_path}")
        return output_path

    def _build_filter(self, layers: list[Path]) -> str:
        n = len(layers)
        filter_parts = []
        
        for i in range(n):
            filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[layer{i}]")
        
        filter_parts.append(f"[layer0]format=yuv420a[base]")
        
        for i in range(1, n):
            filter_parts.append(
                f"[base][layer{i}]overlay=0:0:format=yuv420[base]"
            )
        
        filter_parts.append("[base]format=yuv420p[out]")
        
        return ";".join(filter_parts)

    def _copy_video(self, src: Path, dst: Path) -> Path:
        shutil.copy2(src, dst)
        return dst

    def concatenate_videos(
        self,
        videos: list[Path],
        output_path: Path,
    ) -> Path:
        output_path = Path(output_path)
        concat_file = self.output_dir / "_concat.txt"
        
        with open(concat_file, "w") as f:
            for video in videos:
                f.write(f"file '{video.resolve()}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Compositor] Erro: {result.stderr}")
            raise RuntimeError(f"FFmpeg falhou")
        
        concat_file.unlink()
        print(f"[Compositor] Vídeos concatenados: {output_path}")
        return output_path

    @classmethod
    def _estilo_para_force_style(cls, estilo: Optional[dict], padrao: str) -> str:
        """Converte o dict `legenda_estilo` do wizard em force_style ASS.

        Cores chegam em #RRGGBB e o ASS quer &HBBGGRR (BGR invertido).
        `posicao`: baixo (padrão do ASS, Alignment=2) / centro (Alignment=5,
        meio exato) / topo (Alignment=8 + MarginV=60).
        Qualquer campo ausente cai no padrão do método.
        """
        if not estilo:
            return padrao

        def _bgr(hexstr, fallback="&H00FFFFFF"):
            try:
                h = str(hexstr).lstrip("#")
                if len(h) != 6:
                    return fallback
                r, g, b = h[0:2], h[2:4], h[4:6]
                return f"&H00{b}{g}{r}".upper()
            except Exception:
                return fallback

        posicao = str(estilo.get("posicao", "baixo")).lower()

        # ⚠️ NOVO (22/09/2026): fonte do BUNDLE do projeto (fonts/*.ttf).
        # Montserrat/Inter não vêm no Windows; sem o arquivo, o FFmpeg caía
        # na fonte padrão silenciosamente. Arial/Verdana/Georgia existem no
        # sistema — FontFile só quando o ttf existe na pasta fonts/.
        fonte_nome = str(estilo.get("fonte", "Montserrat"))
        arquivo_fonte = cls._ttf_da_fonte(fonte_nome)

        partes = [
            f"FontName={fonte_nome}",
            f"FontSize={int(estilo.get('tamanho', 48))}",
            f"PrimaryColour={_bgr(estilo.get('cor'), '&H00FFFFFF')}",
            f"OutlineColour={_bgr(estilo.get('corContorno'), '&H00000000')}",
            "BorderStyle=1",
            f"Outline={int(estilo.get('contorno', 2))}",
            "Shadow=0",
            "Bold=1" if estilo.get("negrito") else "Bold=0",
        ]
        if arquivo_fonte:
            partes.append(f"FontFile={arquivo_fonte}")
        if posicao == "centro":
            partes.append("Alignment=5")
        elif posicao == "topo":
            partes.extend(["Alignment=8", "MarginV=60"])
        return ",".join(partes)

    @staticmethod
    def _ttf_da_fonte(nome: str) -> Optional[str]:
        """Caminho (relativo, com / pro filtro) do ttf na pasta fonts/.

        Devolve None pra fontes do sistema (Arial, Verdana, Georgia...) ou
        se o arquivo não existir — nesse caso o FFmpeg usa a fonte pelo nome.
        """
        mapa = {
            "montserrat": "montserrat-Regular.ttf",
            "inter": "inter-Regular.ttf",
        }
        arquivo = mapa.get(nome.strip().lower())
        if not arquivo:
            return None
        candidatos = [
            Path(__file__).resolve().parent.parent / "fonts" / arquivo,
            Path.cwd() / "fonts" / arquivo,
        ]
        for c_ in candidatos:
            if c_.is_file():
                return c_.as_posix()
        return None

    def add_subtitles(
        self,
        video_path: Path,
        subtitles_path: Path,
        output_path: Path,
        style: str = "FontName=Montserrat,PrimaryColour=&H00FFFFFF,Outline=2",
        estilo: Optional[dict] = None,
    ) -> Path:
        """
        Queima legendas no vídeo (hard subs) via filtro `subtitles` do FFmpeg.

        CORRIGIDO (19/09/2026) — bug de path no Windows.
        O código montava:
            -vf "subtitles='D:\\dev-projetos\\...\\x.srt':force_style='...'"
        No Windows isso quebra por DOIS motivos:
          1. As barras invertidas são interpretadas como ESCAPE pelo parser de
             filtros do FFmpeg → o path chega como
             "dev-projetosMusicClipStudiooutputx.srt" (tudo colado).
          2. O `:` do drive (D:) colide com o separador de opções do filtro.

        A forma correta e portável é escapar o path com a regra do FFmpeg
        (barra normal + escape do `:`) e NÃO envolver em quotes simples:
            subtitles=filename='D\\:/dev-projetos/.../x.srt':force_style='...'
        """
        output_path = Path(output_path)

        # Path seguro para o parser de filtros do FFmpeg:
        #  - tudo em barras normais
        #  - o `:` do drive vira `\:`
        sub_filtro = str(subtitles_path).replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles=filename='{sub_filtro}':force_style='{self._estilo_para_force_style(estilo, style)}'",
            "-c:a", "copy",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Compositor] Erro: {result.stderr}")
            raise RuntimeError("FFmpeg falhou ao queimar legendas")

        print(f"[Compositor] Legendas adicionadas: {output_path}")
        return output_path

    def normalize_audio(
        self,
        video_path: Path,
        output_path: Path,
        target_loudness: float = -14.0,
    ) -> Path:
        output_path = Path(output_path)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-af", f"loudnorm=I={target_loudness}",
            "-c:v", "copy",
            str(output_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Compositor] Erro: {result.stderr}")
            return video_path
        
        print(f"[Compositor] Áudio normalizado: {output_path}")
        return output_path
