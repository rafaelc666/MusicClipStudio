"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Toaster, toast } from "sonner";
import { ArrowLeft, Bell, HelpCircle, Command as CmdIcon, Save, FolderOpen, KeyRound, LogOut, Loader2 } from "lucide-react";
import { StudioSidebar, STUDIO_STEPS, type StudioStepKey } from "@/components/studio/StudioSidebar";
import { StudioIntro, useIntroDeSessao } from "@/components/studio/StudioIntro";
import { AuthProvider, useAuth } from "@/components/studio/AuthProvider";
import { LoginGate } from "@/components/studio/LoginGate";
import { ProvedoresDialog } from "@/components/studio/ProvedoresDialog";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { salvarProjeto } from "@/lib/projetos-api";

/**
 * Contexto simples para os passos do wizard compartilharem estado do projeto
 * (letra, legenda, audio, etc) sem precisar de prop drill.
 */

/* ⚠️ NOVO (22/09/2026) — estilo da legenda (mesma forma do page.tsx;
   duplicado de propósito: arquivo leaf, sem import cíclico). */
export type EstiloLegenda = {
  cor: string;
  corContorno: string;
  fonte: string;
  tamanho: number;
  contorno: number;
  posicao: "baixo" | "centro" | "topo";
  negrito: boolean;
};

export const ESTILO_PADRAO_LEGENDA: EstiloLegenda = {
  cor: "#FFFFFF",
  corContorno: "#000000",
  fonte: "Montserrat",
  tamanho: 48,
  contorno: 2,
  posicao: "baixo",
  negrito: false,
};
/**
 * ⚠️ NOVO (24/09/2026) — uma música da playlist que será juntada numa faixa só.
 * `path` é o nome do arquivo em output/uploads (o mesmo que
 * POST /api/upload/audio devolve), e é ele que vai pra POST /api/audio/juntar.
 */
export interface FaixaAudio {
  path: string;
  url: string;
  nome: string;
  tamanhoBytes: number;
  duracao?: number;
}

export interface StudioProjectState {
  id: string;
  title: string;
  createdAt: number;
  letra: string;
  legenda: any[];
  /** ⚠️ NOVO (22/09/2026) — estilo da legenda queimada (cor, fonte,
   * tamanho, contorno, posição). Vira force_style do FFmpeg. */
  legendaEstilo?: EstiloLegenda;
  /**
   * Música PRONTA enviada pelo usuário (arquitetura Opção A: o app não
   * gera música). `arquivo` é o caminho relativo devolvido por
   * POST /api/upload/audio, servido em /static/<arquivo>.
   * `duracao` vem da leitura real do arquivo no navegador e define o
   * tamanho do clipe.
   */
  musica: {
    duracao: number;
    arquivo?: string;
    url?: string;
    nomeArquivo?: string;
    tamanhoBytes?: number;
  };
  /**
   * ⚠️ NOVO (24/09/2026) — músicas enviadas que ainda NÃO viraram faixa única.
   * A ordem da lista é a ordem de execução no clipe, e "Juntar com crossfade"
   * chama POST /api/audio/juntar pra produzir a faixa que o engine consome
   * (`musica`). A lista NÃO vai pro backend: o que persiste é a faixa já
   * juntada, que continua em output/uploads/.
   */
  faixasAudio?: FaixaAudio[];
  /** Segundos de sobreposição entre uma música e a seguinte (0 = corte seco). */
  crossfadeSeg?: number;
  imagens: any[];
  midia: any[];
  /** ⚠️ NOVO (23/09/2026) — tema visual livre digitado na etapa 04
   * ("chuva lenta", "carros antigos"…). Qualifica as queries do agente. */
  temaVisual?: string;
  /**
   * Proporção da SAÍDA do vídeo. O backend (_DIMS em engine.py) aceita:
   *   9/16  → 1080×1920  (shorts, reels, tiktok)
   *   16/9  → 1920×1080  (youtube, twitter)
   *   3/4   → 1080×1440  (feed instagram retrato)
   *   4/3   → 1440×1080  (feed instagram paisagem)
   *   1/1   → 1080×1080  (feed instagram quadrado)
   */
  formato: "9/16" | "16/9" | "3/4" | "4/3" | "1/1";
  completedSteps: Partial<Record<StudioStepKey, boolean>>;
  activeStep: StudioStepKey;
}

const StudioCtx = React.createContext<{
  state: StudioProjectState;
  setState: React.Dispatch<React.SetStateAction<StudioProjectState>>;
  setStep: (k: StudioStepKey) => void;
  markDone: (k: StudioStepKey) => void;
} | null>(null);

export function useStudio() {
  const ctx = React.useContext(StudioCtx);
  if (!ctx) throw new Error("useStudio só funciona dentro de <StudioClientShell>");
  return ctx;
}

const DEFAULT_STATE: StudioProjectState = {
  id: "local_" + Math.random().toString(36).slice(2, 10),
  title: "Novo clipe musical",
  createdAt: Date.now(),
  letra: "",
  legenda: [],
  legendaEstilo: ESTILO_PADRAO_LEGENDA,
  musica: { duracao: 0 },
  faixasAudio: [],
  crossfadeSeg: 2,
  imagens: [],
  midia: [],
  formato: "9/16",
  completedSteps: {},
  activeStep: "letra",
};

export function StudioClientShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  /**
   * ⚠️ PROTEÇÃO ADICIONADA (21/09/2026) — "a música sumiu" / "a letra sumiu".
   *
   * `useState(DEFAULT_STATE)` zera o wizard inteiro quando o componente é
   * REMONTADO. Isso acontece em 3 situações comuns:
   *   1) Fast Refresh do Turbopack depois de eu editar `StudioClientShell`
   *      (ou qualquer arquivo exportado por ele): o HMR não preserva
   *      estado e o useState volta ao DEFAULT_STATE.
   *   2) O usuário recarrega a aba com F5.
   *   3) (já blindado) `router.push` mudando a URL — a árvore remonta.
   *
   * A música enviada fica em `output/uploads/<arquivo>` no disco, então o
   * arquivo NÃO sumiu — só a referência no estado (e por isso a Etapa 06
   * dizia "Aguardando início" e bloqueava o render com o toast
   * "Envie a música antes de gerar"). Persistir o estado no
   * `localStorage` resolve os três casos sem mudança de UX.
   *
   * Restaura uma única vez na primeira montagem e re-salva em qualquer
   * mudança (com cuidado para não looppar com o próprio restore).
   */
  const STATE_KEY = "musicclipstudio_wizard_v1";

  const initialState = React.useMemo<StudioProjectState>(() => {
    if (typeof window === "undefined") return DEFAULT_STATE;
    try {
      const cru = window.localStorage.getItem(STATE_KEY);
      if (!cru) return DEFAULT_STATE;
      const salvo = JSON.parse(cru);
      // só restaura se tinha algo realmente coletado; caso contrário
      // começa limpo (evita ficar preso em estado de outra sessão).
      const tinhaAlgo =
        (salvo.letra && String(salvo.letra).trim()) ||
        (salvo.musica && salvo.musica.arquivo) ||
        (salvo.midia && salvo.midia.length) ||
        (salvo.imagens && salvo.imagens.length);
      return tinhaAlgo ? { ...DEFAULT_STATE, ...salvo, completedSteps: salvo.completedSteps ?? {} } : DEFAULT_STATE;
    } catch {
      return DEFAULT_STATE;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [state, setState] = React.useState<StudioProjectState>(initialState);
  const [salvando, setSalvando] = React.useState(false);
  const primeiraCarga = React.useRef(true);

  // Salva no localStorage em cada mudança de estado (lightweight: ~ a cada
  // 300ms no máximo para não spammar enquanto digita letra/transcreve).
  React.useEffect(() => {
    if (primeiraCarga.current) {
      primeiraCarga.current = false;
      return;
    }
    if (typeof window === "undefined") return;
    const t = window.setTimeout(() => {
      try {
        window.localStorage.setItem(STATE_KEY, JSON.stringify(state));
      } catch {
        // localStorage cheio ou bloqueado — não trava o usuário.
      }
    }, 300);
    return () => window.clearTimeout(t);
  }, [state]);

  /**
   * Persiste o projeto no backend (SQLite local).
   * Antes era só um toast de mentira — o projeto se perdia ao fechar a aba.
   */
  const salvar = React.useCallback(async () => {
    setSalvando(true);
    const id = toast.loading("Salvando projeto…");
    try {
      const gravado = await salvarProjeto({
        id: state.id,
        title: state.title,
        createdAt: state.createdAt,
        letra: state.letra,
        legenda: state.legenda,
        legendaEstilo: state.legendaEstilo,
        musica: state.musica,
        imagens: state.imagens,
        midia: state.midia,
        formato: state.formato,
        completedSteps: state.completedSteps,
        activeStep: state.activeStep,
      });
      if (gravado) {
        toast.success("Projeto salvo", {
          id,
          description: `${gravado.title} · ${gravado.id.slice(0, 12)}`,
        });
      } else {
        toast.error("Não foi possível salvar", {
          id,
          description: "Backend offline? O projeto continua na aba, mas não foi gravado.",
        });
      }
    } finally {
      setSalvando(false);
    }
  }, [state]);

  // Ctrl/Cmd+S salva o projeto
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        void salvar();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [salvar]);

  // Inferir passo ativo a partir da URL quando dentro de /studio/[id]/*
  React.useEffect(() => {
    if (!pathname) return;
    const stepsKeys = STUDIO_STEPS.map((s) => s.key);
    const match = pathname.match(/\/studio\/[^/]+\/([a-z]+)/);
    if (match && stepsKeys.includes(match[1] as any)) {
      setState((s) => ({ ...s, activeStep: match[1] as StudioStepKey }));
    }
  }, [pathname]);

  const setStep = React.useCallback((k: StudioStepKey) => {
    // ⚠️ NÃO usar router.push aqui.
    //
    // O estado do projeto (musica enviada, letra, midia) vive NESTE
    // componente. Um `router.push` troca os search params e faz o App
    // Router remontar a árvore — o useState(DEFAULT_STATE) roda de novo e
    // TODO o estado é perdido. Era por isso que a música sumia na Etapa 3
    // e que navegar pelo menu lateral (que também chama setStep) zerava o
    // wizard, enquanto avançar com os botões parecia funcionar.
    //
    // Trocar só o estado é suficiente: o wizard lê `state.activeStep` e a
    // URL é mantida em sincronia pelo history.replaceState (sem remount).
    setState((s) => ({ ...s, activeStep: k }));
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `/studio/new?step=${k}`);
    }
  }, []);

  const markDone = React.useCallback((k: StudioStepKey) => {
    setState((s) => ({
      ...s,
      completedSteps: { ...s.completedSteps, [k]: true },
    }));
  }, []);

  const isWizard = pathname?.includes("/new") || pathname?.match(/\/studio\/[^/]+\/[a-z]+/);

  /* ⚠️ NOVO (23/09/2026) — INTRO DE ABERTURA: uma vez por sessão da aba.
     Clique pula; renderiza por cima de tudo (z-9999) e não bloqueia o app
     por trás (o conteúdo já está montado). */
  const mostrarIntro = useIntroDeSessao();
  const [introAtiva, setIntroAtiva] = React.useState(true);
  const introVisivel = mostrarIntro && introAtiva;

  /* ⚠️ NOVO (23/09/2026) — LOGIN + CHAVES: portão de sessão, diálogo de
     provedores e estado do usuário para o header. */
  const { usuario, carregando: authCarregando, sair } = useAuth();
  const [dialogProvedores, setDialogProvedores] = React.useState(false);

  /* Etapa 04 ("Configurar provedores") pede para abrir o diálogo via evento
     de janela — o diálogo vive aqui no shell, acima de todas as telas. */
  React.useEffect(() => {
    const abrir = () => setDialogProvedores(true);
    window.addEventListener("mcs:abrir-provedores", abrir);
    return () => window.removeEventListener("mcs:abrir-provedores", abrir);
  }, []);

  return (
    <StudioCtx.Provider value={{ state, setState, setStep, markDone }}>
      {introVisivel && <StudioIntro onDone={() => setIntroAtiva(false)} />}
      {/* Portão de login: enquanto carrega a sessão não mostra nada (evita
          flash da tela de login num F5 com sessão válida). */}
      {authCarregando ? (
        <div className="fixed inset-0 z-[500] flex items-center justify-center bg-bg-0">
          <Loader2 className="h-6 w-6 animate-spin text-neon" />
        </div>
      ) : !usuario ? (
        <LoginGate />
      ) : null}
      <ProvedoresDialog aberto={dialogProvedores} onFechar={() => setDialogProvedores(false)} />
      <div className="relative flex h-screen w-screen overflow-hidden bg-bg-0 text-fg-1">
        {/* Backdrop grid global */}
        <div className="pointer-events-none absolute inset-0 bg-studio-grid opacity-40" />
        <div className="pointer-events-none absolute inset-0 bg-noise" />

        <StudioSidebar
          activeStep={isWizard ? state.activeStep : "dashboard"}
          completedSteps={state.completedSteps}
          onStep={isWizard ? setStep : undefined}
          projectId={state.id}
          onAbrirConfiguracoes={() => setDialogProvedores(true)}
        />

        {/* Área principal */}
        <div className="relative z-10 flex min-w-0 flex-1 flex-col">
          {/* Top Bar */}
          <header className="flex h-14 shrink-0 items-center gap-3 border-b border-white/5 bg-bg-1/60 backdrop-blur-md px-5">
            {/* ⚠️ NOVO (23/09/2026) — estado do login montado num hook interno
                para o header poder usar (o shell inteiro já está sob o
                AuthProvider, ver export default no fim do arquivo). */}
            {/*
              ⚠️ AQUI NÃO vai link para a raiz "/".
              A raiz é a página de MARKETING do BlueBookStudio (abas
              Studio51 / MusicClipStudio / BlueBookStudio / Agente009) —
              nada a ver com o gerador de clipes. Um botão "Landing" apontando
              para "/" tirava o usuário do programa sem querer.
              No wizard, volta para a lista de projetos (/studio).
            */}
            {isWizard ? (
              <Link
                href="/studio"
                className="flex items-center gap-1.5 text-[12px] text-fg-3 hover:text-fg-0 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Meus projetos
              </Link>
            ) : (
              <span className="flex items-center gap-1.5 text-[12px] text-fg-3 select-none">
                <FolderOpen className="h-3.5 w-3.5" />
                Meus projetos
              </span>
            )}

            <div className="h-4 w-px bg-white/10 mx-2" />

            <div className="flex items-center gap-2">
              <span className="text-[13px] text-fg-0 font-semibold truncate max-w-[300px]">
                {state.title || "Novo clipe musical"}
              </span>
              {isWizard && (
                <span className="rounded-full border border-neon/20 bg-neon/10 px-2 py-0.5 text-[10px] text-neon font-semibold tracking-wide">
                  WIZARD · 6 ETAPAS
                </span>
              )}
            </div>

            <div className="ml-auto flex items-center gap-2">
              <CommandHint />
              {/* ⚠️ NOVO (23/09/2026) — CHAVES DE API no menu (pedido: precisa
                  ser a primeira coisa a ser feita). Abre o diálogo de
                  provedores de qualquer tela. */}
              <Button
                size="sm"
                variant="outline"
                onClick={() => setDialogProvedores(true)}
              >
                <KeyRound className="h-3.5 w-3.5" />
                Chaves de API
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => void salvar()}
                disabled={salvando}
              >
                <Save className="h-3.5 w-3.5" />
                {salvando ? "Salvando…" : "Salvar"}
              </Button>
              <Button size="icon" variant="ghost" aria-label="Notificações">
                <Bell className="h-[17px] w-[17px]" />
              </Button>
              <Button size="icon" variant="ghost" aria-label="Ajuda">
                <HelpCircle className="h-[17px] w-[17px]" />
              </Button>
              {/* Usuário logado + Sair */}
              {usuario && (
                <span className="flex items-center gap-2 border-l border-white/10 pl-3">
                  <span className="max-w-[140px] truncate rounded-full border border-neon/25 bg-neon/10 px-2.5 py-1 text-[11.5px] text-neon">
                    {usuario.username}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="gap-1 px-2 text-[11.5px] text-fg-2 hover:text-red-300"
                    aria-label={`Sair da conta ${usuario.username}`}
                    onClick={() => {
                      // ⚠️ 23/09/2026 — SAIR = RESET COMPLETO DO APP (pedido do
                      // Rafael): a próxima pessoa que logar começa do zero.
                      // As chaves de API FICAM no servidor, na conta do
                      // usuário — não são dados locais.
                      window.localStorage.removeItem("musicclipstudio_wizard_v1");
                      window.localStorage.removeItem("musicclipstudio_audio_excluidos_v1");
                      setState((s) => ({
                        ...DEFAULT_STATE,
                        id: "local_" + Math.random().toString(36).slice(2, 10),
                        createdAt: Date.now(),
                      }));
                      void sair();
                    }}
                  >
                    <LogOut className="h-[14px] w-[14px]" />
                    Sair
                  </Button>
                </span>
              )}
            </div>
          </header>

          {/* Conteúdo scrollável */}
          <main className="relative flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-[1400px] px-6 py-6">
              {children}
            </div>
          </main>
        </div>

        {/* Sonner (toasts) — estilo neon minimalista */}
        <Toaster
          theme="dark"
          position="bottom-right"
          richColors
          closeButton
          toastOptions={{
            style: {
              background: "var(--bg-2)",
              color: "var(--fg-1)",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: "10px",
              boxShadow: "0 10px 30px -12px rgba(0,0,0,0.85)",
              fontSize: "13px",
            },
          }}
        />
      </div>
    </StudioCtx.Provider>
  );
}

function CommandHint() {
  return (
    <div className={cn(
      "hidden md:flex items-center gap-1.5 rounded-sm border border-white/5 bg-bg-2/70 px-2 py-1",
      "text-[11px] text-fg-3 font-mono"
    )}>
      <span className="text-fg-2"><CmdIcon className="h-3 w-3 inline" /></span>
      <span>K</span>
      <span className="mx-1 text-fg-3/60">·</span>
      <span>buscar</span>
    </div>
  );
}
