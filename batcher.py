"""
Batcher de clipes musicais v2.

Gera múltiplos clipes a partir de prompts, com agente de IA
e banco de dados de mídia.
"""

import sys
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import ClipConfig, load_config
from MusicClipStudio.agent import ClipAgent


@dataclass
class BatchConfig:
    """Configuração de geração em lote."""
    prompts: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    lyrics_list: list[str] = field(default_factory=list)
    music_prompts: list[str] = field(default_factory=list)
    imagens_base: list[str] = field(default_factory=list)
    duracao: int = 30
    formato: str = "9/16"
    usa_agente: bool = True
    usa_banco: bool = True
    paralelo: bool = False


@dataclass
class BatchResult:
    """Resultado de um clipe no batch."""
    clip_id: str = ""
    prompt: str = ""
    sucesso: bool = False
    arquivo_video: str = ""
    mensagem: str = ""
    duracao_geracao: float = 0.0


class ClipBatcher:
    """Batcher para geração de múltiplos clipes v2."""

    def __init__(self, config: Optional[ClipConfig] = None):
        self.config = config or load_config()
        self.pipeline = None  # Lazy init
        self.agent = ClipAgent(self.config)
        self.batch_config: Optional[BatchConfig] = None
        self.results: dict[str, BatchResult] = {}

    def _init_pipeline(self):
        if self.pipeline is None:
            from MusicClipStudio.pipeline import MusicClipPipeline
            self.pipeline = MusicClipPipeline(self.config)

    def criar_batch(
        self,
        prompts: Optional[list[str]] = None,
        descriptions: Optional[list[str]] = None,
        lyrics_list: Optional[list[str]] = None,
        imagens: Optional[list[str]] = None,
        duracao: int = 30,
        formato: str = "9/16",
        usa_agente: bool = True,
        usa_banco: bool = True,
    ) -> "ClipBatcher":
        self.batch_config = BatchConfig(
            prompts=prompts or [],
            descriptions=descriptions or [],
            lyrics_list=lyrics_list or [],
            imagens_base=imagens or [],
            duracao=duracao,
            formato=formato,
            usa_agente=usa_agente,
            usa_banco=usa_banco,
        )
        return self

    def executar(self) -> dict[str, BatchResult]:
        """Executa o batch."""
        if not self.batch_config:
            raise ValueError("Chame criar_batch() primeiro.")

        self.results = {}

        prompts = (
            self.batch_config.prompts +
            self.batch_config.descriptions +
            self.batch_config.lyrics_list
        )

        for i, prompt in enumerate(prompts, 1):
            clip_id = f"batch_{i:03d}"
            print(f"[Batch] [{i}/{len(prompts)}] Gerando {clip_id}...")
            inicio = time.time()

            try:
                self._init_pipeline()

                # Determinar tipo de conteúdo
                has_lyrics = i <= len(self.batch_config.lyrics_list)
                has_description = i <= len(self.batch_config.descriptions) + len(self.batch_config.lyrics_list)

                if has_lyrics:
                    idx = i - 1 - len(self.batch_config.descriptions) if i > len(self.batch_config.descriptions) else 0
                    lyrics = self.batch_config.lyrics_list[idx] if idx < len(self.batch_config.lyrics_list) else prompt
                    resultado = self.pipeline.executar_rapido(lyrics=lyrics, music_prompt=prompt)
                else:
                    descricao = self.batch_config.descriptions[i - 1] if has_description else prompt
                    resultado = self.pipeline.gerar_com_agente(
                        descricao=descricao,
                        music_prompt=prompt,
                    )

                duracao_geracao = time.time() - inicio
                sucesso = resultado is not None

                self.results[clip_id] = BatchResult(
                    clip_id=clip_id,
                    prompt=prompt,
                    sucesso=sucesso,
                    arquivo_video=str(resultado) if resultado else "",
                    duracao_geracao=duracao_geracao,
                )
                status = "[OK]" if sucesso else "[FAIL]"
                print(f"  {status} {clip_id}: {resultado}")

            except Exception as e:
                duracao_geracao = time.time() - inicio
                self.results[clip_id] = BatchResult(
                    clip_id=clip_id, prompt=prompt,
                    sucesso=False, mensagem=str(e),
                    duracao_geracao=duracao_geracao,
                )
                print(f"  [ERROR] {clip_id}: {e}")

        return self.results

    def resultados_resumidos(self) -> dict:
        total = len(self.results)
        sucessos = sum(1 for r in self.results.values() if r.sucesso)
        return {
            "total": total,
            "sucessos": sucessos,
            "falhas": total - sucessos,
            "taxa_sucesso": sucessos / total if total > 0 else 0,
            "clips": self.results,
        }

    def gerar_com_agente_lote(
        self,
        descricoes: list[str],
        music_prompts: Optional[list[str]] = None,
    ) -> dict[str, BatchResult]:
        """
        Gera múltiplos clipes com agente de IA.

        Cada descrição é analisada pelo agente para criar direção visual única.
        """
        self.batch_config = BatchConfig(
            descriptions=descricoes,
            music_prompts=music_prompts or ["" for _ in descricoes],
            duracao=30,
            usa_agente=True,
            usa_banco=True,
        )
        return self.executar()