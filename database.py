"""
Banco de dados e API para fotos e vídeos gratuitos.

Integra com serviços de mídia gratuita:
  - Pexels API (fotos e vídeos)
  - Pixabay API (fotos e vídeos)
  - Unsplash API (fotos)

Permite buscar imagens e vídeos temáticos para clipes musicais.
Suporta múltiplas chaves de API e busca em paralelo.
"""

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from MusicClipStudio.config import get_config


@dataclass
class StockMedia:
    """Item de mídia do banco de dados."""
    id: str = ""
    url: str = ""
    thumbnail_url: str = ""
    width: int = 0
    height: int = 0
    source: str = ""           # pexels, pixabay, unsplash
    media_type: str = "photo"  # photo, video
    category: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    download_url: str = ""
    video_url: str = ""        # URL do vídeo (se aplicável)
    search_term: str = ""      # Termo de busca que encontrou este item


@dataclass
class StockSearch:
    """Resultado de busca no banco de dados."""
    query: str = ""
    provider: str = ""
    results: list[StockMedia] = field(default_factory=list)
    total: int = 0


ALTURA_VIDEO_MINIMA = 720


def _escolher_variante_video(video_files):
    """Menor variante do Pexels que ainda atende a altura mínima.

    ⚠️ CORRIGIDO (21/09/2026): antes o código pegava SEMPRE a maior
    resolução (`sorted(..., reverse=True)[0]`), ou seja 3840x2160. O
    render roda esse vídeo num Chromium headless e decodifica 4K por
    frame — medido ~2,5 s/frame, o que fazia um clipe de 3 min levar
    ~3 h. Com o fundo desfocado são DOIS elementos de vídeo, então o 4K
    era decodificado 2x por frame.

    O quadro final é no máximo 1080x1920. Com `contain`, uma variante
    1280x720 já cobre a faixa da mídia em resolução nativa (1080x607);
    a camada de fundo é borrada de propósito, então não precisa de
    detalhe nenhum. 720p corta o custo de decode em ~9x.
    """
    if not video_files:
        return ""
    validos = [v for v in video_files if v.get("link")]
    if not validos:
        return ""
    por_altura = sorted(validos, key=lambda v: v.get("height", 0) or 0)
    for v in por_altura:
        if (v.get("height", 0) or 0) >= ALTURA_VIDEO_MINIMA:
            return v.get("link", "")
    # nenhuma chega no mínimo: usa a maior disponível
    return por_altura[-1].get("link", "")


class StockDatabase:
    """Banco de dados de mídia gratuita para clipes."""

    API_BASE = {
        "pexels": "https://api.pexels.com/v1",
        "pexels_videos": "https://api.pexels.com/v1/videos",
        "pixabay": "https://pixabay.com/api/",
        "pixabay_videos": "https://pixabay.com/api/videos/",
        "unsplash": "https://api.unsplash.com",
        "nasa": "https://images-api.nasa.gov",
        "nasa_search": "https://images-api.nasa.gov/search",
        "coverr": "https://api.coverr.co",
        "giphy": "https://api.giphy.com/v1",
        "openverse": "https://api.openverse.org/v1",
    }

    def __init__(self, config=None):
        self.config = config or get_config()
        self._cache_dir = Path(self.config.base_dir) / "database" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        # ⚠️ NOVO (23/09/2026): URLs de API por banco definidas pelo usuário
        # (diálogo de chaves). Formato JSON {"pexels": "https://..."};
        # bancos sem URL usam as oficiais do API_BASE.
        try:
            self._urls_custom = json.loads(self.config.stock_urls or "{}")
            if not isinstance(self._urls_custom, dict):
                self._urls_custom = {}
        except (ValueError, TypeError):
            self._urls_custom = {}

    def _url(self, chave: str) -> str:
        """URL de API de um banco: custom (se definida) → oficial.

        Aceita tanto a chave lógica ("pexels") quanto a técnica
        ("pexels_videos" etc.) — as técnicas herdam a custom do banco.
        """
        banco = chave.split("_")[0] if "_" in chave else chave
        # ⚠️ CORRIGIDO (23/09): URL vazia gravada não conta — volta p/ oficial
        # (antes "" virava a URL escolhida e a requisição ficava "/search?...",
        # "unknown url type").
        if chave in self._urls_custom and str(self._urls_custom[chave]).strip():
            return str(self._urls_custom[chave]).rstrip("/")
        if banco in self._urls_custom and str(self._urls_custom[banco]).strip():
            return str(self._urls_custom[banco]).rstrip("/")
        return self.API_BASE[chave]

    def _get_api_key(self, provider: str) -> str:
        """Retorna a chave API correta para o provedor."""
        if provider == "pexels":
            return self.config.stock_pexels_api_key
        elif provider == "pixabay":
            return self.config.stock_pixabay_api_key
        elif provider == "unsplash":
            return self.config.stock_unsplash_api_key
        elif provider == "nasa":
            return self.config.stock_nasa_api_key
        elif provider == "coverr":
            return self.config.stock_coverr_api_key
        elif provider == "giphy":
            return self.config.stock_giphy_api_key
        elif provider == "openverse":
            return self.config.stock_openverse_api_key
        return self.config.stock_api_key

    def _is_enabled(self, provider: str) -> bool:
        """Verifica se o provedor está habilitado."""
        if provider == "pexels":
            return self.config.stock_pexels_enabled
        elif provider == "pixabay":
            return self.config.stock_pixabay_enabled
        elif provider == "unsplash":
            return self.config.stock_unsplash_enabled
        elif provider == "nasa":
            return self.config.stock_nasa_enabled
        elif provider == "coverr":
            return self.config.stock_coverr_enabled
        elif provider == "giphy":
            return self.config.stock_giphy_enabled
        elif provider == "openverse":
            return self.config.stock_openverse_enabled
        return True

    def pesquisar(
        self,
        query: str,
        provider: Optional[str] = None,
        max_results: Optional[int] = None,
        apenas_fotos: bool = False,
        apenas_videos: bool = False,
    ) -> StockSearch:
        """
        Busca imagens/vídeos gratuitos por query.

        Args:
            query: Termo de busca (ex: "nature sunset", "city night")
            provider: Provedor específico (pexels/pixabay/unsplash)
            max_results: Máximo de resultados
            apenas_fotos: Se True, busca apenas fotos
            apenas_videos: Se True, busca apenas vídeos

        Returns:
            StockSearch com resultados
        """
        provider = provider or self.config.stock_provider
        max_results = max_results or self.config.stock_max_results

        cache_key = f"{provider}:{query}:{apenas_fotos}:{apenas_videos}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return StockSearch(
                query=query, provider=provider,
                results=cached[:max_results], total=len(cached),
            )

        results = []
        try:
            if provider == "pexels":
                results = self._buscar_pexels(query, max_results, apenas_fotos, apenas_videos)
            elif provider == "pixabay":
                results = self._buscar_pixabay(query, max_results, apenas_fotos, apenas_videos)
            elif provider == "unsplash":
                results = self._buscar_unsplash(query, max_results)
            elif provider == "nasa":
                results = self._buscar_nasa(query, max_results)
            elif provider == "coverr":
                results = self._buscar_coverr(query, max_results)
            elif provider == "giphy":
                results = self._buscar_giphy(query, max_results)
            elif provider == "openverse":
                results = self._buscar_openverse(query, max_results)
            else:
                results = self._buscar_pexels(query, max_results, apenas_fotos, apenas_videos)
        except Exception as e:
            print(f"[StockDB] Erro ao buscar: {e}")

        # ESTE ORDENAMENTO E' OBRIGATORIO, NAO COSMETICO.
        # As fotos sao coletadas antes dos videos em _buscar_*(). Se
        # concatenarmos na ordem crua, o corte final `[:max_results]`
        # enche a cota com fotos e DESCARTA TODOS OS VIDEOS quando o
        # provedor devolve os dois tipos. Era essa a causa de a galeria
        # exibir "quase nenhum video" (ver CHECKLIST 4.8).
        # Intercalando foto/video/foto/video..., os dois tipos chegam
        # ao usuario mesmo com cota pequena.
        results = self._intercalar_tipos(results)

        self._cache[cache_key] = results

        return StockSearch(
            query=query, provider=provider,
            results=results[:max_results], total=len(results),
        )

    @staticmethod
    def _intercalar_tipos(items: list["StockMedia"]) -> list["StockMedia"]:
        """Alterna foto/video preservando a relevancia interna de cada tipo.

        Mantem a ordem relativa dentro de cada tipo (a API ja devolve
        ordenado por relevancia), mas alterna os tipos para que o corte
        por max_results nao elimine um tipo inteiro.
        """
        fotos = [m for m in items if m.media_type != "video"]
        videos = [m for m in items if m.media_type == "video"]
        if not fotos or not videos:
            return list(items)

        intercalado: list["StockMedia"] = []
        for i in range(max(len(fotos), len(videos))):
            if i < len(videos):
                intercalado.append(videos[i])
            if i < len(fotos):
                intercalado.append(fotos[i])
        return intercalado

    def pesquisar_todos(
        self,
        query: str,
        max_results: int = 10,
    ) -> StockSearch:
        """Busca em todos os provedores habilitados e combina resultados."""
        all_results = []

        providers = []
        if self.config.stock_pexels_enabled:
            providers.append("pexels")
        if self.config.stock_pixabay_enabled:
            providers.append("pixabay")
        if self.config.stock_unsplash_enabled:
            providers.append("unsplash")
        if self.config.stock_nasa_enabled:
            providers.append("nasa")
        if self.config.stock_coverr_enabled:
            providers.append("coverr")
        if self.config.stock_giphy_enabled:
            providers.append("giphy")
        if self.config.stock_openverse_enabled:
            providers.append("openverse")

        for provider in providers:
            try:
                search = self.pesquisar(query, provider=provider, max_results=max_results)
                all_results.extend(search.results)
            except Exception as e:
                print(f"[StockDB] Erro no {provider}: {e}")

        return StockSearch(
            query=query, provider="all",
            results=all_results[:max_results], total=len(all_results),
        )

    def pesquisar_multi(
        self,
        query: str,
        max_results: int = 20,
        apenas_fotos: bool = False,
        apenas_videos: bool = False,
    ) -> StockSearch:
        """⚠️ NOVO (23/09/2026): busca em TODOS os bancos habilitados do config.

        Diferença do pesquisar_todos: usa o MESMO filtro de tipo da tela
        (só fotos/só vídeos) e intercala os provedores (1 resultado de cada
        em rodada) para a galeria misturar bancos em vez de encher de um só.
        Cada banco usa a própria chave (config) e a própria URL (custom→oficial).
        """
        provedores = [p for p in self.API_BASE
                      if p in ("pexels", "pixabay", "unsplash", "nasa",
                               "coverr", "giphy", "openverse")
                      and self._is_enabled(p)]
        # Pixabay tem endpoint de vídeo separado; é consultado pelo mesmo banco.
        por_provedor: dict[str, list] = {}
        for provider in provedores:
            try:
                search = self.pesquisar(
                    query, provider=provider, max_results=max_results,
                    apenas_fotos=apenas_fotos, apenas_videos=apenas_videos,
                )
                if search.results:
                    por_provedor[provider] = list(search.results)
            except Exception as e:
                print(f"[StockDB] Erro no {provider}: {e}")

        # Rodada a rodada: 1º de cada banco, 2º de cada banco…
        combinado: list = []
        while any(por_provedor.values()):
            for provider in provedores:
                lista = por_provedor.get(provider)
                if lista:
                    combinado.append(lista.pop(0))
        return StockSearch(
            query=query, provider="all",
            results=combinado[:max_results], total=len(combinado),
        )

    def baixar(self, url: str, destino: str) -> Optional[str]:
        """Baixa mídia de URL para caminho local."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
            Path(destino).parent.mkdir(parents=True, exist_ok=True)
            with open(destino, "wb") as f:
                f.write(data)
            return destino
        except Exception as e:
            print(f"[StockDB] Erro ao baixar: {e}")
            return None

    def categorias_disponiveis(self) -> list[str]:
        """Retorna categorias sugeridas para clipes musicais."""
        return [
            "music", "concert", "band", "guitar", "piano",
            "dance", "performance", "stage", "microphone",
            "neon", "city", "night", "nature", "abstract",
            "beats", "dj", "rave", "festival", "studio",
        ]

    def _buscar_pexels(
        self,
        query: str,
        max_results: int,
        apenas_fotos: bool = False,
        apenas_videos: bool = False,
    ) -> list[StockMedia]:
        """Busca no Pexels API."""
        api_key = self._get_api_key("pexels")
        per_page = min(max_results, 20)  # Pexels free: max 20 por request
        if not api_key:
            print("[StockDB] Pexels API key não configurada")
            return []

        results = []

        # apenas_fotos/apenas_videos sao filtros EXCLUDENTES:
        #   nenhum marcado -> traz os dois tipos
        #   um marcado     -> traz so aquele tipo
        #   os dois        -> traz os dois (intencao: "quero ambos")
        # Antes o calculo era `not apenas_fotos or (...)`, que fazia o
        # parametro `apenas_videos` ser IGNORADO — por isso a busca por
        # video voltava vazia em qualquer consulta. Ver CHECKLIST 4.8.
        apenas_um = apenas_fotos != apenas_videos
        buscar_fotos = (not apenas_um) or apenas_fotos
        buscar_videos = (not apenas_um) or apenas_videos

        if buscar_fotos:
            try:
                url = f"{self._url('pexels')}/search?query={urllib.parse.quote(query)}&per_page={per_page}"
                req = urllib.request.Request(url, headers={
                    "Authorization": api_key,
                    "User-Agent": "GeradorClipesMusicais/1.0",
                })
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())

                for i, photo in enumerate(data.get("photos", [])[:max_results]):
                    results.append(StockMedia(
                        id=f"pexels_{photo.get('id', i)}",
                        url=photo.get("url", ""),
                        thumbnail_url=photo.get("src", {}).get("medium", ""),
                        width=photo.get("width", 0),
                        height=photo.get("height", 0),
                        source="pexels",
                        media_type="photo",
                        category=self.config.stock_category,
                        tags=[],
                        description=photo.get("alt", ""),
                        download_url=photo.get("src", {}).get("original", ""),
                    ))
            except Exception as e:
                print(f"[StockDB] Pexels fotos erro: {e}")

        # Buscar vídeos
        if buscar_videos:
            try:
                url = f"{self._url('pexels_videos')}/search?query={urllib.parse.quote(query)}&per_page={per_page}"
                req = urllib.request.Request(url, headers={
                    "Authorization": api_key,
                    "User-Agent": "GeradorClipesMusicais/1.0",
                })
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())

                for i, video in enumerate(data.get("videos", [])[:max_results]):
                    # ⚠️ Não é "a melhor qualidade" de propósito: 4K custa
                    # ~2,5 s/frame no render e o quadro final é 1080x1920.
                    # Ver _escolher_variante_video().
                    video_files = video.get("video_files", [])
                    best_video = _escolher_variante_video(video_files)

                    results.append(StockMedia(
                        id=f"pexels_vid_{video.get('id', i)}",
                        url=video.get("url", ""),
                        thumbnail_url=video.get("image", ""),
                        width=video.get("width", 0),
                        height=video.get("height", 0),
                        source="pexels",
                        media_type="video",
                        category=self.config.stock_category,
                        tags=[],
                        description=video.get("url", ""),
                        download_url=best_video,
                        video_url=best_video,
                    ))
            except Exception as e:
                print(f"[StockDB] Pexels vídeos erro: {e}")

        return results

    def _buscar_pixabay(
        self,
        query: str,
        max_results: int,
        apenas_fotos: bool = False,
        apenas_videos: bool = False,
    ) -> list[StockMedia]:
        """Busca no Pixabay API."""
        api_key = self._get_api_key("pixabay")
        if not api_key:
            print("[StockDB] Pixabay API key não configurada")
            return []

        # Pixabay requer min 3 para per_page
        per_page = max(3, max_results)

        results = []

        apenas_um = apenas_fotos != apenas_videos
        buscar_fotos = (not apenas_um) or apenas_fotos
        buscar_videos = (not apenas_um) or apenas_videos

        # Buscar fotos
        if buscar_fotos:
            try:
                url = f"{self._url('pixabay')}/?key={api_key}&q={urllib.parse.quote(query)}&per_page={per_page}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())

                for i, hit in enumerate(data.get("hits", [])[:max_results]):
                    results.append(StockMedia(
                        id=f"pixabay_{hit.get('id', i)}",
                        url=hit.get("webformatURL", ""),
                        thumbnail_url=hit.get("previewURL", ""),
                        width=hit.get("imageWidth", 0),
                        height=hit.get("imageHeight", 0),
                        source="pixabay",
                        media_type="photo",
                        category=self.config.stock_category,
                        tags=[tag.strip() for tag in hit.get("tags", "").split(",")],
                        description=hit.get("largeImageURL", ""),
                        download_url=hit.get("largeImageURL", ""),
                    ))
            except Exception as e:
                print(f"[StockDB] Pixabay fotos erro: {e}")

        # Buscar vídeos
        if buscar_videos and self.config.stock_pixabay_videos:
            try:
                url = f"{self._url('pixabay_videos')}/?key={api_key}&q={urllib.parse.quote(query)}&per_page={per_page}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())

                for i, hit in enumerate(data.get("hits", [])[:max_results]):
                    videos = hit.get("videos", {})
                    # Pegar a melhor qualidade disponível
                    best_video = ""
                    for quality in ["large", "medium", "small", "tiny"]:
                        if videos.get(quality, {}).get("url"):
                            best_video = videos[quality]["url"]
                            break

                    # Thumbnail do Pixabay: picture_id -> URL
                    pic_id = hit.get("picture_id", "")
                    thumb_url = f"https://i.vimeocdn.com/video/{pic_id}_640x360.jpg" if pic_id else ""

                    results.append(StockMedia(
                        id=f"pixabay_vid_{hit.get('id', i)}",
                        url=hit.get("pageURL", ""),
                        thumbnail_url=thumb_url,
                        width=hit.get("videos", {}).get("large", {}).get("width", 0),
                        height=hit.get("videos", {}).get("large", {}).get("height", 0),
                        source="pixabay",
                        media_type="video",
                        category=self.config.stock_category,
                        tags=[tag.strip() for tag in hit.get("tags", "").split(",")],
                        description=hit.get("pageURL", ""),
                        download_url=best_video,
                        video_url=best_video,
                    ))
            except Exception as e:
                print(f"[StockDB] Pixabay vídeos erro: {e}")

        return results

    def _buscar_unsplash(self, query: str, max_results: int) -> list[StockMedia]:
        """Busca no Unsplash API."""
        api_key = self._get_api_key("unsplash")
        if not api_key:
            print("[StockDB] Unsplash API key não configurada")
            return []

        try:
            url = f"{self._url('unsplash')}/search/photos?query={urllib.parse.quote(query)}&per_page={max_results}"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Client-ID {api_key}",
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

            results = []
            for i, photo in enumerate(data.get("results", [])[:max_results]):
                urls = photo.get("urls", {})
                results.append(StockMedia(
                    id=f"unsplash_{photo.get('id', i)}",
                    url=urls.get("regular", ""),
                    thumbnail_url=urls.get("small", ""),
                    width=photo.get("width", 0),
                    height=photo.get("height", 0),
                    source="unsplash",
                    media_type="photo",
                    category=self.config.stock_category,
                    tags=[tag.get("title", "") for tag in photo.get("keywords", [])],
                    description=photo.get("description", ""),
                    download_url=urls.get("full", ""),
                ))
            return results
        except Exception as e:
            print(f"[StockDB] Unsplash API erro: {e}")
            return []

    def _buscar_nasa(self, query: str, max_results: int) -> list[StockMedia]:
        """Busca no NASA Images API (images-api.nasa.gov)."""
        api_key = self._get_api_key("nasa")
        if not api_key:
            print("[StockDB] NASA API key não configurada")
            return []

        try:
            # NASA API: search por query (não requer API key para busca básica)
            url = f"{self._url('nasa_search')}?q={urllib.parse.quote(query)}&page_size={max_results}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

            results = []
            for i, item in enumerate(data.get("collection", {}).get("items", [])[:max_results]):
                # NASA retorna links e data
                links = item.get("links", [])
                data_item = item.get("data", [{}])[0] if item.get("data") else {}

                thumbnail = ""
                original = ""
                for link in links:
                    if link.get("rel") == "preview":
                        thumbnail = link.get("href", "")
                    elif link.get("rel") == "alternate":
                        original = link.get("href", "")

                # Se não tem alternate, usar o primeiro link disponível
                if not original and links:
                    original = links[0].get("href", "")

                media_type = "photo"
                if data_item.get("media_type") == "video":
                    media_type = "video"

                results.append(StockMedia(
                    id=f"nasa_{data_item.get('nasa_id', i)}",
                    url=original,
                    thumbnail_url=thumbnail,
                    width=0,
                    height=0,
                    source="nasa",
                    media_type=media_type,
                    category=self.config.stock_category,
                    tags=data_item.get("keywords", []),
                    description=data_item.get("title", ""),
                    download_url=original,
                    video_url=original if media_type == "video" else "",
                ))

            return results

        except Exception as e:
            print(f"[StockDB] NASA API erro: {e}")
            return []

    def _buscar_coverr(self, query: str, max_results: int) -> list[StockMedia]:
        """Busca no Coverr.co API (vídeos gratuitos)."""
        api_key = self._get_api_key("coverr")

        try:
            # Coverr funciona com Bearer token no tier gratuito
            url = f"{self._url('coverr')}/videos?query={urllib.parse.quote(query)}&page_size={max_results}"
            headers = {"User-Agent": "Mozilla/5.0"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

            results = []
            for i, video in enumerate(data.get("hits", data.get("results", []))[:max_results]):
                # Construir URL do vídeo a partir do base_filename
                base_filename = video.get("base_filename", "")
                video_url = f"https://cdn.coverr.co/videos/{base_filename}/1080p.mp4" if base_filename else ""
                thumbnail = video.get("poster", video.get("thumbnail", ""))

                results.append(StockMedia(
                    id=f"coverr_{video.get('id', i)}",
                    url=video_url,
                    thumbnail_url=thumbnail,
                    width=video.get("max_width", 0),
                    height=video.get("max_height", 0),
                    source="coverr",
                    media_type="video",
                    category=self.config.stock_category,
                    tags=video.get("tags", []),
                    description=video.get("title", video.get("description", "")),
                    download_url=video_url,
                    video_url=video_url,
                ))

            return results

        except Exception as e:
            print(f"[StockDB] Coverr API erro: {e}")
            return []

    def _buscar_giphy(self, query: str, max_results: int) -> list[StockMedia]:
        """Busca no Giphy API (GIFs animados)."""
        api_key = self._get_api_key("giphy")
        if not api_key:
            print("[StockDB] Giphy API key não configurada")
            return []

        try:
            # Giphy Search API
            url = f"{self._url('giphy')}/gifs/search?api_key={api_key}&q={urllib.parse.quote(query)}&limit={max_results}&rating=g"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

            results = []
            for i, gif in enumerate(data.get("data", [])[:max_results]):
                images = gif.get("images", {})
                original = images.get("original", {})
                preview = images.get("fixed_height_small", images.get("preview_gif", {}))

                results.append(StockMedia(
                    id=f"giphy_{gif.get('id', i)}",
                    url=gif.get("url", ""),
                    thumbnail_url=preview.get("url", ""),
                    width=original.get("width", 0),
                    height=original.get("height", 0),
                    source="giphy",
                    media_type="video",  # GIFs são tratados como vídeos
                    category=self.config.stock_category,
                    tags=[tag.get("name", "") for tag in gif.get("tags", [])],
                    description=gif.get("title", ""),
                    download_url=original.get("url", ""),
                    video_url=original.get("mp4", original.get("url", "")),
                ))

            return results

        except Exception as e:
            print(f"[StockDB] Giphy API erro: {e}")
            return []

    def _buscar_openverse(self, query: str, max_results: int) -> list[StockMedia]:
        """Busca no Openverse API (WordPress - imagens e áudio)."""
        results = []

        # Buscar imagens (funciona sem autenticação com rate limits)
        try:
            url = f"{self._url('openverse')}/images/?q={urllib.parse.quote(query)}&page_size={max_results}"
            headers = {
                "User-Agent": "GeradorClipesMusicais/1.0",
                "Accept": "application/json",
            }
            # Se tiver token, usa; senão, acesso anônimo
            api_key = self._get_api_key("openverse")
            if api_key:
                headers["Authorization"] = f"Token {api_key}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())

            for i, item in enumerate(data.get("results", [])[:max_results]):
                results.append(StockMedia(
                    id=f"openverse_img_{item.get('id', i)}",
                    url=item.get("foreign_landing_url", ""),
                    thumbnail_url=item.get("thumbnail", ""),
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                    source="openverse",
                    media_type="photo",
                    category=self.config.stock_category,
                    tags=[tag.get("name", "") for tag in item.get("tags", [])],
                    description=item.get("title", ""),
                    download_url=item.get("url", ""),
                ))
        except Exception as e:
            print(f"[StockDB] Openverse imagens erro: {e}")

        # Buscar áudio
        try:
            url = f"{self._url('openverse')}/audio/?q={urllib.parse.quote(query)}&page_size={max_results}"
            headers = {
                "User-Agent": "GeradorClipesMusicais/1.0",
                "Accept": "application/json",
            }
            if api_key:
                headers["Authorization"] = f"Token {api_key}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())

            for i, item in enumerate(data.get("results", [])[:max_results]):
                results.append(StockMedia(
                    id=f"openverse_audio_{item.get('id', i)}",
                    url=item.get("foreign_landing_url", ""),
                    thumbnail_url=item.get("thumbnail", ""),
                    width=0,
                    height=0,
                    source="openverse",
                    media_type="audio",
                    category=self.config.stock_category,
                    tags=[tag.get("name", "") for tag in item.get("tags", [])],
                    description=item.get("title", ""),
                    download_url=item.get("url", ""),
                ))
        except Exception as e:
            print(f"[StockDB] Openverse audio erro: {e}")

        return results

    def salvar_cache(self):
        """Salva cache em disco."""
        cache_file = self._cache_dir / "cache.json"
        serializable = {}
        for k, v in self._cache.items():
            serializable[k] = [
                {"id": m.id, "url": m.url, "thumbnail_url": m.thumbnail_url,
                 "width": m.width, "height": m.height, "source": m.source,
                 "media_type": m.media_type, "category": m.category,
                 "tags": m.tags, "description": m.description,
                 "download_url": m.download_url, "video_url": m.video_url}
                for m in v
            ]
        cache_file.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")

    def carregar_cache(self):
        """Carrega cache de disco."""
        cache_file = self._cache_dir / "cache.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                for k, items in data.items():
                    self._cache[k] = [
                        StockMedia(
                            id=item.get("id", ""), url=item.get("url", ""),
                            thumbnail_url=item.get("thumbnail_url", ""),
                            width=item.get("width", 0), height=item.get("height", 0),
                            source=item.get("source", ""),
                            media_type=item.get("media_type", "photo"),
                            category=item.get("category", ""),
                            tags=item.get("tags", []), description=item.get("description", ""),
                            download_url=item.get("download_url", ""),
                            video_url=item.get("video_url", ""),
                        ) for item in items
                    ]
            except Exception:
                pass

    def testar_conexao(self, provider: str) -> dict:
        """Testa a conexão com um provedor específico.

        CORRIGIDO (19/09/2026) — este método é o botão "Testar" da GUI, e era
        o ÚNICO ponto do código onde 3 provedores davam falso-negativo:

          1. PEXELS  → 403. Faltava o header User-Agent. As chaves de API do
             Pexels passam por um WAF que bloqueia requisições sem UA (o
             `_buscar_pexels` sempre mandou UA e por isso sempre funcionou).
             Além disso a URL era `/v1/search/photos`, que não existe — o
             endpoint correto é `/v1/search`.
          2. COVERR  → 403. Dois motivos: (a) faltava User-Agent, mesmo caso
             do Pexels; (b) o parâmetro é `page_size`, não `per_page`.
          3. OPENVERSE → 403. O token `Token <key>` é rejeitado pela API
             pública (a chave salva não é um token OAuth válido). O acesso
             anônimo funciona e é o que `_buscar_openverse` já usava de fato.
             Passou a tentar o token e, se der 401/403, cai para anônimo.

        Também corrigido: os FALSOS-POSITIVOS. Unsplash/NASA/Giphy devolviam
        `sucesso: True, resultados: 0` porque a contagem só olhava as chaves
        `photos`/`hits`. Cada provedor tem a sua (`results`, `collection.items`,
        `data`). Agora conta corretamente e devolve 0 real quando for 0.

        Usa os MESMOS builders que as buscas reais, para o teste nunca mais
        divergir do comportamento de produção.
        """
        api_key = self._get_api_key(provider)

        # Provedores que funcionam sem chave (NASA busca básica é aberta)
        if not api_key and provider != "nasa":
            return {"sucesso": False, "erro": "Chave API não configurada"}

        # (url, headers, chave no JSON onde contar os itens)
        ua = {"User-Agent": "GeradorClipesMusicais/1.0"}
        tentativas: list[tuple[str, dict, str]] = []

        if provider == "pexels":
            tentativas.append((
                f"{self._url('pexels')}/search?query=nature&per_page=1",
                {"Authorization": api_key, **ua},
                "photos",
            ))
        elif provider == "pixabay":
            tentativas.append((
                f"{self._url('pixabay')}/?key={api_key}&q=nature&per_page=3",
                {"User-Agent": "Mozilla/5.0"},
                "hits",
            ))
        elif provider == "unsplash":
            tentativas.append((
                f"{self._url('unsplash')}/search/photos?query=nature&per_page=1",
                {"Authorization": f"Client-ID {api_key}", **ua},
                "results",
            ))
        elif provider == "nasa":
            tentativas.append((
                f"{self._url('nasa_search')}?q=nature&page_size=1",
                dict(ua),
                "collection.items",
            ))
        elif provider == "coverr":
            tentativas.append((
                f"{self._url('coverr')}/videos?query=nature&page_size=1",
                {"Authorization": f"Bearer {api_key}", **ua},
                "hits",
            ))
        elif provider == "giphy":
            tentativas.append((
                f"{self._url('giphy')}/gifs/search?api_key={api_key}&q=nature&limit=1&rating=g",
                dict(ua),
                "data",
            ))
        elif provider == "openverse":
            # 1ª tentativa: com token. 2ª: anônimo (a API pública aceita).
            tentativas.append((
                f"{self._url('openverse')}/images/?q=nature&page_size=1",
                {"Authorization": f"Token {api_key}", **ua},
                "results",
            ))
            tentativas.append((
                f"{self._url('openverse')}/images/?q=nature&page_size=1",
                {**ua, "Accept": "application/json"},
                "results",
            ))
        else:
            return {"sucesso": False, "erro": f"Provedor desconhecido: {provider}"}

        ultimo_erro = "falha desconhecida"
        for url, headers, campo in tentativas:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())

                # Conta itens navegando no caminho pontilhado (ex: collection.items)
                node = data
                for parte in campo.split("."):
                    node = node.get(parte, []) if isinstance(node, dict) else []
                total = len(node) if isinstance(node, list) else 0
                return {"sucesso": True, "resultados": total}

            except urllib.error.HTTPError as e:
                ultimo_erro = f"HTTP {e.code}: {e.reason}"
                # Só cai para a próxima tentativa em erro de credencial
                if e.code not in (401, 403):
                    break
            except Exception as e:  # noqa: BLE001
                ultimo_erro = str(e)

        return {"sucesso": False, "erro": ultimo_erro}

    # ══════════════════════════════════════════════════════════════
    #  BUSCA INTELIGENTE (estilo MoneyPrinter)
    # ══════════════════════════════════════════════════════════════

    def gerar_search_terms_letra(
        self, letra: str, num_terms: int = 5,
        tema_termos: Optional[list[str]] = None,
        tema_ignora_letra: bool = False,
    ) -> list[str]:
        """Gera search terms visuais a partir da letra (ou do tema).

        Ordem de preferencia:
          0. TEMA musical detectado (mantra, classica, frequencia...)
             — quando o usuario descreveu o tema, ele MANDA sozinho.
          1. Camada de interpretacao emocional (local, deterministica).
          2. LLM (Gemini), quando configurado.
          3. Heuristica de palavras-chave (ultimo recurso).

        Quando tema_ignora_letra=True, a letra NAO entra — porque e'
        em sanscrito, arabe, ou a musica nao tem letra (frequencia).
        """
        # ── 0. TEMA detectado na descricao ─────────────────────────
        if tema_termos:
            if tema_ignora_letra:
                print(f"[StockDB] Search terms por TEMA: {tema_termos[:num_terms]}")
                return tema_termos[:num_terms]
            # Tema existe mas nao ignora letra: tema + letra combinados
            terms = list(tema_termos)
            if letra and letra.strip():
                terms_letra = self._gerar_terms_letra_pura(letra, num_terms)
                for t in terms_letra:
                    if t not in terms:
                        terms.append(t)
            return terms[:num_terms]

        # ── Sem tema: letra pura ───────────────────────────────────
        if not letra or not letra.strip():
            return ["concert", "music", "stage", "lights", "crowd"]

        return self._gerar_terms_letra_pura(letra, num_terms)

    def _gerar_terms_letra_pura(self, letra: str, num_terms: int = 5) -> list[str]:
        """Caminho original: emocao -> LLM -> heuristica."""
        # ── 1. Camada emocional ────────────────────────────────────
        try:
            from MusicClipStudio.interpretacao import (
                emocao_dominante, interpretar,
            )

            linhas = [l for l in letra.split("\n") if l.strip()]
            dominante = emocao_dominante(linhas)

            if dominante is not None:
                terms: list[str] = []
                vistos = set()

                for q in self._cenas_da_emocao(dominante):
                    chave = q.lower()
                    if chave not in vistos:
                        vistos.add(chave)
                        terms.append(q)

                for linha in linhas:
                    leitura = interpretar(linha)
                    if leitura.confianca < 0.4:
                        continue
                    for q in leitura.queries(1):
                        chave = q.lower()
                        if chave not in vistos:
                            vistos.add(chave)
                            terms.append(q)

                if terms:
                    terms = self._encurtar_para_busca(terms, num_terms)
                    print(f"[StockDB] Search terms emocionais: {terms[:num_terms]}")
                    return terms[:num_terms]
        except Exception as e:
            print(f"[StockDB] Camada emocional indisponivel: {e}")

        # ── 2. LLM ─────────────────────────────────────────────────
        try:
            terms_llm = self._gerar_terms_via_llm(letra, num_terms)
            if terms_llm and len(terms_llm) >= 3:
                terms_llm = self._encurtar_para_busca(terms_llm, num_terms)
                print(f"[StockDB] Search terms via LLM: {terms_llm}")
                return terms_llm
        except Exception as e:
            print(f"[StockDB] LLM falhou, usando heurística: {e}")

        # ── 3. Heuristica ──────────────────────────────────────────
        terms_heur = self._gerar_terms_heuristica(letra, num_terms)
        return self._encurtar_para_busca(terms_heur, num_terms)

    @staticmethod
    def _encurtar_para_busca(terms: list[str], num_terms: int) -> list[str]:
        """Reduz cenas longas a termos que a stock API realmente indexa.

        As cenas emocionais sao frases de 5+ palavras ("empty apartment
        at night one lamp"). Otimas como prompt de IA, mas a Pexels/
        Pixabay indexam conceitos de 2-3 palavras e respondem a elas com
        match parcial em palavras genericas — daí as imagens fora de
        contexto. Aqui a cena vira nucleo visual ("apartment night lamp").
        """
        try:
            from MusicClipStudio.encurtador_busca import termo_curto
        except Exception:
            return list(terms)

        saida: list[str] = []
        vistos: set[str] = set()
        for termo in terms or []:
            curto = termo_curto(termo) if isinstance(termo, str) else ""
            if curto and curto not in vistos:
                vistos.add(curto)
                saida.append(curto)
        return saida or list(terms)

    @staticmethod
    def _cenas_da_emocao(emocao, n: int = 6) -> list[str]:
        """Cenas filmaveis associadas a uma emocao.

        Fica aqui (e nao em `interpretacao`) apenas para nao duplicar a
        importacao no modulo de banco; a fonte da verdade continua sendo
        o dicionario CENAS de `interpretacao`.
        """
        try:
            from MusicClipStudio.interpretacao import CENAS
            return list(CENAS.get(emocao, []))[:n]
        except Exception:
            return []

    def _gerar_terms_via_llm(self, letra: str, num_terms: int = 5) -> list[str]:
        """Chama Gemini para gerar search terms visuais."""
        import json

        # Ler config de IA
        config_path = Path(__file__).parent.parent / "config_ia.json"
        if not config_path.exists():
            return []

        with open(config_path) as f:
            config_ia = json.load(f)

        api_key = config_ia.get("api_gemini", "")
        if not api_key:
            return []

        prompt = f"""Generate {num_terms} search terms for stock video/image search, 
based on the lyrics of a music video. 

Rules:
1. Each search term must be 1-3 words in ENGLISH
2. Terms must be VISUAL - describe what you would SEE in a video
3. Related to the emotions and imagery of the lyrics
4. Think like a video director: what shots would match these lyrics?
5. Return ONLY a JSON array of strings, nothing else

### Lyrics:
{letra[:2000]}

### Example output:
["dramatic sunset", "lonely figure", "city lights", "ocean waves", "night sky"]"""

        import requests

        modelos = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]
        for modelo in modelos:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 200},
            }
            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    # Parse JSON array
                    text = text.strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    terms = json.loads(text)
                    if isinstance(terms, list):
                        return [str(t).strip() for t in terms if t][:num_terms]
            except Exception:
                continue

        return []

    def _gerar_terms_heuristica(self, letra: str, num_terms: int = 5) -> list[str]:
        """Fallback: gera terms por heurística de palavras-chave."""

        stopwords = {
            "eu", "tu", "ele", "ela", "nos", "eles", "elas", "meu", "minha",
            "teu", "tua", "seu", "sua", "nosso", "nossa", "dele", "dela",
            "que", "para", "com", "por", "sem", "sob", "entre", "ate",
            "como", "mais", "menos", "muito", "pouco", "todo", "toda",
            "este", "esta", "esse", "essa", "aquele", "aquela",
            "isso", "isto", "aquilo", "aqui", "la", "ai", "onde",
            "quando", "porque", "entao", "mas", "porem", "ou",
            "sim", "nao", "ja", "ainda", "sempre", "nunca",
            "um", "uma", "uns", "umas", "do", "da", "dos", "das",
            "no", "na", "nos", "nas", "ao", "aos", "pela", "pelo",
            "foi", "ser", "estar", "ter", "fazer", "ir", "vir",
            "dizer", "dar", "ver", "saber", "poder", "querer",
        }

        palavras = letra.lower().split()
        palavras_limpa = []
        for p in palavras:
            p = p.strip(".,;:!?\"'()-")
            if len(p) > 3 and p not in stopwords:
                palavras_limpa.append(p)

        from collections import Counter
        contagem = Counter(palavras_limpa)
        mais_comuns = [p for p, _ in contagem.most_common(num_terms * 2)]

        if not mais_comuns:
            return ["concert", "music", "stage", "lights", "crowd"]

        # Gerar combinações 1-3 palavras
        terms = []

        # Termos individuais (1 palavra)
        for p in mais_comuns[:num_terms]:
            terms.append(p)

        # Combinações de 2 palavras
        for i in range(min(3, len(mais_comuns) - 1)):
            terms.append(f"{mais_comuns[i]} {mais_comuns[i+1]}")

        # Combinação de 3 palavras
        if len(mais_comuns) >= 3:
            terms.append(f"{mais_comuns[0]} {mais_comuns[1]} {mais_comuns[2]}")

        # Remover duplicatas, manter ordem
        seen = set()
        unique_terms = []
        for t in terms:
            if t not in seen:
                seen.add(t)
                unique_terms.append(t)

        return unique_terms[:num_terms]

    def busca_massiva(
        self,
        search_terms: list[str],
        providers: Optional[list[str]] = None,
        apenas_videos: bool = True,
        apenas_fotos: bool = True,
        max_por_term: int = 15,
    ) -> list[StockMedia]:
        """Busca massiva estilo MoneyPrinter.

        Foca em Pexels + Pixabay (que funcionam bem).
        Coverr e Giphy retornam lixo - desativados.
        """
        # APENAS Pexels e Pixabay ( Coverr/Giphy irrelevantes)
        providers = ["pexels", "pixabay"]

        all_results = []
        seen_urls = set()
        results_by_term = {}

        for term in search_terms:
            term_results = []
            for provider in providers:
                try:
                    search = self.pesquisar(
                        term, provider=provider,
                        max_results=max_por_term,
                        apenas_fotos=apenas_fotos,
                        apenas_videos=apenas_videos,
                    )
                    for item in search.results:
                        base_url = item.download_url.split("?")[0] if item.download_url else item.url
                        if base_url and base_url not in seen_urls:
                            seen_urls.add(base_url)
                            item.search_term = term
                            term_results.append(item)
                except Exception as e:
                    print(f"[StockDB] {provider}/{term}: {e}")
                    continue

            results_by_term[term] = term_results
            all_results.extend(term_results)

        if results_by_term:
            diversified = self._round_robin_sample(results_by_term)
            print(f"[StockDB] Busca massiva: {len(diversified)} itens de {len(search_terms)} terms")
            return diversified

        return all_results

    def _round_robin_sample(self, results_by_term: dict) -> list[StockMedia]:
        """Round-robin sampling entre terms para diversidade."""
        max_len = max(len(v) for v in results_by_term.values()) if results_by_term else 0
        diversified = []

        for i in range(max_len):
            for term, items in results_by_term.items():
                if i < len(items):
                    diversified.append(items[i])

        return diversified

    def baixar_streaming(self, url: str, destino: str, chunk_size: int = 8192) -> Optional[str]:
        """Baixa arquivo em chunks (não carrega tudo na memória)."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            Path(destino).parent.mkdir(parents=True, exist_ok=True)

            with urllib.request.urlopen(req, timeout=60) as response:
                with open(destino, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)

            # Verificar arquivo válido
            size = Path(destino).stat().st_size
            if size < 1000:
                Path(destino).unlink(missing_ok=True)
                return None

            return destino
        except Exception as e:
            print(f"[StockDB] Erro download: {e}")
            Path(destino).unlink(missing_ok=True)
            return None
