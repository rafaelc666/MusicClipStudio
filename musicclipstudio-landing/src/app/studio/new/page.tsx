"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  ArrowRight, ArrowLeft, Wand2, Upload, FileText as FileIcon,
  Download, Play, Pause, Sparkles, Search, ImagePlus,
  CheckCircle2, MonitorPlay, FolderOpen, Music as MusicIconI, Trash2, Clock,
} from "lucide-react";
import { WizardStepper } from "@/components/studio/WizardStepper";
import { STUDIO_STEPS, type StudioStepKey } from "@/components/studio/StudioSidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useStudio } from "@/app/studio/StudioClientShell";
import { cn, API_BASE } from "@/lib/utils";
import { authApi, type ResumoProvedores } from "@/lib/auth-api";
import { useAuth } from "@/components/studio/AuthProvider";

/* ═══════════════════════════════════════════════════════════════════════
   Página · /studio/new — Wizard de criação em 6 etapas
   Integração real com backend FastAPI: GET /api/health, /api/letra/analisar, etc.
   ═══════════════════════════════════════════════════════════════════════ */

export default function NewStudioWizardPage() {
  const search = useSearchParams();
  const router = useRouter();
  const { state, setStep, markDone } = useStudio();

  /**
   * ⚠️ FONTE DE VERDADE ÚNICA: `state.activeStep`.
   *
   * Antes o passo ativo vinha da URL (?step=) e havia um efeito tentando
   * sincronizar URL → estado. Isso criava duas fontes de verdade: navegar
   * pelo menu lateral mudava o estado, mas a URL continuava a antiga (e o
   * efeito desfazia a troca); ao mesmo tempo, qualquer troca de search
   * param remontava o shell e zerava o projeto (música enviada etc.).
   *
   * Agora a URL é só um espelho: `setStep` a atualiza via replaceState,
   * sem remount. O estado manda.
   */
  const stepParam = search.get("step") as StudioStepKey | null;

  // Adota o ?step= da URL apenas na PRIMEIRA carga (deep-link / F5).
  const adotouUrl = React.useRef(false);
  React.useEffect(() => {
    if (adotouUrl.current) return;
    adotouUrl.current = true;
    if (stepParam && STUDIO_STEPS.some((s) => s.key === stepParam)) {
      if (state.activeStep !== stepParam) setStep(stepParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeKey =
    STUDIO_STEPS.find((s) => s.key === state.activeStep)?.key ??
    STUDIO_STEPS[0].key;
  const activeIdx = Math.max(0, STUDIO_STEPS.findIndex((s) => s.key === activeKey));

  const onBack = () => {
    if (activeIdx > 0) setStep(STUDIO_STEPS[activeIdx - 1].key);
    else router.push("/studio");
  };
  const onNext = () => {
    markDone(activeKey);
    if (activeIdx < STUDIO_STEPS.length - 1) setStep(STUDIO_STEPS[activeIdx + 1].key);
    else toast.success("Todas etapas preenchidas!", { description: "Pronto para gerar." });
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-up">
      {/* Stepper no topo */}
      <WizardStepper
        activeStep={activeKey}
        completedSteps={state.completedSteps}
        onChange={(k) => setStep(k)}
      />

      {/* Corpo: 2 colunas — conteúdo à esq + preview live à dir */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
        <div className="min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeKey}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.28, ease: [.2,.7,.2,1] }}
            >
              {activeKey === "chaves"  && <Step0Chaves onNext={onNext} />}
              {activeKey === "letra"   && <Step1Letra onNext={onNext} />}
              {activeKey === "audio"   && <Step3Audio />}
              {activeKey === "legenda" && <Step2Legenda onNext={onNext} />}
              {activeKey === "imagens" && <Step4Imagens onNext={onNext} />}
              {activeKey === "midia"   && <Step5Midia  onNext={onNext} />}
              {activeKey === "gerar"   && <Step6Gerar />}
            </motion.div>
          </AnimatePresence>

          {/* Botões navegação */}
          <div className="mt-6 flex items-center justify-between">
            <Button variant="ghost" onClick={onBack}>
              <ArrowLeft className="h-4 w-4" />
              {activeIdx === 0 ? "Voltar para projetos" : "Voltar"}
            </Button>

            <div className="flex items-center gap-3">
              <div className="hidden md:flex flex-col items-end">
                <span className="text-[11px] text-fg-3 font-mono">
                  ETAPA {activeIdx + 1} · {STUDIO_STEPS[activeIdx].numero}
                </span>
                <Progress
                  variant="neon"
                  value={Math.round(((activeIdx + 1) / STUDIO_STEPS.length) * 100)}
                  className="mt-1 w-52"
                />
              </div>
              {activeKey !== "gerar" ? (
                <Button variant="neon" size="lg" onClick={onNext}>
                  {activeIdx === STUDIO_STEPS.length - 2 ? "Ir para gerar" : "Avançar"}
                  <ArrowRight className="h-4 w-4 ml-1" strokeWidth={2.5} />
                </Button>
              ) : null}
            </div>
          </div>
        </div>

        {/* Painel Preview Live */}
        <LivePreviewPanel stepKey={activeKey} />
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   ETAPA 01 · LETRA
   ═══════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════
   ETAPA 01 · CHAVE API (a pedido do usuário, 23/09/2026)
   "A configuração das chaves de API precisa ser a primeira coisa a ser
   feita, caso contrário o programa não vai funcionar." Cada banco mostra:
   onde criar a chave + botão que ABRE O SITE OFICIAL.
   ═══════════════════════════════════════════════════════════════════════ */

/** Site onde o usuário CRIA a chave de cada banco (não é a URL da API). */
const SITES_DAS_CHAVES: Array<{
  id: string; nome: string; site: string; tipo: string;
  gratis: boolean; como: string;
}> = [
  {
    id: "pexels", nome: "Pexels", site: "https://www.pexels.com/api/",
    tipo: "fotos + vídeos", gratis: true,
    como: "Crie a conta, clique em “Your API” e aceite — a chave aparece na hora.",
  },
  {
    id: "pixabay", nome: "Pixabay", site: "https://pixabay.com/api/docs/",
    tipo: "fotos + vídeos", gratis: true,
    como: "Entre na conta → embaixo da doc aparece a sua chave pronta.",
  },
  {
    id: "unsplash", nome: "Unsplash", site: "https://unsplash.com/developers",
    tipo: "fotos", gratis: true,
    como: "Register as a developer → New Application → aceitar os termos.",
  },
  {
    id: "nasa", nome: "NASA Images", site: "https://api.nasa.gov/",
    tipo: "fotos + vídeos", gratis: true,
    como: "Generate API Key: só e-mail. Funciona até sem chave (limite menor).",
  },
  {
    id: "coverr", nome: "Coverr", site: "https://coverr.co",
    tipo: "vídeos", gratis: true,
    como: "Criar conta → API → a chave e o App ID ficam no painel.",
  },
  {
    id: "giphy", nome: "Giphy", site: "https://developers.giphy.com/dashboard/",
    tipo: "gifs / vídeos", gratis: true,
    como: "Create an App → seleciona “API” → a key sai na hora (dev).",
  },
  {
    id: "openverse", nome: "Openverse", site: "https://api.openverse.org/v1/#:~:text=register",
    tipo: "fotos", gratis: true,
    como: "Register → confirmar e-mail → chave em Settings. Funciona sem chave também.",
  },
];

function Step0Chaves({ onNext }: { onNext: () => void }) {
  const { usuario } = useAuth();
  const [resumo, setResumo] = React.useState<ResumoProvedores | null>(null);
  const [carregando, setCarregando] = React.useState(true);

  const recarregar = React.useCallback(() => {
    if (!usuario) return;
    setCarregando(true);
    authApi.provedores()
      .then(setResumo)
      .catch(() => setResumo(null))
      .finally(() => setCarregando(false));
  }, [usuario]);

  React.useEffect(recarregar, [recarregar]);

  const porId = React.useMemo(() => {
    const m = new Map<string, { configurada: boolean; previa: string; habilitado: boolean }>();
    resumo?.fixos.forEach((p) => m.set(p.id, p));
    return m;
  }, [resumo]);

  const configurados = SITES_DAS_CHAVES.filter((b) => porId.get(b.id)?.configurada).length;

  return (
    <div className="mx-auto w-full max-w-[760px] space-y-4">
      <div>
        <h2 className="text-[17px] font-semibold text-fg-0">Chaves de API — bancos de mídia</h2>
        <p className="mt-1 text-[12.5px] leading-relaxed text-fg-2">
          O clipe é montado com fotos e vídeos gratuitos destes bancos. <b>Pelo menos 1 banco
          configurado</b> já permite buscar mídia; com vários, a busca mistura todos.
          Crie a chave no site do banco (botão abaixo), cole no diálogo e pronto —
          fica guardada <b>criptografada na sua conta</b>, neste computador.
        </p>
      </div>

      {!usuario ? (
        <p className="rounded-sm border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[12px] text-amber-200">
          Entre na sua conta para configurar as chaves.
        </p>
      ) : carregando ? (
        <p className="text-[12px] text-fg-3">Carregando status…</p>
      ) : (
        <>
          <p className={cn("text-[12px] font-medium", configurados > 0 ? "text-emerald-300" : "text-fg-3")}>
            {configurados > 0
              ? `✓ ${configurados} de 7 bancos configurados`
              : "Nenhum banco configurado ainda — comece pelo Pexels (mais rápido)."}
          </p>

          <div className="grid gap-2.5">
            {SITES_DAS_CHAVES.map((b) => {
              const st = porId.get(b.id);
              return (
                <div key={b.id} className="rounded-sm border border-white/10 bg-bg-2/40 p-3.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[13.5px] font-medium text-fg-0">{b.nome}</span>
                    <span className="text-[10.5px] font-mono text-fg-3">{b.tipo}</span>
                    {st?.configurada ? (
                      <Badge variant="neon" className="text-[9.5px]">✓ configurado {st.previa}</Badge>
                    ) : (
                      <span className="rounded-full border border-white/15 px-1.5 py-0.5 text-[9.5px] text-fg-3">
                        falta chave
                      </span>
                    )}
                    <a
                      href={b.site}
                      target="_blank"
                      rel="noreferrer"
                      className="ml-auto inline-flex items-center gap-1 rounded-sm border border-neon/40 px-2 py-1 text-[11px] text-neon transition-colors hover:bg-neon/10"
                    >
                      Abrir site da chave <ArrowRight className="h-3 w-3" />
                    </a>
                  </div>
                  <p className="mt-1.5 text-[11.5px] leading-relaxed text-fg-3">
                    {b.como}
                  </p>
                  <button
                    type="button"
                    onClick={() => window.dispatchEvent(new Event("mcs:abrir-provedores"))}
                    className="mt-1.5 text-[11.5px] font-medium text-neon/90 underline-offset-2 hover:underline"
                  >
                    {st?.configurada
                      ? "ver/colar a chave no diálogo"
                      : "→ colar a chave aqui (abre o diálogo)"}
                  </button>
                </div>
              );
            })}
          </div>
        </>
      )}

      <div className="flex justify-end pt-1">
        <Button variant="neon" onClick={onNext}>
          {configurados > 0 ? "Continuar" : "Continuar sem chave (não recomendado)"}
          <ArrowRight className="h-4 w-4 ml-1" strokeWidth={2.5} />
        </Button>
      </div>
    </div>
  );
}

/* ⚠️ NOVO (23/09/2026) — no lugar do botão "Configurar provedores" da etapa
   de Imagens: AVISO DE STATUS. Configurou? verde "chaves OK · N bancos".
   Não configurou? amarelo mandando de volta ao passo 1. */
function AvisoStatusChaves() {
  const [n, setN] = React.useState<number | null>(null);
  React.useEffect(() => {
    let vivo = true;
    authApi.provedores()
      .then((r) => {
        if (vivo) {
          setN(r.fixos.filter((p) => p.configurada).length + r.custom.filter((c) => c.configurada).length);
        }
      })
      .catch(() => { if (vivo) setN(0); });
    return () => { vivo = false; };
  }, []);
  if (n === null) return null;
  return n > 0 ? (
    <span className="inline-flex items-center gap-1 rounded-sm border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-300">
      <CheckCircle2 className="h-3.5 w-3.5" />
      chaves OK · {n} banco{n > 1 ? "s" : ""}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-sm border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-200">
      ⚠ sem chaves — volte ao <b className="mx-0.5">passo 1</b> e configure
    </span>
  );
}

function Step1Letra({ onNext }: { onNext: () => void }) {
  const { state, setState } = useStudio();
  const [analysing, setAnalysing] = React.useState(false);
  const [result, setResult] = React.useState<{ beats: number; duracao: string; palavras: number } | null>(null);

  const PLACEHOLDER = `Cole aqui a letra da sua música...

Ex.:
  Quando a noite cai sobre a cidade
  Eu ainda escuto a tua voz
  O tempo não apagou a tua lembrança
  Mesmo de longe sinto o teu calor

Dica: você também pode carregar um arquivo .txt ou transcrever do áudio na próxima etapa.`;

  const doAnalyse = async () => {
    if (!state.letra.trim()) {
      toast.error("Cole uma letra antes");
      return;
    }
    setAnalysing(true);
    const toastId = toast.loading("Analisando estrutura da letra...");
    try {
      const r = await fetch(`${API_BASE}/api/letra/analisar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lyrics: state.letra, description: "", duration_beat: 5,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setResult({
        beats: json.total_beats ?? 0,
        duracao: `${json.duracao_estimada_seg ?? 0}s`,
        palavras: json.total_palavras ?? 0,
      });
      toast.success("Letra analisada", { id: toastId, description: `${json.total_beats} beats detectados` });
    } catch (e: any) {
      toast.error("API offline ou inválida", {
        id: toastId,
        description: "Simulando resultado (modo offline).",
      });
      // Fallback offline
      const palavras = state.letra.split(/\s+/).filter(Boolean).length;
      const beats = Math.max(4, Math.round(palavras / 6));
      setResult({ beats, duracao: `${beats * 5}s`, palavras });
    } finally {
      setAnalysing(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <StepHeader
        step="01"
        title="Letra da música"
        description="Cole ou digite a letra. O Studio irá dividir em beats visuais automaticamente."
        icon={<FileIcon className="h-5 w-5" />}
        accent="neon"
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Texto da música</CardTitle>
              <CardDescription>Quanto mais estruturada (estrofes/versos), melhor a sincronia.</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline">
                <Upload className="h-3.5 w-3.5" /> Carregar .txt
              </Button>
              <Button
                size="sm"
                variant="subtle"
                onClick={doAnalyse}
                loading={analysing}
                className="gap-2"
              >
                <Wand2 className={cn("h-3.5 w-3.5", analysing && "animate-spin")} />
                Analisar letra
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Textarea
              value={state.letra}
              onChange={(e) => setState((s) => ({ ...s, letra: e.target.value }))}
              placeholder={PLACEHOLDER}
              className="min-h-[280px] leading-[1.75] font-sans"
            />
            <div className="pointer-events-none absolute right-3 bottom-3 text-[11px] font-mono text-fg-3/70">
              {state.letra.length} caracteres
            </div>
          </div>

          {result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="grid grid-cols-3 gap-3 pt-1"
            >
              <MiniStat label="Palavras" value={result.palavras} icon={<FileIcon className="h-3.5 w-3.5" />} />
              <MiniStat label="Beats visuais" value={result.beats} icon={<Sparkles className="h-3.5 w-3.5" />} accent="neon" />
              <MiniStat label="Duração estimada" value={result.duracao} icon={<Play className="h-3.5 w-3.5" />} accent="ok" />
            </motion.div>
          )}
        </CardContent>
      </Card>

      <div className="rounded-sm border border-white/5 bg-bg-2/50 p-4">
        <div className="flex items-start gap-3">
          <Badge variant="warn" className="shrink-0 mt-0.5">Dica</Badge>
          <div className="text-[13px] text-fg-1 leading-relaxed">
            <span className="text-fg-0 font-medium">Separe as estrofes com linhas em branco.</span>{" "}
            O Studio interpreta cada estrofe como uma mudança visual maior, e cada verso como um beat.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   ETAPA 03 · LEGENDA
   ═══════════════════════════════════════════════════════ */

/* ⚠️ NOVO (22/09/2026) — tipos e padrão do estilo da legenda.
     O estilo viaja no payload como `legenda_estilo` e vira force_style
     do FFmpeg no Compositor (cor, fonte, tamanho, contorno, posição). */
type EstiloLegenda = {
  cor: string;
  corContorno: string;
  fonte: string;
  tamanho: number;
  contorno: number;
  posicao: "baixo" | "centro" | "topo";
  negrito: boolean;
};

const FONTES_LEGENDA = ["Montserrat", "Inter", "Arial", "Verdana", "Georgia", "Courier New"] as const;

const ESTILO_PADRAO: EstiloLegenda = {
  cor: "#FFFFFF",
  corContorno: "#000000",
  fonte: "Montserrat",
  tamanho: 48,
  contorno: 2,
  posicao: "baixo",
  negrito: false,
};

/* ASS (force_style): cores em &HBBGGRR (BGR invertido). */
function _hexParaAss(hex: string): string {
  const h = hex.replace("#", "");
  const r = h.slice(0, 2), g = h.slice(2, 4), b = h.slice(4, 6);
  return `&H00${b}${g}${r}`.toUpperCase();
}

function estiloParaForceStyle(e: EstiloLegenda): string {
  const margemV = e.posicao === "topo" ? "MarginV=60" : e.posicao === "centro" ? "Alignment=5" : "";
  return [
    `FontName=${e.fonte}`,
    `FontSize=${e.tamanho}`,
    `PrimaryColour=${_hexParaAss(e.cor)}`,
    `OutlineColour=${_hexParaAss(e.corContorno)}`,
    `BorderStyle=1`,
    `Outline=${e.contorno}`,
    `Shadow=0`,
    e.negrito ? "Bold=1" : "Bold=0",
    margemV,
  ].filter(Boolean).join(",");
}

function Step2Legenda({ onNext }: { onNext: () => void }) {
  const { state, setState, setStep } = useStudio();
  const [transcrevendo, setTranscrevendo] = React.useState(false);

  /* ⚠️ NOVO (22/09/2026) — estilo da legenda persistido no projeto.
     Fontes: as que o Google Fonts já carrega no HTML (Montserrat/Inter)
     + opções de sistema seguras no render do FFmpeg (Arial, Verdana). */
  const estiloLegenda = state.legendaEstilo ?? ESTILO_PADRAO;

  const linhas = state.legenda.length > 0
    ? state.legenda
    : gerarLinhasDaLetra(state.letra);

  /**
   * ⚠️ CORRIGIDO (21/09/2026) — A TRANSCRIÇÃO ERA FALSA.
   *
   * ANTES: `setTimeout(1400)` + um `map` que inventava tempos de 3 em 3
   * segundos (`i * 3`). Não chamava backend nenhum, não abria o áudio, não
   * rodava Whisper. O botão dizia "Transcrição concluída" e entregava a
   * própria letra com tempos chutados — o mesmo padrão de "IA de fachada"
   * que já tinha aparecido na etapa 04 (setTimeout + array fixo).
   *
   * AGORA: chama POST /api/legenda/transcrever com o áudio enviado na etapa
   * 02 e usa os tempos reais que o Whisper devolve. Se não houver áudio,
   * avisa e manda para a etapa 02 — é justamente por isso que a ordem
   * passou a ser letra → áudio → legenda.
   */
  const onTranscrever = async () => {
    const audio = state.musica?.arquivo;
    if (!audio) {
      toast.error("Nenhum áudio enviado", {
        description: "Volte à etapa 02 (Áudio) e envie a música — a transcrição roda em cima dela.",
      });
      setStep("audio");
      return;
    }

    setTranscrevendo(true);
    const id = toast.loading("Transcrevendo com Whisper...", {
      description: "Pode levar alguns minutos, dependendo do tamanho da música.",
    });
    try {
      // ⚠️ 23/09/2026: transcrição via JOB + polling. O proxy do Next abortava
      // respostas lentas (~60s) e o navegador recebia 500 com o backend OK.
      const r0 = await fetch(`${API_BASE}/api/legenda/transcrever-job`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_path: audio }),
      });
      if (!r0.ok) {
        const detalhe0 = await r0.json().catch(() => null);
        throw new Error(detalhe0?.detail || `HTTP ${r0.status}`);
      }
      const { job_id } = (await r0.json()) as { job_id: string };

      // Polling a cada 1,5s até done/error (limite de segurança: 15 min).
      let json: any = null;
      const t0 = Date.now();
      for (;;) {
        await new Promise((res) => setTimeout(res, 1500));
        const rj = await fetch(`${API_BASE}/api/jobs/${job_id}`);
        if (!rj.ok) throw new Error(`HTTP ${rj.status} ao consultar o job`);
        const st = await rj.json();
        if (typeof st.progress === "number" && st.progress > 0) {
          toast.loading(`Transcrevendo com Whisper... ${Math.min(99, st.progress)}%`, { id, description: "Modelo analisando o áudio — mantenha esta aba aberta." });
        }
        if (st.status === "done") { json = st.result; break; }
        if (st.status === "error") throw new Error(st.error || "o job de transcrição falhou");
        if (Date.now() - t0 > 15 * 60 * 1000) throw new Error("tempo limite da transcrição (15 min)");
      }
      // ⚠️ 23/09/2026: áudio INSTRUMENTAL (sem fala) não é erro — o backend
      // responde ok=false + instrumental=true. Avisa e segue o fluxo.
      if (json?.instrumental) {
        toast.info("Música instrumental detectada", {
          id,
          description: "Sem voz para transcrever — o clipe segue sem legenda (você pode escrever as linhas à mão).",
          duration: 8000,
        });
        return;
      }
      const vindas: any[] = Array.isArray(json?.linhas) ? json.linhas : [];
      if (vindas.length === 0) {
        throw new Error("a transcrição não devolveu nenhuma linha");
      }

      const novas = vindas.map((l) => ({
        texto: String(l.texto ?? "").trim(),
        start: Number(l.inicio ?? 0).toFixed(2),
        end: Number(l.fim ?? 0).toFixed(2),
        dur: `${Math.max(0, Number(l.fim ?? 0) - Number(l.inicio ?? 0)).toFixed(1)}s`,
        tempo: true,
      }));

      setState((s) => ({
        ...s,
        legenda: novas,
        // Sem letra digitada, a transcrição É a letra.
        letra: (s.letra || "").trim()
          ? s.letra
          : String(json.texto_completo || novas.map((n) => n.texto).join("\n")),
      }));

      toast.success("Transcrição concluída", {
        id,
        description: `${novas.length} linhas com tempos reais${json.idioma ? ` · idioma ${json.idioma}` : ""}`,
      });
    } catch (e) {
      toast.error("A transcrição falhou", {
        id,
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setTranscrevendo(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <StepHeader
        step="03"
        title="Revisar legenda"
        description="Confirme cada linha, tempos e ortografia. É a fonte da verdade para os beats."
        icon={<FileIcon className="h-5 w-5" />}
        accent="violet"
      />

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Transcrição & tempos</CardTitle>
              <CardDescription>
                Se a letra veio de transcrição, confira os tempos. Você também pode importar um .SRT.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="neon" loading={transcrevendo} onClick={onTranscrever}>
                <Upload className="h-3.5 w-3.5" />
                Transcrever do áudio
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  if (linhas.length === 0) {
                    toast.error("Nada para revisar");
                    return;
                  }
                  // Limpeza de erros comuns de transcrição: espaços
                  // duplicados, pontuação colada e minúscula pós-frase.
                  let mudadas = 0;
                  const novas = linhas.map((l: any) => {
                    const original = String(l.texto || "");
                    const limpo = original
                      .replace(/ {2,}/g, " ")
                      .replace(/ +([,.!?;:])/g, "$1")
                      .replace(/([,.!?;:])(?=[^ ])/g, "$1 ")
                      .replace(/(^|[.!?] +)([a-záàâãéèêíïóôõöúçñ])/g, (_m: string, pre: string, ch: string) => pre + ch.toUpperCase())
                      .trim();
                    if (limpo !== original) mudadas += 1;
                    return { ...l, texto: limpo };
                  });
                  setState((s) => ({ ...s, legenda: novas }));
                  toast.success("Ortografia revisada", {
                    description: mudadas > 0 ? `${mudadas} de ${linhas.length} linhas ajustadas` : "Nenhum erro comum encontrado",
                  });
                }}
              >
                <Wand2 className="h-3.5 w-3.5" />
                Revisar ortografia
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  if (linhas.length === 0) {
                    toast.error("Nada para exportar", { description: "Transcreva do áudio ou cole a letra primeiro." });
                    return;
                  }
                  // SRT: tempos reais quando existem; senão distribui ao
                  // longo da duração da música.
                  const temTempos = linhas.every((l: any) => typeof l.inicio === "number" && typeof l.fim === "number");
                  const dur = Math.max(1, state.musica.duracao || linhas.length * 4);
                  const por = dur / linhas.length;
                  const fmt = (seg: number) => {
                    const h = Math.floor(seg / 3600), m2 = Math.floor((seg % 3600) / 60), s2 = Math.floor(seg % 60), ms = Math.round((seg % 1) * 1000);
                    return `${String(h).padStart(2, "0")}:${String(m2).padStart(2, "0")}:${String(s2).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
                  };
                  const srt = linhas.map((l: any, i: number) => {
                    const ini = temTempos ? l.inicio : i * por;
                    const fim = temTempos ? l.fim : (i + 1) * por - 0.05;
                    const ini2 = fmt(ini);
                    const fim2 = fmt(fim);
                    return `${i + 1}\n${ini2} --> ${fim2}\n${(l.texto || "").trim()}\n`;
                  }).join("\n");
                  const blob = new Blob([srt], { type: "text/plain;charset=utf-8" });
                  const a = document.createElement("a");
                  a.href = URL.createObjectURL(blob);
                  a.download = `${state.title || "legenda"}.srt`.replace(/\s+/g, "_");
                  a.click();
                  URL.revokeObjectURL(a.href);
                  toast.success("SRT exportado", { description: `${linhas.length} linhas` });
                }}
              >
                <Download className="h-3.5 w-3.5" />
                .SRT
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="overflow-hidden rounded-sm border border-white/5 bg-bg-0/40">
            <div className="grid grid-cols-[76px_1fr_64px_72px] gap-2 border-b border-white/5 px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-fg-3">
              <span>Tempo</span>
              <span>Texto da linha</span>
              <span className="text-right">Duração</span>
              <span className="text-right">Ações</span>
            </div>

            <div className="max-h-[340px] overflow-y-auto">
              {linhas.length === 0 && (
                <div className="px-5 py-14 text-center text-[13px] text-fg-3">
                  Sem linhas ainda. Volte para a Etapa 01 e cole uma letra,
                  ou envie a música na Etapa 02 e clique em "Transcrever do áudio".
                </div>
              )}

              {linhas.map((l: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className="grid grid-cols-[76px_1fr_64px_72px] items-center gap-2 border-b border-white/5 px-3 py-2 hover:bg-bg-3/30 transition-colors group"
                >
                  <div className="flex items-center gap-1 text-[11px] font-mono text-neon">
                    <span className="text-fg-3">{String(i + 1).padStart(2, "0")}</span>
                    {l.tempo ? (
                      <Badge variant="neon" className="text-[10px] px-1.5">
                        {formatT(l.start)}
                      </Badge>
                    ) : (
                      <Badge variant="default" className="text-[10px] px-1.5">—</Badge>
                    )}
                  </div>
                  <input
                    className="w-full bg-transparent text-[13px] text-fg-0 outline-none focus:px-2 focus:rounded-sm focus:bg-bg-3/40 py-1 transition-colors"
                    defaultValue={l.texto}
                    onBlur={(e) => {
                      const novo = [...linhas];
                      novo[i] = { ...(novo[i] || {}), texto: e.target.value };
                      setState((s) => ({ ...s, legenda: novo }));
                    }}
                  />
                  <div className="text-right text-[11px] font-mono text-fg-3 group-hover:text-fg-1 transition-colors">
                    {l.dur || `${4 + (i % 3)}s`}
                  </div>
                  <div className="flex items-center justify-end gap-0.5">
                    {/* ⚠️ NOVO (23/09/2026): + linha insere uma frase nova logo
                        abaixo (herda a janela de tempo entre esta linha e a
                        próxima); × remove a linha de vez. Antes não dava para
                        nem adicionar nem excluir linhas — só apagar o texto,
                        que deixava linha vazia na lista. */}
                    <button
                      type="button"
                      title="adicionar linha abaixo"
                      onClick={() => {
                        const proxima = linhas[i + 1];
                        const iniNum = Number(l.end ?? l.inicio ?? i * 4);
                        const fimNum = Number(proxima?.start ?? proxima?.inicio ?? iniNum + 4);
                        const ini = isFinite(iniNum) ? iniNum : i * 4;
                        const fim = isFinite(fimNum) && fimNum > ini ? Math.min(ini + (fimNum - ini) / 2, ini + 6) : ini + 3;
                        const nova = {
                          texto: "",
                          ...(l.tempo
                            ? { start: ini.toFixed(2), end: fim.toFixed(2), dur: `${(fim - ini).toFixed(1)}s`, tempo: true }
                            : {}),
                        };
                        const novo = [...linhas.slice(0, i + 1), nova, ...linhas.slice(i + 1)];
                        setState((s) => ({ ...s, legenda: novo }));
                      }}
                      className="h-6 w-6 rounded-sm text-fg-3 opacity-0 transition-opacity hover:bg-bg-3 hover:text-fg-0 group-hover:opacity-100"
                    >
                      +
                    </button>
                    <button
                      type="button"
                      title="remover esta linha"
                      onClick={() => {
                        setState((s) => ({ ...s, legenda: linhas.filter((_, k) => k !== i) }));
                      }}
                      className="h-6 w-6 rounded-sm text-err/70 opacity-0 transition-opacity hover:bg-err/15 hover:text-err group-hover:opacity-100"
                    >
                      ×
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* ⚠️ NOVO (22/09/2026) — ESTILO DA LEGENDA (queimada no MP4 via
              force_style do FFmpeg). Cor, fonte, tamanho, contorno, posição.
              A pré-visualização usa o MESMO estilo pra dar WYSIWYG. */}
          <div className="mt-5 rounded-sm border border-white/8 bg-bg-2/40 p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-[11px] uppercase tracking-wider text-fg-3 font-mono">
                estilo da legenda (queimada no vídeo)
              </span>
              <button
                type="button"
                onClick={() => setState((s) => ({ ...s, legendaEstilo: ESTILO_PADRAO }))}
                className="text-[11px] text-fg-3 hover:text-fg-0 transition-colors"
              >
                restaurar padrão
              </button>
            </div>

            {/* Pré-visualização sobre fundo escuro */}
            <div className="mb-4 flex h-20 items-end justify-center overflow-hidden rounded-sm bg-gradient-to-b from-[#1a1a2e] to-[#0d0d1f] pb-3">
              <span
                style={{
                  fontFamily: `"${estiloLegenda.fonte}", sans-serif`,
                  fontSize: estiloLegenda.tamanho * 0.45,
                  color: estiloLegenda.cor,
                  WebkitTextStroke: `${Math.max(1, estiloLegenda.contorno * 0.4)}px ${estiloLegenda.corContorno}`,
                  fontWeight: estiloLegenda.negrito ? 800 : 500,
                }}
              >
                {linhas[0]?.texto || "Exemplo de legenda"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-fg-3">Cor do texto</span>
                <input
                  type="color"
                  value={estiloLegenda.cor}
                  onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, cor: e.target.value } }))}
                  className="h-8 w-full cursor-pointer rounded-sm border border-white/10 bg-bg-2/60"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-fg-3">Cor do contorno</span>
                <input
                  type="color"
                  value={estiloLegenda.corContorno}
                  onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, corContorno: e.target.value } }))}
                  className="h-8 w-full cursor-pointer rounded-sm border border-white/10 bg-bg-2/60"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-fg-3">Fonte</span>
                <select
                  value={estiloLegenda.fonte}
                  onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, fonte: e.target.value } }))}
                  className="h-8 rounded-sm border border-white/10 bg-bg-2/60 px-2 text-[12px] text-fg-0 outline-none focus:border-neon/40"
                >
                  {FONTES_LEGENDA.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-fg-3">Tamanho ({estiloLegenda.tamanho}px)</span>
                <input
                  type="range"
                  min={24} max={96} step={2}
                  value={estiloLegenda.tamanho}
                  onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, tamanho: Number(e.target.value) } }))}
                  className="accent-neon mt-2"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-fg-3">Contorno ({estiloLegenda.contorno}px)</span>
                <input
                  type="range"
                  min={0} max={6} step={1}
                  value={estiloLegenda.contorno}
                  onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, contorno: Number(e.target.value) } }))}
                  className="accent-neon mt-2"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-fg-3">Posição vertical</span>
                <select
                  value={estiloLegenda.posicao}
                  onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, posicao: e.target.value as EstiloLegenda["posicao"] } }))}
                  className="h-8 rounded-sm border border-white/10 bg-bg-2/60 px-2 text-[12px] text-fg-0 outline-none focus:border-neon/40"
                >
                  <option value="baixo">Baixo</option>
                  <option value="centro">Centro</option>
                  <option value="topo">Topo</option>
                </select>
              </label>
            </div>
            <label className="mt-3 flex cursor-pointer items-center gap-2 text-[12px] text-fg-2">
              <input
                type="checkbox"
                checked={estiloLegenda.negrito}
                onChange={(e) => setState((s) => ({ ...s, legendaEstilo: { ...estiloLegenda, negrito: e.target.checked } }))}
                className="h-3.5 w-3.5 accent-neon"
              />
              Negrito
            </label>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   ETAPA 02 · ÁUDIO — upload da música pronta

   ARQUITETURA (Opção A): o MusicClipStudio NÃO gera música. O usuário
   envia a música pronta e o app monta o clipe em cima dela, com imagens
   de bancos gratuitos. A geração por IA (ACE-Step) foi removida em
   19/09/2026 — sem servidor para rodar IA musical e o modelo travava
   acima de ~1 min, inviável para clipes de 3+ minutos.
   ═══════════════════════════════════════════════════════════════════════ */

function Step3Audio() {
  const { state, setState } = useStudio();
  const [enviando, setEnviando] = React.useState(false);
  const [progresso, setProgresso] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  const [tocando, setTocando] = React.useState(false);
  const [tempoAtual, setTempoAtual] = React.useState(0);

  /**
   * ⚠️ NOVO (21/09/2026) — RECUPERAÇÃO DE UPLOAD.
   *
   * Antes: se o Fast Refresh do Turbopack remontava o shell, `state.musica`
   * zerava e o arquivo de áudio (que continua em `output/uploads/`) ficava
   * órfão — o usuário tinha que abrir o Explorer, caçar o .mp3 e reenviar.
   *
   * Agora: ao entrar na etapa sem áudio carregado, listamos os últimos
   * uploads reais (não o cache de teste < 1 KB) e oferecemos "Reanexar"
   * com um clique. A referência volta para o estado sem precisar tocar no disco.
   */
  /**
   * ⚠️ NOVO (23/09/2026) — EXCLUSÃO DEFINITIVA.
   * Ao remover a música, o path do upload vai para a lista de excluídos
   * (localStorage). O banner "Detectamos N arquivos anteriores" deixa de
   * oferecer o arquivo que o usuário acabou de descartar — antes ele voltava
   * listado na hora, parecendo que a exclusão "não pegava".
   */
  const EXCLUIDOS_KEY = "musicclipstudio_audio_excluidos_v1";
  const pathsExcluidos = (): Set<string> => {
    try {
      return new Set(JSON.parse(window.localStorage.getItem(EXCLUIDOS_KEY) ?? "[]"));
    } catch {
      return new Set();
    }
  };
  const [recentes, setRecentes] = React.useState<Array<{
    path: string; url: string; nome: string; size_bytes: number; mtime: number;
  }> | null>(null);
  React.useEffect(() => {
    if (state.musica.arquivo) return;        // já tem áudio — não precisa
    let cancelado = false;
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/api/upload/audio/recente?limite=5`);
        if (!r.ok || cancelado) return;
        const j = await r.json();
        if (!j.ok || cancelado) return;
        // Esconde da recuperação o que o usuário excluiu de propósito.
        const excl = pathsExcluidos();
        const itens = (Array.isArray(j.itens) ? j.itens : []).filter(
          (it: { path: string }) => !excl.has(it.path),
        );
        setRecentes(itens);
      } catch {
        /* backend offline — silencioso, sem toast */
      }
    })();
    return () => { cancelado = true; };
  }, [state.musica.arquivo]);

  const reanexar = async (item: {
    path: string; url: string; nome: string; size_bytes: number;
  }) => {
    // Descobre a duração real do arquivo tocando-o no navegador.
    const duracao = await new Promise<number>((resolve) => {
      const a = new Audio(`${API_BASE}${item.url}`);
      a.preload = "metadata";
      const onMeta = () => {
        a.removeEventListener("loadedmetadata", onMeta);
        const d = isFinite(a.duration) ? Math.round(a.duration) : 0;
        resolve(d);
      };
      a.addEventListener("loadedmetadata", onMeta);
      a.addEventListener("error", onMeta);  // fallback se falhar
      setTimeout(() => resolve(0), 4000);
    });
    setState((s) => ({
      ...s,
      musica: {
        ...s.musica,
        arquivo: item.path,
        url: item.url,
        nomeArquivo: item.nome,
        duracao: duracao || s.musica.duracao,
        tamanhoBytes: item.size_bytes,
      },
    }));
    setRecentes(null);
    toast.success("Áudio reanexado", { description: item.nome });
  };

  /**
   * URL tocável da música enviada. O backend devolve `url` já no formato
   * servível (/static/output/uploads/...). Monta sobre API_BASE porque o
   * dev server do Next fica em outra porta.
   */
  const urlAudio = state.musica.url
    ? `${API_BASE}${state.musica.url}`
    : null;

  const enviarArquivo = async (file: File) => {
    const ehAudio = /\.(mp3|wav|m4a|aac|ogg|flac)$/i.test(file.name);
    if (!ehAudio) {
      toast.error("Formato não suportado", {
        description: "Envie um arquivo .mp3, .wav, .m4a, .aac, .ogg ou .flac",
      });
      return;
    }

    setEnviando(true);
    setProgresso(0);
    const id = toast.loading(`Enviando ${file.name}…`);
    try {
      const fd = new FormData();
      fd.append("file", file);

      const resp = await fetch(`${API_BASE}/api/upload/audio`, {
        method: "POST",
        body: fd,
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      // Descobre a duração real do arquivo no navegador — é ela que manda
      // no tamanho do clipe (não um slider chutado).
      const duracao = await medirDuracao(URL.createObjectURL(file));

      setProgresso(100);
      setState((s) => ({
        ...s,
        musica: {
          ...s.musica,
          arquivo: data.path,
          url: data.url,
          nomeArquivo: file.name,
          duracao: Math.round(duracao) || s.musica.duracao,
          tamanhoBytes: data.size_bytes,
        },
      }));
      toast.success("Música carregada", {
        id,
        description: `${file.name} · ${formatarDuracao(duracao)}`,
      });
    } catch (e) {
      toast.error("Falha ao enviar a música", {
        id,
        description:
          e instanceof Error && e.message.startsWith("HTTP")
            ? "O backend recusou o arquivo. Ele está rodando?"
            : "Backend offline — suba com RUN_WEB.bat e tente de novo.",
      });
    } finally {
      setEnviando(false);
    }
  };

  const aoEscolher = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) void enviarArquivo(f);
    // permite reenviar o mesmo arquivo depois
    e.target.value = "";
  };

  const alternarPlay = () => {
    const el = audioRef.current;
    if (!el) return;
    if (el.paused) void el.play();
    else el.pause();
  };

  const removerMusica = () => {
    audioRef.current?.pause();
    setTocando(false);
    setTempoAtual(0);
    const pathRemovido = state.musica.arquivo;
    if (pathRemovido) {
      try {
        const excl = pathsExcluidos();
        excl.add(pathRemovido);
        window.localStorage.setItem(EXCLUIDOS_KEY, JSON.stringify([...excl]));
      } catch {
        /* localStorage indisponível — a exclusão ainda vale no estado */
      }
    }
    setState((s) => ({
      ...s,
      musica: {
        ...s.musica,
        arquivo: undefined,
        url: undefined,
        nomeArquivo: undefined,
        tamanhoBytes: undefined,
      },
    }));
    toast.success("Música removida", {
      description: "Envie outro arquivo na zona acima.",
    });
  };

  return (
    <div className="flex flex-col gap-5">
      <StepHeader
        step="02"
        title="Sua música"
        description="Envie a música pronta do clipe. O app monta o vídeo em cima dela — ele não compõe música."
        icon={<MusicIconI className="h-5 w-5" />}
        accent="ok"
      />

      <Card>
        <CardHeader>
          <CardTitle>Arquivo de áudio</CardTitle>
          <CardDescription>
            Aceita .mp3, .wav, .m4a, .aac, .ogg ou .flac. A duração da música define o
            tamanho do clipe.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            ref={inputRef}
            type="file"
            accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac"
            className="hidden"
            onChange={aoEscolher}
          />

          {!urlAudio ? (
            <>
              {/* Banner de recuperação: oferece reanexar arquivos que já
                  estão em `output/uploads/` (viram órfãos quando o estado
                  da aba zerou). Só aparece se há áudio carregado no disco. */}
              {recentes && recentes.length > 0 && (
                <div className="rounded-md border border-neon/25 bg-neon/5 p-3">
                  <div className="flex items-start gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-neon/15 border border-neon/30 text-neon text-[11px] font-bold">!</span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] text-fg-1 font-medium">
                        Detectamos {recentes.length} {recentes.length === 1 ? "arquivo" : "arquivos"} enviado{recentes.length === 1 ? "" : "s"} anteriormente.
                      </p>
                      <p className="text-[11.5px] text-fg-3">
                        Se você não precisa de um áudio novo, pode reanexar um deles — é só clicar.
                      </p>
                      <div className="mt-2 space-y-1.5">
                        {recentes.map((item) => (
                          <button
                            key={item.path}
                            type="button"
                            onClick={() => void reanexar(item)}
                            className="group w-full flex items-center justify-between gap-2 rounded-sm border border-white/8 bg-bg-2/60 px-3 py-2 text-left text-[12px] hover:border-neon/40 hover:bg-bg-3/60 transition-colors"
                            title={`Reanexar ${item.nome}`}
                          >
                            <span className="truncate text-fg-1">{item.nome}</span>
                            <span className="flex items-center gap-2 shrink-0">
                              <span className="font-mono text-[11px] text-fg-3">
                                {(item.size_bytes / (1024*1024)).toFixed(1)} MB
                              </span>
                              <span className="rounded-sm bg-neon/15 border border-neon/30 px-2 py-0.5 text-[10px] font-semibold text-neon uppercase tracking-wide">
                                Reanexar
                              </span>
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Zona de drop quando ainda não há música */}
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files?.[0];
                  if (f) void enviarArquivo(f);
                }}
                disabled={enviando}
                className={cn(
                  "w-full rounded-md border border-dashed border-white/12 bg-bg-2/40 p-10",
                  "flex flex-col items-center gap-3 text-center transition-colors",
                  "hover:border-neon/40 hover:bg-bg-2/70 disabled:opacity-60",
                )}
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-neon/10 border border-neon/30 text-neon">
                  <Upload className="h-5 w-5" />
                </span>
                <span className="text-[14px] font-medium text-fg-0">
                  {enviando ? "Enviando…" : "Arraste a música aqui ou clique para escolher"}
                </span>
                <span className="text-[12px] text-fg-3">
                  O arquivo fica no seu computador. Nada é enviado para a nuvem.
                </span>
              </button>
            </>
          ) : (
            /* ⚠️ NOVO (23/09/2026) — CARTÃO ÚNICO do arquivo: player + status
               + ações (Trocar/Excluir) juntos. Antes havia DOIS cartões
               empilhados mostrando o mesmo arquivo (um com Trocar/Remover,
               outro com "Pronta"), parecendo áudio duplicado, e o botão
               "Continuar" repetia o "Avançar" do rodapé do wizard. */
            <div className="rounded-md border border-white/8 bg-gradient-to-br from-bg-0/60 to-bg-3/40 p-4">
              <audio
                ref={audioRef}
                src={urlAudio}
                preload="metadata"
                onPlay={() => setTocando(true)}
                onPause={() => setTocando(false)}
                onEnded={() => {
                  setTocando(false);
                  setTempoAtual(0);
                }}
                onTimeUpdate={(e) => setTempoAtual(e.currentTarget.currentTime)}
              />
              <div className="flex items-center gap-3">
                <Button
                  variant="neon"
                  size="icon"
                  className="h-10 w-10 shrink-0 rounded-full"
                  onClick={alternarPlay}
                  aria-label={tocando ? "Pausar" : "Tocar"}
                >
                  {tocando ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
                </Button>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[13px] font-semibold text-fg-0">
                    {state.musica.nomeArquivo || "Música"}
                  </div>
                  <div className="font-mono text-[11px] text-fg-3">
                    {formatarDuracao(tempoAtual)} / {formatarDuracao(state.musica.duracao)}
                    {state.musica.tamanhoBytes
                      ? ` · ${formatarTamanho(state.musica.tamanhoBytes)}`
                      : ""}
                  </div>
                </div>
                <Badge variant="ok" className="shrink-0">
                  <CheckCircle2 className="mr-1 h-3 w-3" /> Pronta
                </Badge>
              </div>

              {/* Barra de progresso da reprodução */}
              <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full bg-gradient-to-r from-neon to-neon-2 transition-[width] duration-200"
                  style={{
                    width: state.musica.duracao
                      ? `${Math.min(100, (tempoAtual / state.musica.duracao) * 100)}%`
                      : "0%",
                  }}
                />
              </div>

              {/* Ações: trocar ou excluir o áudio */}
              <div className="mt-3 flex items-center justify-end gap-2 border-t border-white/5 pt-3">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={enviando}
                  onClick={() => inputRef.current?.click()}
                >
                  Trocar
                </Button>
                <Button variant="ghost" size="sm" onClick={removerMusica}>
                  <Trash2 className="h-4 w-4 text-err/80" />
                  Excluir
                </Button>
              </div>
            </div>
          )}

          {enviando && <Progress variant="neon" value={progresso} />}

          {/* ⚠️ NOVO (23/09/2026) — REGRA DE DURAÇÃO em destaque: o vídeo tem
              sempre o tamanho do áudio. 1 imagem = fica a música toda;
              1 vídeo = roda em loop; várias mídias = dividem os trechos. */}
          <div className="rounded-md border border-neon/40 bg-neon/5 p-4">
            <div className="flex items-start gap-2">
              <Clock className="mt-0.5 h-4 w-4 shrink-0 text-neon" />
              <div className="min-w-0 flex-1">
                <p className="text-[12.5px] font-semibold text-fg-0">
                  O clipe tem exatamente o tamanho da música
                </p>
                <p className="mt-1 text-[11.5px] leading-relaxed text-fg-2">
                  O vídeo acompanha o áudio do início ao fim. Escolheu só <b>1 imagem</b>?
                  Ela fica na tela durante toda a música. Enviou <b>1 vídeo</b>? Ele roda em
                  loop até o fim. Escolheu várias mídias? Elas se dividem pelos trechos da música.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2 border-neon/50 text-neon hover:bg-neon/10"
                  onClick={() => window.dispatchEvent(new Event("mcs:abrir-provedores"))}
                >
                  Configurar chaves de API (necessário para gerar)
                </Button>
              </div>
            </div>
          </div>

          {/* ⚠️ NOVO (23/09/2026) — ONDE CONSEGUIR MÚSICA: o wizard pede a
              música pronta, mas não diz onde achar uma legal para usar.
              Bancos gratuitos com licença para clipes (conferir a licença
              de cada faixa — algumas pedem crédito). */}
          <div className="rounded-md border border-white/8 bg-bg-2/40 p-4">
            <div className="flex items-center gap-2">
              <span className="text-[12px] font-semibold text-fg-1">
                Sem música? Bancos gratuitos para clipes:
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {[
                { nome: "YouTube Audio Library", url: "https://studio.youtube.com/channel/UC/music", nota: "grátis com crédito" },
                { nome: "Free Music Archive", url: "https://freemusicarchive.org", nota: "por licença CC" },
                { nome: "Pixabay Music", url: "https://pixabay.com/music/", nota: "sem atribuição" },
                { nome: "Incompetech", url: "https://incompetech.com/music/royalty-free/", nota: "crédito obrigatório" },
                { nome: "Chosic", url: "https://www.chosic.com/free-music/", nota: "agrega várias fontes" },
              ].map((b) => (
                <a
                  key={b.nome}
                  href={b.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  title={b.nota}
                  className="rounded-full border border-white/10 bg-bg-2/60 px-2.5 py-1 text-[11px] text-fg-2 transition-colors hover:border-neon/40 hover:text-fg-0"
                >
                  {b.nome} <span className="text-[9.5px] text-fg-3">· {b.nota}</span>
                </a>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-fg-3">
              Baixe a faixa e envie acima — a duração dela define o tamanho do clipe.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/** Lê a duração real de um arquivo de áudio usando o próprio navegador. */
function medirDuracao(url: string): Promise<number> {
  return new Promise((resolve) => {
    const a = document.createElement("audio");
    a.preload = "metadata";
    a.onloadedmetadata = () => {
      resolve(Number.isFinite(a.duration) ? a.duration : 0);
      URL.revokeObjectURL(url);
    };
    a.onerror = () => {
      resolve(0);
      URL.revokeObjectURL(url);
    };
    a.src = url;
  });
}

function formatarDuracao(seg: number): string {
  const s = Math.max(0, Math.round(seg || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function formatarTamanho(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* ═══════════════════════════════════════════════════════
   ETAPA 04 · IMAGENS (prompts IA)
   ═══════════════════════════════════════════════════════ */

function Step4Imagens({ onNext }: { onNext: () => void }) {
  const { state, setState, setStep } = useStudio();
  const [loading, setLoading] = React.useState(false);
  const [erro, setErro] = React.useState<string | null>(null);
  const [meta, setMeta] = React.useState<{ mood?: string; estilo?: string; tema_nome?: string | null } | null>(null);
  /* ⚠️ NOVO (23/09/2026) — TEMA VISUAL LIVRE: a pessoa define o visual que
     quer ("chuva lenta", "carros antigos", "vôlei de praia") sem depender
     de catálogo — catalogar todos os temas é impossível. Vai no payload
     e qualifica todas as queries do agente. Persiste no estado do wizard. */
  const temaSalvo = (state as any).temaVisual ?? "";
  const [tema, setTema] = React.useState<string>(temaSalvo);

  /**
   * ⚠️ CORRIGIDO (21/09/2026) — ESTA ETAPA ERA FALSA.
   *
   * ANTES existia aqui um array `prompts` HARDCODED com 4 frases fixas e
   * `gerarPrompts` fazia só isso:
   *
   *     await new Promise((r) => setTimeout(r, 1200));
   *     setState(imagens: prompts.map((p, i) => ({ ...p,
   *        prompt: `${p.prompt} · variação ${i + 1}` })));
   *
   * Ou seja: dormia 1,2 s e acrescentava "· variação N" numa lista FIXA.
   * Nunca lia `state.letra` e nunca chamava o backend. Daí a reclamação
   * "mesmo mudando a letra as opções são as mesmas" — eram literalmente
   * as mesmas, vinham de uma constante.
   *
   * AGORA: chama POST /api/imagens/gerar-prompts com a letra real e
   * guarda o que o agente devolve. Sem letra, avisa em vez de inventar.
   */
  const prompts: any[] = state.imagens || [];

  const gerarPrompts = async () => {
    const letra = (state.letra || "").trim();
    if (!letra) {
      toast.error("Não há letra para interpretar", {
        description: "Volte à etapa 01, escreva a letra e gere os prompts de novo.",
      });
      return;
    }

    setLoading(true);
    setErro(null);
    const id = toast.loading("Agente IA · interpretando a letra...");
    try {
      const r = await fetch(`${API_BASE}/api/imagens/gerar-prompts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lyrics: letra,
          description: state.title || "",
          music_prompt: "",
          theme: tema.trim(),
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      const lista: any[] = Array.isArray(json?.prompts) ? json.prompts : [];
      if (lista.length === 0) throw new Error("o agente não devolveu nenhum prompt");

      setState((s) => ({
        ...s,
        temaVisual: tema.trim(),
        imagens: lista.map((p, i) => ({
          beat: p.beat_id ?? i + 1,
          prompt: p.prompt,
          categoria: p.categoria ?? "",
          confianca: p.confianca ?? 0,
          checked: true,
        })),
      }));
      setMeta({ mood: json.mood, estilo: json.estilo, tema_nome: json.tema_nome });

      toast.success(`${lista.length} cenas geradas a partir da letra`, {
        id,
        description: `${json.tema_nome ? `Tema: ${json.tema_nome} · ` : ""}Mood: ${json.mood} · avance para buscar as mídias`,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setErro(msg);
      toast.error("Falha ao gerar os prompts", {
        id,
        description: `O backend na porta 8300 respondeu? (${msg})`,
      });
    } finally {
      setLoading(false);
    }
  };

  const togglePrompt = (i: number) => {
    setState((s) => ({
      ...s,
      imagens: (s.imagens || []).map((p, j) => (j === i ? { ...p, checked: !p.checked } : p)),
    }));
  };

  return (
    <div className="flex flex-col gap-5">
      <StepHeader
        step="04"
        title="Direção visual & prompts"
        description="Agente de IA lê a letra e sugere imagens por beat. Ajuste antes de buscar."
        icon={<ImagePlus className="h-5 w-5" />}
        accent="warn"
      />

      {/* ⚠️ NOVO (23/09/2026) — TEMA VISUAL LIVRE (opcional). */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-fg-1">
              Tema visual (opcional) — o que você quer ver no clipe?
            </label>
            <Input
              value={tema}
              onChange={(e) => setTema(e.target.value)}
              placeholder='Ex.: "chuva lenta", "carros antigos", "vôlei de praia", "futebol com amigos"…'
            />
            <span className="text-[11.5px] text-fg-3">
              Catalogar todos os temas é impossível: digite o seu. Ele direciona TODAS as cenas
              (a letra continua influindo nas emoções). Deixe vazio para o agente seguir só a letra.
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Prompts de busca por beat</CardTitle>
              <CardDescription>A IA lê a letra e cria um termo de busca por beat — eles alimentam a etapa 05. Você também pode buscar por conta própria lá.</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {/* ⚠️ NOVO (23/09/2026): o botão estava MORTO (sem onClick).
                  Dispara um evento que o shell escuta para abrir o diálogo
                  de chaves (o diálogo vive no shell, acima de tudo). */}
              <AvisoStatusChaves />
              <Button size="sm" variant="neon" loading={loading} onClick={gerarPrompts}>
                <Wand2 className="h-3.5 w-3.5" />
                Gerar cenas da letra com IA
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {prompts.length === 0 ? (
            <div className="rounded-sm border border-dashed border-white/10 bg-bg-2/40 p-6 text-center">
              <ImagePlus className="mx-auto h-7 w-7 text-fg-3" />
              <p className="mt-2 text-[13px] text-fg-1">
                Nenhum prompt ainda — nada aqui é inventado.
              </p>
              <p className="mt-1 text-[12px] text-fg-3">
                Clique em <span className="text-fg-1">Gerar cenas da letra com IA</span> para o agente
                ler a letra da etapa 01 e criar uma cena por beat.
                {(state.letra || "").trim() ? "" : " (a letra ainda está vazia.)"}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {prompts.map((p: any, i: number) => (
                <motion.div
                  key={`${p.beat}-${i}`}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className={cn(
                    "flex gap-3 rounded-sm border p-3 transition-colors",
                    p.checked
                      ? "bg-bg-3/50 border-neon/25"
                      : "bg-bg-2/50 border-white/5 hover:border-white/10"
                  )}
                >
                  <label className="pt-0.5">
                    <input
                      type="checkbox"
                      checked={!!p.checked}
                      onChange={() => togglePrompt(i)}
                      className="accent-neon h-4 w-4"
                    />
                  </label>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <Badge variant="subtle" className="text-[10px] font-mono">
                        Beat {String(p.beat ?? i + 1).padStart(2, "0")}
                      </Badge>
                      <div className="flex items-center gap-2">
                        {typeof p.confianca === "number" && p.confianca > 0 && (
                          <span className="text-[10px] text-fg-3 font-mono">
                            conf {Math.round(p.confianca * 100)}%
                          </span>
                        )}
                        <CheckCircle2 className={cn("h-3.5 w-3.5", p.checked ? "text-neon" : "text-fg-3")} />
                      </div>
                    </div>
                    <p className="text-[13px] text-fg-1 leading-snug">{p.prompt}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {meta && (
            <p className="mt-3 text-[11px] text-fg-3 font-mono">
              mood detectado: {meta.mood} · estilo: {meta.estilo}
            </p>
          )}
          {erro && (
            <p className="mt-2 text-[12px] text-red-400">
              Último erro: {erro}. Confira se o backend está de pé na porta 8300.
            </p>
          )}
          {prompts.length > 0 && (
            <div className="mt-4 flex items-center justify-between">
              <Button variant="ghost" size="sm" onClick={() => setStep("midia")}>
                Ir buscar as mídias destes prompts <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
              <Button variant="outline" size="sm" onClick={gerarPrompts} loading={loading}>
                <Wand2 className="h-3.5 w-3.5" /> Regerar
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   ETAPA 05 · MÍDIA (galeria)
   ═══════════════════════════════════════════════════════ */

/* Tipos do que a API /api/midia/buscar devolve (nomes em PT, mapeados no backend) */
type MidiaStock = {
  id: string;
  titulo?: string | null;
  url_thumbnail?: string | null;
  url_full?: string | null;
  url_preview?: string | null;
  video_url?: string | null;
  tipo?: string | null;
  provider?: string | null;
  duracao?: number | null;
  /**
   * Dimensões. O stock devolve (Pexels/Pixabay). Sem elas não dá para saber
   * se a mídia vai ser cortada no formato escolhido — `0` ou ausente = "?".
   */
  largura?: number | null;
  altura?: number | null;
  /** Qual prompt da letra produziu esta mídia (só existe na busca por letra). */
  origem?: string | null;
};

/** Uma mídia escolhida, na ordem em que entra no clipe, com o seu efeito. */
type MidiaEscolhida = {
  i: number;          // índice dentro de `resultados` (só para marcar o card)
  url: string;        // imagem/vídeo em tamanho usable pelo render
  thumb: string;
  tipo: string;       // FOTO | VIDEO
  provider: string;
  titulo: string;
  origem: string;
  efeito: string;
};

/**
 * Efeitos REAIS — são os mesmos ids que o `html_renderer` do backend
 * transforma em animação CSS (`.fx-*`). Não inventar nomes aqui: se o id
 * não existir lá, a imagem entra sem movimento nenhum.
 */
const EFEITOS_IMAGEM: Array<{ id: string; nome: string }> = [
  { id: "ken_burns", nome: "Ken Burns (padrão)" },
  { id: "zoom_in",   nome: "Zoom aproximando" },
  { id: "zoom_out",  nome: "Zoom afastando" },
  { id: "pan_left",  nome: "Panorâmica ←" },
  { id: "pan_right", nome: "Panorâmica →" },
  { id: "static",    nome: "Parada (sem movimento)" },
];

function Step5Midia({ onNext }: { onNext: () => void }) {
  const { state, setState, setStep } = useStudio();
  const [buscando, setBuscando] = React.useState(false);
  /* ⚠️ NOVO (22/09/2026) — FILTROS DE BUSCA da etapa 05.
     · tipo: "ambos" | "foto" | "video" — mandar só fotos ou só vídeos pro clipe.
     · orientacaoEntrada: orientação PEDIDA PARA A BUSCA de mídia (retrato/
       paisagem/quadrado) — independente do formato de saída, que só é
       escolhido na geração. "qualquer" não filtra. Mídia sem dimensões (?)
       nunca é escondida. */
  const [filtroTipo, setFiltroTipo] = React.useState<"ambos" | "foto" | "video">("ambos");
  const [orientacaoEntrada, setOrientacaoEntrada] = React.useState<"qualquer" | "retrato" | "paisagem" | "quadrado">("qualquer");
  const [q, setQ] = React.useState("");
  const [resultados, setResultados] = React.useState<MidiaStock[]>([]);
  const [buscou, setBuscou] = React.useState(false);
  const [termosUsados, setTermosUsados] = React.useState<string[]>([]);

  /**
   * ⚠️ CORRIGIDO (21/09/2026) — A BUSCA IGNORAVA A LETRA.
   *
   * O campo de busca começava com o termo FIXO "city night cinematic" e
   * não tinha nenhuma ligação com a etapa 04. Somado à etapa 04 falsa,
   * o efeito era exatamente o relatado: mudar a letra não mudava nada.
   *
   * AGORA os prompts gerados pela IA a partir da letra alimentam a busca:
   *  - viram sugestões clicáveis;
   *  - e, ao entrar na etapa, disparam a busca automaticamente.
   */
  const sugestoes = React.useMemo(
    () =>
      (state.imagens || [])
        .map((p: any) => String(p?.prompt || "").trim())
        .filter(Boolean),
    [state.imagens]
  );

  /* Preenche o campo com o 1º prompt da letra enquanto o usuário não digitar. */
  const digitou = React.useRef(false);
  React.useEffect(() => {
    if (digitou.current) return;
    if (sugestoes.length > 0) setQ(sugestoes[0]);
  }, [sugestoes]);

  const buscarVarios = async (termos: string[]) => {
    const limpos = termos.map((t) => t.trim()).filter(Boolean);
    if (limpos.length === 0) return;

    setBuscando(true);
    const id = toast.loading(
      limpos.length === 1
        ? `Buscando: "${limpos[0]}"`
        : `Buscando ${limpos.length} cenas da letra...`
    );
    try {
      const grupos = await Promise.all(
        limpos.map(async (t) => {
          const r = await fetch(`${API_BASE}/api/midia/buscar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // ⚠️ NOVO (22/09/2026): filtros de tipo (só fotos/só vídeos) e
            // orientação compatível com o formato de saída vão NA BUSCA —
            // o provedor já devolve só o que interessa.
            body: JSON.stringify({
              query: t,
              max_results: 8,
              apenas_fotos: filtroTipo === "foto",
              apenas_videos: filtroTipo === "video",
            }),
          });
          if (!r.ok) throw new Error(`HTTP ${r.status} em "${t}"`);
          const json: { resultados?: MidiaStock[] } = await r.json();
          let lista = Array.isArray(json.resultados) ? json.resultados : [];
          if (orientacaoEntrada !== "qualquer") {
            // ⚠️ CORRIGIDO (22/09/2026): a escolha de orientação é da ENTRADA
            // (o que você quer buscar), não da saída — que só se decide na
            // geração. A orientação é escolhida aqui, na mão.
            lista = lista.filter((m) => {
              const w = m.largura ?? 0;
              const h = m.altura ?? 0;
              if (!w || !h) return true; // sem dimensão, não corta ninguém
              const r2 = w / h;
              if (orientacaoEntrada === "retrato") return r2 < 0.85;
              if (orientacaoEntrada === "paisagem") return r2 > 1.15;
              return r2 >= 0.85 && r2 <= 1.15; // quadrado
            });
          }
          return lista
            .filter((m) => m.url_thumbnail || m.url_preview)
            .map((m) => ({ ...m, origem: t }));
        })
      );

      const novos = grupos.flat();
      /* ⚠️ NOVO (23/09/2026): a busca ACUMULA em vez de substituir.
         Antes: entrar na etapa já buscava as 3 primeiras cenas; clicar em
         "Buscar tudo da letra" buscava as MESMAS cenas e a grade ficava
         idêntica — parecia que o botão não fazia nada. Agora cada busca
         (letra, tema ou termo livre) ADICIONA opções novas à grade. */
      const vistos = new Set(resultados.map((m) => m.id));
      const extras = novos.filter((m) => !vistos.has(m.id));
      setResultados([...resultados, ...extras]);
      setBuscou(true);
      setTermosUsados((prev) => [...new Set([...prev, ...limpos])]);

      if (extras.length === 0) {
        toast.info("Esses termos já estão na grade", {
          id,
          description: "Tente um tema rápido acima ou escrever outro termo.",
        });
      } else {
        toast.success(`${extras.length} novas mídias na grade`, {
          id,
          description:
            limpos.length > 1
              ? `De ${limpos.length} buscas: ${limpos[0]}, ${limpos[1]}…`
              : `Busca: "${limpos[0]}"`,
        });
      }
    } catch (e) {
      setBuscou(false);
      toast.error("A busca falhou", {
        id,
        description: `Verifique se o backend está rodando na porta 8300. (${e instanceof Error ? e.message : e})`,
      });
    } finally {
      setBuscando(false);
    }
  };

  /* Busca automática ao chegar na etapa: se a letra já virou prompts,
     a grade já nasce com as cenas da música — não com imagens locais. */
  const auto = React.useRef(false);
  React.useEffect(() => {
    if (auto.current) return;
    if (sugestoes.length === 0) return;
    auto.current = true;
    void buscarVarios(sugestoes.slice(0, 3));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sugestoes]);

  const doSearch = async () => {
    digitou.current = true;
    await buscarVarios([q]);
  };

  const buscarPelaLetra = async () => {
    if (sugestoes.length === 0) {
      toast.error("Ainda não há prompts da letra", {
        description: "Volte à etapa 04 e clique em “Gerar cenas da letra com IA”.",
      });
      return;
    }
    await buscarVarios(sugestoes.slice(0, 6));
  };

  /* ⚠️ NOVO (23/09/2026) — TEMAS DE BUSCA RÁPIDA.
     Casos de uso reais (ex.: vídeo de chuva com música de fundo, clipe
     animado com gente dançando) não dependem da letra: a pessoa quer
     buscar por TEMA com um clique. Cada chip roda uma busca multi-termo
     imediatamente. */
  const TEMAS: Array<{ rotulo: string; emoji: string; termos: string[] }> = [
    { rotulo: "Chuva",         emoji: "🌧️", termos: ["rain window", "rain city night", "storm clouds lightning"] },
    { rotulo: "Natureza",      emoji: "🌿", termos: ["forest fog", "waterfall aerial", "ocean waves sunset"] },
    { rotulo: "Dança",         emoji: "💃", termos: ["person dancing street", "dance silhouette neon", "crowd dancing concert"] },
    { rotulo: "Cidade",        emoji: "🌃", termos: ["city night lights", "urban traffic timelapse", "neon street rain"] },
    { rotulo: "Relâmpago",     emoji: "⚡", termos: ["lightning storm sky", "thunderstorm timelapse"] },
    { rotulo: "Espaço",        emoji: "🚀", termos: ["space stars nebula", "galaxy timelapse", "moon night sky"] },
    { rotulo: "Amor",          emoji: "❤️", termos: ["couple sunset silhouette", "holding hands closeup", "romantic candle light"] },
    { rotulo: "Festa",         emoji: "🎉", termos: ["party fireworks", "friends celebrating night", "confetti crowd"] },
  ];
  const [temaAtivo, setTemaAtivo] = React.useState<string>("");

  /**
   * ⚠️ CORRIGIDO (21/09/2026)
   *
   * ANTES: o botão "Buscar" chamava a API, mostrava um toast com o total e
   * JOGAVA OS RESULTADOS FORA — nunca guardava em state. A grade renderizava
   * um array `galeria` FIXO com 8 imagens LOCAIS do programa. O usuário
   * clicava em Buscar, via "Encontradas 15 mídias" e a tela continuava com
   * as imagens do próprio app — daí "as imagens ali são do programa, não de
   * busca da internet".
   *
   * AGORA: só existem duas situações — ou a grade mostra os resultados reais
   * do banco de stock, ou mostra um aviso dizendo o que falta. As imagens
   * locais saíram de vez: elas eram a causa da confusão.
   */
  const usandoResultados = resultados.length > 0;

  /**
   * ⚠️ NOVO (21/09/2026) — ORIENTAÇÃO DA MÍDIA vs FORMATO DE SAÍDA.
   *
   * O banco de stock devolve `largura`/`altura`. Com isso dá para dizer
   * ANTES do render o que vai acontecer com cada mídia: se a orientação
   * bate com o formato escolhido, ela entra inteira; se não bate, o
   * `background-size: cover` CORTA o excesso pelo centro (sem distorção e
   * sem tarja preta, mas perdendo pedaço da imagem).
   *
   * Antes o usuário só descobria isso assistindo ao MP4 pronto.
   */
  const orientacaoDe = (m: MidiaStock): "retrato" | "paisagem" | "quadrado" | "?" => {
    const w = Number(m.largura) || 0;
    const h = Number(m.altura) || 0;
    if (!w || !h) return "?";
    const r = w / h;
    if (r < 0.85) return "retrato";
    if (r > 1.15) return "paisagem";
    return "quadrado";
  };

  const orientacaoSaida: "retrato" | "paisagem" | "quadrado" =
    state.formato === "16/9" || state.formato === "4/3" ? "paisagem" :
    state.formato === "1/1"                             ? "quadrado" :
                                                          "retrato";

  const itens = resultados.map((m, i) => {
    const orient = orientacaoDe(m);
    return {
      key: `${m.id}-${i}`,
      src: m.url_thumbnail || m.url_preview || "",
      tipo: (m.tipo || "").toLowerCase() === "video" ? "VIDEO" : "FOTO",
      provider: m.provider || "",
      titulo: m.titulo || m.origem || "",
      origem: m.origem || "",
      orient,
      // "corta" quando a orientação não bate com a saída escolhida.
      // "?" (sem dimensão) não é tratado como incompatível — é só aviso.
      corta: orient !== "?" && orient !== orientacaoSaida,
    };
  });

  /* Filtro de compatibilidade: só mídias que não serão cortadas. */
  const [soCompativeis, setSoCompativeis] = React.useState(false);
  const itensVisiveis = soCompativeis ? itens.filter((it) => !it.corta) : itens;
  const totalCortadas = itens.filter((it) => it.corta).length;

  /**
   * ⚠️ CORRIGIDO (21/09/2026) — A SELEÇÃO NÃO SOBREVIVIA À ETAPA.
   *
   * ANTES: `state.midia` guardava apenas os ÍNDICES (number[]) dentro de
   * `resultados`. Só que `resultados` é estado LOCAL deste componente: ao
   * sair da etapa 05 ele morre, e os índices passavam a não apontar para
   * nada. Pior: a etapa 06 NUNCA lia `state.midia` — o render ia direto
   * para o fim sem nenhuma imagem escolhida. Era o "vai pro fim sem
   * escolher as imagens".
   *
   * AGORA: guardamos a mídia inteira (url, thumb, tipo, provider) mais o
   * EFEITO de cada uma. A ordem do array é a ordem das cenas no clipe.
   */
  const escolhidas: MidiaEscolhida[] = Array.isArray(state.midia) ? state.midia : [];
  const sel = new Set<number>(
    escolhidas.map((m) => (m && typeof m === "object" ? m.i : -1)).filter((v) => v >= 0)
  );

  const salvar = (lista: MidiaEscolhida[]) => setState((s) => ({ ...s, midia: lista }));

  const toggle = (i: number) => {
    const m = resultados[i];
    if (!m) return;
    const atual = [...escolhidas];
    const pos = atual.findIndex((x) => x.i === i);
    if (pos >= 0) {
      atual.splice(pos, 1);
    } else {
      atual.push({
        i,
        // ⚠️ CORRIGIDO (22/09/2026): era `url_preview` — que carregava a
        // PÁGINA do provedor (pexels.com/photo/...), não o arquivo.
        // background-image/video com página não desenha nada: a camada ficava
        // transparente e o clipe saía todo AZUL (fundo do tema VOX_EDITORIAL
        // #1A1A2E), sem nenhuma mídia. Agora vai o ARQUIVO real: url_full
        // (foto .jpeg original / vídeo .mp4) com fallbacks.
        url: m.url_full || m.video_url || m.url_thumbnail || m.url_preview || "",
        thumb: m.url_thumbnail || m.url_preview || "",
        tipo: (m.tipo || "").toLowerCase() === "video" ? "VIDEO" : "FOTO",
        provider: m.provider || "",
        titulo: m.titulo || m.origem || "",
        origem: m.origem || "",
        efeito: "ken_burns",
      });
    }
    salvar(atual);
  };

  const setEfeito = (pos: number, efeito: string) =>
    salvar(escolhidas.map((m, k) => (k === pos ? { ...m, efeito } : m)));

  const mover = (pos: number, dir: -1 | 1) => {
    const dest = pos + dir;
    if (dest < 0 || dest >= escolhidas.length) return;
    const atual = [...escolhidas];
    const temp = atual[pos];
    atual[pos] = atual[dest];
    atual[dest] = temp;
    salvar(atual);
  };

  const remover = (pos: number) => salvar(escolhidas.filter((_, k) => k !== pos));

  return (
    <div className="flex flex-col gap-5">
      <StepHeader
        step="05"
        title="Seleção de mídia"
        description="Busque fotos e vídeos gratuitos. Clique para selecionar por beat."
        icon={<FolderOpen className="h-5 w-5" />}
        accent="violet"
      />

      {/* Preview da arte do clip na seleção atual */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div>
              <CardTitle>Buscar no banco de stock</CardTitle>
              <CardDescription>Por cenas da letra, por tema rápido ou por termo livre. Pexels, Pixabay e mais.</CardDescription>
            </div>
            <div className="flex items-center gap-2 min-w-[360px]">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-fg-3" />
                <Input
                  value={q}
                  onChange={(e) => { digitou.current = true; setQ(e.target.value); }}
                  placeholder="Buscar: 'city lights cinematic'"
                  className="pl-9"
                  onKeyDown={(e) => e.key === "Enter" && doSearch()}
                />
              </div>
              <Button variant="neon" size="sm" loading={buscando} onClick={doSearch}>
                Buscar
              </Button>
            </div>

            {/* ⚠️ NOVO (22/09/2026) — FILTROS DA BUSCA: tipo de mídia e
                orientação compatível com o formato de saída. Aplicam em
                todas as buscas (manual, cena da letra e "buscar tudo"). */}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] uppercase tracking-wide text-fg-3 font-mono">tipo</span>
                <div className="flex rounded-sm border border-white/10 overflow-hidden">
                  {(["ambos", "foto", "video"] as const).map((tp) => (
                    <button
                      key={tp}
                      type="button"
                      onClick={() => setFiltroTipo(tp)}
                      className={cn(
                        "px-2.5 py-1 text-[11px] transition-colors",
                        filtroTipo === tp
                          ? "bg-neon/15 text-fg-0 border-neon/40"
                          : "bg-bg-2/60 text-fg-2 hover:text-fg-0 border-transparent",
                        tp !== "ambos" && "border-l border-white/10"
                      )}
                    >
                      {tp === "ambos" ? "Ambos" : tp === "foto" ? "Só fotos" : "Só vídeos"}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] uppercase tracking-wide text-fg-3 font-mono">orientação</span>
                <div className="flex rounded-sm border border-white/10 overflow-hidden">
                  {(["qualquer", "retrato", "paisagem", "quadrado"] as const).map((or) => (
                    <button
                      key={or}
                      type="button"
                      onClick={() => setOrientacaoEntrada(or)}
                      className={cn(
                        "px-2.5 py-1 text-[11px] capitalize transition-colors",
                        orientacaoEntrada === or
                          ? "bg-neon/15 text-fg-0 border-neon/40"
                          : "bg-bg-2/60 text-fg-2 hover:text-fg-0 border-transparent",
                        or !== "qualquer" && "border-l border-white/10"
                      )}
                    >
                      {or}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ⚠️ NOVO (23/09/2026) — TEMAS RÁPIDOS: mídia à escolha do usuário,
              independente da letra (vídeo de chuva com música de fundo,
              clipe animado com gente dançando…). Cada chip já roda a busca
              com vários termos e ADICIONA à grade. */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-[11px] uppercase tracking-wide text-fg-3 font-mono">
              temas rápidos
            </span>
            {TEMAS.map((t) => (
              <button
                key={t.rotulo}
                type="button"
                disabled={buscando}
                onClick={async () => {
                  setTemaAtivo(t.rotulo);
                  setQ(t.termos[0]);
                  await buscarVarios(t.termos);
                }}
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[11px] transition-colors",
                  temaAtivo === t.rotulo
                    ? "border-neon/40 bg-neon/10 text-fg-0"
                    : "border-white/10 bg-bg-2/60 text-fg-2 hover:border-white/25 hover:text-fg-0"
                )}
                title={`Buscar: ${t.termos.join(", ")}`}
              >
                {t.emoji} {t.rotulo}
              </button>
            ))}
          </div>

          {/* Cenas que a IA tirou da letra — clicar busca só aquela cena.
              ⚠️ DEDUP (23/09/2026): 112 beats viravam 100+ chips repetidos
              ("dark city" ×30). Agora cada termo aparece UMA vez, com um
              contador quando a cena é repetida. */}
          {(() => {
            const vistos = new Map<string, number>();
            const chips = sugestoes.map((s) => {
              const n = (vistos.get(s) ?? 0) + 1;
              vistos.set(s, n);
              return { s, n };
            });
            return chips.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-[11px] uppercase tracking-wide text-fg-3 font-mono">
                  cenas da letra
                </span>
                {chips.map(({ s, n }, i) => (
                  <button
                    key={`${s}-${i}`}
                    type="button"
                    onClick={async () => { setQ(s); await buscarVarios([s]); }}
                    className={cn(
                      "rounded-full border px-2.5 py-1 text-[11px] transition-colors",
                      q === s
                        ? "border-neon/40 bg-neon/10 text-fg-0"
                        : "border-white/10 bg-bg-2/60 text-fg-2 hover:border-white/25 hover:text-fg-0"
                    )}
                    title={n > 1 ? `“${s}” aparece em ${n} beats — clique para buscar esta cena` : `Buscar esta cena`}
                  >
                    {s}{n > 1 && <span className="ml-1 text-[9.5px] text-fg-3">×{n}</span>}
                  </button>
                ))}
                <Button
                  size="sm"
                  variant="outline"
                  loading={buscando}
                  onClick={buscarPelaLetra}
                  className="ml-auto"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Buscar tudo da letra
                </Button>
              </div>
            );
          })()}
        </CardHeader>

        <CardContent>
          {!usandoResultados ? (
            <div className="rounded-sm border border-dashed border-white/10 bg-bg-2/40 p-8 text-center">
              <Search className="mx-auto h-7 w-7 text-fg-3" />
              <p className="mt-2 text-[13px] text-fg-1">
                {sugestoes.length === 0
                  ? "A busca ainda não tem o que procurar."
                  : "Nenhuma mídia voltou do banco de stock."}
              </p>
              <p className="mt-1 text-[12px] text-fg-3">
                {sugestoes.length === 0
                  ? "Volte à etapa 04 e gere os prompts com IA — a busca usa as cenas que o agente tira da letra."
                  : "Tente “Buscar tudo da letra” de novo ou escreva outro termo (em inglês costuma render mais)."}
              </p>
              {sugestoes.length === 0 && (
                <Button size="sm" variant="neon" className="mt-4" onClick={() => setStep("imagens")}>
                  <ArrowLeft className="h-3.5 w-3.5" /> Ir para a etapa 04
                </Button>
              )}
            </div>
          ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {itensVisiveis.map((item) => {
              const i = itens.indexOf(item);
              const isSel = sel.has(i);
              return (
                <motion.button
                  type="button"
                  key={item.key}
                  whileHover={{ y: -2 }}
                  onClick={() => toggle(i)}
                  className={cn(
                    "group relative aspect-video overflow-hidden rounded-sm border transition-all",
                    isSel
                      ? "border-neon ring-2 ring-neon/40 shadow-[0_0_24px_-6px_rgba(34,211,238,0.5)]"
                      : "border-white/5 hover:border-white/15"
                  )}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.src}
                    alt={item.titulo}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                  {/* canto superior-esquerdo: o que acontece com esta mídia */}
                  <div className="absolute left-2 top-2 flex items-center gap-1">
                    <span
                      className={cn(
                        "rounded-sm border px-1.5 py-0.5 text-[9.5px] font-semibold uppercase tracking-wide backdrop-blur",
                        item.orient === "?"
                          ? "border-white/20 bg-black/40 text-white/70"
                          : item.corta
                            ? "border-warn/50 bg-warn/20 text-warn"
                            : "border-ok/50 bg-ok/20 text-ok"
                      )}
                      title={
                        item.orient === "?"
                          ? "orientação desconhecida"
                          : item.corta
                            ? `Esta mídia é ${item.orient} e a saída é ${orientacaoSaida} — o render corta o excesso pelo centro`
                            : `Compatível com a saída ${state.formato}`
                      }
                    >
                      {item.orient === "?" ? "?" : item.corta ? "corta" : "ok"}
                    </span>
                  </div>

                  <div className="absolute bottom-2 left-2 right-2 flex items-end justify-between gap-2">
                    <Badge variant={item.tipo === "VIDEO" ? "neon" : "default"} className="text-[10px] backdrop-blur">
                      {item.tipo}{item.provider ? ` · ${item.provider}` : ""}
                    </Badge>
                    {item.origem && (
                      <span className="truncate text-[10px] text-white/80 font-mono">
                        {item.origem}
                      </span>
                    )}
                    <div className={cn(
                      "flex h-6 w-6 items-center justify-center rounded-full border backdrop-blur",
                      isSel
                        ? "bg-neon border-neon-2 text-black"
                        : "bg-black/40 border-white/20 text-transparent group-hover:text-fg-0"
                    )}>
                      <CheckCircle2 className="h-4 w-4" strokeWidth={2.6} />
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>
          )}

          {/* Aviso + filtro de compatibilidade com o formato de saída */}
          {usandoResultados && (
            <div className="mt-4 rounded-sm border border-white/8 bg-bg-2/50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[12px] text-fg-2">
                  Saída em <span className="font-mono text-fg-0">{state.formato}</span> ({orientacaoSaida}).
                  {totalCortadas === 0
                    ? " Todas as mídias desta busca são compatíveis."
                    : ` ${totalCortadas} de ${itens.length} serão CORTADAS pelo centro (sem distorção, sem tarja).`}
                </p>
                <label className="flex cursor-pointer items-center gap-2 text-[12px] text-fg-2">
                  <input
                    type="checkbox"
                    checked={soCompativeis}
                    onChange={(e) => setSoCompativeis(e.target.checked)}
                    className="h-3.5 w-3.5 accent-neon"
                  />
                  Mostrar só as compatíveis
                </label>
              </div>
            </div>
          )}

          <div className="mt-4 flex items-center justify-between text-[12px] text-fg-2">
            <div className="flex items-center gap-2">
              <Badge variant="neon">{escolhidas.length} selecionadas</Badge>
              <span>/ {itensVisiveis.length} visíveis</span>
              {usandoResultados && termosUsados.length > 0 && (
                <span className="text-fg-3">
                  · {termosUsados.length === 1
                      ? `resultados de “${termosUsados[0]}”`
                      : `${termosUsados.length} cenas da letra`}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setResultados([]);
                  setBuscou(false);
                  setState((s) => ({ ...s, midia: [] }));
                }}
              >
                Limpar
              </Button>
              <Button size="sm" variant="outline"><Upload className="h-3.5 w-3.5" /> Upload manual</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/*
        ⚠️ NOVO (21/09/2026) — o fluxo terminava sem esta tela existir.
        Aqui o usuário vê exatamente o que vai entrar no vídeo, em que ordem
        e com qual efeito por imagem. Antes não havia nada disso: dava para
        chegar na etapa 06 sem ter escolhido uma única imagem.
      */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Sequência do clipe</CardTitle>
              <CardDescription>
                As cenas na ordem em que aparecem, cada uma com o efeito que você escolheu.
              </CardDescription>
            </div>
            <Badge variant={escolhidas.length > 0 ? "neon" : "default"}>
              {escolhidas.length} {escolhidas.length === 1 ? "cena" : "cenas"}
            </Badge>
          </div>
        </CardHeader>

        <CardContent>
          {escolhidas.length === 0 ? (
            <div className="rounded-sm border border-dashed border-white/10 bg-bg-2/40 p-6 text-center">
              <ImagePlus className="mx-auto h-6 w-6 text-fg-3" />
              <p className="mt-2 text-[13px] text-fg-1">Nenhuma imagem escolhida ainda.</p>
              <p className="mt-1 text-[12px] text-fg-3">
                Clique nas fotos e vídeos acima. É esta seleção que entra no vídeo — sem ela
                o clipe é montado no escuro.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {escolhidas.map((m, k) => (
                <div
                  key={`${m.i}-${k}`}
                  className="flex flex-wrap items-center gap-3 rounded-sm border border-white/5 bg-bg-2/40 p-2"
                >
                  <span className="w-6 shrink-0 text-center font-mono text-[11px] text-fg-3">
                    {k + 1}
                  </span>

                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={m.thumb || m.url}
                    alt={m.titulo}
                    className="h-12 w-20 shrink-0 rounded-sm object-cover"
                  />

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[12.5px] text-fg-1">{m.titulo || "sem título"}</p>
                    <p className="truncate font-mono text-[11px] text-fg-3">
                      {m.tipo}
                      {m.provider ? ` · ${m.provider}` : ""}
                    </p>
                  </div>

                  {/* Efeito desta imagem — vai para o backend e vira animação CSS */}
                  <select
                    value={m.efeito || "ken_burns"}
                    onChange={(e) => setEfeito(k, e.target.value)}
                    title="efeito aplicado só nesta imagem"
                    className="h-8 shrink-0 rounded-sm border border-white/10 bg-bg-3 px-2 text-[12px] text-fg-1 outline-none focus:border-neon/40"
                  >
                    {EFEITOS_IMAGEM.map((e) => (
                      <option key={e.id} value={e.id}>{e.nome}</option>
                    ))}
                  </select>

                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      size="sm" variant="ghost"
                      onClick={() => mover(k, -1)} disabled={k === 0}
                      title="subir na sequência"
                    >↑</Button>
                    <Button
                      size="sm" variant="ghost"
                      onClick={() => mover(k, 1)} disabled={k === escolhidas.length - 1}
                      title="descer na sequência"
                    >↓</Button>
                    <Button
                      size="sm" variant="ghost"
                      onClick={() => remover(k)}
                      title="tirar do clipe"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <span className="text-[12px] text-fg-3">
          {escolhidas.length === 0
            ? "Escolha ao menos uma imagem antes de gerar."
            : `${escolhidas.length} cenas · ${new Set(escolhidas.map((m) => m.efeito)).size} efeito(s) diferente(s)`}
        </span>
        {/* ⚠️ REMOVIDO (23/09/2026): o botão "Ir para gerar" aqui duplicava
            o "Ir para gerar" do rodapé do wizard — mesmo onNext, confusão.
            O rodapé (Voltar / Ir para gerar) é a navegação única. */}
        <span className="text-[11.5px] text-fg-3 font-mono hidden md:block">
          Use “Ir para gerar” abaixo quando terminar →
        </span>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   ETAPA 06 · GERAR (long-running + WebSocket)
   ═══════════════════════════════════════════════════════ */

function Step6Gerar() {
  const { state, setState, setStep } = useStudio();
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [pct, setPct] = React.useState(0);
  const [etapa, setEtapa] = React.useState("Aguardando início");
  const [done, setDone] = React.useState(false);
  const [falha, setFalha] = React.useState<string | null>(null);
  const [resultado, setResultado] = React.useState<{ download_url: string; output_path?: string } | null>(null);
  const [logs, setLogs] = React.useState<string[]>([]);
  /* ⚠️ number, não ReturnType<typeof window.setTimeout>: no browser o retorno é
     number, mas o tipo global Timeout do @types/node colide e gerava TS2322. */
  const pollingRef = React.useRef<number | null>(null);
  const finalizadoRef = React.useRef(false);
  const tentativasPollingRef = React.useRef(0);

  React.useEffect(() => () => {
    if (pollingRef.current !== null) window.clearTimeout(pollingRef.current);
  }, []);

  const pararPolling = () => {
    if (pollingRef.current !== null) {
      window.clearTimeout(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const registrarFalha = (mensagem: string) => {
    if (finalizadoRef.current) return;
    finalizadoRef.current = true;
    pararPolling();
    setDone(false);
    setFalha(mensagem);
    setEtapa("Render não concluído");
    setLogs((l) => [...l, `erro: ${mensagem}`].slice(-30));
    toast.error("Não foi possível gerar o clipe", { description: mensagem });
  };

  const tratarFimDoJob = (job: {
    status?: string;
    error?: string;
    resultado?: { download_url?: string; output_path?: string };
  }) => {
    if (finalizadoRef.current) return;

    if (job.status === "done") {
      const url = job.resultado?.download_url;
      if (!url) {
        registrarFalha("O render terminou sem informar um arquivo MP4.");
        return;
      }
      finalizadoRef.current = true;
      pararPolling();
      setResultado({ download_url: url, output_path: job.resultado?.output_path });
      setFalha(null);
      setDone(true);
      setPct(100);
      setEtapa("Render concluído · MP4 pronto");
      setLogs((l) => [...l, "concluído: MP4 disponível para assistir e baixar"].slice(-30));
      toast.success("Clipe gerado", { description: "O arquivo MP4 está pronto." });
      return;
    }

    registrarFalha(job.error || "O backend não conseguiu finalizar a renderização.");
  };

  const monitorarJob = (id: string) => {
    const consultar = async () => {
      try {
        const resposta = await fetch(`${API_BASE}/api/jobs/${encodeURIComponent(id)}`);
        if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
        const job = await resposta.json();
        tentativasPollingRef.current = 0;

        if (job.status === "done" || job.status === "error") {
          tratarFimDoJob(job);
          return;
        }

        if (typeof job.progress === "number") {
          setPct((atual) => Math.max(atual, job.progress));
        }
        if (job.etapa) setEtapa(String(job.etapa));
        pollingRef.current = window.setTimeout(() => void consultar(), 1000);
      } catch {
        tentativasPollingRef.current += 1;
        if (tentativasPollingRef.current >= 3) {
          registrarFalha("O acompanhamento do job perdeu conexão com o backend.");
          return;
        }
        pollingRef.current = window.setTimeout(() => void consultar(), 1000);
      }
    };

    pararPolling();
    void consultar();
  };

  const abrirWS = (id: string) => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const hostApi = API_BASE
      ? API_BASE.replace(/^https?:\/\//, "").replace(/\/$/, "")
      : "127.0.0.1:8300";
    const ws = new WebSocket(`${proto}://${hostApi}/ws/jobs/${id}`);

    ws.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data);
        if (d.type === "event" && d.event === "progress") {
          setPct((atual) => Math.max(atual, Number(d.data?.pct) || 0));
          setEtapa(`${d.data?.etapa || "render"} · ${d.data?.msg || ""}`);
          setLogs((l) => [...l, `${d.data?.etapa || "render"}: ${d.data?.msg || ""}`].slice(-30));
        } else if (d.type === "fim") {
          tratarFimDoJob(d);
          ws.close();
        }
      } catch {
        setLogs((l) => [...l, "aviso: mensagem inválida recebida do job"].slice(-30));
      }
    };
    ws.onerror = () => {
      setLogs((l) => [...l, "aviso: WebSocket indisponível; acompanhando pela API"].slice(-30));
    };
  };

  const gerar = async () => {
    pararPolling();
    finalizadoRef.current = false;
    tentativasPollingRef.current = 0;
    setDone(false); setFalha(null); setResultado(null); setPct(0); setLogs([]);
    setEtapa("Enfileirando render...");

    if (!state.musica.arquivo) {
      toast.error("Envie a música antes de gerar", {
        description: "O clipe é montado em cima da sua música (etapa 02).",
      });
      return;
    }

    /**
     * ⚠️ CORRIGIDO (21/09/2026) — O RENDER IGNORAVA AS IMAGENS ESCOLHIDAS.
     *
     * ANTES o corpo do POST levava só `project` e `audio_path`. As mídias
     * marcadas na etapa 05 ficavam no estado do navegador e nunca saíam
     * dele: o backend montava o clipe por conta própria. Era o "vai pro fim
     * sem escolher as imagens".
     *
     * AGORA a seleção viaja: `project.images` (lista de URLs, já entendida
     * pelo backend de hoje) e `selected_media` (url + efeito por cena,
     * usado quando o backend estiver com o código novo).
     */
    const escolhidas: MidiaEscolhida[] = Array.isArray(state.midia) ? state.midia : [];
    if (escolhidas.length === 0) {
      toast.error("Nenhuma imagem escolhida", {
        description: "Volte à etapa 05 e marque as cenas do clipe — é essa seleção que entra no vídeo.",
      });
      setStep("midia");
      return;
    }

    const toastId = toast.loading("Enfileirando render...");
    try {
      const r = await fetch(`${API_BASE}/api/jobs/gerar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project: {
            lyrics: state.letra,
            title: state.title,
            description: state.letra.slice(0, 300),
            // URLs na ordem da sequência montada na etapa 05.
            images: escolhidas.map((m) => m.url).filter(Boolean),
            // Proporção da saída (vertical, horizontal, quadrado, 3:4, 4:3).
            format: state.formato,
            // Efeito por cena.
            efeitos: escolhidas.map((m) => m.efeito || "ken_burns"),
            // ⚠️ NOVO (22/09/2026): estilo da legenda escolhido na etapa 03.
            legenda_estilo: state.legendaEstilo,
          },
          // ⚠️ NOVO (22/09/2026): legendas com os tempos REAIS da transcrição
          // (Whisper da etapa 03). O backend monta o SRT a partir delas —
          // sincronia de verdade com o áudio. Sem transcrição, manda vazio
          // e o backend cai no SRT por blocos da letra.
          // ⚠️ CORRIGIDO (23/09/2026): a transcrição guarda os tempos como
          // `start`/`end` (string) e o filtro exigia `inicio`/`fim` number —
          // resultava em lista SEMPRE vazia e o render perdia a sincronia do
          // Whisper. Aceita os dois formatos; texto vazio não vai (fica sem
          // legenda naquela janela, sem faixa em branco no vídeo).
          subtitle_lines: (Array.isArray(state.legenda) ? state.legenda : [])
            .map((l: any) => ({
              inicio: Number(l?.inicio ?? l?.start ?? NaN),
              fim: Number(l?.fim ?? l?.end ?? NaN),
              texto: String(l?.texto || "").trim(),
            }))
            .filter((l) => isFinite(l.inicio) && isFinite(l.fim) && l.fim > l.inicio && l.texto)
            .map(({ inicio, fim, texto }) => ({ inicio, fim, texto })),
          selected_media: escolhidas.map((m, i) => ({
            url: m.url,
            tipo: m.tipo,
            provider: m.provider,
            efeito: m.efeito || "ken_burns",
            ordem: i,
          })),
          // A música PRONTA é a fonte oficial da trilha (Opção A).
          audio_path: state.musica.arquivo,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      if (typeof data.job_id !== "string" || !data.job_id) {
        throw new Error("O backend não retornou o identificador do job.");
      }

      setJobId(data.job_id);
      setLogs([`job: ${data.job_id}`, "start: engine.py · MusicClipEngine v2"]);
      toast.success("Job criado", { id: toastId, description: data.job_id });
      monitorarJob(data.job_id);
      abrirWS(data.job_id);
    } catch (erro) {
      const detalhe = erro instanceof Error ? erro.message : "Não foi possível iniciar o job de renderização.";
      toast.error("Não foi possível iniciar a renderização", { id: toastId, description: detalhe });
      registrarFalha(detalhe);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <StepHeader
        step="06"
        title="Gerar clipe final"
        description="Renderização completa: frames, vídeo, áudio e legendas. Acompanhe em tempo real."
        icon={<MonitorPlay className="h-5 w-5" />}
        accent="ok"
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-4">
        {/* Esquerda — preview de saída + progresso */}
        <Card>
          <CardHeader>
            <CardTitle>Progresso da renderização</CardTitle>
            <CardDescription>
              {jobId ? `Job ID: ${jobId}` : "Clique em 'Gerar clipe' para começar."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Preview placeholder */}
            <div className="relative aspect-video overflow-hidden rounded-sm border border-white/5 bg-bg-0">
              <div className="absolute inset-0 bg-studio-grid opacity-40" />
              <div className="absolute inset-0 bg-gradient-to-br from-neon/10 via-transparent to-violet-500/10" />
              <div className="relative h-full flex flex-col items-center justify-center text-center p-6 gap-3">
                {!done ? (
                  <>
                    <div className="relative">
                      <div className="h-16 w-16 rounded-full border-2 border-neon/30" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <MonitorPlay className={cn("h-7 w-7 text-neon", pct > 0 && "animate-pulse")} />
                      </div>
                      <div className="absolute inset-[-6px] h-[calc(100%+12px)] w-[calc(100%+12px)] -z-10 rounded-full bg-gradient-to-tr from-neon/30 to-transparent blur-xl animate-pulse-neon" />
                    </div>
                    <div className="text-[22px] font-bold text-fg-0 tabular-nums tracking-tight">
                      {pct}<span className="text-fg-3">%</span>
                    </div>
                    <div className="text-[13px] text-fg-1 max-w-md">{etapa}</div>
                  </>
                ) : (
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="flex flex-col items-center gap-3"
                  >
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-ok/15 border border-ok/30 text-ok shadow-[0_0_24px_-6px_rgba(52,211,153,0.6)]">
                      <CheckCircle2 className="h-9 w-9" strokeWidth={2.4} />
                    </div>
                    <div className="text-[22px] font-bold text-fg-0">Render concluído! 🎬</div>
                    <div className="text-[13px] text-fg-2">
                      Formato {state.formato} · 30fps · {state.musica.duracao}s
                    </div>
                    <div className="flex items-center gap-2 pt-2">
                      <Button variant="neon" size="md"><Download className="h-4 w-4" /> Download .MP4</Button>
                      <Button variant="outline" size="md"><Play className="h-4 w-4" /> Assistir</Button>
                    </div>
                  </motion.div>
                )}
              </div>
            </div>

            <div>
              <Progress variant="neon" value={pct} />
              <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-fg-3">
                <span className={pct > 0 && !done ? "text-neon" : ""}>
                  {done ? "Pronto · 1x velocidade real" : etapa}
                </span>
                <span>{pct}%</span>
              </div>
            </div>

            {/* Sem música não há clipe: o botão fica desabilitado e explica. */}
            {!state.musica.arquivo && (
              <div className="flex items-center gap-2 rounded-md border border-warn/25 bg-warn/10 px-3 py-2.5 text-[12.5px] text-fg-1">
                <MusicIconI className="h-4 w-4 shrink-0 text-warn" />
                <span>
                  Envie a música na{" "}
                  <button
                    type="button"
                    onClick={() => setStep("audio")}
                    className="font-semibold text-warn underline underline-offset-2 hover:text-fg-0"
                  >
                    etapa 03
                  </button>{" "}
                  — o clipe é montado em cima dela.
                </span>
              </div>
            )}

            <div className="flex items-center justify-end gap-2">
              <Button variant="ghost" size="sm">Cancelar</Button>
              <Button
                variant="neon"
                size="lg"
                loading={pct > 0 && !done}
                onClick={gerar}
                disabled={!state.musica.arquivo || (pct > 0 && !done)}
                className="gap-2"
              >
                <Sparkles className="h-4 w-4" />
                {pct === 0 ? "Gerar clipe" : done ? "Gerar novamente" : "Renderizando..."}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Direita — resumo + logs */}
        <Card>
          <CardHeader>
            <CardTitle>Resumo do projeto</CardTitle>
            <CardDescription>Antes de gerar — confira os parâmetros.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <SummaryRow k="Letra" v={state.letra ? `${state.letra.split(/\s+/).filter(Boolean).length} palavras` : "—"} />
            <SummaryRow k="Legenda" v={state.legenda.length > 0 ? `${state.legenda.length} linhas` : "Automática da letra"} />
            <SummaryRow
              k="Música"
              v={
                state.musica.arquivo
                  ? `${state.musica.nomeArquivo ?? "enviada"} · ${formatarDuracao(state.musica.duracao)}`
                  : "— envie na etapa 03"
              }
            />
            <SummaryRow k="Imagens" v={`${state.imagens.length} prompts por beat`} />
            {/* ⚠️ ANTES: `state.midia.length || 3` — mostrava "3 peças" com zero selecionadas. */}
            <SummaryRow
              k="Mídia"
              v={state.midia.length === 0
                ? "nenhuma cena escolhida"
                : `${state.midia.length} cenas escolhidas`}
            />
            {/* ⚠️ NOVO: o formato da saída agora é editável (vertical, horizontal, quadrado, 3:4).
                O backend já aceita todas essas proporções em _DIMS. */}
            <div className="flex items-start justify-between gap-3 border-b border-white/5 last:border-0 pb-2.5 last:pb-0">
              <span className="text-[12px] text-fg-3 shrink-0">Formato</span>
              <select
                value={state.formato}
                onChange={(e) => setState((s) => ({ ...s, formato: e.target.value as any }))}
                title="proporção do MP4 final"
                className="h-7 max-w-[240px] rounded-sm border border-white/10 bg-bg-3 px-2 text-[12px] text-fg-1 outline-none focus:border-neon/40"
              >
                <option value="9/16">9:16 · 1080×1920 · vertical (shorts, reels)</option>
                <option value="16/9">16:9 · 1920×1080 · horizontal (youtube)</option>
                <option value="1/1">1:1 · 1080×1080 · quadrado (instagram)</option>
                <option value="3/4">3:4 · 1080×1440 · retrato (feed IG)</option>
                <option value="4/3">4:3 · 1440×1080 · paisagem (feed IG)</option>
              </select>
            </div>
            <SummaryRow
              k="Duração do clipe"
              v={
                state.musica.arquivo
                  ? `${formatarDuracao(state.musica.duracao)} · ~${Math.round(state.musica.duracao * 30)} frames`
                  : "—"
              }
            />
            <SummaryRow k="Render" v="HTMLRenderer → Playwright → FFmpeg" />
          </CardContent>

          <div className="border-t border-white/5 mx-5" />

          <div className="p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[12px] font-semibold uppercase tracking-wider text-fg-3">
                Log em tempo real
              </span>
              <span className="text-[10px] font-mono text-fg-3">{logs.length} linhas</span>
            </div>
            <div className="h-56 overflow-y-auto rounded-sm border border-white/5 bg-black/50 p-3 text-[11px] font-mono text-fg-2 leading-relaxed">
              {logs.length === 0 ? (
                <span className="text-fg-3/70 italic">
                  Aguardando início da renderização...
                </span>
              ) : (
                logs.map((l, i) => (
                  <div key={i} className="whitespace-pre-wrap">
                    <span className="text-fg-3/70">{String(i + 1).padStart(2, "0")}  </span>
                    {l}
                  </div>
                ))
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   Componentes auxiliares
   ═══════════════════════════════════════════════════════ */

function StepHeader({ step, title, description, icon, accent }: {
  step: string; title: string; description: string; icon: React.ReactNode;
  accent: "neon" | "ok" | "warn" | "violet";
}) {
  const cls =
    accent === "neon"   ? "bg-neon/15   border-neon/35   text-neon"   :
    accent === "ok"     ? "bg-ok/15     border-ok/35     text-ok"     :
    accent === "warn"   ? "bg-warn/15   border-warn/35   text-warn"   :
                          "bg-violet-500/15 border-violet-500/35 text-violet-400";
  return (
    <div className="flex items-start gap-4">
      <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-sm border", cls)}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-[11px]">ETAPA {step}</Badge>
        </div>
        <h2 className="mt-1 text-[22px] font-bold tracking-tight text-fg-0">{title}</h2>
        <p className="mt-1 text-[13px] text-fg-2 leading-relaxed max-w-2xl">{description}</p>
      </div>
    </div>
  );
}

function MiniStat({ label, value, icon, accent }: {
  label: string; value: any; icon: React.ReactNode; accent?: "neon" | "ok";
}) {
  const acc =
    accent === "neon" ? "text-neon bg-neon/10 border-neon/20" :
    accent === "ok"   ? "text-ok   bg-ok/10   border-ok/20"   :
                        "text-fg-2 bg-bg-3/50 border-white/5";
  return (
    <div className="rounded-sm border border-white/5 bg-bg-2/60 p-3">
      <div className="flex items-center gap-2 mb-1">
        <div className={cn("flex h-6 w-6 items-center justify-center rounded-md border text-[11px]", acc)}>
          {icon}
        </div>
        <span className="text-[11px] uppercase tracking-wider text-fg-3 font-semibold">{label}</span>
      </div>
      <div className="text-[22px] font-bold text-fg-0 leading-none tabular-nums">{value}</div>
    </div>
  );
}

function SummaryRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-white/5 last:border-0 pb-2.5 last:pb-0">
      <span className="text-[12px] text-fg-3 shrink-0">{k}</span>
      <span className="text-[12.5px] text-fg-1 text-right leading-snug truncate">{v}</span>
    </div>
  );
}

function formatT(t: any) {
  if (!t && t !== 0) return "—";
  const s = Number(t);
  if (!isFinite(s)) return "—";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

function gerarLinhasDaLetra(letra: string): any[] {
  return (letra || "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
    .map((texto, i) => ({
      texto,
      start: (i * 4).toFixed(2),
      end:   ((i + 1) * 4 - 0.3).toFixed(2),
      dur:   "4.0s",
      tempo: false,
    }));
}

/* ═══════════════════════════════════════════════════════
   PAINEL PREVIEW LIVE (coluna direita)
   ═══════════════════════════════════════════════════════ */

function LivePreviewPanel({ stepKey }: { stepKey: StudioStepKey }) {
  const { state, setState } = useStudio();
  // ⚠️ NOVO (22/09/2026): estilo da legenda pro preview fidedigno.
  const est = state.legendaEstilo ?? ESTILO_PADRAO;
  const totalBeats = Math.max(4, Math.round(state.letra.split(/\s+/).filter(Boolean).length / 6));
  const idx = STUDIO_STEPS.findIndex((s) => s.key === stepKey);

  return (
    <div className="space-y-4 lg:sticky lg:top-6 self-start">
      <Card className="soft-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-[13px] flex items-center gap-1.5">
                <MonitorPlay className="h-3.5 w-3.5 text-neon" />
                Preview do clipe
              </CardTitle>
              {/* ⚠️ CORRIGIDO (23/09/2026): dizia "Estimativa ao vivo"/LIVE —
                  pessoas achavam que era o vídeo real. A animação continua
                  (gostamos), só o RÓTULO mudou para deixar claro que é
                  ilustrativo. */}
              <CardDescription className="text-[11.5px]">Ilustrativo — não é o vídeo final</CardDescription>
            </div>
            <Badge variant="subtle" className="text-[10px]">DEMO</Badge>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* Fake celular — a proporção segue o formato escolhido na etapa 06 */}
          <div className={cn(
            "relative mx-auto overflow-hidden rounded-[18px] border-[3px] border-bg-4 shadow-[0_30px_60px_-20px_rgba(0,0,0,0.8)]",
            state.formato === "9/16"  && "aspect-[9/16] w-full max-w-[260px]",
            state.formato === "16/9"  && "aspect-[16/9] w-full max-w-[360px]",
            state.formato === "1/1"   && "aspect-square w-full max-w-[260px]",
            state.formato === "3/4"   && "aspect-[3/4] w-full max-w-[240px]",
            state.formato === "4/3"   && "aspect-[4/3] w-full max-w-[340px]",
          )}>
            <div className="absolute inset-0 bg-studio-grid opacity-40" />
            <div className="absolute inset-0 bg-gradient-to-br from-bg-0 via-bg-1/80 to-bg-2" />
            {/* Camada de imagem */}
            <div
              className="absolute inset-0 opacity-50 mix-blend-luminosity bg-cover bg-center"
              style={{ backgroundImage: "url('/assets/images/Editing_video_with_musical_elements_20260917220527.jpeg')" }}
            />
            {/* Overlay escuro */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-black/10" />

            {/* Barra de progresso no topo */}
            <div className="absolute top-0 inset-x-0 h-0.5 bg-white/10">
              <div
                className="h-full bg-gradient-to-r from-neon via-neon-2 to-violet-400 transition-all"
                style={{ width: `${((idx + 1) / STUDIO_STEPS.length) * 100}%` }}
              />
            </div>

            {/* Kinetic title fake */}
            <div className="absolute top-16 left-4 right-4 text-center">
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-neon/80 mb-2">
                {state.title || "Novo clipe"}
              </div>
            </div>

            {/* Legenda animada — ⚠️ CORRIGIDO (22/09/2026): usa o ESTILO escolhido
                na etapa 03 (cor, fonte, tamanho, negrito) e respeita a posição
                (baixo/centro/topo). Antes era estilo fixo. */}
            <div
              className={cn(
                "absolute inset-x-4",
                est.posicao === "topo" ? "top-14" : est.posicao === "centro" ? "top-1/2 -translate-y-1/2" : "bottom-16"
              )}
            >
              <motion.div
                key={stepKey}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className="rounded-xl bg-black/50 border border-white/10 backdrop-blur-md px-3.5 py-2.5 text-center"
              >
                <div
                  className="leading-snug tracking-tight"
                  style={{
                    fontFamily: `"${est.fonte}", sans-serif`,
                    fontSize: Math.max(12, est.tamanho * 0.3),
                    color: est.cor,
                    WebkitTextStroke: `${Math.max(0.6, est.contorno * 0.3)}px ${est.corContorno}`,
                    fontWeight: est.negrito ? 800 : 500,
                  }}
                >
                  {state.letra
                    ? state.letra.split(/\n/).filter(Boolean)[0]?.slice(0, 60) || "Quando a noite cai sobre a cidade"
                    : "Prévia da letra aparecerá aqui"}
                </div>
                <div className="mt-0.5 h-1 w-full rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full w-2/5 bg-gradient-to-r from-neon to-neon-2" />
                </div>
              </motion.div>
            </div>

            {/* Fake equalizador embaixo */}
            <div className="absolute bottom-5 inset-x-0 flex items-center justify-center gap-[2px] h-6 px-8">
              {Array.from({ length: 26 }).map((_, i) => (
                <motion.span
                  key={i}
                  animate={{ height: ["25%", `${25 + ((i * 13 + idx * 7) % 75)}%`, "25%"] }}
                  transition={{ repeat: Infinity, duration: 0.9 + (i % 5) * 0.1, ease: "easeInOut" }}
                  className="w-[3px] rounded-full bg-gradient-to-t from-neon/40 to-neon"
                />
              ))}
            </div>

            {/* Notch fake do celular */}
            <div className="absolute top-1.5 left-1/2 -translate-x-1/2 h-4 w-20 rounded-full bg-black/60 border border-white/5" />
          </div>

          {/* Estatísticas do preview */}
          <div className="mt-5 grid grid-cols-2 gap-2 text-[11px]">
            <Stat label="Beats" value={String(totalBeats).padStart(2, "0")} />
            <Stat label="Duração" value={`${totalBeats * 5}s`} />
            <Stat label="Resolução" value={
                state.formato === "16/9" ? "1920×1080" :
                state.formato === "1/1"  ? "1080×1080" :
                state.formato === "3/4"  ? "1080×1440" :
                state.formato === "4/3"  ? "1440×1080" :
                                           "1080×1920"
              } />
            <Stat label="Etapa atual" value={STUDIO_STEPS[idx].label} />
          </div>

          {/*
            ⚠️ Seletor de FORMATO sempre visível (todas as etapas).
            Antes ele existia só no resumo da etapa 06 — ninguém achava.
            Como a proporção muda o preview, a resolução e o recorte das
            imagens, faz mais sentido decidir isso logo no começo.
          */}
          <div className="mt-4">
            <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wider text-fg-3">
              Formato de saída
            </label>
            <select
              value={state.formato}
              onChange={(e) => setState((s) => ({ ...s, formato: e.target.value as any }))}
              title="proporção do MP4 final"
              className="h-9 w-full rounded-sm border border-white/10 bg-bg-3 px-2 text-[12.5px] text-fg-1 outline-none focus:border-neon/40"
            >
              <option value="9/16">9:16 · 1080×1920 · vertical (shorts, reels)</option>
              <option value="16/9">16:9 · 1920×1080 · horizontal (youtube)</option>
              <option value="1/1">1:1 · 1080×1080 · quadrado (instagram)</option>
              <option value="3/4">3:4 · 1080×1440 · retrato (feed IG)</option>
              <option value="4/3">4:3 · 1440×1080 · paisagem (feed IG)</option>
            </select>
            <p className="mt-1.5 text-[11px] text-fg-3">
              Vale para o preview acima e para o MP4 final.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Card de progresso acumulado do wizard */}
      <Card>
        <CardContent className="pt-5 space-y-3">
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-fg-3">Progresso do wizard</span>
            <span className="font-mono text-fg-0">{idx + 1}/{STUDIO_STEPS.length}</span>
          </div>
          <Progress variant="neon" value={((idx + 1) / STUDIO_STEPS.length) * 100} />
          <div className="space-y-1.5 pt-1">
            {STUDIO_STEPS.map((s, i) => (
              <div key={s.key} className="flex items-center gap-2 text-[11.5px]">
                <div
                  className={cn(
                    "flex h-4 w-4 items-center justify-center rounded-full border",
                    i < idx ? "bg-ok/20 border-ok/40 text-ok" :
                    i === idx ? "bg-neon/15 border-neon/40 text-neon" :
                               "bg-bg-3/50 border-white/5 text-fg-3"
                  )}
                >
                  {i < idx ? <CheckCircle2 className="h-2.5 w-2.5" /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                </div>
                <span className={cn(
                  "text-[11.5px]",
                  i === idx ? "text-fg-0 font-medium" : i < idx ? "text-fg-1" : "text-fg-3"
                )}>
                  {s.numero} · {s.label}
                </span>
              </div>
            ))}
          </div>
          <div className="pt-2">
            <Link href="/studio" className="block w-full">
              <Button variant="outline" size="sm" className="w-full gap-2">
                <ArrowLeft className="h-3.5 w-3.5" />
                Voltar para projetos
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-white/5 bg-bg-2/70 px-2.5 py-1.5">
      <div className="text-[10px] uppercase tracking-wider text-fg-3">{label}</div>
      <div className="text-[12px] font-semibold text-fg-0 font-mono">{value}</div>
    </div>
  );
}
