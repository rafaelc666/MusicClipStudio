import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/contexts/LanguageContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  // ⚠️ O título padrão da raiz é do STUDIO, não da página de vendas.
  // A raiz "/" redireciona para /studio; se a aba mostrasse o título de
  // marketing (mesmo por um instante), o usuário pensaria estar na página
  // de vendas. A landing, em /landing, define o título próprio.
  title: "MusicClipStudio · Studio",
  description: "Estúdio de criação de videoclipes musicais: envie a música e gere o clipe com bancos de imagens da internet.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="pt"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
