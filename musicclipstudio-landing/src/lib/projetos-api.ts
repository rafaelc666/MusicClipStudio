"use client";

import { API_BASE } from "@/lib/utils";

/**
 * Cliente dos endpoints de persistência de projetos (/api/projetos).
 *
 * O backend guarda em SQLite local (ver §14 do STATUS_MIGRACAO_WEB.md).
 * Toda função é tolerante a falha: se a API estiver offline, devolve
 * `null`/`[]` em vez de explodir — o wizard continua utilizável offline.
 */

export interface ProjetoSalvo {
  id: string;
  title: string;
  createdAt: number;
  updatedAt?: number;
  status?: string;
  letra?: string;
  legenda?: unknown[];
  legendaEstilo?: {
    cor: string; corContorno: string; fonte: string; tamanho: number;
    contorno: number; posicao: "baixo" | "centro" | "topo"; negrito: boolean;
  };
  musica?: { prompt?: string; duracao?: number; path?: string };
  imagens?: unknown[];
  midia?: unknown[];
  formato?: "9/16" | "16/9" | "3/4" | "4/3" | "1/1";
  completedSteps?: Record<string, boolean>;
  activeStep?: string;
}

const TIMEOUT_MS = 6000;

async function pedir<T>(
  caminho: string,
  init?: RequestInit,
): Promise<T | null> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(`${API_BASE}${caminho}`, {
      ...init,
      signal: ctrl.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
    if (!r.ok) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

/** Lista os projetos salvos. `[]` se a API estiver offline. */
export async function listarProjetos(limite = 50): Promise<ProjetoSalvo[]> {
  const r = await pedir<{ total: number; projetos: ProjetoSalvo[] }>(
    `/api/projetos?limite=${limite}`,
  );
  return r?.projetos ?? [];
}

/** Busca um projeto por id. */
export async function obterProjeto(id: string): Promise<ProjetoSalvo | null> {
  return pedir<ProjetoSalvo>(`/api/projetos/${encodeURIComponent(id)}`);
}

/** Cria ou atualiza (upsert). Devolve o projeto gravado, ou null se falhou. */
export async function salvarProjeto(
  projeto: Partial<ProjetoSalvo> & { id?: string },
): Promise<ProjetoSalvo | null> {
  const r = await pedir<{ ok: boolean; projeto: ProjetoSalvo }>(
    "/api/projetos",
    { method: "POST", body: JSON.stringify(projeto) },
  );
  return r?.projeto ?? null;
}

/** Remove um projeto. */
export async function apagarProjeto(id: string): Promise<boolean> {
  const r = await pedir<{ ok: boolean }>(
    `/api/projetos/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  );
  return Boolean(r?.ok);
}

/** Estatísticas rápidas do dashboard. */
export async function estatisticasProjetos(): Promise<{ total: number } | null> {
  return pedir<{ total: number; db: string }>("/api/projetos-stats");
}
