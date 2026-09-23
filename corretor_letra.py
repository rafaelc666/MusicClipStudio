"""
Corretor de ortografia portuguesa para letras transcritas.

O Whisper transcreve bem a FONETICA e mal a ORTOGRAFIA: ele ouve
"coração" e escreve "coracao", ouve "voz" e escreve "vois". Como a
letra alimenta a busca de midia (`gerar_search_terms_letra`), um erro
desses vira uma query que nao encontra nada — e o usuario nao faz ideia
do motivo.

Este modulo faz tres coisas:

  1. MARCA   — aponta as palavras que nao existem no portugues
  2. SUGERE  — propoe a correcao, ordenada por proximidade fonetica
  3. NUNCA ESCREVE SOZINHO — devolve sugestoes; quem aceita e' o usuario

O dicionario vem do LibreOffice (dict-pt-BR, Hunspell), que ja esta na
maquina. Se nao estiver, o modulo degrada para "sem dicionario" em vez
de quebrar — o clipe tem que sair mesmo sem corretor.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Caminhos onde o dicionario pt-BR costuma estar (Windows/Linux/mac).
CAMINHOS_DICIONARIO: tuple[str, ...] = (
    r"C:\Program Files\LibreOffice\share\extensions\dict-pt-BR",
    r"C:\Program Files (x86)\LibreOffice\share\extensions\dict-pt-BR",
    "/usr/share/hunspell",
    "/usr/share/myspell/dicts",
    "/Library/Spelling",
    "/Applications/LibreOffice.app/Contents/Resources/extensions/dict-pt-BR",
)

# Palavras muito curtas (a, o, e) nao valem a pena verificar: o custo de
# um falso positivo e' alto (poluir a tela) e o ganho e' nulo.
MIN_LETRAS = 3

# Teto de edicoes para aceitar uma correcao SEM o usuario confirmar.
# Mais alto que isso, a sugestao ainda aparece — mas como sugestao.
MAX_EDICOES_AUTO = 2


# ════════════════════════════════════════════════════════════════
# Dicionario
# ════════════════════════════════════════════════════════════════

class DicionarioPT:
    """Wrapper do Hunspell que nunca levanta excecao.

    Prefere `spylls` (Hunspell puro-Python, le .aff/.dic direto). Sem ele,
    tenta o `.dic` cru — que perde as formas flexionadas, entao usamos
    isso apenas como ultimo recurso e avisamos.
    """

    def __init__(self, pasta: Optional[str] = None):
        self.pasta = Path(pasta) if pasta else self._achar_pasta()
        self._hunspell = None
        self._cru: Optional[set[str]] = None
        self._indice: Optional[dict[str, list[str]]] = None
        self._flags: dict[str, int] = {}
        self.erro = ""

        if self.pasta is None:
            self.erro = "dicionário pt-BR não encontrado"
            return

        self._carregar()

    @staticmethod
    def _achar_pasta() -> Optional[Path]:
        for bruto in CAMINHOS_DICIONARIO:
            p = Path(bruto)
            if not p.exists():
                continue
            # Aceita tanto pt_BR.* quanto pt_BR/ subpasta
            if (p / "pt_BR.aff").exists() or list(p.glob("pt_BR.*")):
                return p
        return None

    def _carregar(self) -> None:
        assert self.pasta is not None

        try:
            from spylls.hunspell import Dictionary

            # spylls aceita o prefixo sem extensao
            alvo = self.pasta / "pt_BR"
            if not alvo.with_suffix(".aff").exists():
                candidatos = list(self.pasta.glob("*.aff"))
                if candidatos:
                    alvo = candidatos[0].with_suffix("")
            self._hunspell = Dictionary.from_files(str(alvo))
            return
        except Exception as e:
            self.erro = f"spylls indisponível: {e}"

        # Fallback: .dic cru (perde flexao, mas ainda pega erro grosseiro)
        try:
            candidatos = list(self.pasta.glob("*.dic"))
            if candidatos:
                palavras = set()
                for linha in candidatos[0].read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()[1:]:
                    p = linha.split("/")[0].strip().lower()
                    if p:
                        palavras.add(p)
                if palavras:
                    self._cru = palavras
                    self.erro = "usando dicionário reduzido (sem flexão)"
        except Exception as e:
            self.erro = f"falha ao ler dicionário: {e}"

    @property
    def ok(self) -> bool:
        return self._hunspell is not None or bool(self._cru)

    @property
    def flags(self) -> dict[str, int]:
        """Contagem de flags morfologicas por palavra (so' as ambíguas).

        `vos` nao tem nenhuma (forma congelada); `voz` tem 5. Serve de
        desempate quando duas correcoes estao a mesma distancia.
        """
        return self._flags

    @property
    def reduzido(self) -> bool:
        """True quando só o .dic cru carregou (marca mais falso positivo)."""
        return self._hunspell is None and bool(self._cru)

    def existe(self, palavra: str) -> bool:
        if not palavra:
            return True
        if self._hunspell is not None:
            try:
                return bool(self._hunspell.lookup(palavra))
            except Exception:
                return True
        if self._cru is not None:
            return palavra.lower() in self._cru
        # Sem dicionario: considera tudo certo (nao marcar e' melhor que
        # marcar errado)
        return True

    def sugerir(self, palavra: str, maximo: int = 5,
                usar_hunspell: bool = False) -> list[str]:
        """Sugestoes para a palavra, do jeito mais rapido que funcione.

        Ordem deliberada: o INDICE FONETICO vem primeiro. Ele responde
        em ~0.001s e devolve "voz" para "vois", "coração" para "corecao".
        O `spylls.suggest()` responde em 0.2s na maioria dos casos, mas
        chega a 30s em palavra muito corrompida ("corecao") — explorar
        todas as edicoes possiveis custa caro. Numa GUI, 30s de espera
        e' pior que uma sugestao a menos.

        `usar_hunspell=True` forca a via lenta, para quando nao houver
        pressa (script, tarefa de fundo).
        """
        candidatos = self.candidatos_foneticos(palavra, maximo=maximo * 3)

        if not usar_hunspell:
            # Se a fonetica ja' deu resultado bom, nem toca no spylls
            if candidatos:
                return candidatos[:maximo]
            # Sem candidato fonetico: vale tentar (aqui e' rapido, porque
            # a palavra nao tinha chave no indice)
            if self._hunspell is None:
                return []

        if self._hunspell is None:
            return candidatos[:maximo]

        try:
            brutas = list(self._hunspell.suggest(palavra))
        except Exception:
            brutas = []

        vistas: set[str] = set()
        juntas: list[str] = []
        for s in candidatos + brutas:
            chave = normalizar_simples(s)
            if chave in vistas:
                continue
            vistas.add(chave)
            juntas.append(s)

        return ordenar_sugestoes(palavra, juntas)[:maximo]

    def candidatos_foneticos(self, palavra: str, maximo: int = 10) -> list[str]:
        """Palavras do dicionario que SOAM como a errada.

        E' o que recupera "voz" para "vois", que o Hunspell nao acha.
        Ordena por proximidade de escrita e corta o excesso: a chave
        `karaka` (de "corecao") tem 93 candidatos, e so' os primeiros
        interessam.
        """
        indice = self._indice_fonetico()
        if not indice:
            return []

        candidatos = indice.get(chave_fonetica(palavra), [])
        if not candidatos:
            return []

        ordenados, _ambigua = ranquear(palavra, candidatos, self._flags)
        return ordenados[:maximo]

    def _indice_fonetico(self) -> dict[str, list[str]]:
        """Constroi (uma vez) o mapa chave_fonetica -> palavras.

        Le o .dic cru: 312k palavras em ~0.2s e o indice em ~4s. Fica
        em cache no objeto e nunca levanta — sem dicionario, devolve
        vazio e o resto do modulo segue sem sugestoes.

        E' chamado SOBRE DEMANDA (primeira palavra suspeita encontrada),
        nunca na construcao: carregar isto junto com o spylls deixa o
        primeiro uso lento demais para a GUI.
        """
        if self._indice is not None:
            return self._indice

        self._indice = {}
        if self.pasta is None:
            return self._indice

        try:
            arquivos = list(self.pasta.glob("*.dic"))
            # hyph_pt_BR.dic e' de hifenizacao, nao de vocabulario
            arquivos = [a for a in arquivos if not a.name.startswith("hyph")]
            if not arquivos:
                return self._indice

            indice: dict[str, list[str]] = {}
            contagem: dict[str, int] = {}
            texto = arquivos[0].read_text(encoding="utf-8", errors="ignore")
            for linha in texto.splitlines()[1:]:
                bruta = linha.strip()
                if not bruta:
                    continue
                palavra, _, sufixo = bruta.partition("/")
                palavra = palavra.strip()
                if len(palavra) < MIN_LETRAS or palavra.isupper():
                    continue
                indice.setdefault(chave_fonetica(palavra), []).append(palavra)
                contagem[palavra] = len(sufixo.strip())

            # So' guardamos a contagem de quem pode realmente empatar: um
            # mapa com 312k entradas a mais pesaria dezenas de MB a troco
            # de nada (palavra sem concorrente nunca e' desempatada).
            for palavras in indice.values():
                if len(palavras) < 2:
                    continue
                for palavra in palavras:
                    self._flags[palavra] = contagem.get(palavra, 0)
            contagem.clear()

            self._indice = indice
        except Exception as e:
            self.erro = f"índice fonético indisponível: {e}"

        return self._indice

    def resumo(self) -> str:
        if not self.ok:
            return f"corretor indisponível ({self.erro})"
        modo = "reduzido" if self.reduzido else "completo"
        return f"dicionário pt-BR {modo}"


# ════════════════════════════════════════════════════════════════
# Fonetica pt-BR
# ════════════════════════════════════════════════════════════════

def chave_fonetica(palavra: str) -> str:
    """Reduz a palavra ao que a FALA preserva, ignorando a grafia.

    Motivo de existir: o Hunspell mede distancia de ESCRITA, entao para
    "vois" ele sugere "voes/voos/bois" e nunca "voz" — mesmo com "voz"
    no dicionario. A chave fonetica captura que "vois" e "voz" soam
    igual, e usa isso para achar candidatos que a escrita nao acharia.

    Ordem das regras importa: `c` antes de `e`/`i` vira /s/ e o resto
    vira /k/ — tratar `c` como /k/ sempre fazia "nacer" (nasar) nao
    casar com "nascer" (nasar), que era o objetivo.
    """
    t = unicodedata.normalize("NFD", (palavra or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")

    # Digrafos consonantais
    t = t.replace("ch", "x").replace("ph", "f")
    t = t.replace("ss", "s").replace("xc", "s").replace("sc", "s")
    # ç e c antes de e/i = /s/  (REGRA QUE VEM PRIMEIRO)
    t = t.replace("ç", "s")
    t = re.sub(r"c(?=[ei])", "s", t)
    # c restante, qu e q = /k/
    t = re.sub(r"(c|q)u(?=[ei])", "k", t)
    t = t.replace("c", "k").replace("q", "k")
    # g antes de e/i = /j/, resto, junto com j
    t = re.sub(r"g(?=[ei])", "j", t)
    t = t.replace("g", "j").replace("y", "i")
    t = t.replace("x", "s")

    # S/Z finais soam igual ("vois"/"voz")
    t = re.sub(r"[sz]$", "z", t)
    # Letras dobradas nao mudam o som
    t = re.sub(r"(.)\1+", r"\1", t)
    # Vogais colapsam: o ouvido nao separa "corecao" de "coracao"
    t = re.sub(r"[aeiou]+", "a", t)

    return t


def _distancia(a: str, b: str) -> int:
    """Levenshtein simples — usado so' para desempatar sugestoes."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            custo = 0 if ca == cb else 1
            atual.append(min(
                anterior[j] + 1,       # remocao
                atual[j - 1] + 1,      # insercao
                anterior[j - 1] + custo,  # substituicao
            ))
        anterior = atual
    return anterior[-1]


def _forma_comparavel(palavra: str) -> str:
    """Normaliza o que NAO distingue som, para medir distancia util.

    `vois` e `voz` diferem em 2 letras na escrita, mas sao a mesma coisa
    falada. Sem isto o `vos` (1 edicao) ganharia de `voz` (2 edicoes),
    que e' justamente o erro que queremos evitar.

    Nao colapsa letra dobrada (isso e' papel da `chave_fonetica`): aqui
    ela custa uma edicao, como deve custar — foi o que fazia "correcao"
    (com rr) parecer identico a "corecao" e ganhar de "coracao" sem
    merecer.
    """
    t = normalizar_simples(palavra)
    t = re.sub(r"[sz]$", "z", t)
    return t


def ranquear(
    errada: str,
    candidatos: list[str],
    flags: Optional[dict] = None,
) -> tuple[list[str], bool]:
    """Ordena os candidatos e diz se ha EMPATE REAL na primeira colocacao.

    Devolve `(ordenados, ambigua)`.

    `ambigua` e' True quando dois ou mais candidatos chegam ao topo pela
    mesma distancia de escrita. Nesse caso nao existe criterio que
    resolva sozinho — "corecao" esta' a 1 edicao de "correcao" E de
    "coracao", e so' o contexto ("o coracao dispara") diz qual e' o
    certo. A palavra tem que ir para o usuario; aceitar automatico aqui
    e' corromper o texto em silencio.

    O desempate dentro da faixa usa o PARADIGMA MORFOLOGICO do
    dicionario: `vos`/`vos` nao tem flag nenhuma (forma congelada,
    pronome arcaico), enquanto `voz` tem `BOVIU`. Palavra com paradigma
    rico tende a ser a forma viva da lingua — e e' o unico sinal de
    frequencia disponivel sem sair da maquina.
    """
    if not candidatos:
        return [], False

    medidos = []
    for c in candidatos:
        fonetica = _distancia(_forma_comparavel(errada), _forma_comparavel(c))
        escrita = _distancia(normalizar_simples(errada), normalizar_simples(c))
        medidos.append((fonetica, escrita, c))

    medidos.sort(key=lambda t: t[0])
    min_fon = medidos[0][0]
    faixa = [t for t in medidos if t[0] == min_fon]
    fora = [t for t in medidos if t[0] != min_fon]
    min_escrita = min(t[1] for t in faixa)

    dic_flags = flags or {}

    def chave(t: tuple[int, int, str]) -> tuple:
        _fon, escrita, palavra = t
        return (
            -dic_flags.get(palavra, 0),  # paradigma rico primeiro
            escrita,
            len(palavra),
            palavra,                     # determinista
        )

    faixa.sort(key=chave)
    fora.sort(key=chave)

    ordenados = [c for _f, _e, c in faixa + fora]
    empatadas = [t for t in faixa if t[1] == min_escrita]
    return ordenados, len(empatadas) > 1


def ordenar_sugestoes(errada: str, sugestoes: list[str]) -> list[str]:
    """Reordena sugestoes pela fonetica (sem acesso ao dicionario)."""
    return ranquear(errada, sugestoes)[0]


# ════════════════════════════════════════════════════════════════
# Encontrar e corrigir
# ════════════════════════════════════════════════════════════════

@dataclass
class PalavraSuspeita:
    """Uma palavra que o dicionario nao reconhece."""

    palavra: str
    linha: int
    coluna: int
    sugestoes: list[str] = field(default_factory=list)
    ambigua: bool = False

    @property
    def melhor(self) -> str:
        return self.sugestoes[0] if self.sugestoes else ""

    @property
    def alta_confianca(self) -> bool:
        """Pode ser aceita sem o usuario confirmar?

        Exige sugestao E ausencia de empate. "vois" tem "vos" e "voz" a
        distancias diferentes mas "razao" so' tem "razao" — a primeira
        vai para a tela, a segunda o sistema resolve.
        """
        return bool(self.melhor) and not self.ambigua

    def resumo(self) -> str:
        if not self.melhor:
            return f"linha {self.linha}: {self.palavra} (sem sugestão)"
        marca = "?" if self.ambigua else "→"
        return f"linha {self.linha}: {self.palavra} {marca} {self.melhor}"


def sugerir_para(
    palavra: str,
    dicionario: DicionarioPT,
    maximo: int = 6,
) -> tuple[list[str], bool]:
    """Sugestoes ordenadas + se ha empate que o usuario tem que resolver."""
    candidatos = dicionario.sugerir(palavra, maximo=maximo * 3)
    if not candidatos:
        return [], False
    return ranquear(palavra, candidatos, dicionario.flags)


# Palavra = letras (com acento), aceitando apostrofo interno (d'água)
_TOKEN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)


def encontrar_suspeitas(
    texto: str,
    dicionario: Optional[DicionarioPT] = None,
    maximo: int = 100,
) -> list[PalavraSuspeita]:
    """Lista as palavras do texto que o dicionario nao reconhece.

    Nao marca: numero, palavra de 1-2 letras, nem palavra que o
    dicionario aceita. Devolve vazio se nao houver dicionario.
    """
    if not texto:
        return []

    dic = dicionario or DicionarioPT()
    if not dic.ok:
        return []

    achadas: list[PalavraSuspeita] = []

    for n_linha, linha in enumerate(texto.splitlines(), 1):
        for m in _TOKEN.finditer(linha):
            palavra = m.group(0)

            # Curta demais: falso positivo e' mais provavel que o erro
            if len(palavra) < MIN_LETRAS:
                continue
            # Ja esta correta
            if dic.existe(palavra):
                continue
            # Toda maiuscula (nome proprio, sigla) — nao arriscar
            if palavra.isupper():
                continue

            sugestoes, ambigua = sugerir_para(palavra, dic, maximo=6)
            achadas.append(PalavraSuspeita(
                palavra=palavra, linha=n_linha,
                coluna=m.start(), sugestoes=sugestoes[:6],
                ambigua=ambigua,
            ))

            if len(achadas) >= maximo:
                return achadas

    return achadas


def corrigir_texto(texto: str, aceitas: dict[str, str]) -> str:
    """Aplica as correcoes que o usuario aceitou.

    `aceitas` mapeia palavra_errada -> palavra_certa. So' troca palavra
    inteira (nao mexe dentro de palavra maior) e preserva maiuscula
    inicial, para nao estragar comeco de frase.

    Trocas sao feitas por LINHA, comparando palavra a palavra: um
    `str.replace` global trocaria tambem pedacos de outras palavras.
    """
    if not texto or not aceitas:
        return texto

    # Compara sem acento/caixa para casar independente de grafia
    mapa = {normalizar_simples(k): v for k, v in aceitas.items()}
    saida: list[str] = []

    for linha in texto.splitlines():
        pedacos: list[str] = []
        ultimo = 0

        for m in _TOKEN.finditer(linha):
            palavra = m.group(0)
            troca = mapa.get(normalizar_simples(palavra))

            # Compara as palavras CRUAS, nao as normalizadas: "razao" ->
            # "razão" normaliza igual nos dois lados, e comparar normalizado
            # faria a unica correcao necessaria (o acento) ser descartada.
            if troca and troca != palavra:
                pedacos.append(linha[ultimo:m.start()])
                pedacos.append(_preservar_caixa(palavra, troca))
                ultimo = m.end()

        pedacos.append(linha[ultimo:])
        saida.append("".join(pedacos))

    return "\n".join(saida)


def normalizar_simples(palavra: str) -> str:
    """Lowercase sem acento — chave de comparacao entre grafias."""
    t = unicodedata.normalize("NFD", (palavra or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _preservar_caixa(original: str, novo: str) -> str:
    """Se a original comeca maiuscula, a nova tambem comeca."""
    if original[:1].isupper():
        return novo[:1].upper() + novo[1:]
    return novo


def corrigir_por_fonetica(
    texto: str,
    dicionario: Optional[DicionarioPT] = None,
) -> dict[str, str]:
    """Aceita automaticamente as correcoes de alta confianca.

    Criterio deliberadamente conservador. Exige as TRES condicoes:

      1. mesma chave fonetica (casa com o que se ouve),
      2. distancia de escrita pequena (1 ou 2 edicoes), E
      3. sem empate — se duas correcoes chegam junto, o sistema NAO
         escolhe ("corecao" e' "correcao" e "coracao" igualmente; so'
         quem sabe a musica decide).

    A condicao 3 e' a que segura o caso "vois": "vos" esta' a 1 edicao e
    "voz" a 2, mas as duas soam igual, entao empate tecnico — aceitar
    "vos" automaticamente trocaria um erro por outro.

    "razao"→"razão" passa (1 edicao, so' acento, sem concorrente).
    "nacer"→"nascer" passa (1 insercao, sem concorrente).

    O que nao passar continua aparecendo como SUGESTAO na tela; apenas
    nao e' aceito sem o usuario clicar.
    """
    mapa: dict[str, str] = {}

    for suspeita in encontrar_suspeitas(texto, dicionario):
        if not suspeita.alta_confianca:
            continue

        if chave_fonetica(suspeita.palavra) != chave_fonetica(suspeita.melhor):
            continue

        # Distancia medida na forma normalizada (sem acento): trocar so'
        # o acento nao deve contar como edicao.
        a = normalizar_simples(suspeita.palavra)
        b = normalizar_simples(suspeita.melhor)
        if _distancia(a, b) > MAX_EDICOES_AUTO:
            continue

        mapa[suspeita.palavra] = suspeita.melhor

    return mapa


def _auto_teste() -> None:  # pragma: no cover
    dic = DicionarioPT()
    print("dicionario:", dic.resumo())

    texto = (
        "quando a noite cai sobre a cidade\n"
        "eu ainda escuto a tua vois\n"
        "o corecao dispara sem razao\n"
        "mas o sol vai nacer de novo"
    )

    print("\n== suspeitas ==")
    for s in encontrar_suspeitas(texto, dic):
        extras = ", ".join(s.sugestoes[1:4])
        print(f"   {s.resumo()}" + (f"   (ou: {extras})" if extras else ""))

    print("\n== alta confianca (fonetica) ==")
    auto = corrigir_por_fonetica(texto, dic)
    for k, v in auto.items():
        print(f"   {k} -> {v}")

    print("\n== texto corrigido com o mapa todo ==")
    todas = {s.palavra: s.melhor
             for s in encontrar_suspeitas(texto, dic) if s.melhor}
    print(corrigir_texto(texto, todas))

    print("\nauto-teste: OK")


if __name__ == "__main__":
    _auto_teste()
