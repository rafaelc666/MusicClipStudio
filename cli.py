"""
CLI para Gerador de Clipes Musicais v2.

Uso:
    python -m MusicClipStudio
    python -m MusicClipStudio --lyrics "Minha letra..."
    python -m MusicClipStudio --descricao "Vídeo épico"
    python -m MusicClipStudio --lista-presets
    python -m MusicClipStudio --buscar-fotos natureza
    python -m MusicClipStudio --agente "Crie um clipe sobre..."
    python -m MusicClipStudio --config-api
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de Clipes Musicais v2 — GeradorYouTube Unificado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --lyrics "Minha letra aqui" --prompt "epic music"
  %(prog)s --descricao "Clipe épico com montanha"
  %(prog)s --lista-presets
  %(prog)s --agente "Crie um clipe sobre o amor"
  %(prog)s --buscar-fotos natureza concerto
        """,
    )

    # ── Conteúdo principal ─────────────────────────
    content_group = parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument("--lyrics", "-l", help="Letra da música")
    content_group.add_argument("--descricao", "-d", help="Descrição do clipe")
    content_group.add_argument("--lyrics-file", "-lf", help="Arquivo com letra")
    content_group.add_argument("--lista-presets", action="store_true", help="Lista presets")
    content_group.add_argument("--buscar-fotos", "-b", nargs="+", help="Buscar fotos no banco")
    content_group.add_argument("--agente", "-a", help="Agente gera clipe a partir de descrição")
    content_group.add_argument("--batch", "-bt", help="Arquivo com prompts (um por linha)")
    content_group.add_argument("--integrar", "-i", nargs="+", help="Integração: audio imagens saida")
    content_group.add_argument("--config-api", action="store_true", help="Abrir configuração de APIs")

    # ── Opções ─────────────────────────────────────
    parser.add_argument("--prompt", "-p", default="", help="Prompt de música (ACE-Step)")
    parser.add_argument("--imagens", "-im", nargs="+", default=[], help="Caminhos de imagens")
    parser.add_argument("--duracao", "-dur", type=int, default=30, help="Duração em segundos")
    parser.add_argument("--formato", "-f", default="9/16", choices=["9/16", "16/9", "3/4", "4/3", "1/1"])
    parser.add_argument("--saida", "-o", default="", help="Caminho de saída")
    parser.add_argument("--agente-modelo", "-m", default="", help="Modelo LLM para agente")
    parser.add_argument("--agente-mood", "-mo", default="epic", choices=["epic","calm","romantic","energetic","dark","joyful","cinematic","minimal"])
    parser.add_argument("--agente-estilo", "-es", default="music_video", choices=["cinematic","music_video","lyric_video","abstract","narrative","performance"])
    parser.add_argument("--stock-provider", "-sp", default="pexels", choices=["pexels","pixabay","unsplash","nasa","coverr","giphy"])
    parser.add_argument("--stock-api", "-sa", default="", help="API key para banco de fotos")
    parser.add_argument("--moneyprinter", "-mp", default="", help="Caminho moneyprinter")
    parser.add_argument("--letra-file", default="", help="Arquivo de letras alternativo")

    args = parser.parse_args()

    # ── Ações ──────────────────────────────────────
    if args.config_api:
        _abrir_configuracao()
        return

    if args.lista_presets:
        _listar_presets()
        return

    if args.buscar_fotos:
        _buscar_fotos(args.buscar_fotos, args.stock_provider, args.stock_api)
        return

    if args.agente:
        _executar_agente(args)
        return

    if args.batch:
        _executar_batch(args)
        return

    if args.integrar:
        _executar_integracao(args)
        return

    # Gerar clipe
    lyrics = ""
    if args.lyrics:
        lyrics = args.lyrics
    elif args.lyrics_file:
        p = Path(args.lyrics_file)
        if p.exists():
            lyrics = p.read_text(encoding="utf-8")

    descricao = ""
    if args.descricao:
        descricao = args.descricao

    if lyrics:
        _executar_clip_letras(args, lyrics)
    elif descricao:
        _executar_clip_descricao(args, descricao)


def _listar_presets():
    from MusicClipStudio.audio import listar_presets, PRESETS_CLIP, PRESETS_NARRACAO
    from MusicClipStudio.agent import AgentMood, AgentStyle

    print("\n[MUSIC] Presets de Trilha Musical:")
    for i, (nome, prompt) in enumerate(PRESETS_CLIP, 1):
        print(f"  {i:2d}. {nome}")
        print(f"      \"{prompt}\"")

    print("\n[MOOD] Presets de Agente (Mood):")
    for mood in AgentMood:
        print(f"  - {mood.value}")

    print("\n[STYLE] Presets de Agente (Estilo):")
    for style in AgentStyle:
        print(f"  - {style.value}")
    print()


def _buscar_fotos(queries, provider, api_key):
    from MusicClipStudio.database import StockDatabase, ClipConfig

    cfg = ClipConfig(stock_api_key=api_key, stock_provider=provider)
    db = StockDatabase(cfg)

    for query in queries:
        search = db.pesquisar(query)
        print(f"\n[SEARCH] '{query}' ({provider}) — {search.total} resultados:")
        for i, item in enumerate(search.results[:5], 1):
            print(f"  {i}. [{item.source}] {item.thumbnail_url}")

    print()


def _executar_agente(args):
    from MusicClipStudio.pipeline import MusicClipPipeline
    from MusicClipStudio.config import ClipConfig

    cfg = ClipConfig(
        agent_mood=args.agente_mood,
        agent_style=args.agente_estilo,
        agent_model=args.agente_modelo,
        stock_api_key=args.stock_api,
        stock_provider=args.stock_provider,
    )
    pipeline = MusicClipPipeline(cfg)

    print(f"\n[AGENT] Agente: {args.agente}")
    print(f"   Mood: {args.agente_mood}, Estilo: {args.agente_estilo}")
    print(f"   Formato: {args.formato}, Duração: {args.duracao}s")

    resultado = pipeline.gerar_com_agente(
        descricao=args.agente,
        music_prompt=args.prompt,
        formato=args.formato,
    )

    if resultado:
        print(f"\n[OK] Clipe gerado: {resultado}")
    else:
        print("\n[ERROR] Falha na geração")
        sys.exit(1)


def _executar_clip_letras(args, lyrics):
    from MusicClipStudio.pipeline import MusicClipPipeline
    from MusicClipStudio.config import ClipConfig

    cfg = ClipConfig(
        stock_api_key=args.stock_api,
        stock_provider=args.stock_provider,
    )
    pipeline = MusicClipPipeline(cfg)

    print(f"\n[MUSIC] Gerando clipe com letras...")
    print(f"   Letras: {len(lyrics)} caracteres")
    print(f"   Prompt música: {args.prompt or 'padrão'}")
    print(f"   Formato: {args.formato}, Duração: {args.duracao}s")

    resultado = pipeline.executar_rapido(
        lyrics=lyrics,
        music_prompt=args.prompt,
        images=args.imagens if args.imagens else None,
        duracao=args.duracao,
        formato=args.formato,
    )

    if resultado:
        print(f"\n[OK] Clipe gerado: {resultado}")
    else:
        print("\n[ERROR] Falha na geração")
        sys.exit(1)


def _executar_clip_descricao(args, descricao):
    from MusicClipStudio.pipeline import MusicClipPipeline
    from MusicClipStudio.config import ClipConfig

    cfg = ClipConfig(
        agent_mood=args.agente_mood,
        agent_style=args.agente_estilo,
        stock_api_key=args.stock_api,
        stock_provider=args.stock_provider,
    )
    pipeline = MusicClipPipeline(cfg)

    print(f"\n[AGENT] Gerando clipe por descrição (agente)...")
    print(f"   Descrição: {descricao}")

    resultado = pipeline.gerar_com_agente(
        descricao=descricao,
        music_prompt=args.prompt,
        formato=args.formato,
    )

    if resultado:
        print(f"\n[OK] Clipe gerado: {resultado}")
    else:
        print("\n[ERROR] Falha na geração")
        sys.exit(1)


def _executar_batch(args):
    from MusicClipStudio.batcher import ClipBatcher
    from MusicClipStudio.config import ClipConfig

    p = Path(args.batch)
    if not p.exists():
        print(f"Arquivo não encontrado: {p}")
        sys.exit(1)

    prompts = p.read_text(encoding="utf-8").strip().split("\n")
    prompts = [x.strip() for x in prompts if x.strip()]

    batcher = ClipBatcher()
    batcher.criar_batch(prompts=prompts, duracao=args.duracao, formato=args.formato)

    print(f"[BATCH] Batch: {len(prompts)} clipes")
    resultados = batcher.executar()
    resumo = batcher.resultados_resumidos()

    print(f"\n[RESULT] Resultado: {resumo['sucessos']}/{resumo['total']} clipes")
    for cid, info in resultados.items():
        status = "[OK]" if info.sucesso else "[FAIL]"
        print(f"  {status} {cid}: {info.arquivo_video or info.mensagem}")


def _executar_integracao(args):
    from MusicClipStudio.integrar import integrar_clipe_audio

    if len(args.integrar) < 2:
        print("Uso --integrar: audio.wav pasta_imagens/ clipe.mp4")
        sys.exit(1)

    audio = args.integrar[0]
    imagens = args.integrar[1:-1]
    saida = args.integrar[-1]

    resultado = integrar_clipe_audio(
        audio_path=audio,
        imagens=imagens,
        saida=saida,
    )

    if resultado:
        print(f"[OK] Integração concluída: {resultado}")
    else:
        print("[ERROR] Falha na integração")
        sys.exit(1)


def _abrir_configuracao():
    """Abre a janela de configuração de APIs."""
    try:
        from MusicClipStudio.ui_config import APIConfigUI
        app = APIConfigUI()
        app.show()
    except Exception as e:
        print(f"Erro ao abrir configuração: {e}")
        print("Execute: pip install tkinter (se necessário)")
        sys.exit(1)


if __name__ == "__main__":
    main()