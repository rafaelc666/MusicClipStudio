import type { Metadata } from "next";
import { AuthProvider } from "@/components/studio/AuthProvider";
import { StudioClientShell } from "./StudioClientShell";

export const metadata: Metadata = {
  title: "Studio · MusicClipStudio",
  description: "Painel de projetos e wizard de criação de clipes musicais.",
};

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  // ⚠️ NOVO (23/09/2026): AuthProvider envolve o shell inteiro — sessão
  // disponível em todas as telas do /studio.
  return (
    <AuthProvider>
      <StudioClientShell>{children}</StudioClientShell>
    </AuthProvider>
  );
}

