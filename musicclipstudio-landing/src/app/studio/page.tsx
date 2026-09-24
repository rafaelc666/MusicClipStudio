"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Plus, Play, Clock, Film, Sparkles, ArrowUpRight,
  FileText, Music, FolderOpen, Rocket, Trash2, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  listarProjetos, apagarProjeto,
  type ProjetoSalvo,
} from "@/lib/projetos-api";

/** Formato que a UI consome — derivado do projeto salvo. */
interface ProjetoCard {
  id: string;
  title: string;
  artist: string;
  status: "concluido" | "andamento" | "rascunho";
  duracao: string;
  thumbnail: string;
  updatedAt: number;
  stepsDone: number;
}

/** Thumbnails de fallback (projetos reais ainda não têm imagem própria). */
const THUMBS = [
  "/assets/images/studio51-set.jpeg",
  "/assets/images/omega-interface.jpeg",
  "/assets/images/supernatural-hallway.jpeg",
  "/assets/images/bluebook-network.jpeg",
];

/** Converte o projeto salvo no cartão que a UI desenha. */
function paraCard(p: ProjetoSalvo, idx: number): ProjetoCard {
  const passos = p.completedSteps ?? {};
  const stepsDone = Object.values(passos).filter(Boolean).length;
  const status: ProjetoCard["status"] =
    p.status === "concluido" ? "concluido"
    : stepsDone >= 6 || stepsDone >= 3 ? "andamento"
    : "rascunho";
  const dur = p.musica?.duracao;
  return {
    id: p.id,
    title: p.title || "Clipe sem título",
    artist: (p as { artist?: string }).artist || "—",
    status,
    duracao: dur ? `${Math.round(dur)}s` : "—",
    thumbnail: THUMBS[idx % THUMBS.length],
    updatedAt: p.updatedAt ?? p.createdAt ?? Date.now(),
    stepsDone,
  };
}

const STAT_ICONS = [FolderOpen, Film, Rocket, Clock] as const;

const TEMPLATES = [
  { id: "t1", name: "Épico Cinematográfico", desc: "Batidas fortes, estilo Vox Editorial", tag: "9:16", color: "from-neon/30 to-violet/20" },
  { id: "t2", name: "Lo-fi Relaxante",       desc: "Imagens calmas, tipografia arredondada", tag: "16:9", color: "from-ok/25 to-neon/15" },
  { id: "t3", name: "Pop Animado",           desc: "Transições rápidas, kinetic titles",     tag: "9:16", color: "from-warn/30 to-err/15" },
];

export default function StudioDashboardPage() {
  const [projetos, setProjetos] = React.useState<ProjetoCard[]>([]);
  const [carregando, setCarregando] = React.useState(true);
  const [offline, setOffline] = React.useState(false);

  // Carrega os projetos salvos (SQLite local via /api/projetos)
  const carregar = React.useCallback(async () => {
    setCarregando(true);
    const brutos = await listarProjetos();
    if (brutos === null) {
      setOffline(true);
      setProjetos([]);
    } else {
      setOffline(false);
      setProjetos(brutos.map(paraCard));
    }
    setCarregando(false);
  }, []);

  React.useEffect(() => {
    void carregar();
  }, [carregar]);

  const remover = async (id: string) => {
    const ok = await apagarProjeto(id);
    if (ok) setProjetos((ps) => ps.filter((p) => p.id !== id));
  };

  // Stats do dashboard — "Projetos" vem do banco real.
  const stats = React.useMemo(
    () => [
      { label: "Projetos", value: String(projetos.length), icon: STAT_ICONS[0], accent: "neon" },
      { label: "Minutos renderizados", value: "—", icon: STAT_ICONS[1], accent: "ok" },
      { label: "Cliipes publicados", value: "—", icon: STAT_ICONS[2], accent: "violet" },
      { label: "Tempo médio", value: "—", icon: STAT_ICONS[3], accent: "warn" },
    ],
    [projetos.length],
  );

  // Spotlight: faz o brilho seguir o cursor nos cards (só CSS var, zero estado)
  const seguirCursor = (e: React.MouseEvent<HTMLElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty("--mx", `${e.clientX - r.left}px`);
    e.currentTarget.style.setProperty("--my", `${e.clientY - r.top}px`);
  };

  return (
    <div className="aurora-bg flex flex-col gap-8 animate-fade-up">
      {/* HERO DO DASHBOARD */}
      <section
        onMouseMove={seguirCursor}
        className="spotlight relative overflow-hidden rounded-lg border border-white/[0.07] p-6 md:p-8 card-v2"
      >
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-neon/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-20 -bottom-24 h-72 w-72 rounded-full bg-violet-500/10 blur-3xl" />

        <div className="relative grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] items-center gap-8">
          <div>
            <span className="eyebrow mb-3 inline-flex items-center gap-2">
              <span className="live-dot" />
              Estúdio on-line
            </span>

            <h1 className="display-xl mt-1">
              Olá! Vamos criar um{" "}
              <span className="text-gradient-neon">clipe musical inesquecível</span> hoje.
            </h1>

            <p className="mt-3 max-w-xl text-[14.5px] text-fg-2 leading-relaxed">
              Selecione um projeto recente abaixo, comece um novo do zero,
              ou acelere com um dos templates otimizados do Studio.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Link href="/studio/new">
                <Button variant="neon" size="lg" className="btn-shine gap-2">
                  <Plus className="h-4 w-4" strokeWidth={2.6} />
                  Criar novo projeto
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="gap-2">
                <Play className="h-4 w-4" />
                Assistir tour de 1 min
              </Button>
            </div>
          </div>

          {/* Stats card */}
          <div className="grid grid-cols-2 gap-3">
            {stats.map((s) => {
              const Ico = s.icon;
              const accentCls =
                s.accent === "neon" ? "text-neon bg-neon/10 border-neon/25" :
                s.accent === "ok"   ? "text-ok   bg-ok/10   border-ok/25" :
                s.accent === "warn" ? "text-warn bg-warn/10 border-warn/25" :
                s.accent === "violet"? "text-violet-500 bg-violet-500/10 border-violet-500/25":
                "";
              return (
                <div
                  key={s.label}
                  className="lift spotlight rounded-md border border-white/[0.06] bg-bg-2/70 p-4"
                  onMouseMove={seguirCursor}
                >
                  <div className={cn("mb-2 inline-flex h-8 w-8 items-center justify-center rounded-md border", accentCls)}>
                    <Ico className="h-4 w-4" />
                  </div>
                  <div className="text-[22px] font-bold text-fg-0 leading-none tabular-nums">
                    {s.value}
                  </div>
                  <div className="mt-1 text-[12px] text-fg-3">{s.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* TEMPLATES */}
      <section>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <span className="eyebrow">Comece rápido</span>
            <h2 className="display-lg mt-1">Templates rápidos</h2>
            <p className="text-[13px] text-fg-2">Estilos prontos — adapte letra e siga.</p>
          </div>
          <Link href="/studio/templates" className="text-[12px] text-neon hover:underline">
            Ver todos <ArrowUpRight className="inline h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TEMPLATES.map((tpl) => (
            <Link key={tpl.id} href={`/studio/new?template=${tpl.id}`}>
              <motion.div
                whileHover={{ y: -3 }}
                transition={{ type: "spring", stiffness: 320, damping: 24 }}
                onMouseMove={seguirCursor}
                className="group spotlight relative overflow-hidden rounded-lg border border-white/[0.06] bg-bg-2/70 p-4 card-v2"
              >
                <div className={cn("mb-4 h-28 rounded-md bg-gradient-to-br", tpl.color, "flex items-center justify-center border border-white/5 overflow-hidden")}>
                  <Sparkles className="h-8 w-8 text-fg-0/70 group-hover:scale-110 transition-transform duration-500" />
                </div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-[14px] font-semibold text-fg-0">{tpl.name}</h3>
                  <Badge variant="outline" className="text-[10px]">{tpl.tag}</Badge>
                </div>
                <p className="text-[12px] text-fg-2 leading-snug">{tpl.desc}</p>
              </motion.div>
            </Link>
          ))}
        </div>
      </section>

      {/* PROJETOS RECENTES */}
      <section>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <span className="eyebrow">Histórico</span>
            <h2 className="display-lg mt-1">Projetos recentes</h2>
            <p className="text-[13px] text-fg-2">
              {offline
                ? "Backend offline — mostrando vazio."
                : "Continue de onde parou. Salvo localmente no seu computador."}
            </p>
          </div>
          <div className="chip">
            {carregando ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> carregando…</>
            ) : (
              <><FileText className="h-3.5 w-3.5" /> {projetos.length} projeto{projetos.length === 1 ? "" : "s"}</>
            )}
          </div>
        </div>

        {/* Vazio / offline */}
        {!carregando && projetos.length === 0 && (
          <div className="rounded-lg border border-dashed border-white/10 bg-bg-2/40 p-10 text-center">
            <FolderOpen className="mx-auto mb-3 h-8 w-8 text-fg-3" />
            <p className="text-[14px] font-medium text-fg-1">
              {offline ? "Não foi possível ler os projetos" : "Nenhum projeto ainda"}
            </p>
            <p className="mx-auto mt-1 max-w-md text-[12.5px] text-fg-3">
              {offline
                ? "O backend parece estar offline. Inicie com RUN_WEB.bat e recarregue."
                : "Crie um projeto no wizard e clique em Salvar (ou Ctrl+S) para ele aparecer aqui."}
            </p>
            {!offline && (
              <Link href="/studio/new" className="mt-4 inline-block">
                <Button variant="neon" size="sm" className="gap-2">
                  <Plus className="h-3.5 w-3.5" /> Criar o primeiro
                </Button>
              </Link>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {projetos.map((p, idx) => {
            type StatusKey = "concluido" | "andamento" | "rascunho";
            const STATUS_MAP: Record<StatusKey, { label: string; variant: "ok" | "neon" | "default"; icon: typeof Rocket }> = {
              concluido: { label: "Concluído", variant: "ok", icon: Rocket },
              andamento: { label: "Em andamento", variant: "neon", icon: Music },
              rascunho:   { label: "Rascunho", variant: "default", icon: FileText },
            };
            const info = STATUS_MAP[p.status] ?? STATUS_MAP.rascunho;
            const Ico = info.icon;
            return (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05, duration: 0.3 }}
              >
                <Card className="overflow-hidden group transition-all hover:border-neon/30 hover:-translate-y-0.5">
                  <div className="relative aspect-[16/10] overflow-hidden bg-bg-3/60 border-b border-white/5">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={p.thumbnail}
                      alt={p.title}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
                    />
                    <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-bg-0/80 to-transparent" />
                    <Badge
                      variant={info.variant}
                      className="absolute left-3 top-3 backdrop-blur-sm"
                    >
                      <Ico className="h-3 w-3 mr-1" />
                      {info.label}
                    </Badge>
                    <div className="absolute right-3 bottom-3 flex items-center gap-1 rounded-full bg-black/60 border border-white/10 backdrop-blur px-2 py-0.5 text-[11px] font-mono text-fg-1">
                      <Clock className="h-3 w-3" /> {p.duracao}
                    </div>
                  </div>

                  <CardContent className="!p-4">
                    <div className="flex items-start justify-between gap-2">
                      {/*
                        ⚠️ O título apontava para /studio/${p.id} — rota que NÃO
                        EXISTE (não há página por projeto ainda). Dava 404 ao
                        clicar. Por ora abre o wizard na primeira etapa, que é
                        o que o usuário espera de "abrir o projeto".
                      */}
                      <Link
                        href={`/studio/new?step=letra&projeto=${encodeURIComponent(p.id)}`}
                        className="min-w-0 flex-1"
                      >
                        <h3 className="truncate text-[14px] font-semibold text-fg-0 hover:text-neon transition-colors">
                          {p.title}
                        </h3>
                        <p className="truncate text-[12px] text-fg-3">{p.artist || "—"}</p>
                      </Link>
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label={`Apagar ${p.title}`}
                        className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => void remover(p.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-err/80" />
                      </Button>
                    </div>

                    <div className="mt-3 flex items-center justify-between text-[11px] text-fg-3">
                      <span>
                        {p.stepsDone}/6 etapas
                      </span>
                      <span>{relativeTime(p.updatedAt)}</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function relativeTime(ts: number) {
  const d = Date.now() - ts;
  const min = Math.floor(d / 60000);
  if (min < 1) return "agora";
  if (min < 60) return `${min}m atrás`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h atrás`;
  const d_ = Math.floor(h / 24);
  return `${d_}d atrás`;
}
