import type { NextConfig } from "next";

/**
 * ⚠️ POR QUE EXISTE ESTE PROXY REVERSO
 *
 * O navegador do usuário pode ter PROXY DO SISTEMA configurado
 * (HTTP_PROXY/HTTPS_PROXY → http://127.0.0.1:51889). Esse proxy intercepta
 * QUALQUER requisição, inclusive para localhost, e devolve
 * "502 Bad Gateway" quando o destino é o backend FastAPI.
 *
 * Sintoma que isso causava no wizard:
 *   - Etapa 3 (música): upload falhava silenciosamente
 *   - demais etapas: pareciam "não carregar"
 * O backend estava 100% OK (testado: POST /api/upload/audio → 200); era o
 * navegador que não conseguia falar com ele.
 *
 * SOLUÇÃO: o navegador passa a falar SÓ com a porta do frontend (mesma
 * origem, portanto imune ao proxy). O dev server do Next repassa /api/* e
 * /static/* para o backend por dentro — no processo servidor, onde o proxy
 * do navegador não interfere.
 *
 * Isso é permanente e não depende de mexer nas configurações do Windows.
 *
 * ─── PORTAS DEDICADAS (2026-09-20) ──────────────────────────────────────
 * O projeto SAU DE 3000/8000. Essas são as portas que todo projeto
 * Next/FastAPI pega por padrão, e isso já gerou conflito repetidas vezes
 * nesta máquina. Agora:
 *
 *     frontend (Next)     → 3100
 *     backend  (FastAPI)  → 8300
 *
 * Referência canônica: `_utils/_portas.py`. Se mudar lá, mudar aqui.
 */
const BACKEND = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8300";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost"],

  async rewrites() {
    return [
      // API do FastAPI
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
      // Arquivos gerados/servidos pelo backend (áudio enviado, thumbnails, vídeos)
      { source: "/static/:path*", destination: `${BACKEND}/static/:path*` },
    ];
  },
};

export default nextConfig;
