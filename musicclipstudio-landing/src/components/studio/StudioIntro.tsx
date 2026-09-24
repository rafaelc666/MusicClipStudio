"use client";

/**
 * ⚠️ NOVO (23/09/2026) — INTRO DE ABERTURA do MusicClipStudio WEB.
 *
 * Referências (neon logo reveal + equalizer, padrão de apps de música):
 *   - Envato/VideoBolt "neon logo reveal": logo entra com brilho varrendo
 *   - Dribbble "splash screen music": equalizer de barras animadas
 * Aplicado à identidade do Studio: fundo escuro, ciano neon, grade de
 * fundo — os MESMOS tokens do app (bg-0, neon, studio-grid).
 *
 * Sequência (~4.2s total):
 *   0.0s  barras do equalizer "acordam" uma a uma do centro pra fora
 *   0.6s  wordmark MusiClipStudio surge com glow
 *   1.5s  shimmer varre o texto (brilho de reveal)
 *   3.4s  intro desvanece e libera o app
 *
 * Mostra UMA vez por sessão (sessionStorage) — F5 não repete, fechar e
 * reabrir a aba mostra de novo. Clique/tecla pula.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

const INTRO_JA_VISTA = "musicclipstudio_intro_v1";

/** Duração da intro: ~4,2s de animação + 0,45s de fade-out. */
const INTRO_DURACAO_MS = 4200;

/** 9 barras de equalizer; alturas em % animadas via CSS (stagger no delay). */
const BARRAS = [28, 55, 38, 80, 64, 92, 46, 70, 34];

export function StudioIntro({ onDone }: { onDone?: () => void }) {
  const [fase, setFase] = React.useState<"entrando" | "saindo" | "fora">("entrando");

  React.useEffect(() => {
    const t1 = window.setTimeout(() => setFase("saindo"), INTRO_DURACAO_MS);
    const t2 = window.setTimeout(() => {
      setFase("fora");
      onDone?.();
    }, INTRO_DURACAO_MS + 450);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [onDone]);

  const pular = React.useCallback(() => {
    setFase("fora");
    onDone?.();
  }, [onDone]);

  if (fase === "fora") return null;

  return (
    <div
      role="button"
      aria-label="Abertura do MusicClipStudio — clique para pular"
      onClick={pular}
      onKeyDown={pular}
      tabIndex={0}
      className={cn(
        "fixed inset-0 z-[9999] flex cursor-pointer flex-col items-center justify-center bg-bg-0 transition-opacity duration-400",
        fase === "saindo" ? "opacity-0" : "opacity-100"
      )}
    >
      {/* Grade de fundo (mesma do app) + vinheta */}
      <div className="pointer-events-none absolute inset-0 bg-studio-grid opacity-30" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(0,0,0,0.55)_100%)]" />

      <div className="relative flex flex-col items-center gap-7">
        {/* ── Equalizer ─────────────────────────────────────────── */}
        <div className="flex h-24 items-end gap-[7px]" aria-hidden>
          {BARRAS.map((altura, i) => {
            const doCentro = Math.abs(i - (BARRAS.length - 1) / 2);
            return (
              <span
                key={i}
                className="w-[9px] rounded-t-[3px] bg-gradient-to-t from-neon/40 via-neon to-neon-2 shadow-[0_0_18px_rgba(34,211,238,0.45)]"
                style={{
                  animation: `intro-barra 1.1s ease-in-out ${0.08 * doCentro}s infinite alternate, intro-nascer .5s cubic-bezier(.2,.7,.2,1) ${0.07 * i}s both`,
                  ["--h" as string]: `${altura}%`,
                }}
              />
            );
          })}
        </div>

        {/* ── Wordmark ──────────────────────────────────────────── */}
        <div className="relative animate-fade-up" style={{ animationDelay: "0.55s" }}>
          <h1 className="text-[42px] font-extrabold tracking-tight text-fg-0">
            <span className="text-neon drop-shadow-[0_0_24px_rgba(34,211,238,0.55)]">MusiClip</span>
            <span>Studio</span>
          </h1>
          {/* Shimmer: o brilho do "reveal" varre o texto uma vez */}
          <span
            aria-hidden
            className="pointer-events-none absolute inset-0 overflow-hidden"
            style={{ animation: "intro-shimmer 1s ease-out 1.35s both" }}
          >
            <span
              className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              style={{ animation: "intro-varredura .9s ease-in-out 1.35s both" }}
            />
          </span>
        </div>

        {/* ── Subtítulo ─────────────────────────────────────────── */}
        <p
          className="text-[12px] font-mono uppercase tracking-[0.35em] text-fg-3 animate-fade-up"
          style={{ animationDelay: "0.9s" }}
        >
          clipes musicais · web
        </p>
      </div>

      {/* Dica de pular */}
      <span className="absolute bottom-6 text-[11px] text-fg-3/70 animate-fade-up" style={{ animationDelay: "1.5s" }}>
        clique para pular
      </span>

      {/* Keyframes locais (escopo: só a intro) */}
      <style>{`
        @keyframes intro-nascer {
          from { height: 4%; opacity: 0; }
          to   { height: var(--h); opacity: 1; }
        }
        @keyframes intro-barra {
          from { height: calc(var(--h) * 0.45); }
          to   { height: var(--h); }
        }
        @keyframes intro-varredura {
          from { left: -40%; }
          to   { left: 120%; }
        }
        @keyframes intro-shimmer {
          from { opacity: 0; }
          20%  { opacity: 1; }
          to   { opacity: 0; }
        }
        @media (prefers-reduced-motion: reduce) {
          /* Acessibilidade: sem animação, intro estática curta */
          [style*="intro-barra"], [style*="intro-nascer"],
          [style*="intro-varredura"], [style*="intro-shimmer"] { animation: none !important; }
        }
      `}</style>
    </div>
  );
}

/**
 * Guard de sessão: mostra a intro só na primeira abertura da aba.
 * Uso: `const mostrarIntro = useIntroDeSessao();`
 *
 * ⚠️ CORRIGIDO (23/09/2026): em dev o StrictMode monta→desmonta→remaonta
 * o componente; o 1º efeito gravava a flag no sessionStorage e o 2º mount
 * lia a PRÓPRIA flag que acabou de gravar — a intro nunca aparecia.
 * A decisão agora fica em variável de módulo (sobrevive ao remount da
 * mesma carga da página) e o sessionStorage só separa aba nova de aba
 * já usada.
 */
let _decisaoTomada = false;
let _decisao = false;

export function useIntroDeSessao(): boolean {
  const [mostrar, setMostrar] = React.useState(false);

  React.useEffect(() => {
    if (_decisaoTomada) {
      setMostrar(_decisao);
      return;
    }
    _decisaoTomada = true;
    try {
      _decisao = !window.sessionStorage.getItem(INTRO_JA_VISTA);
      if (_decisao) window.sessionStorage.setItem(INTRO_JA_VISTA, "1");
    } catch {
      _decisao = true; // sessionStorage bloqueado — mostra (comportamento seguro)
    }
    setMostrar(_decisao);
  }, []);

  return mostrar;
}
