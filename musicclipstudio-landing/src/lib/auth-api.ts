"use client";

/**
 * ⚠️ NOVO (23/09/2026) — Cliente dos endpoints /api/auth/* e /api/provedores/*.
 *
 * A sessão vive em cookie httpOnly (o backend define) — aqui não guardamos
 * token nenhum no localStorage (imune a XSS). `credentials: "include"` é
 * redundante same-origin, mas explícito para o proxy do dev.
 */

import { API_BASE } from "@/lib/utils";

export type Usuario = { id: string; username: string };

export type ProvedorEstado = {
  id: string;
  nome: string;
  tipo?: string;
  gratuita_sem_chave?: boolean;
  configurada: boolean;
  previa: string;
  habilitado: boolean;
  // ⚠️ NOVO (23/09/2026): endpoint de API do banco (custom) + oficial.
  url?: string;
  url_oficial?: string;
};

export type ResumoProvedores = { ok: boolean; fixos: ProvedorEstado[]; custom: ProvedorEstado[] };

async function post<T>(caminho: string, corpo?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${caminho}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((json as { detail?: string })?.detail || `HTTP ${r.status}`);
  return json as T;
}

export const authApi = {
  eu: async (): Promise<{ logado: boolean; usuario?: Usuario }> => {
    const r = await fetch(`${API_BASE}/api/auth/eu`);
    if (!r.ok) return { logado: false };
    return r.json();
  },
  registrar: (username: string, password: string) =>
    post<{ ok: boolean; usuario: Usuario }>("/api/auth/registrar", { username, password }),
  login: (username: string, password: string) =>
    post<{ ok: boolean; usuario: Usuario }>("/api/auth/login", { username, password }),
  logout: () => post<{ ok: boolean }>("/api/auth/logout"),

  provedores: async (): Promise<ResumoProvedores> => {
    const r = await fetch(`${API_BASE}/api/provedores`);
    const json = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((json as { detail?: string })?.detail || `HTTP ${r.status}`);
    return json as ResumoProvedores;
  },
  // ⚠️ 23/09/2026: `url` opcional — endpoint de API do banco (proxy/endpoint
  // próprio). Vazio/removeu = usa a URL oficial do banco. `chave: null` =
  // não mexer na chave salva (salvar só a URL).
  salvarChave: (provedor_id: string, chave: string | null, url = "") =>
    post<ResumoProvedores>("/api/provedores/chave", {
      provedor_id,
      chave: chave ?? undefined,
      url,
    }),
  habilitar: (provedor_id: string, habilitado: boolean) =>
    post<{ ok: boolean }>("/api/provedores/habilitar", { provedor_id, habilitado }),
  renomearCustom: (idx: number, nome: string) =>
    post<{ ok: boolean }>("/api/provedores/custom/renomear", { idx, nome }),
  // ⚠️ 23/09/2026: slots próprios ILIMITADOS — adicionar/remover pela UI.
  adicionarCustom: (tipo: string, nome = "") =>
    post<ResumoProvedores>("/api/provedores/custom/adicionar", { tipo, nome }),
  removerCustom: (idx: number) =>
    post<ResumoProvedores>("/api/provedores/custom/remover", { idx, nome: "" }),
  testar: (provedor_id: string, chave = "", url = "") =>
    post<{ ok: boolean; mensagem: string }>("/api/provedores/testar", { provedor_id, chave, url }),
  // ⚠️ NOVO (23/09/2026): 1 clique copia as chaves do .env desta máquina para
  // a conta do usuário (as que ele já salvou não são sobrescritas).
  importarGlobais: () =>
    post<{ ok: boolean; importadas: string[]; resumo: ResumoProvedores }>(
      "/api/provedores/importar-globais",
      {},
    ),
};
