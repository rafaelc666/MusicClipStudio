"""
Agente de direção de imagens para clipes musicais.

Usa IA para decidir:
  - Que tipo de imagem/vídeo usar para cada beat
  - Estilo visual baseado no humor/mood da música
  - Composição e efeitos a aplicar
  - Seleção automática de mídias do banco de dados

Pode funcionar com ou sem LLM externo (regras baseadas em template).
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from MusicClipStudio.config import get_config
from MusicClipStudio.schema import MusicBeat, MusicVisualElement, ClipComponentType
from MusicClipStudio.interpretacao import (
    LeituraEmocional,
    Emocao,
    interpretar,
    emocao_dominante,
)


class AgentMood(str, Enum):
    """Humor/mood do clipe."""
    EPIC = "epic"
    CALM = "calm"
    ROMANTIC = "romantic"
    ENERGETIC = "energetic"
    DARK = "dark"
    JOYFUL = "joyful"
    CINEMATIC = "cinematic"
    MINIMAL = "minimal"


class AgentStyle(str, Enum):
    """Estilo visual do clipe."""
    CINEMATIC = "cinematic"
    MUSIC_VIDEO = "music_video"
    LYRIC_VIDEO = "lyric_video"
    ABSTRACT = "abstract"
    NARRATIVE = "narrative"
    PERFORMANCE = "performance"


@dataclass
class AgentDecision:
    """Decisão do agente para um beat."""
    beat_id: int = 0
    component_type: str = ""
    effect: str = "zoom_in"
    accent_color: str = "#FFCC00"
    bg_color: str = "#1A1A2E"
    photo_query: str = ""
    image_category: str = ""
    animation: str = "fade_in"
    style_note: str = ""
    confidence: float = 0.0


@dataclass
class AgentPlan:
    """Plano completo do agente para o clipe."""
    project_id: str = ""
    mood: AgentMood = AgentMood.EPIC
    style: AgentStyle = AgentStyle.MUSIC_VIDEO
    beats: list[AgentDecision] = field(default_factory=list)
    global_effects: list[str] = field(default_factory=list)
    color_palette: dict[str, str] = field(default_factory=dict)


class ClipAgent:
    """Agente de direção de imagens para clipes musicais."""

    # Mapeamento mood → cores principais
    MOOD_COLORS = {
        AgentMood.EPIC: {"primary": "#FFCC00", "secondary": "#1A1A2E", "accent": "#FF6B35"},
        AgentMood.CALM: {"primary": "#4A90D9", "secondary": "#0D1B2A", "accent": "#7EC8E3"},
        AgentMood.ROMANTIC: {"primary": "#E84393", "secondary": "#2D1B4E", "accent": "#FD79A8"},
        AgentMood.ENERGETIC: {"primary": "#FF006E", "secondary": "#1A0033", "accent": "#FFBE0B"},
        AgentMood.DARK: {"primary": "#666666", "secondary": "#0A0A0A", "accent": "#FF0000"},
        AgentMood.JOYFUL: {"primary": "#06D6A0", "secondary": "#1A3A2E", "accent": "#FFD166"},
        AgentMood.CINEMATIC: {"primary": "#FFCC00", "secondary": "#141414", "accent": "#FF8C00"},
        AgentMood.MINIMAL: {"primary": "#FFFFFF", "secondary": "#1A1A1A", "accent": "#CCCCCC"},
    }

    # Mapeamento mood → queries de imagem padrão
    MOOD_QUERIES = {
        AgentMood.EPIC: ["epic landscape", "mountain sunset", "cinematic sky", "orchestra stage"],
        AgentMood.CALM: ["ocean waves", "forest morning", "peaceful lake", "soft clouds"],
        AgentMood.ROMANTIC: ["rose flowers", "sunset couple", "candle light", "romantic city"],
        AgentMood.ENERGETIC: ["concert crowd", "neon lights", "dance floor", "sports action"],
        AgentMood.DARK: ["dark city", "rainy street", "shadow figure", "night skyline"],
        AgentMood.JOYFUL: ["colorful party", "beach day", "flowers garden", "sunny park"],
        AgentMood.CINEMATIC: ["film grain", "movie scene", "dramatic lighting", "director frame"],
        AgentMood.MINIMAL: ["clean desk", "single object", "white background", "product shot"],
    }

    def __init__(self, config=None):
        self.config = config or get_config()
        self.model = self.config.agent_model
        self.enabled = self.config.agent_enabled
        self.mood = AgentMood(self.config.agent_mood) if self.config.agent_mood else AgentMood.EPIC
        self.style = AgentStyle(self.config.agent_style) if self.config.agent_style else AgentStyle.MUSIC_VIDEO

        # Cores do mood
        self.colors = self.MOOD_COLORS.get(self.mood, self.MOOD_COLORS[AgentMood.EPIC])

        # ⚠️ NOVO (23/09/2026): tema musical detectado da letra (temas_musicais).
        # Quando existe, o repertório DELE alimenta as queries de fallback —
        # antes beats sem emoção forte caíam nas 4 queries fixas do mood
        # (ex.: DARK → "dark city" x112) mesmo a letra sendo gospel,
        # sertaneja, etc. Agora "Coração Igual ao Teu" cai no tema gospel e
        # o fallback vira "cross silhouette sunset", "hands raised worship"…
        self._tema = None

    # ── NOVO (01/10/2026): a letra precisa chegar NA BUSCA. ─────────────
    # Até aqui, linha sem emoção mapeada caía no repertório do mood
    # ("Minhas raízes descem fundo" → busca "ocean waves") — a queixa
    # crônica de que a busca não tem a ver com a música. Duas camadas novas,
    # nessa ordem de prioridade:
    #   1. leitura emocional confiável  (metáfora → cena filmável) — existente
    #   2. LLM local (ollama) rescrevendo a linha como busca de stock
    #   3. palavras concretas da linha (dicionário PT→EN abaixo)
    #   4. repertório do tema/mood — último recurso, como era
    CONCRETOS: dict = {
        # terra e natureza
        "terra": "earth soil", "raiz": "tree roots", "raizes": "tree roots",
        "semente": "seed sprout", "germina": "sprouting seed close up",
        "fruto": "ripe fruit branch", "galho": "tree branch",
        "folha": "leaf falling", "arvore": "tree", "floresta": "forest",
        "flor": "flower", "jardim": "garden", "campo": "open field",
        "montanha": "mountain", "pedra": "rock stone", "rocha": "cliff rock",
        "solo": "soil ground", "chao": "ground earth close up",
        "poeira": "dust light beam", "estrada": "road path",
        "caminho": "path trail", "rio": "river", "agua": "water",
        "chuva": "rain window", "tempestade": "storm sky",
        "vento": "wind blowing", "mar": "ocean waves", "onda": "wave",
        "areia": "sand beach", "ceu": "sky clouds", "sol": "sunlight",
        "lua": "moon night", "estrela": "stars night sky",
        "estrelas": "stars night sky", "noite": "night city",
        "manha": "morning light", "alvorada": "dawn sky", "fogo": "fire flame",
        "chama": "flame close up", "cinzas": "ashes embers",
        "luz": "light beam", "sombra": "shadow", "trilha": "forest trail",
        # gente e corpo
        "mao": "hand close up", "maos": "hands together",
        "dedos": "fingers close up", "olho": "eye close up",
        "olhos": "eyes close up", "rosto": "face portrait",
        "corpo": "body silhouette", "pe": "barefoot ground",
        "passo": "walking feet", "caminhada": "walking road",
        "coracao": "heart", "alma": "soul light", "sangue": "red drip",
        "beijo": "kiss couple", "abraco": "hugging embrace",
        "crianca": "child playing", "menino": "boy", "menina": "girl",
        "avo": "elderly hands", "velho": "old man",
        "nao": "", "filho": "son father", "filha": "daughter",
        "pais": "parents family", "mae": "mother", "pai": "father",
        "gente": "crowd people", "povo": "people crowd",
        "nacao": "flag country", "pais_patrio": "homeland landscape",
        # lugares e coisas
        "casa": "house home", "porta": "door open", "janela": "window",
        "telhado": "rooftop", "rua": "street", "cidade": "city skyline",
        "interior": "countryside", "igreja": "church",
        "cruz": "cross silhouette", "ceu_aberto": "open sky",
        "carro": "car driving", "trem": "train tracks",
        "avi": "airplane sky", "barco": "boat sea",
        "vinho": "wine glass", "pao": "bread table",
        "mesa": "wooden table", "cadeira": "empty chair",
        "relagio": "old clock", "relogio": "old clock",
        "espelho": "mirror reflection", "fotografia": "old photo",
        "foto": "old photo", "carta": "letter paper",
        "livro": "open book", "cancao": "singing microphone",
        "musica": "music vinyl", "guitarra": "guitar",
        "violao": "acoustic guitar", "piano": "piano keys",
        "tambo": "drum", "cadeia": "chains", "corrente": "chain link",
        "faca": "knife", "arma": "weapon dark", "gun": "weapon dark",
        "corrente_grande": "chain", "memo": "",
    }
    # plurais e variantes que o normalizador deixa passar como palavra:
    CONCRETOS.update({"raizes": "tree roots", "sementes": "seeds sowing",
                      "frutos": "fruit harvest", "galhos": "branches",
                      "pedras": "rocks stones", "montanhas": "mountains",
                      "vales": "valley", "vale": "valley", "rios": "river",
                      "casas": "village houses", "ruas": "street alley",
                      "janelas": "window rain", "portas": "doors",
                      "estrelas ": "stars", "flores": "flowers",
                      "cinzas ": "ashes", "sombras": "shadows",
                      "luces": "", "espelhos": "mirror",
                      "mãos": "hands", "maos2": ""})

    def _concretos_da_linha(self, linha: str) -> str:
        """Extrai da linha os substantivos/verbos visuais conhecidos e os
        traduz para a lingua dos bancos de stock (inglês).
        'Minhas raízes descem fundo' -> 'tree roots soil ground'."""
        try:
            from MusicClipStudio.interpretacao import normalizar
            palavras = normalizar(linha or "").split()
        except Exception:
            palavras = (linha or "").lower().replace("\n", " ").split()
        achados: list[str] = []
        for w in palavras:
            termo = self.CONCRETOS.get(w, "")
            if termo and termo not in achados:
                achados.append(termo)
        return " ".join(achados[:3])

    def _queries_via_gemini(self, linhas: list[str], chave: str) -> dict[int, str]:
        """(01/10/2026) Buscas do agente via nuvem — ROTEIA POR PREFIXO:
        AIza/AQ. -> Gemini; gsk_ -> Groq; sk-or- -> OpenRouter; sk- -> OpenAI-
        compat. Reutiliza ia_busca._chamar_llm; se ele nao estiver no path ou
        o prefixo for desconhecido, cai no caminho direto do Gemini. Contrato:
        devolve {indice: query} e {} em QUALQUER falha — upgrade, nunca
        dependencia (o fluxo segue com ollama/regras locais)."""
        import os, json, re as _re
        try:
            lista_txt = "\n".join(f"{i+1}. {l}" for i, l in enumerate(linhas))
            instr = (
                "Para cada LINHA de letra de musica, escreva UMA busca de "
                "3 a 6 palavras, em INGLES, para achar a imagem (foto ou "
                "video de stock) que representa a cena da linha — literal "
                "ou metafórica, cinematográfica. Ex.: 'Minhas raizes "
                "descem fundo' -> 'tree roots deep soil'. "
                "Responda SOMENTE um JSON list de strings, na ordem, sem "
                "numeracao nem comentarios.\nLINHAS:\n" + lista_txt)

            bruto = ""
            # 1a) roteador genérico por prefixo
            try:
                import ia_busca as _iab
                bruto = _iab._chamar_llm(chave, modelo="", prompt=instr, timeout=45) or ""
            except Exception:
                bruto = ""

            # 1b) fallback direto Gemini (se ia_busca ausente ou prefixo desconhecido)
            if not bruto:
                import urllib.request
                modelo = os.environ.get("MCS_GEMINI_MODELO", "gemini-3.8-flash")
                url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                       f"{modelo}:generateContent?key={chave}")
                body = json.dumps({"contents": [{"parts": [{"text": instr}]}],
                                   "generationConfig": {"temperature": 0.1}}).encode()
                req = urllib.request.Request(url, data=body,
                    headers={"Content-Type": "application/json"})
                resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
                partes = (resp.get("candidates", [{}])[0]
                              .get("content", {}).get("parts", []))
                bruto = "".join(p.get("text", "") for p in partes)

            mm = _re.search(r"\[.*\]", bruto, _re.S)
            if not mm:
                return {}
            itens = json.loads(mm.group(0))
            saida: dict[int, str] = {}
            for i, q in enumerate(itens[:len(linhas)]):
                q = str(q).strip().strip('\"').strip("'")
                if q and len(q.split()) <= 8:
                    saida[i] = q
            return saida
        except Exception:
            return {}

    def _queries_via_llm(self, linhas: list[str]) -> dict[int, str]:
        """(01/10/2026) Reescreve cada linha como busca de stock via LLM
        local (ollama). Uma chamada única com a lista toda; se o ollama não
        estiver no ar ou responder errado, devolve {} e o fluxo segue com as
        regras — o LLM é upgrade, nunca dependência. Desative com MCS_LLM=0."""
        import os, json, re as _re
        if os.environ.get("MCS_LLM", "1") == "0":
            return {}
        # ⚠️ NOVO (01/10/2026): GEMINI_API_KEY no .env → camada nuvem primeiro
        # (chave do usuário medida funcionando; free tier sem cartão). Sem
        # Gemini ou em falha, cai no ollama local — e sem os dois, nas regras.
        # ordem: (1) Gemini específica do usuário logado → (2) chave genérica
        # do cofre dele → (3) GEMINI_API_KEY global → (4) STOCK_IA_API_KEY
        # global. Todas passam pelo MESMO roteador por prefixo.
        chaves_nuvem = [
            (getattr(self, "_gemini_key", "") or "").strip(),
            (getattr(self, "_ia_gen_key", "") or "").strip(),
            (os.environ.get("GEMINI_API_KEY") or "").strip(),
            (os.environ.get("STOCK_IA_API_KEY") or "").strip(),
        ]
        for ch in chaves_nuvem:
            if not ch:
                continue
            saida_g = self._queries_via_gemini(linhas, ch)
            if saida_g:
                return saida_g
        try:
            import urllib.request
            modelo = os.environ.get("MCS_LLM_MODELO", "qwen2.5-coder:7b")
            listing = urllib.request.urlopen(
                "http://127.0.0.1:11434/api/tags", timeout=2).read()
            nomes = [m.get("name", "") for m in
                     json.loads(listing).get("models", [])]
            if not any(modelo.split(":")[0] in n for n in nomes):
                return {}
            lista_txt = "\n".join(f"{i+1}. {l}" for i, l in enumerate(linhas))
            instr = (
                "Para cada LINHA de letra de música, escreva UMA busca de "
                "3 a 6 palavras, em INGLÊS, para achar a imagem (foto ou "
                "vídeo de stock) que representa a cena da linha — literal "
                "ou metafórica, cinematográfica. Ex.: \"Minhas raízes "
                "descem fundo\" -> \"tree roots deep soil\". "
                "Responda SOMENTE um JSON list de strings, na ordem, sem "
                "numeração nem comentários.\nLINHAS:\n" + lista_txt)
            body = json.dumps({"model": modelo, "prompt": instr,
                               "temperature": 0.1, "stream": False,
                               "options": {"num_ctx": 4096}}).encode()
            req = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                data=body, headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
            bruto = resp.get("response", "")
            m = _re.search(r"\[.*\]", bruto, _re.S)
            if not m:
                return {}
            itens = json.loads(m.group(0))
            saida: dict[int, str] = {}
            for i, q in enumerate(itens[:len(linhas)]):
                q = str(q).strip().strip("\"'")
                if q and len(q.split()) <= 8:
                    saida[i] = q
            return saida
        except Exception:
            return {}

    def analisar(
        self,
        lyrics: str = "",
        description: str = "",
        music_prompt: str = "",
    ) -> AgentPlan:
        """
        Analisa conteúdo e gera plano visual para o clipe.

        Detecta mood, estilo, cores e decisões visuais para cada beat.
        """
        # Detectar mood a partir do conteúdo
        detected_mood = self._detectar_mood(lyrics, description, music_prompt)
        self.mood = detected_mood
        self.colors = self.MOOD_COLORS.get(detected_mood, self.MOOD_COLORS[AgentMood.EPIC])

        # ⚠️ NOVO (23/09/2026): detectar o TEMA musical da letra — ele dá o
        # repertório visual coerente com o gênero (gospel, rock, clássica…).
        try:
            from MusicClipStudio.temas_musicais import detectar_tema
            self._tema = detectar_tema(f"{lyrics} {description} {music_prompt}")
        except Exception:
            self._tema = None

        # ⚠️ NOVO (23/09/2026): tema LIVRE digitado pelo usuário (payload
        # `theme` da API) — catalogar todos os gêneros é impossível, então
        # quem define o tema é o usuário. Ele vira QUALIFICADOR das queries:
        #   tema "chuva lenta" + cena "rain window"
        #   → "rain window (slow motion video)"
        self._tema_livre = getattr(self, "_tema_livre", "") or ""

        plan = AgentPlan(
            project_id=f"plan_{int(__import__('time').time())}",
            mood=detected_mood,
            style=self.style,
            color_palette=self.colors,
        )

        # Gerar decisões para cada beat baseado no conteúdo
        from MusicClipStudio.schema import letras_para_beats, descricao_para_beats, MusicBeat
        beats = []
        if lyrics.strip():
            beats = letras_para_beats(lyrics, duration_estimada=5.0)
        elif description.strip():
            beats = descricao_para_beats(description, duration_estimada=5.0)

        # ⚠️ NOVO (01/10/2026): uma passada de LLM local sobre todas as
        # linhas, antes do loop — transforma letra em busca de stock com
        # cabeça. Sem ollama no ar, o dict vazio e as regras assumem.
        self._llm_queries = self._queries_via_llm(
            [getattr(b, "lyrics_line", "") or "" for b in beats]
        ) if beats else {}

        # ⚠️ CORRIGIDO (21/09/2026): o índice do beat entra na decisão.
        # Sem ele, todo beat que caía no repertório do mood recebia a MESMA
        # query (queries[0]) — a busca devolvia 4 prompts idênticos e o
        # usuário via "as mesmas opções" mesmo trocando a letra.
        for i, beat in enumerate(beats):
            decision = self._decidir_beat(beat, plan, indice=i)
            plan.beats.append(decision)

        # Efeitos globais baseados no mood
        plan.global_effects = self._efeitos_globais(detected_mood)

        return plan

    def direcionar_imagem(
        self,
        beat: MusicBeat,
        mood: Optional[AgentMood] = None,
        indice: int = 0,
    ) -> AgentDecision:
        """
        Decide que tipo de imagem/vídeo usar para um beat.

        Args:
            beat: o beat musical.
            mood: mood global do clipe (default: o detectado no init).
            indice: posição do beat no clipe. Usado para VARIAR a query
                quando dois beats caem na mesma cena/mood — antes todos
                recebiam `queries[0]` e a busca repetia.

        Returns:
            AgentDecision com tipo de componente, query de imagem, cores, etc.
        """
        mood = mood or self.mood

        beat_type = getattr(beat, 'type', 'verse')
        is_chorus = "chorus" in beat_type.lower() or "refrão" in getattr(beat, 'script', '').lower()
        is_hook = "hook" in beat_type.lower()

        # Determinar componente visual baseado no tipo de beat
        if is_hook:
            component = ClipComponentType.HIGHLIGHT_SWIPE
            effect = "highlight_sweep"
        elif is_chorus:
            component = ClipComponentType.KINETIC_TITLE
            effect = "zoom_in_out"
        else:
            component = ClipComponentType.KINETIC_TITLE
            effect = "zoom_in"

        # Se o beat tem imagens específicas, usar parallax_image
        if getattr(beat.visual, 'images', []):
            component = ClipComponentType.PARALLAX_IMAGE

        # ── Query de imagem ─────────────────────────────────────────
        # A letra NÃO vai crua para a busca. Ela passa pela camada de
        # interpretação, que traduz metáfora em emoção e emoção em cena
        # filmável. Sem isso, "estou de coração partido" viraria uma
        # busca por corações despedaçados — o oposto do que o clipe quer.
        leitura = self._leitura_da_letra(beat)
        cenas = leitura.queries(3) if leitura is not None else []
        confianca = float(getattr(leitura, "confianca", 0.0) or 0.0)

        # ⚠️ CORRIGIDO (21/09/2026): a cena escolhida agora gira com o
        # índice do beat. Antes era sempre `cenas[0]`, então dois beats
        # com a mesma emoção viravam duas buscas idênticas.
        if cenas and confianca >= 0.4:
            # A letra trouxe emoção clara: a cena dela manda.
            # (0.4 é o limiar de segurança da camada de interpretação:
            # abaixo disso a linha é neutra/ambígua e a cena seria chute.)
            photo_query = cenas[indice % len(cenas)]
            origem = "letra"
        else:
            # ⚠️ NOVO (01/10/2026): antes do repertório cego do mood, a
            # própria linha vira a busca — primeiro pela reescrita do LLM
            # local, depois pelos concretos traduzidos da letra. Assim
            # "Minhas raízes descem fundo" busca raízes, não "ocean waves".
            llm = getattr(self, "_llm_queries", {}) or {}
            concreto = self._concretos_da_linha(getattr(beat, "lyrics_line", "") or "")
            if indice in llm:
                photo_query = llm[indice]
                origem = "letra_llm"
            elif concreto:
                photo_query = f"{concreto} cinematic"
                origem = "letra_concreta"
            else:
                # Linha sem carga e sem palavra visual: repertório do
                # tema/mood global, girando pelo índice.
                photo_query = self._query_do_mood(mood, indice)
                origem = "mood"

        # ⚠️ NOVO (23/09/2026): tema livre do usuário qualifica a query
        # final (sufixo curto, estilo busca de stock). Tema musical também
        # qualifica quando a cena veio da emoção da linha, para puxar a
        # estética do gênero (gospel → luz/céu) sem apagar a cena.
        livre = (getattr(self, "_tema_livre", "") or "").strip()
        if livre:
            photo_query = f"{photo_query} ({livre})"
        elif origem == "letra":
            tema = getattr(self, "_tema", None)
            estetica = getattr(tema, "estetica", "") if tema else ""
            if estetica:
                photo_query = f"{photo_query} ({estetica})"

        return AgentDecision(
            beat_id=getattr(beat, 'id', 0),
            component_type=component.value,
            effect=effect,
            accent_color=self.colors["primary"],
            bg_color=self.colors["secondary"],
            photo_query=photo_query,
            image_category=self.config.stock_category,
            animation=getattr(beat.visual, 'animation', 'fade_in'),
            style_note=(
                f"Style: {self.style.value}, Mood: {mood.value}"
                + (f", Tema: {getattr(self, '_tema', None).id}" if getattr(self, "_tema", None) else "")
                + (f", Emoção: {leitura.emocao.value}" if leitura else "")
                + f", Query de: {origem}"
            ),
            # Antes era 0.85 fixo — um número inventado que dizia que o
            # agente tinha certeza até quando estava chutando o mood.
            # Agora reflete a confiança real da leitura da letra.
            confidence=(confianca if origem != "mood" else 0.35),
        )

    def _leitura_da_letra(self, beat: MusicBeat) -> Optional[LeituraEmocional]:
        """Interpreta a linha de letra do beat, se houver uma."""
        linha = getattr(beat, "lyrics_line", "") or ""
        if not linha.strip():
            return None
        return interpretar(linha)

    def _query_do_mood(self, mood: AgentMood, indice: int = 0) -> str:
        """Query de reserva, quando a linha não tem emoção forte.

        ⚠️ NOVO (23/09/2026): o TEMA detectado da letra manda antes do
        repertório fixo do mood. Antes, uma letra gospel caía no mood DARK
        e recebia "dark city"/"rainy street" — sem nenhuma relação com a
        música. Agora recebe os termos do tema (gospel → cruz, luz, céu,
        mãos em adoração…), girando pelo índice para variar as cenas.
        """
        tema = getattr(self, "_tema", None)
        if tema is not None and getattr(tema, "termos_busca", None):
            termos = tema.termos_busca
            return termos[indice % len(termos)]
        queries = self.MOOD_QUERIES.get(mood, self.MOOD_QUERIES[AgentMood.EPIC])
        return queries[indice % len(queries)]

    def _detectar_mood(self, lyrics: str, description: str, music_prompt: str) -> AgentMood:
        """Detecta o mood a partir do conteúdo fornecido.

        Prioriza a camada de interpretação emocional sobre a busca por
        palavra-chave. O motivo é concreto: casar palavra solta faz
        "coração partido" cair em ROMANTIC (por causa de "coração"), que
        buscaria flores e casais — o oposto da emoção da linha.
        """
        # ── 1) Emoção real da letra, linha por linha ────────────────
        # Só decide se a letra tiver carga emocional de verdade. Uma
        # letra como "epic music" descreve estilo, não sentimento, e
        # nesse caso é correto deixar a busca por palavra-chave abaixo
        # resolver — ela sim entende "epic".
        if lyrics and lyrics.strip():
            linhas = [l for l in lyrics.splitlines() if l.strip()]
            if linhas:
                emocao = emocao_dominante(linhas)
                if emocao is not None:
                    mood = self._emocao_para_mood(emocao)
                    if mood is not None:
                        return mood

        # ── 2) Busca por palavra-chave (reserva) ────────────────────
        text = f"{lyrics} {description} {music_prompt}".lower()

        mood_keywords = {
            AgentMood.EPIC: ["epic", "powerful", "dramatic", "cinematic", "grande"],
            AgentMood.CALM: ["calm", "peaceful", "soft", "gentle", "tranquil", "calmo", "suave"],
            AgentMood.ROMANTIC: ["love", "romantic", "kiss", "amor", "apaixonado", "beijo"],
            AgentMood.ENERGETIC: ["energy", "fast", "power", "intense", "explosive", "energético"],
            AgentMood.DARK: ["dark", "shadow", "evil", "depressing", "sombrio", "escuridão"],
            AgentMood.JOYFUL: ["happy", "joy", "fun", "bright", "celebrate", "alegre", "feliz"],
            AgentMood.CINEMATIC: ["cinematic", "film", "movie", "scene", "director", "cinematográfico"],
            AgentMood.MINIMAL: ["minimal", "simple", "clean", "basic", "simples", "limpo"],
        }

        for mood, keywords in mood_keywords.items():
            for kw in keywords:
                if kw in text:
                    return mood

        # Default baseado no music_prompt
        if "epic" in music_prompt.lower() or "powerful" in music_prompt.lower():
            return AgentMood.EPIC
        if "calm" in music_prompt.lower() or "soft" in music_prompt.lower():
            return AgentMood.CALM
        if "sad" in music_prompt.lower() or "dark" in music_prompt.lower():
            return AgentMood.DARK

        return AgentMood.EPIC

    @staticmethod
    def _emocao_para_mood(emocao: Emocao) -> Optional["AgentMood"]:
        """Converte uma emoção da letra no mood visual correspondente."""
        mapa = {
            Emocao.TRISTEZA: AgentMood.DARK,
            Emocao.SAUDADE: AgentMood.CALM,
            Emocao.SOLIDAO: AgentMood.DARK,
            Emocao.RAIVA: AgentMood.ENERGETIC,
            Emocao.MEDO: AgentMood.DARK,
            Emocao.AMOR: AgentMood.ROMANTIC,
            Emocao.PAZ: AgentMood.CALM,
            Emocao.ALEGRIA: AgentMood.JOYFUL,
            Emocao.EUFORIA: AgentMood.ENERGETIC,
            Emocao.ESPERANCA: AgentMood.CALM,
            Emocao.TENSAO: AgentMood.CINEMATIC,
            Emocao.MELANCOLIA: AgentMood.CINEMATIC,
        }
        return mapa.get(emocao)

    def _decidir_beat(self, beat: MusicBeat, plan: AgentPlan, indice: int = 0) -> AgentDecision:
        """Gera decisão para um beat específico."""
        decision = self.direcionar_imagem(beat, plan.mood, indice=indice)

        # Ajustes baseados no conteúdo da letra
        if hasattr(beat, 'lyrics_line') and beat.lyrics_line:
            line = beat.lyrics_line.lower()
            if "amor" in line or "love" in line:
                decision.accent_color = "#E84393"
                decision.style_note = "Tom romântico detectado"
            elif "fogo" in line or "fire" in line or "poder" in line:
                decision.accent_color = "#FF006E"
                decision.style_note = "Tom intenso detectado"

        return decision

    def _efeitos_globais(self, mood: AgentMood) -> list[str]:
        """Retorna efeitos globais baseados no mood."""
        effects = {
            AgentMood.EPIC: ["film_grain", "light_leaks", "lens_flare"],
            AgentMood.CALM: ["bokeh", "film_grain", "blur_fade"],
            AgentMood.ROMANTIC: ["light_leaks", "lens_flare", "energy_particles"],
            AgentMood.ENERGETIC: ["energy_particles", "lens_flare", "dust_scratches"],
            AgentMood.DARK: ["dust_scratches", "film_grain", "vignette_pulse"],
            AgentMood.JOYFUL: ["energy_particles", "lens_flare", "bokeh"],
            AgentMood.CINEMATIC: ["film_grain", "vignette_pulse", "color_grade_shift"],
            AgentMood.MINIMAL: [],
        }
        return effects.get(mood, [])

    def selecionar_imagens_banco(
        self,
        n_imagens: int = 4,
        query: Optional[str] = None,
    ) -> list:
        """
        Seleciona imagens do banco de dados para o clipe.

        Returns:
            Lista de URLs de imagens
        """
        from MusicClipStudio.database import StockDatabase

        db = StockDatabase()
        q = query or f"{self.mood.value} {self.style.value}"
        search = db.pesquisar(q, max_results=n_imagens)

        return [r.thumbnail_url for r in search.results if r.thumbnail_url][:n_imagens]

    def aplicar_cores(self) -> dict:
        """Retorna paleta de cores atual."""
        return {
            "primary": self.colors.get("primary", "#FFCC00"),
            "secondary": self.colors.get("secondary", "#1A1A2E"),
            "accent": self.colors.get("accent", "#FF6B35"),
            "text": "#FFFFFF",
        }