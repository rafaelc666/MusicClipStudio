"use client";

/**
 * ⚠️ NOVO (23/09/2026) — Contexto de autenticação do Studio WEB.
 *
 * Carrega a sessão uma vez (GET /api/auth/eu) e expõe { usuario, login,
 * registrar, sair }. Enquanto carrega, `carregando=true` — as telas que
 * exigem login esperam esse estado para não piscar a tela de login.
 */

import * as React from "react";
import { authApi, type Usuario } from "@/lib/auth-api";

type AuthCtx = {
  usuario: Usuario | null;
  carregando: boolean;
  entrar: (username: string, senha: string) => Promise<void>;
  registrar: (username: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  recarregar: () => Promise<void>;
};

const Ctx = React.createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = React.useState<Usuario | null>(null);
  const [carregando, setCarregando] = React.useState(true);

  const recarregar = React.useCallback(async () => {
    try {
      const r = await authApi.eu();
      setUsuario(r.logado ? r.usuario ?? null : null);
    } catch {
      setUsuario(null); // backend fora do ar — tratar como deslogado
    } finally {
      setCarregando(false);
    }
  }, []);

  React.useEffect(() => {
    void recarregar();
  }, [recarregar]);

  const entrar = React.useCallback(async (username: string, senha: string) => {
    const r = await authApi.login(username, senha);
    setUsuario(r.usuario);
  }, []);

  const registrar = React.useCallback(async (username: string, senha: string) => {
    const r = await authApi.registrar(username, senha);
    setUsuario(r.usuario);
  }, []);

  const sair = React.useCallback(async () => {
    await authApi.logout().catch(() => undefined);
    setUsuario(null);
  }, []);

  const valor = React.useMemo(
    () => ({ usuario, carregando, entrar, registrar, sair, recarregar }),
    [usuario, carregando, entrar, registrar, sair, recarregar]
  );
  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const ctx = React.useContext(Ctx);
  if (!ctx) throw new Error("useAuth fora de <AuthProvider>");
  return ctx;
}
