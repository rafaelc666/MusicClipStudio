"use client";

/**
 * ⚠️ NOVO (23/09/2026) — Tela de login/registro do Studio WEB.
 *
 * Regras do produto (decisão do usuário): nome + senha, multiusuário,
 * sem freemium. Login e registro na MESMA tela (aba) para não espantar —
 * registrar já entra (o backend devolve a sessão pronta).
 */

import * as React from "react";
import { motion } from "framer-motion";
import { KeyRound, Loader2, Music4 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useAuth } from "./AuthProvider";

export function LoginGate() {
  const { entrar, registrar } = useAuth();
  const [modo, setModo] = React.useState<"entrar" | "criar">("entrar");
  const [username, setUsername] = React.useState("");
  const [senha, setSenha] = React.useState("");
  const [senha2, setSenha2] = React.useState("");
  const [erro, setErro] = React.useState("");
  const [ocupado, setOcupado] = React.useState(false);

  const submeter = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    if (!username.trim() || !senha) {
      setErro("Preencha usuário e senha.");
      return;
    }
    if (modo === "criar" && senha !== senha2) {
      setErro("As senhas não conferem.");
      return;
    }
    setOcupado(true);
    try {
      if (modo === "entrar") await entrar(username.trim(), senha);
      else await registrar(username.trim(), senha);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Falha inesperada");
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[500] flex items-center justify-center bg-bg-0">
      <div className="pointer-events-none absolute inset-0 bg-studio-grid opacity-30" />
      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
        className="relative w-full max-w-[380px] rounded-sm border border-white/10 bg-bg-1/80 p-7 shadow-[0_24px_80px_-24px_rgba(0,0,0,0.8)] backdrop-blur-md"
      >
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-sm border border-neon/30 bg-neon/10">
            <Music4 className="h-5 w-5 text-neon" />
          </span>
          <div>
            <h1 className="text-[16px] font-semibold text-fg-0">
              Music<span className="text-neon">Clip</span>Studio
            </h1>
            <p className="text-[11px] text-fg-3">Entre para configurar suas chaves e gerar clipes</p>
          </div>
        </div>

        {/* Abas Entrar / Criar conta */}
        <div className="mb-5 grid grid-cols-2 gap-1 rounded-sm border border-white/10 bg-bg-2/60 p-1">
          {(["entrar", "criar"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => { setModo(m); setErro(""); }}
              className={cn(
                "rounded-sm px-3 py-1.5 text-[12px] font-medium transition-colors",
                modo === m ? "bg-neon/15 text-neon" : "text-fg-3 hover:text-fg-0"
              )}
            >
              {m === "entrar" ? "Entrar" : "Criar conta"}
            </button>
          ))}
        </div>

        <form onSubmit={submeter} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-wide text-fg-3">Usuário</span>
            <Input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="seu.nome"
              autoComplete="username"
              autoFocus
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-wide text-fg-3">Senha</span>
            <Input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              placeholder="••••••••"
              autoComplete={modo === "entrar" ? "current-password" : "new-password"}
            />
          </label>
          {modo === "criar" && (
            <label className="flex flex-col gap-1.5">
              <span className="text-[11px] uppercase tracking-wide text-fg-3">Repetir senha</span>
              <Input
                type="password"
                value={senha2}
                onChange={(e) => setSenha2(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </label>
          )}

          {erro && (
            <p className="rounded-sm border border-red-500/30 bg-red-500/10 px-3 py-2 text-[12px] text-red-300">
              {erro}
            </p>
          )}

          <Button type="submit" variant="neon" disabled={ocupado} className="mt-1 w-full">
            {ocupado ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
            {modo === "entrar" ? "Entrar" : "Criar conta e entrar"}
          </Button>
        </form>

        <p className="mt-5 text-[11px] leading-relaxed text-fg-3">
          Cada usuário guarda as <span className="text-fg-1">próprias chaves de API</span> dos bancos
          de foto/vídeo — criptografadas no seu computador, nunca enviadas para fora.
        </p>
      </motion.div>
    </div>
  );
}
