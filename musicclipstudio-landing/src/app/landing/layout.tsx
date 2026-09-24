import type { Metadata } from "next";

/**
 * Metadata da página de MARKETING.
 *
 * Fica num layout próprio porque `page.tsx` é client component ('use client')
 * e client components não podem exportar `metadata`. Este é o título que
 * pertencia à raiz "/" antes de 20/09/2026 — quando a raiz passou a
 * redirecionar para /studio, o título de marketing veio junto para cá.
 */
export const metadata: Metadata = {
  title: "MusicClipStudio - Transforme letras em videoclipes com IA",
  description:
    "Uma ferramenta independente e poderosa para criar lyric videos e videoclipes musicais usando inteligência artificial. Apoie o desenvolvimento deste projeto inovador.",
};

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
