import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Base da API FastAPI.
 *
 * ⚠️ POR QUE O PADRÃO É "" (mesma origem) E NÃO uma URL direta do backend
 *
 * O navegador do usuário pode ter um proxy do sistema que intercepta até o
 * localhost e devolve 502 quando o destino é o backend FastAPI. Se o front
 * chamar `http://127.0.0.1:8300/api/...` direto, o proxy entra no meio e a
 * chamada morre — foi o que quebrava o upload da música na Etapa 3.
 *
 * Com "" o front chama `/api/...` na PRÓPRIA origem (porta 3100), e o
 * `next.config.ts` repassa para o backend por dentro do servidor
 * (`rewrites`), onde o proxy do navegador não interfere.
 *
 * Portas dedicadas: frontend 3100, backend 8300 (ver _utils/_portas.py).
 *
 * Para apontar para outro backend explicitamente, defina
 * NEXT_PUBLIC_API_URL (ex.: em produção, onde não há esse proxy).
 */
declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace NodeJS {
    interface ProcessEnv {
      NEXT_PUBLIC_API_URL?: string;
    }
  }
}

export const API_BASE: string =
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) || "";
