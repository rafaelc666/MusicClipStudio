"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  FileText, Captions, Music, Image as ImageIcon,
  FolderOpen, Rocket, Check, KeyRound,
} from "lucide-react";
import { STUDIO_STEPS, type StudioStepKey } from "./StudioSidebar";

interface Props {
  activeStep: StudioStepKey;
  completedSteps?: Partial<Record<StudioStepKey, boolean>>;
  onChange?: (k: StudioStepKey) => void;
}

const STEP_ICON: Record<string, any> = {
  chaves: KeyRound, letra: FileText, legenda: Captions, audio: Music,
  imagens: ImageIcon, midia: FolderOpen, gerar: Rocket,
};

export function WizardStepper({ activeStep, completedSteps = {}, onChange }: Props) {
  const activeIdx = STUDIO_STEPS.findIndex((s) => s.key === activeStep);

  return (
    <div className="relative w-full rounded-sm border border-white/5 bg-bg-2/70 px-6 py-4 soft-shadow">
      <div className="flex items-center justify-between gap-2">
        {STUDIO_STEPS.map((s, i) => {
          const Icon = STEP_ICON[s.key];
          const isActive = s.key === activeStep;
          const isDone = !!completedSteps[s.key];
          const isPast = i < activeIdx || isDone;
          const clickable = !!onChange && (isPast || i === activeIdx + 1 || true);

          const Wrapper: any = clickable ? "button" : "div";
          const wrapperProps = clickable
            ? { onClick: () => onChange!(s.key), type: "button" as const }
            : {};

          return (
            <div key={s.key} className="relative flex flex-1 items-center last:flex-none">
              <Wrapper
                {...wrapperProps}
                className={cn(
                  "group relative flex flex-col items-center gap-1.5 rounded-sm px-2 py-1 transition-all",
                  clickable && "hover:bg-bg-3/40"
                )}
              >
                <span className="relative">
                  <span
                    className={cn(
                      "flex h-9 w-9 items-center justify-center rounded-full border transition-all duration-300",
                      isActive
                        ? "bg-neon/15 border-neon/60 text-neon shadow-[0_0_24px_-8px_rgba(34,211,238,0.6)]"
                        : isPast || isDone
                        ? "bg-ok/10 border-ok/40 text-ok"
                        : "bg-bg-3/60 border-white/5 text-fg-3"
                    )}
                  >
                    {isDone ? (
                      <Check className="h-4 w-4" strokeWidth={2.6} />
                    ) : (
                      <Icon className="h-[17px] w-[17px]" strokeWidth={2} />
                    )}
                  </span>
                  {isActive && (
                    <motion.span
                      className="pointer-events-none absolute inset-0 rounded-full"
                      style={{ boxShadow: "0 0 0 3px rgba(34,211,238,0.14)" }}
                      layoutId="step-ping"
                      transition={{ type: "spring", stiffness: 300, damping: 26 }}
                    />
                  )}
                </span>

                <div className="flex flex-col items-center gap-0.5 min-w-[80px]">
                  <span
                    className={cn(
                      "text-[11px] font-semibold tracking-wide",
                      isActive ? "text-fg-0" : isPast ? "text-fg-1" : "text-fg-3"
                    )}
                  >
                    {s.label}
                  </span>
                  <span className="text-[10px] font-mono text-fg-3/70">
                    ETAPA {s.numero}
                  </span>
                </div>
              </Wrapper>

              {/* Conector entre steps */}
              {i < STUDIO_STEPS.length - 1 && (
                <div className="relative mx-2 h-px w-full max-w-[100px] min-w-[32px] overflow-hidden rounded-full bg-white/5">
                  <motion.div
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-neon via-neon-2 to-ok"
                    initial={false}
                    animate={{ width: isPast ? "100%" : isActive ? "50%" : "0%" }}
                    transition={{ duration: 0.6, ease: "easeInOut" }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
