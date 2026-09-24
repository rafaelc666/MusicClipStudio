# -*- coding: utf-8 -*-
"""Camada de IA genérica para a busca interna nos bancos de mídia.

Uma chave única serve para Google (Gemini), Groq, OpenRouter ou
qualquer endpoint OpenAI-compatible — o provedor é detectado pelo
prefixo da chave. A IA NÃO faz a busca: ela só traduz a intenção
(letra/consulta em português → termos visuais em inglês), porque
Pexels/Pixabay/Unsplash indexam o acervo em inglês e respondem mal a
"praia pôr do sol".

Regras deste módulo (importantes):
  * Nunca excepciona para fora. Sem chave, sem rede, provedor
    respondendo lixo → devolve [] e o chamador segue no caminho
    determinístico antigo (emoção → heurística). A busca nunca quebra
    por causa da chave.
  * Cache por texto (memória + disco): a mesma letra não paga a API
    duas vezes.
"""

import hashlib
import json
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - requests é dependência do projeto
    requests = None

# ── Detecção de provedor pelo prefixo da chave ───────────────────
# Ordem importa: "sk-or-" precisa ser testado antes de "sk-".
PREFIXOS = (
    ("AIza", "gemini"),
    ("gsk_", "groq"),
    ("sk-or-", "openrouter"),
    ("sk-", "openai"),
)

# Modelo default por provedor — todos com cota gratuita.
# (groq/openrouter: llama-3.3-70b, mesmo "espírito" do flash do Google)
MODELOS_PADRAO = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "openai": "gpt-4o-mini",
}

GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              "{modelo}:generateContent?key={chave}")
OPENAI_BASE = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
}

_PROMPT = """Generate {n} search terms for stock video/image search.

Rules:
1. Each term must be 1-3 words in ENGLISH
2. Terms must be VISUAL - what a video director would SHOW on screen
3. Capture the imagery and emotion of the input text
4. Return ONLY a JSON array of strings, nothing else

### Input:
{texto}

### Example output:
["dramatic sunset", "lonely figure", "city lights", "ocean waves", "night sky"]"""


def detectar_provedor(chave: str) -> str:
    """Provedor pelo prefixo da chave ('' quando não reconhecido)."""
    chave = (chave or "").strip()
    for prefixo, nome in PREFIXOS:
        if chave.startswith(prefixo):
            return nome
    return ""


def _modelo_de(provedor: str, modelo: str) -> str:
    return (modelo or "").strip() or MODELOS_PADRAO.get(provedor, "")


# ── Chamadas por família de API ──────────────────────────────────
def _chat_openai_compat(provedor: str, chave: str, modelo: str,
                        prompt: str, base_url: str = "", timeout: int = 25) -> str:
    """Groq, OpenRouter e genérico OpenAI-compatible (mesmo shape)."""
    if requests is None:
        raise RuntimeError("instale 'requests' para usar a IA de busca")
    base = (base_url or "").strip().rstrip("/") or OPENAI_BASE.get(provedor, "")
    if not base:
        raise RuntimeError(f"sem URL base para o provedor '{provedor}' — preencha o campo base URL")
    headers = {
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json",
    }
    if provedor == "openrouter":
        headers["HTTP-Referer"] = "https://musicclipstudio.local"
        headers["X-Title"] = "MusicClipStudio"
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 220,
    }
    resp = requests.post(f"{base}/chat/completions",
                         headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _chat_gemini(chave: str, modelo: str, prompt: str, timeout: int = 25) -> str:
    if requests is None:
        raise RuntimeError("instale 'requests' para usar a IA de busca")
    url = GEMINI_URL.format(modelo=modelo, chave=chave)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 220},
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _chamar_llm(chave: str, modelo: str, prompt: str,
                base_url: str = "", timeout: int = 25) -> str:
    provedor = detectar_provedor(chave)
    modelo = _modelo_de(provedor, modelo)
    if not provedor:
        raise RuntimeError(
            "prefixo de chave não reconhecido (aceitos: AIza…, gsk_…, sk-or-…, sk-…)")
    if provedor == "gemini":
        return _chat_gemini(chave, modelo, prompt, timeout=timeout)
    return _chat_openai_compat(provedor, chave, modelo, prompt,
                               base_url=base_url, timeout=timeout)


# ── Parsing da resposta ──────────────────────────────────────────
def _parsear_termos(texto: str, num_terms: int) -> list[str]:
    """Extrai o array JSON (tolerante a cercas ``` e prose em volta)."""
    texto = (texto or "").strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[-1].rsplit("```", 1)[0]
    inicio, fim = texto.find("["), texto.rfind("]")
    if inicio == -1 or fim <= inicio:
        return []
    try:
        dados = json.loads(texto[inicio:fim + 1])
    except ValueError:
        return []
    saida, vistos = [], set()
    for item in dados if isinstance(dados, list) else []:
        termo = str(item).strip().lower()
        if termo and termo not in vistos:
            vistos.add(termo)
            saida.append(termo)
    return saida[:num_terms]


# ── Cache (memória + disco) ──────────────────────────────────────
_MEMORIA: dict[str, list[str]] = {}


def _arquivo_cache(cache_dir) -> Path:
    return Path(cache_dir) / "ia_termos.json"


def _carregar_cache(cache_dir) -> dict:
    try:
        return json.loads(_arquivo_cache(cache_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _salvar_cache(cache_dir, dados: dict) -> None:
    try:
        arq = _arquivo_cache(cache_dir)
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# ── API pública ──────────────────────────────────────────────────
def termos_de_texto(texto: str, num_terms: int = 5, chave: str = "",
                    modelo: str = "", base_url: str = "",
                    cache_dir=None) -> list[str]:
    """Termos de busca em inglês para um texto PT via IA. [] em falha.

    Nunca levanta exceção: qualquer erro (chave vazia, HTTP, JSON
    malformado) resulta em [] e o chamador cai no fluxo determinístico.
    """
    texto = (texto or "").strip()
    if not texto or not (chave or "").strip() or requests is None:
        return []

    chave_cache = hashlib.sha1(
        f"{detectar_provedor(chave)}|{_modelo_de(detectar_provedor(chave), modelo)}"
        f"|{num_terms}|{texto[:4000]}".encode("utf-8")
    ).hexdigest()

    if chave_cache in _MEMORIA:
        return _MEMORIA[chave_cache]

    arquivo = _arquivo_cache(cache_dir) if cache_dir else None
    if arquivo and arquivo.exists():
        disco = _carregar_cache(cache_dir)
        if chave_cache in disco:
            _MEMORIA[chave_cache] = disco[chave_cache]
            return disco[chave_cache]

    try:
        bruto = _chamar_llm(chave, modelo,
                            _PROMPT.format(n=num_terms, texto=texto[:4000]),
                            base_url=base_url)
        termos = _parsear_termos(bruto, num_terms)
    except Exception as erro:  # rede/HTTP/JSON — degrada em silêncio
        print(f"[IABusca] indisponivel ({detectar_provedor(chave) or 'chave?'}): {erro}")
        return []

    if termos:
        _MEMORIA[chave_cache] = termos
        if cache_dir:
            disco = _carregar_cache(cache_dir)
            disco[chave_cache] = termos
            _salvar_cache(cache_dir, disco)
    return termos


def testar(chave: str, modelo: str = "", base_url: str = "") -> dict:
    """Botão 'Testar' do diálogo de chaves: responde {ok, provedor, modelo, ...}."""
    provedor = detectar_provedor(chave or "")
    if not (chave or "").strip():
        return {"ok": False, "erro": "sem chave informada"}
    if not provedor:
        return {"ok": False, "erro": "prefixo não reconhecido (AIza/gsk_/sk-or-/sk-)"}
    try:
        bruto = _chamar_llm(chave, modelo,
                            _PROMPT.format(n=3, texto="silhueta solitária ao pôr do sol"),
                            base_url=base_url)
        termos = _parsear_termos(bruto, 3)
    except Exception as erro:
        return {"ok": False, "provedor": provedor,
                "modelo": _modelo_de(provedor, modelo), "erro": str(erro)}
    if not termos:
        return {"ok": False, "provedor": provedor,
                "modelo": _modelo_de(provedor, modelo),
                "erro": "resposta não era um array de termos"}
    return {"ok": True, "provedor": provedor,
            "modelo": _modelo_de(provedor, modelo), "amostra": termos}
