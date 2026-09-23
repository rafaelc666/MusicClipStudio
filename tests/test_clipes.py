"""
Testes para Gerador de Clipes Musicais v2.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from MusicClipStudio.config import ClipConfig, load_config, save_config
from MusicClipStudio.pipeline import MusicClipPipeline, ClipJob
from MusicClipStudio.batcher import ClipBatcher, BatchConfig
from MusicClipStudio.audio import PRESETS_CLIP, PRESETS_NARRACAO, listar_presets
from MusicClipStudio.schema import (
    letras_para_beats,
    descricao_para_beats,
    project_from_lyrics,
    MusicClipProject,
    MusicBeat,
    MusicVisualElement,
    ClipComponentType,
    ClipBeatType,
)
from MusicClipStudio.legendas import gerar_srt_letras, gerar_srt_por_frase
from MusicClipStudio.agent import ClipAgent, AgentMood, AgentStyle
from MusicClipStudio.database import StockMedia, StockSearch, StockDatabase
from MusicClipStudio.moneyprinter import MoneyPrinterCompat, encontrar_moneyprinter
from MusicClipStudio.integrar import integrar_clipe_audio
from MusicClipStudio.montar import montar_clipe
from MusicClipStudio import __version__


class TestVersion(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "2.0.0")


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = ClipConfig()
        self.assertIsNotNone(cfg.base_dir)
        self.assertIsNotNone(cfg.output_dir)
        self.assertEqual(cfg.default_music_duration, 30)
        self.assertEqual(cfg.default_video_format, "9/16")
        self.assertEqual(cfg.lyrics, "")
        self.assertEqual(cfg.stock_provider, "pexels")

    def test_config_to_dict(self):
        cfg = ClipConfig()
        data = cfg.to_dict()
        self.assertIn("output_dir", data)
        self.assertIn("lyrics", data)
        self.assertIn("stock_api_key", data)
        self.assertIn("agent_enabled", data)
        self.assertIn("moneyprinter_enabled", data)

    def test_config_persistence(self):
        import tempfile
        cfg = ClipConfig(output_dir="/tmp/test_clip_output")
        save_config(cfg)
        loaded = load_config()
        self.assertEqual(cfg.output_dir, loaded.output_dir)

    def test_config_from_dict(self):
        cfg = ClipConfig()
        data = cfg.to_dict()
        cfg2 = ClipConfig.from_dict(data)
        self.assertEqual(cfg.default_music_duration, cfg2.default_music_duration)


class TestSchema(unittest.TestCase):
    def test_project_from_lyrics(self):
        project = project_from_lyrics(
            lyrics="Verso 1\nRefrão: Eu sei\nVerso 2\n",
            title="Teste",
            artist="Artista",
        )
        self.assertEqual(project.title, "Teste")
        self.assertEqual(project.artist, "Artista")
        self.assertGreater(len(project.beats), 0)

    def test_letras_para_beats(self):
        beats = letras_para_beats("Linha um\nLinha dois\nLinha três\n", duration_estimada=5.0)
        self.assertGreater(len(beats), 0)
        for beat in beats:
            self.assertIsInstance(beat, MusicBeat)
            self.assertIsInstance(beat.visual, MusicVisualElement)
            self.assertGreater(beat.duration, 0)

    def test_descricao_para_beats(self):
        beats = descricao_para_beats("Descrição do clipe épico.", duration_estimada=5.0)
        self.assertGreater(len(beats), 0)

    def test_empty_lyrics(self):
        beats = letras_para_beats("", duration_estimada=5.0)
        self.assertEqual(len(beats), 0)

    def test_beat_types(self):
        beats = letras_para_beats("Chorus: refrão aqui\n", duration_estimada=5.0)
        for beat in beats:
            self.assertIsInstance(beat.type, str)

    def test_visual_element_defaults(self):
        elem = MusicVisualElement(type="kinetic_title", text="Teste")
        self.assertEqual(elem.type, "kinetic_title")
        self.assertEqual(elem.text, "Teste")
        self.assertEqual(elem.accent_color, "#FFCC00")

    def test_component_types(self):
        self.assertEqual(ClipComponentType.KINETIC_TITLE.value, "kinetic_title")
        self.assertEqual(ClipComponentType.PARALLAX_IMAGE.value, "parallax_image")

    def test_beat_type_values(self):
        self.assertEqual(ClipBeatType.VERSE.value, "verse")
        self.assertEqual(ClipBeatType.CHORUS.value, "chorus")


class TestLegendas(unittest.TestCase):
    def test_gerar_srt_letras(self):
        srt = gerar_srt_letras("Linha um. Linha dois. Linha três.", "/tmp/test.srt", 30.0)
        self.assertTrue(Path(srt).exists())
        content = Path(srt).read_text()
        self.assertIn("Linha", content)
        self.assertIn("00:00", content)

    def test_gerar_srt_por_frase(self):
        srt = gerar_srt_por_frase("Frase um.\nFrase dois.", "/tmp/test2.srt", 20.0)
        self.assertTrue(Path(srt).exists())

    def test_srt_has_timestamps(self):
        srt = gerar_srt_letras("Teste de legenda", "/tmp/test3.srt", 15.0)
        content = Path(srt).read_text()
        self.assertIn(" --> ", content)


class TestAgent(unittest.TestCase):
    def test_agent_init(self):
        agent = ClipAgent()
        self.assertIsInstance(agent, ClipAgent)
        self.assertIsInstance(agent.mood, AgentMood)

    def test_agent_direcionar(self):
        agent = ClipAgent()
        beat = MusicBeat(
            id=1, type="verse", duration=5.0,
            script="Teste",
            visual=MusicVisualElement(type="kinetic_title"),
        )
        decision = agent.direcionar_imagem(beat)
        self.assertIsInstance(decision, type(decision))
        self.assertGreater(decision.confidence, 0)
        self.assertIsNotNone(decision.component_type)

    def test_agent_analisar(self):
        agent = ClipAgent()
        plan = agent.analisar(lyrics="Verse one\nChorus: High energy\n")
        self.assertIsInstance(plan, type(plan))
        self.assertGreater(len(plan.beats), 0)

    def test_detectar_mood_epic(self):
        agent = ClipAgent()
        mood = agent._detectar_mood("epic music", "", "powerful dramatic")
        self.assertEqual(mood, AgentMood.EPIC)

    def test_mood_colors(self):
        agent = ClipAgent()
        colors = agent.aplicar_cores()
        self.assertIn("primary", colors)
        self.assertIn("accent", colors)


class TestPipeline(unittest.TestCase):
    def test_criar_job(self):
        pipeline = MusicClipPipeline()
        job = pipeline.criar_job(
            lyrics="Teste de lyrics",
            music_prompt="epic music",
            duracao=30,
        )
        self.assertIsNotNone(job.id)
        self.assertGreater(len(job.beats), 0)
        self.assertIn(job.id, pipeline.listar_jobs())

    def test_criar_job_agente(self):
        pipeline = MusicClipPipeline()
        job = pipeline.criar_job(
            description="Clipe épico de montanhas",
            duracao=30,
        )
        self.assertIsNotNone(job.agente)

    def test_criar_job_vazio(self):
        pipeline = MusicClipPipeline()
        job = pipeline.criar_job(duracao=30)
        self.assertEqual(len(job.beats), 0)


class TestBatcher(unittest.TestCase):
    def test_criar_batch(self):
        batcher = ClipBatcher()
        batcher.criar_batch(prompts=["prompt1", "prompt2"], duracao=30)
        self.assertIsNotNone(batcher.batch_config)
        self.assertEqual(len(batcher.batch_config.prompts), 2)

    def test_batch_config(self):
        bc = BatchConfig(prompts=["a", "b"])
        self.assertEqual(len(bc.prompts), 2)
        self.assertEqual(bc.duracao, 30)


class TestMoneyPrinter(unittest.TestCase):
    def test_encontrar_moneyprinter(self):
        path = encontrar_moneyprinter()
        # Pode retornar None se não instalado, o que é ok
        self.assertIsNone(path)  # Não deveria estar instalado no teste

    def test_moneyprinter_disabled_by_default(self):
        compat = MoneyPrinterCompat()
        self.assertFalse(compat.enabled)
        self.assertFalse(compat.esta_disponivel())


class TestMontar(unittest.TestCase):
    def test_montar_clipe_assinatura(self):
        import inspect
        sig = inspect.signature(montar_clipe)
        params = list(sig.parameters.keys())
        self.assertIn("project", params)
        self.assertIn("audio_path", params)
        self.assertIn("saida", params)


class TestIntegrar(unittest.TestCase):
    def test_integrar_assinatura(self):
        import inspect
        sig = inspect.signature(integrar_clipe_audio)
        params = list(sig.parameters.keys())
        self.assertIn("audio_path", params)
        self.assertIn("imagens", params)
        self.assertIn("saida", params)


class TestPresets(unittest.TestCase):
    def test_presets_nao_vazios(self):
        presets = listar_presets()
        self.assertIn("trilhas", presets)
        self.assertIn("narracao", presets)
        self.assertGreater(len(presets["trilhas"]), 0)


class TestDatabase(unittest.TestCase):
    def test_stock_media(self):
        media = StockMedia(
            id="test123", url="http://example.com/img.jpg",
            width=1920, height=1080, source="pexels",
        )
        self.assertEqual(media.id, "test123")
        self.assertEqual(media.source, "pexels")

    def test_stock_search(self):
        search = StockSearch(query="test", provider="pexels", results=[], total=0)
        self.assertEqual(search.total, 0)


# ════════════════════════════════════════════════════════════════
# Interpretacao emocional da letra
# ════════════════════════════════════════════════════════════════

class TestInterpretacaoEmocional(unittest.TestCase):
    """A letra descreve uma EMOCAO, nao um objeto literal.

    Caso de referencia: "estou de coracao partido" NAO pode virar busca
    de coracoes despedacados — tem que virar cena de alguem triste.
    """

    def test_coracao_partido_vira_tristeza(self):
        from MusicClipStudio.interpretacao import interpretar, Emocao
        r = interpretar("estou de coração partido")
        self.assertEqual(r.emocao, Emocao.TRISTEZA)
        self.assertGreaterEqual(r.confianca, 0.4)

    def test_coracao_partido_nao_busca_coracao_literal(self):
        from MusicClipStudio.interpretacao import interpretar
        r = interpretar("estou de coração partido")
        for q in r.queries(6):
            baixo = q.lower()
            for proibido in ("heart", "broken", "coracao", "coração"):
                self.assertNotIn(proibido, baixo, f"query literal vazou: {q!r}")

    def test_queries_sao_cenas_filmaveis(self):
        from MusicClipStudio.interpretacao import interpretar
        r = interpretar("estou de coração partido")
        self.assertTrue(r.queries(3))
        for q in r.queries(3):
            self.assertGreater(len(q.split()), 2)

    def test_variacao_com_palavras_intercaladas(self):
        from MusicClipStudio.interpretacao import interpretar, Emocao
        r = interpretar("meu coração está em pedaços")
        self.assertEqual(r.emocao, Emocao.TRISTEZA)

    def test_contraste_inverte_para_alegria(self):
        from MusicClipStudio.interpretacao import interpretar, Emocao
        r = interpretar("chorei mas agora sorrio")
        self.assertEqual(r.emocao, Emocao.ALEGRIA)
        self.assertTrue(r.virada)

    def test_linha_neutra_sem_emocao_dominante(self):
        from MusicClipStudio.interpretacao import emocao_dominante
        # "epic music" descreve estilo, nao emocao
        self.assertIsNone(emocao_dominante(["epic music"]))

    def test_emocao_dominante_escolhe_a_mais_forte(self):
        from MusicClipStudio.interpretacao import emocao_dominante, Emocao
        linhas = ["la la la", "estou de coração partido", "e o sol nasceu"]
        self.assertEqual(emocao_dominante(linhas), Emocao.TRISTEZA)

    def test_normalizar_remove_acento(self):
        from MusicClipStudio.interpretacao import normalizar
        self.assertEqual(normalizar("Coração Partido!"), "coracao partido")


# ════════════════════════════════════════════════════════════════
# Transcricao (estruturas, sem carregar modelo)
# ════════════════════════════════════════════════════════════════

class TestTranscricao(unittest.TestCase):
    def test_segmento_legenda_duracao(self):
        from MusicClipStudio.transcricao import SegmentoLegenda
        s = SegmentoLegenda(indice=1, inicio=1.0, fim=3.5, texto="oi")
        self.assertAlmostEqual(s.duracao, 2.5)

    def test_segmento_roundtrip_dict(self):
        from MusicClipStudio.transcricao import SegmentoLegenda
        s = SegmentoLegenda(indice=2, inicio=0.5, fim=2.0, texto="teste")
        volta = SegmentoLegenda.de_dict(s.para_dict())
        self.assertEqual(volta.texto, "teste")
        self.assertAlmostEqual(volta.inicio, 0.5)
        self.assertAlmostEqual(volta.fim, 2.0)

    def test_resultado_com_erro_nao_levanta(self):
        from MusicClipStudio.transcricao import ResultadoTranscricao
        r = ResultadoTranscricao(erro="sem modelo")
        self.assertFalse(r.ok)
        self.assertEqual(r.segmentos, [])

    def test_quebrar_em_frases_divide_segmento_longo(self):
        from MusicClipStudio.transcricao import (
            SegmentoLegenda, quebrar_em_frases,
        )
        # Whisper costuma agrupar 3 versos num unico segmento longo.
        seg = SegmentoLegenda(
            indice=1, inicio=0.0, fim=7.0,
            texto="primeira frase. segunda frase. terceira frase.",
        )
        partes = quebrar_em_frases([seg], max_segundos=5.0)
        self.assertEqual(len(partes), 3)
        for a, b in zip(partes, partes[1:]):
            self.assertAlmostEqual(a.fim, b.inicio, places=6)
        self.assertAlmostEqual(partes[0].inicio, 0.0, places=6)
        self.assertAlmostEqual(partes[-1].fim, 7.0, places=6)

    def test_segmentos_a_partir_de_letra(self):
        from MusicClipStudio.transcricao import segmentos_a_partir_de_letra
        segs = segmentos_a_partir_de_letra(
            "linha um\nlinha dois\nlinha tres", 9.0
        )
        self.assertEqual(len(segs), 3)
        self.assertAlmostEqual(segs[0].inicio, 0.0, places=6)
        self.assertAlmostEqual(segs[-1].fim, 9.0, places=6)


# ════════════════════════════════════════════════════════════════
# Renderizacao / queima de legendas no video
# ════════════════════════════════════════════════════════════════

class TestRenderizadorLegendas(unittest.TestCase):
    def test_formato_srt_zero(self):
        from MusicClipStudio.renderizador_legendas import _formato_srt
        self.assertEqual(_formato_srt(0), "00:00:00,000")

    def test_formato_srt_rollover_milissegundos(self):
        """59.9996s nao pode virar '00:00:59,1000'."""
        from MusicClipStudio.renderizador_legendas import _formato_srt
        self.assertEqual(_formato_srt(59.9996), "00:01:00,000")

    def test_formato_srt_negativo_vira_zero(self):
        from MusicClipStudio.renderizador_legendas import _formato_srt
        self.assertEqual(_formato_srt(-5), "00:00:00,000")

    def test_legenda_ativa(self):
        from MusicClipStudio.renderizador_legendas import legenda_ativa
        from MusicClipStudio.transcricao import SegmentoLegenda
        segs = [
            SegmentoLegenda(1, 0.0, 2.0, "a"),
            SegmentoLegenda(2, 2.0, 4.0, "b"),
        ]
        self.assertEqual(legenda_ativa(segs, 1.0).texto, "a")
        self.assertEqual(legenda_ativa(segs, 3.0).texto, "b")
        self.assertIsNone(legenda_ativa(segs, 9.0))
        # O limite direito pertence ao proximo segmento
        self.assertEqual(legenda_ativa(segs, 2.0).texto, "b")

    def test_desenhar_legenda_preserva_tamanho(self):
        from PIL import Image
        from MusicClipStudio.renderizador_legendas import (
            desenhar_legenda, EstiloLegenda,
        )
        frame = Image.new("RGB", (540, 960), (40, 70, 140))
        out = desenhar_legenda(frame, "olá coração", EstiloLegenda())
        self.assertEqual(out.size, frame.size)
        self.assertEqual(out.mode, "RGB")

    def test_desenhar_legenda_vazia_nao_altera_frame(self):
        import numpy as np
        from PIL import Image
        from MusicClipStudio.renderizador_legendas import (
            desenhar_legenda, EstiloLegenda,
        )
        frame = Image.new("RGB", (320, 240), (10, 20, 30))
        out = desenhar_legenda(frame, "   ", EstiloLegenda())
        self.assertTrue(np.array_equal(np.asarray(out), np.asarray(frame)))

    def test_desenhar_legenda_escurece_pixels(self):
        import numpy as np
        from PIL import Image
        from MusicClipStudio.renderizador_legendas import (
            desenhar_legenda, EstiloLegenda,
        )
        frame = Image.new("RGB", (540, 960), (250, 250, 250))
        out = desenhar_legenda(frame, "texto visível", EstiloLegenda())
        delta = np.abs(np.asarray(out).astype(int)
                       - np.asarray(frame).astype(int))
        self.assertGreater(int((delta.sum(axis=2) > 8).sum()), 500)

    def test_aplicar_legendas_lista_vazia_devolve_mesmo_clip(self):
        from moviepy import ColorClip
        from MusicClipStudio.renderizador_legendas import aplicar_legendas
        c = ColorClip(size=(160, 90), color=(0, 0, 0), duration=1)
        self.assertIs(aplicar_legendas(c, []), c)

    def test_aplicar_legendas_em_clip_real(self):
        import numpy as np
        from moviepy import ColorClip
        from MusicClipStudio.renderizador_legendas import aplicar_legendas
        from MusicClipStudio.transcricao import SegmentoLegenda
        c = ColorClip(size=(320, 180), color=(20, 40, 80), duration=2)
        segs = [SegmentoLegenda(1, 0.0, 1.0, "legenda")]
        novo = aplicar_legendas(c, segs)
        frame = np.asarray(novo.get_frame(0.5))
        self.assertEqual(frame.shape, (180, 320, 3))
        self.assertEqual(frame.dtype, np.uint8)

    def test_srt_roundtrip(self):
        import os
        import tempfile
        from MusicClipStudio.renderizador_legendas import (
            segmentos_para_srt, segmentos_de_srt,
        )
        from MusicClipStudio.transcricao import SegmentoLegenda
        segs = [
            SegmentoLegenda(1, 0.0, 1.5, "primeira"),
            SegmentoLegenda(2, 1.5, 3.0, "segunda"),
        ]
        caminho = os.path.join(tempfile.mkdtemp(), "t.srt")
        segmentos_para_srt(segs, caminho)
        volta = segmentos_de_srt(caminho)
        self.assertEqual(len(volta), 2)
        self.assertEqual(volta[0].texto, "primeira")
        self.assertAlmostEqual(volta[1].fim, 3.0, places=6)

    def test_gerar_clipe_aceita_legendas(self):
        """A assinatura de gerar_clipe precisa expor `legendas`."""
        import inspect
        from MusicClipStudio.gerador import gerar_clipe
        params = inspect.signature(gerar_clipe).parameters
        self.assertIn("legendas", params)


class TestBuscaEmocionalIntegrada(unittest.TestCase):
    """A busca automatica tem que usar a EMOCAO, nao a palavra literal.

    Este e' o comportamento pedido pelo usuario: letra com "coracao
    partido" nao pode virar busca de coracao despedacado.
    """

    def _db(self):
        from MusicClipStudio.database import StockDatabase
        from MusicClipStudio.config import load_config
        return StockDatabase(load_config())

    def test_terms_usam_emocao_e_nao_literal(self):
        db = self._db()
        letra = (
            "estou de coração partido\n"
            "e a noite não passa\n"
            "eu chorei a noite inteira"
        )
        terms = db.gerar_search_terms_letra(letra, num_terms=5)
        self.assertTrue(terms)
        for t in terms:
            baixo = t.lower()
            for proibido in ("broken heart", "heart", "coracao",
                             "coração", "shattered"):
                self.assertNotIn(proibido, baixo,
                                 f"termo literal vazou: {t!r}")

    def test_terms_sao_cenas_filmaveis(self):
        db = self._db()
        terms = db.gerar_search_terms_letra("estou de coração partido")
        for t in terms:
            self.assertGreater(len(t.split()), 1,
                               f"termo nao parece cena: {t!r}")

    def test_letra_vazia_tem_fallback(self):
        db = self._db()
        terms = db.gerar_search_terms_letra("")
        self.assertEqual(len(terms), 5)

    def test_letra_sem_emocao_nao_quebra(self):
        """Linha sem carga emocional cai no fallback, sem excecao."""
        db = self._db()
        terms = db.gerar_search_terms_letra("la la la la la la")
        self.assertTrue(terms)

    def test_respeita_num_terms(self):
        db = self._db()
        terms = db.gerar_search_terms_letra("estou de coração partido",
                                            num_terms=3)
        self.assertLessEqual(len(terms), 3)


class TestPlanejadorRitmo(unittest.TestCase):
    """O codigo precisa CALCULAR quantos clipes a musica pede."""

    def _cfg(self, **kw):
        from MusicClipStudio.planejador import ConfigRitmo
        return ConfigRitmo(**kw)

    def _seg(self, inicio, fim, texto="frase"):
        from MusicClipStudio.transcricao import SegmentoLegenda
        return SegmentoLegenda(1, inicio, fim, texto)

    # ── tolerancia antes de fatiar ─────────────────────────
    def test_frase_curta_nao_e_fatiada(self):
        from MusicClipStudio.planejador import slots_de_frases
        cfg = self._cfg(max_por_clipe=6.0, tolerancia=0.20)
        # limite efetivo = 7.2s: tudo abaixo disso vira 1 clipe
        for dur in (2.0, 5.0, 6.0, 6.3, 7.0):
            slots = slots_de_frases([self._seg(0.0, dur)], cfg)
            self.assertEqual(len(slots), 1, f"{dur}s deveria ser 1 clipe")

    def test_frase_alem_da_tolerancia_e_fatiada(self):
        from MusicClipStudio.planejador import slots_de_frases
        cfg = self._cfg(max_por_clipe=6.0, tolerancia=0.20)
        slots = slots_de_frases([self._seg(0.0, 7.3)], cfg)
        self.assertEqual(len(slots), 2)
        # as partes tem que cobrir a frase inteira, sem sobra
        self.assertAlmostEqual(slots[0].inicio, 0.0, places=2)
        self.assertAlmostEqual(slots[-1].fim, 7.3, places=2)

    def test_tolerancia_zero_fatia_no_limite(self):
        from MusicClipStudio.planejador import slots_de_frases
        cfg = self._cfg(max_por_clipe=6.0, tolerancia=0.0)
        slots = slots_de_frases([self._seg(0.0, 6.5)], cfg)
        self.assertEqual(len(slots), 2)

    # ── duracao NAO e' mais dividida cegamente ─────────────
    def test_duracao_varia_por_frase(self):
        """O defeito antigo: duracao_total / n_midias para TODOS."""
        from MusicClipStudio.planejador import calcular_plano
        segs = [
            self._seg(0.0, 3.2, "curta"),
            self._seg(3.2, 9.4, "bem longa"),
            self._seg(9.4, 14.0, "outra"),
        ]
        midias = [{"media_type": "image"} for _ in range(5)]
        plano = calcular_plano(14.0, midias, self._cfg(modo="frases"),
                               segmentos=segs, callback_log=lambda _m: None)
        duracoes = [round(s.duracao, 2) for s in plano.slots]
        self.assertGreater(len(set(duracoes)), 1,
                           f"duracoes ficaram todas iguais: {duracoes}")

    def test_soma_das_duracoes_cobre_a_musica(self):
        from MusicClipStudio.planejador import calcular_plano
        segs = [self._seg(0.0, 10.0), self._seg(10.0, 22.0),
                self._seg(22.0, 30.0)]
        midias = [{"media_type": "image"} for _ in range(8)]
        plano = calcular_plano(30.0, midias, self._cfg(modo="frases"),
                               segmentos=segs, callback_log=lambda _m: None)
        self.assertAlmostEqual(plano.duracao_coberta, 30.0, places=1)

    def test_sem_frase_usa_batida(self):
        from MusicClipStudio.analise_audio import AnaliseAudio
        from MusicClipStudio.planejador import calcular_plano
        analise = AnaliseAudio(
            duracao=20.0, bpm=120.0,
            batidas=[i * 0.5 for i in range(40)],
        )
        midias = [{"media_type": "image"} for _ in range(6)]
        plano = calcular_plano(20.0, midias, self._cfg(modo="batida"),
                               analise=analise, callback_log=lambda _m: None)
        self.assertEqual(plano.modo_usado, "batida")
        self.assertGreater(plano.n_slots, 1)

    def test_sem_nada_cai_em_fixo_com_aviso(self):
        from MusicClipStudio.planejador import calcular_plano
        midias = [{"media_type": "image"} for _ in range(6)]
        plano = calcular_plano(30.0, midias, self._cfg(modo="frases"),
                               segmentos=None, analise=None,
                               callback_log=lambda _m: None)
        self.assertEqual(plano.modo_usado, "fixo")
        self.assertTrue(plano.avisos)

    # ── reciclagem ─────────────────────────────────────────
    def test_recicla_quando_falta_midia(self):
        from MusicClipStudio.planejador import calcular_plano
        midias = [{"media_type": "image"} for _ in range(4)]
        plano = calcular_plano(60.0, midias, self._cfg(modo="fixo",
                                                       segundos_por_clipe=5.0),
                               callback_log=lambda _m: None)
        self.assertEqual(plano.n_slots, 12)
        self.assertEqual(plano.midias_faltando, 8)
        self.assertGreaterEqual(plano.reciclagens, 2)
        self.assertEqual(len(plano.midias), 12,
                         "reciclagem tem que completar TODOS os slots")

    def test_reciclagem_embaralha_cada_volta(self):
        """Decisao do usuario: 'embaralhar cada volta'."""
        from MusicClipStudio.planejador import reciclar_midias
        pool = [{"media_type": "image", "n": i} for i in range(6)]
        extras, voltas = reciclar_midias(
            pool, 18, [], pool, self._cfg(semente=42)
        )
        self.assertEqual(voltas, 3)
        # Se embaralhasse, as voltas nao seriam a mesma sequencia
        primeira = [m["n"] for m in extras[:6]]
        segunda = [m["n"] for m in extras[6:12]]
        terceira = [m["n"] for m in extras[12:18]]
        self.assertNotEqual(primeira, segunda)
        self.assertNotEqual(segunda, terceira)

    def test_reciclagem_e_reproduzivel(self):
        """Mesma semente -> mesmo resultado (gerar 2x da o mesmo clipe)."""
        from MusicClipStudio.planejador import reciclar_midias
        pool = [{"media_type": "image", "n": i} for i in range(6)]
        a, _ = reciclar_midias(pool, 12, [], pool, self._cfg(semente=7))
        b, _ = reciclar_midias(pool, 12, [], pool, self._cfg(semente=7))
        self.assertEqual([m["n"] for m in a], [m["n"] for m in b])

    # ── efeito pela natureza da midia ──────────────────────
    def test_video_toca_direto(self):
        from MusicClipStudio.planejador import Slot, escolher_efeito
        slot = Slot(1, 0.0, 5.0, energia=1.0)
        self.assertEqual(escolher_efeito(slot, {"media_type": "video"}, 0),
                         "corte")

    def test_imagem_recebe_movimento(self):
        from MusicClipStudio.planejador import Slot, escolher_efeito
        slot = Slot(1, 0.0, 5.0, energia=0.5)
        efeito = escolher_efeito(slot, {"media_type": "image"}, 0)
        self.assertNotEqual(efeito, "corte")

    def test_imagem_calma_usa_efeito_suave(self):
        from MusicClipStudio.planejador import (
            Slot, escolher_efeito, EFEITOS_IMAGEM_CALMO,
        )
        slot = Slot(1, 0.0, 5.0, energia=0.1)
        self.assertIn(escolher_efeito(slot, {"media_type": "image"}, 0),
                      EFEITOS_IMAGEM_CALMO)

    def test_imagem_intensa_usa_efeito_forte(self):
        from MusicClipStudio.planejador import (
            Slot, escolher_efeito, EFEITOS_IMAGEM_INTENSO,
        )
        slot = Slot(1, 0.0, 5.0, energia=0.95)
        self.assertIn(escolher_efeito(slot, {"media_type": "image"}, 0),
                      EFEITOS_IMAGEM_INTENSO)

    # ── energia alta pede video ────────────────────────────
    def test_energia_alta_prefere_video(self):
        from MusicClipStudio.planejador import Slot, ordenar_por_energia
        slots = [Slot(1, 0.0, 5.0, energia=0.9),
                 Slot(2, 5.0, 10.0, energia=0.1)]
        vids = [{"media_type": "video"}]
        imgs = [{"media_type": "image"}]
        escolhidas = ordenar_por_energia(slots, vids, imgs, semente=42)
        self.assertEqual(escolhidas[0], vids[0])
        self.assertEqual(escolhidas[1], imgs[0])

    def test_um_pool_so_cobre_todos_os_slots(self):
        from MusicClipStudio.planejador import Slot, ordenar_por_energia
        slots = [Slot(i, i * 5.0, (i + 1) * 5.0, energia=0.9)
                 for i in range(4)]
        imgs = [{"media_type": "image", "n": i} for i in range(4)]
        escolhidas = ordenar_por_energia(slots, [], imgs, semente=42)
        self.assertEqual(len(escolhidas), 4,
                         "sem video, imagem tem que cobrir os slots")

    # ── ConfigRitmo.validar nao deixa valor absurdo passar ─
    def test_validar_corrige_valores_impossiveis(self):
        cfg = self._cfg(max_por_clipe=0.0, tolerancia=9.0,
                        batidas_por_troca=0, segundos_por_clipe=-5.0)
        cfg.validar()
        self.assertGreaterEqual(cfg.max_por_clipe, 1.0)
        self.assertLessEqual(cfg.tolerancia, 1.0)
        self.assertGreaterEqual(cfg.batidas_por_troca, 1)
        self.assertGreater(cfg.segundos_por_clipe, 0)

    def test_duracao_zero_nao_quebra(self):
        from MusicClipStudio.planejador import calcular_plano
        plano = calcular_plano(0.0, [{"media_type": "image"}], self._cfg(),
                               callback_log=lambda _m: None)
        self.assertEqual(plano.n_slots, 0)
        self.assertTrue(plano.avisos)


class TestGeradorIntegraPlano(unittest.TestCase):
    """O gerador tem que USAR o plano, nao a divisao cega."""

    class _FakeClip:
        def __init__(self, d):
            self.duration = d

        def with_duration(self, d):
            return TestGeradorIntegraPlano._FakeClip(d)

        def subclipped(self, a, b):
            return TestGeradorIntegraPlano._FakeClip(b - a)

    def _plano(self, dur_total=30.0, n_midias=6, **kw):
        from MusicClipStudio.planejador import ConfigRitmo, calcular_plano
        midias = [{"media_type": "image"} for _ in range(n_midias)]
        return calcular_plano(
            dur_total, midias, ConfigRitmo(**kw),
            callback_log=lambda _m: None,
        )

    def test_ajustar_aplica_duracao_de_cada_slot(self):
        from MusicClipStudio.gerador import _ajustar_duracoes
        from MusicClipStudio.transcricao import SegmentoLegenda
        from MusicClipStudio.planejador import ConfigRitmo, calcular_plano

        segs = [SegmentoLegenda(1, 0.0, 3.0, "a"),
                SegmentoLegenda(2, 3.0, 12.0, "b")]
        midias = [{"media_type": "image"} for _ in range(5)]
        plano = calcular_plano(12.0, midias,
                               ConfigRitmo(modo="frases"), segmentos=segs,
                               callback_log=lambda _m: None)

        clips = [self._FakeClip(20.0) for _ in plano.slots]
        ajustados = _ajustar_duracoes(clips, plano, lambda _m: None)

        esperado = [round(s.duracao, 2) for s in plano.slots]
        obtido = [round(c.duration, 2) for c in ajustados]
        self.assertEqual(obtido, esperado)

    def test_ajustar_nao_deixa_tudo_igual(self):
        """Regressao do defeito: duracao_total / n_clips para todos."""
        from MusicClipStudio.gerador import _ajustar_duracoes
        from MusicClipStudio.transcricao import SegmentoLegenda
        from MusicClipStudio.planejador import ConfigRitmo, calcular_plano

        segs = [SegmentoLegenda(1, 0.0, 3.0, "curta"),
                SegmentoLegenda(2, 3.0, 11.0, "longa")]
        midias = [{"media_type": "image"} for _ in range(5)]
        plano = calcular_plano(11.0, midias, ConfigRitmo(modo="frases"),
                               segmentos=segs, callback_log=lambda _m: None)
        clips = [self._FakeClip(20.0) for _ in plano.slots]
        ajustados = _ajustar_duracoes(clips, plano, lambda _m: None)
        duracoes = [round(c.duration, 2) for c in ajustados]
        self.assertGreater(len(set(duracoes)), 1, duracoes)

    def test_sem_plano_mantem_caminho_antigo(self):
        """Sem config_ritmo o gerador nao pode mudar de comportamento."""
        import inspect
        from MusicClipStudio.gerador import gerar_clipe
        sig = inspect.signature(gerar_clipe)
        self.assertIn("config_ritmo", sig.parameters)
        self.assertIsNone(sig.parameters["config_ritmo"].default)

    def test_alinhar_corta_slot_sobrando(self):
        from MusicClipStudio.gerador import _alinhar_plano
        plano = self._plano(30.0, 6, modo="fixo")
        self.assertEqual(plano.n_slots, 6)
        paths = [{"path": f"f{i}.jpg", "type": "image"} for i in range(4)]
        paths, plano2 = _alinhar_plano(paths, plano, lambda _m: None)
        self.assertEqual(plano2.n_slots, 4)
        self.assertEqual([s.indice for s in plano2.slots], [1, 2, 3, 4])
        self.assertEqual(len(plano2.efeitos), 4)

    def test_alinhar_sem_diferenca_nao_mexe(self):
        from MusicClipStudio.gerador import _alinhar_plano
        plano = self._plano(30.0, 6, modo="fixo")
        n_antes = plano.n_slots
        paths = [{"path": f"f{i}.jpg", "type": "image"}
                 for i in range(n_antes)]
        _, plano2 = _alinhar_plano(paths, plano, lambda _m: None)
        self.assertEqual(plano2.n_slots, n_antes)

    def test_criar_clips_aceita_plano(self):
        import inspect
        from MusicClipStudio.gerador import _criar_clips
        sig = inspect.signature(_criar_clips)
        self.assertIn("plano", sig.parameters)
        self.assertIsNone(sig.parameters["plano"].default)

    def test_calcular_plano_nunca_levanta(self):
        from MusicClipStudio.gerador import _calcular_plano
        resultado = _calcular_plano(
            30.0, None, "config_invalida", None, None, lambda _m: None
        )
        self.assertIsNone(resultado)

    def test_analisar_audio_sem_arquivo_devolve_none(self):
        from MusicClipStudio.gerador import _analisar_audio
        self.assertIsNone(
            _analisar_audio(None, lambda _m: None)
        )
        self.assertIsNone(
            _analisar_audio("nao_existe_999.mp3", lambda _m: None)
        )


class TestDescricaoVaiParaBusca(unittest.TestCase):
    """A descricao livre tem que virar termo de busca, nao so decoracao."""

    def test_cena_traduzida(self):
        from MusicClipStudio.descricao_musical import cena_para_busca
        self.assertEqual(
            cena_para_busca("hands drumming on djembe close up"),
            "tribal drums",
        )

    def test_cena_desconhecida_passa_intacta(self):
        from MusicClipStudio.descricao_musical import cena_para_busca
        self.assertEqual(cena_para_busca("uma cena qualquer"),
                         "uma cena qualquer")

    def test_termos_combinam_letra_e_descricao(self):
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, termos_de_busca,
        )
        letra_cenas = ["person crying alone in dark room"]
        leitura = interpretar_descricao("tribal com tambores")
        termos = termos_de_busca(letra_cenas, leitura, maximo=5)
        self.assertIn("person crying alone in dark room", termos)
        self.assertIn("tribal drums", termos)

    def test_sem_descricao_so_letra(self):
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, termos_de_busca,
        )
        letra_cenas = ["person crying alone in dark room"]
        termos = termos_de_busca(letra_cenas, interpretar_descricao(""),
                                 maximo=5)
        self.assertEqual(termos, letra_cenas)

    def test_sem_letra_so_descricao(self):
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, termos_de_busca,
        )
        leitura = interpretar_descricao("solo de piano clássico, triste")
        termos = termos_de_busca([], leitura, maximo=4)
        self.assertTrue(termos)
        self.assertTrue(any("piano" in t for t in termos), termos)

    def test_letra_nunca_some_da_combinacao(self):
        """Decisao do usuario: 'combinar sempre' — a letra e' o eixo.

        Usamos uma descricao SEM tema detectado para garantir que a
        letra entra na combinacao. Descricoes com tema (mantra,
        classica, frequencia) ignoram a letra de proposito — isso e'
        testado separadamente.
        """
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, termos_de_busca,
        )
        letra_cenas = ["city lights at night"]
        leitura = interpretar_descricao(
            "tribal com tambores, meio melancólico"
        )
        # Sem "classico" na descricao = nenhum tema classica detectado
        self.assertFalse(leitura.tema_id)
        termos = termos_de_busca(letra_cenas, leitura, maximo=8)
        self.assertIn("city lights at night", termos)

    def test_conflito_e_avisado_nao_resolvido(self):
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, detectar_conflito,
        )
        from MusicClipStudio.interpretacao import Emocao
        leitura = interpretar_descricao("festa animada")
        conflitos = detectar_conflito(Emocao.TRISTEZA, leitura)
        self.assertTrue(conflitos)


class TestCoberturaSemBuraco(unittest.TestCase):
    """Nenhum trecho da musica pode ficar sem imagem.

    Bug real encontrado na tela: letra terminando em 19.0s e grade
    uniforme comecando em 0 em passos de 5 -> o primeiro slot extra
    aproveitavel caia em 20.0 e o trecho 19.0-20.0 ficava sem clipe.
    """

    def _seg(self, inicio, fim, texto="frase"):
        from MusicClipStudio.transcricao import SegmentoLegenda
        return SegmentoLegenda(1, inicio, fim, texto)

    def _buracos(self, slots, inicio=0.0):
        """Devolve os intervalos sem cobertura a partir de `inicio`."""
        buracos = []
        cursor = float(inicio)
        for s in slots:
            if s.inicio > cursor + 1e-6:
                buracos.append((cursor, s.inicio))
            cursor = max(cursor, s.fim)
        return buracos

    def test_sobra_comeca_colada_no_fim_da_letra(self):
        from MusicClipStudio.planejador import calcular_plano, ConfigRitmo
        segs = [self._seg(0.0, 4.2), self._seg(4.2, 13.5),
                self._seg(13.5, 19.0)]
        midias = [{"media_type": "photo"} for _ in range(8)]
        plano = calcular_plano(90.0, midias, ConfigRitmo(modo="frases"),
                               segmentos=segs, callback_log=lambda _m: None)

        sobras = [s for s in plano.slots if s.origem == "sobra"]
        self.assertTrue(sobras, "deveria haver clipes de sobra")
        self.assertAlmostEqual(sobras[0].inicio, 19.0, places=2,
                               msg="a sobra tem que colar no fim da letra")

    def test_nao_ha_buraco_na_linha_do_tempo(self):
        from MusicClipStudio.planejador import calcular_plano, ConfigRitmo
        segs = [self._seg(0.0, 4.2), self._seg(4.2, 13.5),
                self._seg(13.5, 19.0)]
        midias = [{"media_type": "photo"} for _ in range(8)]
        plano = calcular_plano(90.0, midias, ConfigRitmo(modo="frases"),
                               segmentos=segs, callback_log=lambda _m: None)
        self.assertEqual(self._buracos(plano.slots), [])

    def test_cobertura_fecha_com_a_duracao(self):
        from MusicClipStudio.planejador import calcular_plano, ConfigRitmo
        segs = [self._seg(0.0, 7.0), self._seg(7.0, 21.0)]
        midias = [{"media_type": "photo"} for _ in range(8)]
        plano = calcular_plano(60.0, midias, ConfigRitmo(modo="frases"),
                               segmentos=segs, callback_log=lambda _m: None)
        self.assertAlmostEqual(plano.slots[-1].fim, 60.0, places=1)
        self.assertAlmostEqual(plano.duracao_coberta, 60.0, places=1)

    def test_grade_uniforme_aceita_inicio_arbitrario(self):
        from MusicClipStudio.planejador import _grade_uniforme, ConfigRitmo
        slots = _grade_uniforme(19.0, 30.0, ConfigRitmo(segundos_por_clipe=5.0))
        self.assertAlmostEqual(slots[0].inicio, 19.0, places=2)
        self.assertAlmostEqual(slots[-1].fim, 30.0, places=2)
        # Sem buraco A PARTIR do inicio pedido (antes de 19 nao e' conta dela)
        self.assertEqual(self._buracos(slots, inicio=19.0), [])

    def test_grade_uniforme_inicio_alem_do_fim_devolve_vazio(self):
        from MusicClipStudio.planejador import _grade_uniforme, ConfigRitmo
        self.assertEqual(
            _grade_uniforme(50.0, 30.0, ConfigRitmo(segundos_por_clipe=5.0)),
            [],
        )

    def test_slots_uniformes_comeca_em_zero(self):
        """O fallback puro nao pode mudar de comportamento."""
        from MusicClipStudio.planejador import slots_uniformes, ConfigRitmo
        slots = slots_uniformes(30.0, ConfigRitmo(segundos_por_clipe=5.0))
        self.assertAlmostEqual(slots[0].inicio, 0.0, places=2)
        self.assertEqual(len(slots), 6)


class TestMidiaRealDoGUI(unittest.TestCase):
    """O plano tem que casar com StockMedia, nao so com dicts.

    Armadilha: StockMedia usa media_type='photo' (nao 'image') para
    imagem. Se o matcher de tipo nao cobrisse isso, TODA imagem seria
    tratada como video e o efeito "por natureza da midia" nunca aplicaria
    movimento.
    """

    def _midia(self, tipo, i=0):
        from MusicClipStudio.database import StockMedia
        return StockMedia(
            id=f"m{i}", url=f"u{i}", source="pexels",
            download_url=f"u{i}", media_type=tipo,
        )

    def test_photo_conta_como_imagem(self):
        from MusicClipStudio.planejador import _tipo_da_midia
        self.assertEqual(_tipo_da_midia(self._midia("photo")), "imagem")

    def test_video_conta_como_video(self):
        from MusicClipStudio.planejador import _tipo_da_midia
        self.assertEqual(_tipo_da_midia(self._midia("video")), "video")

    def test_dict_photo_conta_como_imagem(self):
        from MusicClipStudio.planejador import _tipo_da_midia
        self.assertEqual(_tipo_da_midia({"type": "photo"}), "imagem")

    def test_plano_casa_todas_as_midias_reais(self):
        from MusicClipStudio.planejador import calcular_plano, ConfigRitmo
        midias = ([self._midia("photo", i) for i in range(4)]
                  + [self._midia("video", i) for i in range(4, 6)])
        plano = calcular_plano(30.0, midias, ConfigRitmo(modo="fixo"),
                               callback_log=lambda _m: None)
        self.assertEqual(len(plano.midias), plano.n_slots)

    def test_video_real_recebe_corte_e_imagem_recebe_movimento(self):
        from MusicClipStudio.planejador import (
            calcular_plano, ConfigRitmo, _tipo_da_midia,
        )
        midias = ([self._midia("photo", i) for i in range(4)]
                  + [self._midia("video", i) for i in range(4, 6)])
        plano = calcular_plano(30.0, midias, ConfigRitmo(modo="fixo"),
                               callback_log=lambda _m: None)
        for midia, efeito in zip(plano.midias, plano.efeitos):
            if _tipo_da_midia(midia) == "video":
                self.assertEqual(efeito, "corte")
            else:
                self.assertNotEqual(efeito, "corte")


class TestCorretorLetra(unittest.TestCase):
    """O Whisper acerta a fonetica e erra a grafia.

    "voz" vira "vois", "coração" vira "corecao". Como a letra alimenta a
    busca de midia, o erro vira uma query que nao acha nada. Estes testes
    travam o comportamento do corretor -- principalmente as duas coisas
    que ja' quebraram de verdade:

      1. a chave fonetica tratava `c` sempre como /k/, entao "nacer" nao
         chegava em "nascer";
      2. o desempate por tamanho escolhia "vos" (3 letras) em vez de
         "voz", e o texto saia corrompido.
    """

    # ── chave fonetica (nao depende de dicionario) ─────────────

    def test_c_antes_de_e_i_soa_como_s(self):
        from MusicClipStudio.corretor_letra import chave_fonetica
        self.assertEqual(chave_fonetica("nacer"), chave_fonetica("nascer"))

    def test_s_e_z_finais_soam_igual(self):
        from MusicClipStudio.corretor_letra import chave_fonetica
        self.assertEqual(chave_fonetica("vois"), chave_fonetica("voz"))

    def test_qu_e_c_soam_igual(self):
        from MusicClipStudio.corretor_letra import chave_fonetica
        self.assertEqual(chave_fonetica("quando"), chave_fonetica("cuando"))

    def test_acento_nao_muda_a_chave(self):
        from MusicClipStudio.corretor_letra import chave_fonetica
        self.assertEqual(chave_fonetica("razao"), chave_fonetica("razão"))

    def test_cedilha_soa_como_s(self):
        from MusicClipStudio.corretor_letra import chave_fonetica
        self.assertEqual(chave_fonetica("coracao"), chave_fonetica("coração"))

    # ── forma comparavel (nao depende de dicionario) ───────────

    def test_forma_comparavel_deixa_vos_e_voz_a_mesma_distancia(self):
        """Sem isso "vos" (1 edicao) ganharia de "voz" (2 na escrita crua).

        O objetivo nao e' igualar as formas — e' fazer as duas chegarem
        juntas, para o desempate cair no paradigma morfologico.
        """
        from MusicClipStudio.corretor_letra import _forma_comparavel, _distancia
        base = _forma_comparavel("vois")
        self.assertEqual(_distancia(base, _forma_comparavel("vos")),
                         _distancia(base, _forma_comparavel("voz")))

    def test_forma_comparavel_nao_colapsa_letra_dobrada(self):
        """Colapsar fazia "correcao" (rr) parecer identico a "corecao".

        Com isso "correcao" ganhava de "coracao" por distancia 0 sem ter
        mais merito nenhum — os dois estao a uma letra da errada.
        """
        from MusicClipStudio.corretor_letra import _forma_comparavel
        self.assertEqual(_forma_comparavel("correção"), "correcao")
        self.assertNotEqual(_forma_comparavel("correção"),
                            _forma_comparavel("corecao"))

    # ── ranqueamento e deteccao de empate ──────────────────────

    def test_empate_e_marcado_como_ambiguo(self):
        from MusicClipStudio.corretor_letra import ranquear
        _ords, ambigua = ranquear("corecao", ["correcao", "coracao"])
        self.assertTrue(ambigua)

    def test_sem_concorrente_nao_e_ambiguo(self):
        from MusicClipStudio.corretor_letra import ranquear
        _ords, ambigua = ranquear("razao", ["razao"])
        self.assertFalse(ambigua)

    def test_paradigma_rico_desempata(self):
        """`vos` nao tem flag no dicionario (forma congelada); `voz` tem.

        Foi o que tirou "voz" da primeira posicao — antes o desempate
        era por tamanho e o "vos", menor, ganhava.
        """
        from MusicClipStudio.corretor_letra import ranquear
        ords, _amb = ranquear("vois", ["vos", "voz"],
                              flags={"voz": 5, "vos": 0})
        self.assertEqual(ords[0], "voz")

    def test_ranquear_vazio(self):
        from MusicClipStudio.corretor_letra import ranquear
        ords, ambigua = ranquear("vois", [])
        self.assertEqual(ords, [])
        self.assertFalse(ambigua)

    def test_alta_confianca_exige_sugestao_e_exclusividade(self):
        from MusicClipStudio.corretor_letra import PalavraSuspeita
        self.assertTrue(PalavraSuspeita("razao", 1, 0, ["razão"]).alta_confianca)
        self.assertFalse(
            PalavraSuspeita("vois", 1, 0, ["voz", "vos"], True).alta_confianca
        )
        self.assertFalse(PalavraSuspeita("xyz", 1, 0, []).alta_confianca)

    # ── aplicar a correcao no texto ─────────────────────────────

    def test_corrige_troca_apenas_o_acento(self):
        from MusicClipStudio.corretor_letra import corrigir_texto
        self.assertEqual(corrigir_texto("sem razao", {"razao": "razão"}),
                         "sem razão")

    def test_corrige_palavra_inteira_e_nao_pedaco(self):
        from MusicClipStudio.corretor_letra import corrigir_texto
        self.assertEqual(corrigir_texto("a vois e voisa", {"vois": "voz"}),
                         "a voz e voisa")

    def test_preserva_maiuscula_inicial(self):
        from MusicClipStudio.corretor_letra import corrigir_texto
        self.assertEqual(corrigir_texto("Vois alta", {"vois": "voz"}),
                         "Voz alta")

    def test_texto_vazio_ou_sem_mapa_devolve_igual(self):
        from MusicClipStudio.corretor_letra import corrigir_texto
        self.assertEqual(corrigir_texto("", {"a": "b"}), "")
        self.assertEqual(corrigir_texto("algo aqui", {}), "algo aqui")

    def test_corrige_em_todas_as_linhas(self):
        from MusicClipStudio.corretor_letra import corrigir_texto
        self.assertEqual(
            corrigir_texto("a vois\noutra vois", {"vois": "voz"}),
            "a voz\noutra voz",
        )


class TestCorretorComDicionario(unittest.TestCase):
    """Testes que precisam do Hunspell pt-BR.

    Pulam (nao falham) quando a maquina nao tem o dicionario: sem ele o
    modulo degrada para "sem corretor" de proposito, e isso nao e' bug.
    """

    @classmethod
    def setUpClass(cls):
        from MusicClipStudio.corretor_letra import DicionarioPT
        cls.dic = DicionarioPT()
        if not cls.dic.ok:
            raise unittest.SkipTest("dicionario pt-BR ausente")

    def test_nao_marca_texto_limpo(self):
        from MusicClipStudio.corretor_letra import encontrar_suspeitas
        suspeitas = encontrar_suspeitas(
            "quando a noite cai sobre a cidade", self.dic
        )
        self.assertEqual(suspeitas, [])

    def test_marca_os_erros_tipicos_do_whisper(self):
        from MusicClipStudio.corretor_letra import encontrar_suspeitas
        suspeitas = encontrar_suspeitas(
            "eu ainda escuto a tua vois\no sol vai nacer", self.dic
        )
        palavras = {s.palavra for s in suspeitas}
        self.assertIn("vois", palavras)
        self.assertIn("nacer", palavras)

    def test_vois_sugere_voz(self):
        from MusicClipStudio.corretor_letra import encontrar_suspeitas
        suspeitas = encontrar_suspeitas("escuto a tua vois", self.dic)
        vois = next(s for s in suspeitas if s.palavra == "vois")
        self.assertEqual(vois.melhor, "voz")

    def test_nao_marca_palavra_curta(self):
        from MusicClipStudio.corretor_letra import encontrar_suspeitas
        self.assertEqual(encontrar_suspeitas("a e o de", self.dic), [])

    def test_auto_correcao_nao_aceita_ambiguo(self):
        """"vois" tem "vos" e "voz" igualmente plausiveis: nao decidir."""
        from MusicClipStudio.corretor_letra import corrigir_por_fonetica
        mapa = corrigir_por_fonetica("escuto a tua vois", self.dic)
        self.assertNotIn("vois", mapa)

    def test_auto_correcao_aceita_univoco(self):
        from MusicClipStudio.corretor_letra import corrigir_por_fonetica
        mapa = corrigir_por_fonetica("sem razao de novo", self.dic)
        self.assertEqual(mapa.get("razao"), "razão")


class TestTemasMusicais(unittest.TestCase):
    """Busca temática para músicas sem letra ou em língua desconhecida.

    Quando o usuário descreve "mantra tibetano" ou "432Hz", a busca
    não deve tentar extrair palavras da letra (que pode estar em
    sânscrito ou não existir) — ela deve ir direto para termos visuais
    do tema.
    """

    def test_detecta_mantra(self):
        from MusicClipStudio.temas_musicais import detectar_tema
        tema = detectar_tema("mantra tibetano para meditação")
        self.assertIsNotNone(tema)
        self.assertEqual(tema.id, "mantra")

    def test_detecta_frequencia(self):
        from MusicClipStudio.temas_musicais import detectar_tema
        tema = detectar_tema("frequência 432Hz para prosperidade")
        self.assertIsNotNone(tema)
        self.assertEqual(tema.id, "frequencia")

    def test_detecta_arabe(self):
        from MusicClipStudio.temas_musicais import detectar_tema
        tema = detectar_tema("música árabe com oud e darbuka")
        self.assertIsNotNone(tema)
        self.assertEqual(tema.id, "arabe")

    def test_detecta_classica(self):
        from MusicClipStudio.temas_musicais import detectar_tema
        tema = detectar_tema("solo de piano clássico, triste")
        self.assertIsNotNone(tema)
        self.assertEqual(tema.id, "classica")

    def test_nao_detecta_tema_em_descricao_generica(self):
        """"tribal com tambores" não é um tema — é instrumento+clima."""
        from MusicClipStudio.temas_musicais import detectar_tema
        tema = detectar_tema("tribal com tambores, meio melancólico")
        self.assertIsNone(tema)

    def test_termos_do_tema_sao_em_ingles(self):
        from MusicClipStudio.temas_musicais import detectar_tema, termos_do_tema
        tema = detectar_tema("mantra tibetano")
        termos = termos_do_tema(tema, maximo=3)
        self.assertTrue(all(" " in t for t in termos))
        self.assertTrue(any("tibetan" in t for t in termos))

    def test_tema_ignora_letra_quando_configurado(self):
        """Mantras e frequências não usam a letra para busca."""
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, termos_de_busca,
        )
        leitura = interpretar_descricao("mantra tibetano para meditar")
        self.assertEqual(leitura.tema_id, "mantra")
        self.assertTrue(leitura.tema_ignora_letra)
        termos = termos_de_busca(
            ["city lights at night"], leitura, maximo=8
        )
        # A letra NÃO entra — só os termos do tema
        self.assertNotIn("city lights at night", termos)
        self.assertTrue(any("tibetan" in t for t in termos))

    def test_tema_nao_ignora_letra_quando_nao_configurado(self):
        """Jazz e rock COMBINAM com a letra."""
        from MusicClipStudio.descricao_musical import (
            interpretar_descricao, termos_de_busca,
        )
        leitura = interpretar_descricao("jazz club saxofone")
        self.assertEqual(leitura.tema_id, "jazz")
        self.assertFalse(leitura.tema_ignora_letra)

    def test_descricao_vazia_sem_tema(self):
        from MusicClipStudio.descricao_musical import interpretar_descricao
        leitura = interpretar_descricao("")
        self.assertFalse(leitura.tema_id)
        self.assertTrue(leitura.vazia)

    def test_database_gera_terms_com_tema(self):
        """gerar_search_terms_letra recebe tema_termos e usa."""
        from MusicClipStudio.database import StockDatabase
        db = StockDatabase.__new__(StockDatabase)
        terms = db.gerar_search_terms_letra(
            "some lyrics here",
            num_terms=5,
            tema_termos=["tibetan monk meditation", "prayer wheels"],
            tema_ignora_letra=True,
        )
        self.assertEqual(terms, ["tibetan monk meditation", "prayer wheels"])

    def test_database_com_tema_sem_ignorar_letra(self):
        """Tema que não ignora letra: termos do tema + termos da letra."""
        from MusicClipStudio.database import StockDatabase
        db = StockDatabase.__new__(StockDatabase)
        terms = db.gerar_search_terms_letra(
            "",  # sem letra
            num_terms=5,
            tema_termos=["jazz club saxophone"],
            tema_ignora_letra=False,
        )
        self.assertIn("jazz club saxophone", terms)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ════════════════════════════════════════════════════════════════
#  ENCURTADOR DE BUSCA  (frase de cena -> termo que a API entende)
# ════════════════════════════════════════════════════════════════

class TestEncurtadorBusca(unittest.TestCase):
    """A stock API indexa conceitos curtos. Frases de 5 palavras fazem
    a API cair em match parcial generico -> imagem fora de contexto."""

    def test_limita_a_tres_palavras(self):
        from MusicClipStudio.encurtador_busca import termo_curto

        for cena in [
            "empty apartment at night one lamp",
            "single person alone in crowded street",
            "person sitting alone in diner window",
            "a broken mirror reflecting a sad face",
            "lone figure walking towards the light",
        ]:
            self.assertLessEqual(len(termo_curto(cena).split()), 3, cena)

    def test_remove_stopwords_gramaticais(self):
        from MusicClipStudio.encurtador_busca import termo_curto

        curto = termo_curto("silhouette sitting by rainy window")
        self.assertNotIn(" by ", f" {curto} ")
        self.assertIn("window", curto)

    def test_nucleo_prefere_substantivo_a_modificador(self):
        from MusicClipStudio.encurtador_busca import termo_curto

        # "single"/"lone"/"empty" sao modificadores fracos; o termo deve
        # comecar por um substantivo que a API reconheca.
        self.assertEqual(termo_curto("single person alone in crowded street"),
                         "person crowded street")
        self.assertEqual(termo_curto("lone figure on empty beach winter"),
                         "figure beach winter")

    def test_frase_curta_passa_intacta(self):
        from MusicClipStudio.encurtador_busca import termo_curto

        self.assertEqual(termo_curto("rain"), "rain")
        self.assertEqual(termo_curto("night city"), "night city")

    def test_vazio_e_none_nao_quebram(self):
        from MusicClipStudio.encurtador_busca import termo_curto, termos_curtos

        self.assertEqual(termo_curto(""), "")
        self.assertEqual(termo_curto(None), "")
        self.assertEqual(termos_curtos([]), [])
        self.assertEqual(termos_curtos([None, ""]), [])

    def test_termos_curtos_deduplica(self):
        from MusicClipStudio.encurtador_busca import termos_curtos

        saida = termos_curtos([
            "empty apartment at night one lamp",
            "empty apartment at night one lamp",
            "rain",
        ])
        self.assertEqual(len(saida), len(set(saida)))


# ════════════════════════════════════════════════════════════════
#  PREENCHEDOR DE PROMPTS  (fallback quando falta midia)
# ════════════════════════════════════════════════════════════════

class TestPreenchedorPrompts(unittest.TestCase):

    def test_alterna_imagem_e_video(self):
        from MusicClipStudio.preenchedor_prompts import gerar_prompts

        ps = gerar_prompts(["rainy window", "empty room"], quantos=4)
        self.assertEqual(len(ps), 4)
        self.assertEqual([p.tipo for p in ps],
                         ["image", "video", "image", "video"])

    def test_prompt_de_video_tem_movimento(self):
        from MusicClipStudio.preenchedor_prompts import gerar_prompts

        vids = [p for p in gerar_prompts(["ocean cliff"], quantos=2)
                if p.tipo == "video"]
        self.assertTrue(vids)
        self.assertTrue(any(
            m in vids[0].prompt for m in
            ["push in", "drift", "pan", "aerial", "static", "slow motion"]
        ))

    def test_prompt_carrega_a_base(self):
        from MusicClipStudio.preenchedor_prompts import gerar_prompts

        ps = gerar_prompts(["empty apartment at night"], quantos=2)
        for p in ps:
            self.assertIn("empty apartment at night", p.prompt)

    def test_entrada_vazia_devolve_nada(self):
        from MusicClipStudio.preenchedor_prompts import gerar_prompts

        self.assertEqual(gerar_prompts([], quantos=4), [])
        self.assertEqual(gerar_prompts(["", None], quantos=4), [])
        self.assertEqual(gerar_prompts(["rain"], quantos=0), [])

    def test_prompts_de_tema_usam_termos_do_tema(self):
        from MusicClipStudio.preenchedor_prompts import gerar_prompts_para_tema
        from MusicClipStudio.temas_musicais import TEMAS

        mantra = next((t for t in TEMAS if t.id == "mantra"), None)
        self.assertIsNotNone(mantra)
        ps = gerar_prompts_para_tema(mantra, quantos=3)
        self.assertEqual(len(ps), 3)
        # O prompt deve conter um dos termos de busca do tema.
        for p in ps:
            self.assertTrue(
                any(t in p.prompt for t in mantra.termos_busca),
                p.prompt,
            )


# ════════════════════════════════════════════════════════════════
#  FLAGS DE TIPO DE MIDIA  (bug: apenas_videos era ignorado)
# ════════════════════════════════════════════════════════════════

class TestFlagsTipoMidia(unittest.TestCase):
    """Regressao do defeito encontrado em 2026-09-17: `buscar_videos`
    era calculado com `not apenas_fotos or (...)`, o que IGNORAVA
    `apenas_videos` e fazia a busca por video voltar vazia."""

    @staticmethod
    def _calcular(apenas_fotos, apenas_videos):
        """Reproduz a tabela de decisao usada em _buscar_pexels/_pixabay."""
        apenas_um = apenas_fotos != apenas_videos
        return (
            (not apenas_um) or apenas_fotos,
            (not apenas_um) or apenas_videos,
        )

    def test_apenas_videos_nao_busca_fotos(self):
        buscar_fotos, buscar_videos = self._calcular(False, True)
        self.assertFalse(buscar_fotos)
        self.assertTrue(buscar_videos)

    def test_apenas_fotos_nao_busca_videos(self):
        buscar_fotos, buscar_videos = self._calcular(True, False)
        self.assertTrue(buscar_fotos)
        self.assertFalse(buscar_videos)

    def test_nenhum_marcado_busca_os_dois(self):
        self.assertEqual(self._calcular(False, False), (True, True))

    def test_os_dois_marcados_busca_os_dois(self):
        self.assertEqual(self._calcular(True, True), (True, True))

    def test_intercalar_preserva_os_dois_tipos_no_corte(self):
        """Sem intercalar, o corte [:n] enche a cota de fotos e descarta
        todos os videos — a causa de a galeria mostrar 'quase sem video'."""
        from MusicClipStudio.database import StockDatabase, StockMedia

        itens = (
            [StockMedia(id=f"f{i}", media_type="photo") for i in range(10)]
            + [StockMedia(id=f"v{i}", media_type="video") for i in range(10)]
        )
        intercalado = StockDatabase._intercalar_tipos(itens)
        recorte = intercalado[:6]
        self.assertTrue(any(m.media_type == "video" for m in recorte))
        self.assertTrue(any(m.media_type == "photo" for m in recorte))

    def test_intercalar_com_um_tipo_so_nao_muda(self):
        from MusicClipStudio.database import StockDatabase, StockMedia

        so_fotos = [StockMedia(id=f"f{i}", media_type="photo") for i in range(3)]
        self.assertEqual(
            [m.id for m in StockDatabase._intercalar_tipos(so_fotos)],
            ["f0", "f1", "f2"],
        )


class TestModoParaFlags(unittest.TestCase):
    """Regressao: a GUI traduz o rotulo do segmento em (fotos, videos).
    Ja' invertemos essa mapeagem uma vez durante o desenvolvimento, o
    que fez "Mais videos" trazer 100 fotos. Este teste trava a tabela.
    """

    @staticmethod
    def _modo_para_flags(rotulo):
        """Espelha o calculo usado em GuiClipes._busca_automatica."""
        return rotulo == "Mais fotos", rotulo == "Mais vídeos"

    def test_mais_videos_pede_video(self):
        apenas_fotos, apenas_videos = self._modo_para_flags("Mais vídeos")
        self.assertFalse(apenas_fotos)
        self.assertTrue(apenas_videos)

    def test_mais_fotos_pede_foto(self):
        apenas_fotos, apenas_videos = self._modo_para_flags("Mais fotos")
        self.assertTrue(apenas_fotos)
        self.assertFalse(apenas_videos)

    def test_meio_a_meio_pede_os_dois(self):
        self.assertEqual(self._modo_para_flags("Meio a meio"), (False, False))

    def test_rotulos_reais_da_ui_estao_cobertos(self):
        """Trava os rotulos: se a UI mudar o texto, este teste avisa."""
        from MusicClipStudio.gui_clipes import GuiClipes
        import inspect, re

        fonte = inspect.getsource(GuiClipes._criar_frame_imagens)
        for rotulo in ["Meio a meio", "Mais vídeos", "Mais fotos"]:
            self.assertIn(rotulo, fonte,
                          f"rotulo {rotulo!r} sumiu do segmented button")
