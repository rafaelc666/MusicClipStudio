"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  FileText,
  Captions,
  Music,
  Image as ImageIcon,
  FolderOpen,
  Rocket,
  Settings,
  LayoutDashboard,
  Sparkles,
  ChevronRight,
  KeyRound,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type StudioStepKey =
  | "dashboard"
  | "chaves"
  | "letra"
  | "audio"
  | "legenda"
  | "imagens"
  | "midia"
  | "gerar";

export const STUDIO_STEPS: Array<{
  key: StudioStepKey;
  label: string;
  numero: string;
  icon: any;
  desc: string;
}> = [
  /**
   * ⚠️ ORDEM ALTERADA (21/09/2026) a pedido do usuário:
   *
   *   01 letra → 02 áudio → 03 legenda
   *
   * Motivo: quando NÃO há letra, o caminho natural é subir a música e
   * transcrever o áudio. Com a legenda ANTES do áudio, quem não tem letra
   * caía na etapa de transcrição sem ter nenhum áudio carregado — a ordem
   * invertida obrigava a voltar. Agora a sequência já é a correta para os
   * dois casos: com letra (digita e segue) e sem letra (sobe o áudio e
   * transcreve na etapa seguinte).
   *
   * ⚠️ ORDEM ALTERADA (23/09/2026) de novo, a pedido do usuário:
   *
   *   01 CHAVES DE API → 02 letra → … → 07 gerar (7 etapas)
   *
   * Motivo: "a configuração das chaves de API precisa ser a primeira coisa
   * a ser feita, caso contrário o programa não vai funcionar" — sem chave
   * de banco de mídia a etapa de busca não encontra nada. A etapa 01
   * explica onde criar cada chave e abre o site oficial de cada banco.
   */
  { key: "chaves",  label: "Chave API", numero: "01", icon: KeyRound, desc: "Bancos de mídia" },
  { key: "letra",   label: "Letra",    numero: "02", icon: FileText, desc: "Texto da música" },
  { key: "audio",   label: "Áudio",    numero: "03", icon: Music,    desc: "Trilha sonora" },
  { key: "legenda", label: "Legenda",  numero: "04", icon: Captions, desc: "Transcrição & tempos" },
  { key: "imagens", label: "Imagens",  numero: "05", icon: ImageIcon, desc: "Prompts IA" },
  { key: "midia",   label: "Mídia",    numero: "06", icon: FolderOpen, desc: "Seleção de mídia" },
  { key: "gerar",   label: "Gerar",    numero: "07", icon: Rocket,   desc: "Render final" },
];

interface Props {
  /** ⚠️ NOVO (23/09/2026): abre o diálogo de chaves de API do item Configurações. */
  onAbrirConfiguracoes?: () => void;
  activeStep?: StudioStepKey;
  onStep?: (k: StudioStepKey) => void;
  completedSteps?: Partial<Record<StudioStepKey, boolean>>;
  projectId?: string;
}

export function StudioSidebar({ activeStep, onStep, completedSteps = {}, projectId, onAbrirConfiguracoes }: Props) {
  const pathname = usePathname();

  const isDashboard =
    activeStep === "dashboard" ||
    (!activeStep && pathname === "/studio");

  return (
    <aside className="relative h-full w-[248px] shrink-0 border-r border-white/5 bg-gradient-to-b from-bg-1 via-bg-1/95 to-bg-0/95">
      {/* Grid de fundo sutil */}
      <div className="pointer-events-none absolute inset-0 bg-studio-grid opacity-[0.35]" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-60" />

      <div className="relative z-10 flex h-full flex-col p-4">
        {/* Logo */}
        <Link href="/studio" className="group mb-6 flex items-center gap-3 px-2">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-md bg-gradient-to-br from-neon/25 to-neon-3/20 border border-neon/30 shadow-[0_0_20px_-6px_rgba(34,211,238,0.4)] transition-all duration-500 group-hover:shadow-[0_0_32px_-6px_rgba(34,211,238,0.6)]">
            <Sparkles className="h-5 w-5 text-neon transition-transform duration-500 group-hover:rotate-12" strokeWidth={2.2} />
          </div>
          <div className="flex flex-col">
            <span className="text-[14px] font-semibold tracking-tight text-fg-0">
              MusicClip<span className="text-neon">Studio</span>
            </span>
            <span className="text-[11px] text-fg-3 tracking-wide">
              WEB · v0.1
            </span>
          </div>
        </Link>

        {/* Estado da stack (backend/frontend) */}
        <div className="mb-5 px-2">
          <span className="chip chip-neon w-full justify-center text-[10px]">
            <span className="live-dot" />
            Backend conectado
          </span>
        </div>

        {/* Dashboard link */}
        <SidebarLink
          href="/studio"
          active={isDashboard}
          icon={<LayoutDashboard className="h-[17px] w-[17px]" />}
          label="Meus Projetos"
          hint="Dashboard"
        />

        {/* Separador */}
        <div className="mt-5 mb-3 px-2 flex items-center gap-2">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          <span className="text-[10px] uppercase tracking-[0.18em] text-fg-3 font-semibold">
            Wizard
          </span>
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>

        {/* Steps do wizard */}
        <div className="flex flex-col gap-1">
          {STUDIO_STEPS.map((step) => {
            const Icon = step.icon;
            const active = activeStep === step.key;
            const done = !!completedSteps[step.key];

            /*
             * ⚠️ NÃO NAVEGAR. Trocar de etapa é mudança de ESTADO, não de rota.
             *
             * Antes isto montava `/studio/${projectId}/${step.key}` quando havia
             * projectId — rota que NÃO EXISTE. Resultado: clicar no menu levava
             * a um 404 (`GET /studio/local_ym60th0i/audio 404`) e a etapa não
             * mudava. Era exatamente o "pelo menu da esquerda não muda" que o
             * usuário relatou; seguindo a sequência (botão "Avançar") funcionava,
             * porque aí o caminho é outro.
             *
             * Agora o item do menu é um <button> que só chama onStep — sem href,
             * sem navegação, sem remontar a árvore (que também zeraria o estado
             * do projeto, como já corrigimos no setStep).
             *
             * Se não houver onStep (menu fora do wizard), cai para o link
             * clássico do wizard.
             */
            const href = `/studio/new?step=${step.key}`;

            const handleClick = (e: React.MouseEvent) => {
              if (onStep) {
                e.preventDefault();
                onStep(step.key);
              }
            };

            const className = cn(
              "group relative flex items-center gap-3 rounded-sm px-2.5 py-2 text-[13px] transition-all text-left w-full cursor-pointer",
              active
                ? "text-fg-0 bg-bg-3/80 border border-neon/25 shadow-[0_0_0_1px_rgba(34,211,238,0.1)]"
                : "text-fg-2 hover:text-fg-0 hover:bg-bg-3/40 border border-transparent"
            );

            const conteudo = (
              <>
                {active && (
                  <motion.span
                    layoutId="activeStepGlow"
                    className="pointer-events-none absolute inset-0 rounded-sm shadow-[inset_0_0_0_1px_rgba(34,211,238,0.18),0_0_24px_-8px_rgba(34,211,238,0.35)]"
                    transition={{ type: "spring", stiffness: 260, damping: 28 }}
                  />
                )}

                <span
                  className={cn(
                    "relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border text-[11px] font-bold tracking-tight transition-colors",
                    active
                      ? "bg-neon/15 border-neon/40 text-neon"
                      : done
                      ? "bg-ok/10 border-ok/30 text-ok"
                      : "bg-bg-3/70 border-white/5 text-fg-3"
                  )}
                >
                  {done ? (
                    <svg viewBox="0 0 20 20" className="h-3.5 w-3.5 fill-current">
                      <path d="M7.629 14.571 3.343 10.286l-1.414 1.414 5.7 5.7 11-11-1.414-1.414z" />
                    </svg>
                  ) : (
                    step.numero
                  )}
                </span>

                <span className="relative z-10 flex flex-1 flex-col overflow-hidden">
                  <span
                    className={cn(
                      "truncate text-[13px] font-medium",
                      active ? "text-fg-0" : ""
                    )}
                  >
                    {step.label}
                  </span>
                  <span className="truncate text-[11px] text-fg-3/90">
                    {step.desc}
                  </span>
                </span>

                <ChevronRight
                  className={cn(
                    "h-4 w-4 shrink-0 transition-all",
                    active ? "text-neon translate-x-0" : "text-transparent group-hover:text-fg-3/60 group-hover:translate-x-0 -translate-x-1"
                  )}
                />
              </>
            );

            // Com onStep = dentro do wizard: botão que só troca a etapa.
            // Sem onStep = menu solto: link normal do wizard.
            return onStep ? (
              <button
                key={step.key}
                type="button"
                onClick={handleClick}
                className={className}
              >
                {conteudo}
              </button>
            ) : (
              <Link key={step.key} href={href} className={className}>
                {conteudo}
              </Link>
            );
          })}
        </div>

        {/* Espaçador */}
        <div className="flex-1" />

        {/* Roda pé */}
        <div className="mt-4 border-t border-white/5 pt-3 px-2 flex items-center justify-between">
          {/* ⚠️ ATUALIZADO (23/09/2026): o item agora ABRE o diálogo de
              chaves de API (antes era texto inerte — a rota /studio/settings
              nunca existiu). */}
          <button
            type="button"
            onClick={onAbrirConfiguracoes}
            className="flex items-center gap-2 text-[12px] text-fg-3 hover:text-fg-0 transition-colors select-none"
          >
            <Settings className="h-3.5 w-3.5" />
            Configurações
          </button>
          <span className="text-[10px] text-fg-3/60 font-mono">
            OK · {projectId ? projectId.slice(0, 6) : "local"}
          </span>
        </div>
      </div>
    </aside>
  );
}

function SidebarLink({
  href,
  active,
  icon,
  label,
  hint,
}: {
  href: string;
  active?: boolean;
  icon: React.ReactNode;
  label: string;
  hint?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-[13px] transition-all border",
        active
          ? "text-fg-0 bg-bg-3/80 border-neon/25"
          : "text-fg-2 hover:text-fg-0 hover:bg-bg-3/40 border-transparent"
      )}
    >
      <span
        className={cn(
          "flex h-7 w-7 items-center justify-center rounded-md border",
          active
            ? "bg-neon/15 border-neon/40 text-neon"
            : "bg-bg-3/70 border-white/5 text-fg-3"
        )}
      >
        {icon}
      </span>
      <div className="flex flex-col">
        <span className="truncate font-medium">{label}</span>
        {hint && <span className="text-[10px] text-fg-3 -mt-0.5">{hint}</span>}
      </div>
    </Link>
  );
}
