"use client";

/**
 * ⚠️ NOVO (24/09/2026) — Busca de trilha pronta no Epidemic Sound (Partner API).
 *
 * Fecha o fluxo da Etapa 03: em vez de o usuário baixar música no site do ES e
 * subir o arquivo à mão, ele busca aqui e o botão "Baixar pra sequência" cria a
 * faixa direto na playlist (mesmo formato de /api/upload/audio), pronta para
 * ser juntada com as dele pelo crossfade.
 *
 * A chave vive no cofre do usuário (Etapa 01) — ou no .env desta máquina. O
 * front NUNCA vê a chave: fala só com /api/musica/epidemic/*.
 */

import * as React from "react";
import { Download, Loader2, Music2, Search, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { API_BASE } from "@/lib/utils";
import { toast } from "sonner";
import type { FaixaAudio } from "@/app/studio/StudioClientShell";

type FaixaES = {
  id: string;
  titulo: string;
  artistas: string[];
  duracao: number;
  bpm?: number | null;
  moods: string[];
  generos: string[];
  capa?: string;
  com_voz?: boolean;
};

type Filtro = { id: string; nome: string };

const mmss = (s: number) => {
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
};

export function BuscaEpidemic({
  aoBaixar,
}: {
  /** Chamado quando o download termina: a faixa entra na playlist da Etapa 03. */
  aoBaixar: (faixa: FaixaAudio) => void;
}) {
  const [termo, setTermo] = React.useState("");
  const [genero, setGenero] = React.useState("");
  const [humor, setHumor] = React.useState("");
  const [ordem, setOrdem] = React.useState("Relevance");
  const [filtros, setFiltros] = React.useState<{ generos: Filtro[]; humores: Filtro[] }>({
    generos: [],
    humores: [],
  });
  const [faixas, setFaixas] = React.useState<FaixaES[]>([]);
  const [buscando, setBuscando] = React.useState(false);
  const [erro, setErro] = React.useState("");
  const [aberto, setAberto] = React.useState(false);
  const [baixando, setBaixando] = React.useState<string | null>(null);

  // Gêneros/humores só na primeira abertura — o backend não guarda cache (regra
  // do próprio Epidemic), então evitamos repetir a chamada sem necessidade.
  React.useEffect(() => {
    if (!aberto || filtros.generos.length) return;
    fetch(`${API_BASE}/api/musica/epidemic/filtros`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((j) => setFiltros({ generos: j.generos ?? [], humores: j.humores ?? [] }))
      .catch(() => {
        /* sem filtros ainda dá para buscar pelo termo */
      });
  }, [aberto, filtros.generos.length]);

  const buscar = async () => {
    setBuscando(true);
    setErro("");
    try {
      const qs = new URLSearchParams({ limite: "20", ordem });
      if (termo.trim()) qs.set("termo", termo.trim());
      if (genero) qs.set("genero", genero);
      if (humor) qs.set("humor", humor);
      const r = await fetch(`${API_BASE}/api/musica/epidemic/buscar?${qs}`);
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j?.detail || `HTTP ${r.status}`);
      setFaixas(j.faixas ?? []);
      if (!(j.faixas ?? []).length) setErro("Nenhuma faixa encontrada com esses filtros.");
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha na busca");
      setFaixas([]);
    } finally {
      setBuscando(false);
    }
  };

  const baixar = async (f: FaixaES) => {
    setBaixando(f.id);
    const id = toast.loading(`Baixando “${f.titulo}”…`);
    try {
      const r = await fetch(`${API_BASE}/api/musica/epidemic/baixar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_id: f.id, titulo: f.titulo, qualidade: "high" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j?.detail || `HTTP ${r.status}`);
      aoBaixar({
        path: j.path,
        url: j.url,
        nome: `${f.titulo} — ${f.artistas.join(", ") || "Epidemic Sound"}.mp3`,
        tamanhoBytes: j.size_bytes ?? 0,
        duracao: j.duracao ?? f.duracao,
      });
      toast.success("Faixa adicionada à sequência", { id, description: f.titulo });
    } catch (e) {
      toast.error("Não deu para baixar a faixa", {
        id,
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setBaixando(null);
    }
  };

  return (
    <div className="rounded-md border border-neon/25 bg-neon/[0.03] p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-[12.5px] font-semibold text-fg-1">
          <Music2 className="h-4 w-4 text-neon" />
          Buscar trilha no Epidemic Sound
          <Badge variant="neon" className="text-[9.5px]">catálogo pago</Badge>
        </span>
        <Button size="sm" variant="ghost" onClick={() => setAberto((v) => !v)}>
          {aberto ? "Fechar busca" : "Abrir busca"}
        </Button>
      </div>
      <p className="mt-1 text-[11px] leading-relaxed text-fg-3">
        Precisa da chave da Partner API na <b>etapa 01</b>. A faixa baixada entra na
        sequência abaixo como se você tivesse enviado o arquivo.
      </p>

      {aberto && (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              value={termo}
              onChange={(e) => setTermo(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && buscar()}
              placeholder="Ex.: cinematic epic, lo-fi, happy…"
              className="h-8 min-w-[180px] flex-1 text-[12px]"
            />
            <select
              value={genero}
              onChange={(e) => setGenero(e.target.value)}
              className="h-8 rounded-sm border border-white/10 bg-bg-2 px-2 text-[12px] text-fg-1"
              aria-label="Gênero"
            >
              <option value="">Gênero: qualquer</option>
              {filtros.generos.map((g) => (
                <option key={g.id} value={g.id}>{g.nome}</option>
              ))}
            </select>
            <select
              value={humor}
              onChange={(e) => setHumor(e.target.value)}
              className="h-8 rounded-sm border border-white/10 bg-bg-2 px-2 text-[12px] text-fg-1"
              aria-label="Humor"
            >
              <option value="">Humor: qualquer</option>
              {filtros.humores.map((h) => (
                <option key={h.id} value={h.id}>{h.nome}</option>
              ))}
            </select>
            <select
              value={ordem}
              onChange={(e) => setOrdem(e.target.value)}
              className="h-8 rounded-sm border border-white/10 bg-bg-2 px-2 text-[12px] text-fg-1"
              aria-label="Ordenar por"
            >
              {["Relevance", "Popularity", "Date", "Title", "Duration", "BPM"].map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
            <Button size="sm" variant="outline" onClick={buscar} disabled={buscando}>
              {buscando ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
              Buscar
            </Button>
          </div>

          {erro && (
            <p className="rounded-sm border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200">
              {erro}
            </p>
          )}

          {faixas.length > 0 && (
            <div className="grid max-h-[320px] gap-2 overflow-y-auto pr-1">
              {faixas.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center gap-3 rounded-sm border border-white/10 bg-bg-2/40 p-2.5"
                >
                  {f.capa ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={f.capa} alt="" className="h-10 w-10 flex-none rounded-sm object-cover" />
                  ) : (
                    <div className="h-10 w-10 flex-none rounded-sm bg-white/5" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[12.5px] font-medium text-fg-0">{f.titulo}</p>
                    <p className="truncate text-[11px] text-fg-3">
                      <User className="mr-1 inline h-3 w-3" />
                      {f.artistas.join(", ") || "—"}
                      {" · "}
                      {mmss(f.duracao)}
                      {f.bpm ? ` · ${f.bpm} BPM` : ""}
                      {f.com_voz ? " · com voz" : ""}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="neon"
                    onClick={() => void baixar(f)}
                    disabled={baixando === f.id}
                  >
                    {baixando === f.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Download className="h-3.5 w-3.5" />
                    )}
                    Baixar pra sequência
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
