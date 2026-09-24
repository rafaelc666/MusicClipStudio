"use client";

/**
 * ⚠️ NOVO (23/09/2026) — Diálogo "Configurar provedores" (chaves de API).
 *
 * Abre pelo item "Configurações" da sidebar e pelo botão da etapa 04.
 * Mostra os 7 bancos fixos + 2 slots livres, com:
 *  - campo de chave (só grava no botão; guardada criptografada no backend);
 *  - botão Testar (bate na API real do banco);
 *  - toggle liga/desliga (desligado = o motor ignora o banco na busca);
 *  - rename dos slots livres.
 * As chaves NUNCA voltam abertas do backend — só prévia "…abcd".
 */

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, Pencil, Plus, Power, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { authApi, type ProvedorEstado, type ResumoProvedores } from "@/lib/auth-api";
import { useAuth } from "./AuthProvider";

/** Engines de busca disponíveis para um banco próprio (mesmas dos fixos). */
const ENGINES = [
  { id: "pexels", nome: "Pexels" },
  { id: "pixabay", nome: "Pixabay" },
  { id: "unsplash", nome: "Unsplash" },
  { id: "nasa", nome: "NASA" },
  { id: "coverr", nome: "Coverr" },
  { id: "giphy", nome: "Giphy" },
  { id: "openverse", nome: "Openverse" },
];

type LinhaProps = {
  p: ProvedorEstado;
  custom?: boolean;
  onSalvo: (r: ResumoProvedores) => void;
  onRemover?: (idx: number) => void;
};

function LinhaProvedor({ p, custom = false, onSalvo, onRemover }: LinhaProps) {
  const [chave, setChave] = React.useState("");
  // ⚠️ NOVO (23/09/2026): endpoint de API do banco — vazio = URL oficial.
  const [url, setUrl] = React.useState(p.url || "");
  const urlMudou = (url.trim() || "") !== (p.url || "");
  const [nome, setNome] = React.useState(p.nome);
  const [editandoNome, setEditandoNome] = React.useState(false);
  const [ocupado, setOcupado] = React.useState<"salvar" | "testar" | null>(null);
  const [teste, setTeste] = React.useState<{ ok: boolean; msg: string } | null>(null);

  const salvar = async () => {
    // Permite salvar SO a URL (chave null = não mexer na salva) ou a chave
    // digitada + o estado atual da URL (None-on-wire não existe aqui; enviamos
    // sempre a url do estado e o backend trata "" como voltar p/ oficial).
    if (!chave.trim() && !urlMudou) return;
    setOcupado("salvar");
    setTeste(null);
    try {
      onSalvo(await authApi.salvarChave(p.id, chave.trim() || null, url.trim()));
      setChave("");
    } catch (e) {
      setTeste({ ok: false, msg: e instanceof Error ? e.message : "erro" });
    } finally {
      setOcupado(null);
    }
  };

  const testar = async () => {
    setOcupado("testar");
    try {
      // Testa com a chave/URL recém-digitadas (antes de salvar).
      const r = await authApi.testar(p.id, chave.trim(), url.trim());
      setTeste({ ok: !!r.ok, msg: r.mensagem || (r.ok ? "Conectado" : "Falhou") });
    } catch (e) {
      setTeste({ ok: false, msg: e instanceof Error ? e.message : "erro" });
    } finally {
      setOcupado(null);
    }
  };

  const alternar = async () => {
    try {
      await authApi.habilitar(p.id, !p.habilitado);
      onSalvo(await authApi.provedores());
    } catch {
      /* silencioso */
    }
  };

  return (
    <div className="rounded-sm border border-white/10 bg-bg-2/40 p-3">
      <div className="flex items-center gap-2">
        {custom && editandoNome ? (
          <Input
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            onBlur={async () => {
              setEditandoNome(false);
              const idx = Number(p.id.split("_")[1]);
              try {
                await authApi.renomearCustom(idx, nome);
                const r = await authApi.provedores();
                onSalvo(r);
              } catch { /* silencioso */ }
            }}
            onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
            autoFocus
            className="h-7 max-w-[200px] text-[12px]"
          />
        ) : (
          <span className="flex items-center gap-1.5 text-[13px] font-medium text-fg-0">
            {p.nome}
            {custom && (
              <button
                type="button"
                aria-label="Renomear"
                onClick={() => setEditandoNome(true)}
                className="text-fg-3 hover:text-fg-0"
              >
                <Pencil className="h-3 w-3" />
              </button>
            )}
          </span>
        )}
        {p.tipo && <span className="text-[10px] text-fg-3 font-mono">{p.tipo}</span>}
        {custom && onRemover && (
          <button
            type="button"
            aria-label="Remover este banco"
            title="Remover este banco"
            onClick={() => onRemover(Number(p.id.split("_")[1]))}
            className="text-fg-3/70 transition-colors hover:text-red-300"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
        {p.gratuita_sem_chave && (
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-1.5 py-0.5 text-[9.5px] text-emerald-300">
            grátis sem chave
          </span>
        )}
        <button
          type="button"
          onClick={alternar}
          aria-label={p.habilitado ? "Desligar provedor" : "Ligar provedor"}
          className={cn("ml-auto rounded-sm p-1.5 transition-colors",
            p.habilitado ? "text-neon hover:bg-neon/10" : "text-fg-3/60 hover:bg-white/5")}
        >
          <Power className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <Input
          type="password"
          value={chave}
          onChange={(e) => setChave(e.target.value)}
          placeholder={p.configurada ? `Salva ${p.previa} — digite para trocar` : "Cole a chave da API…"}
          className="h-8 flex-1 font-mono text-[12px]"
        />
        <Button size="sm" variant="outline" onClick={salvar} disabled={(!chave.trim() && !urlMudou) || ocupado !== null}>
          {ocupado === "salvar" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
          Salvar
        </Button>
        <Button size="sm" variant="ghost" onClick={testar} disabled={ocupado !== null || (!p.configurada && !chave.trim())}>
          {ocupado === "testar" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
          Testar
        </Button>
      </div>

      {/* ⚠️ NOVO (23/09/2026): endpoint da API do banco. Vazio = oficial.
          Mostrado como campo técnico (mono, menor) — a maioria não precisa
          mexer, mas bancos próprios/proxy exigem. */}
      <div className="mt-1.5">
        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={`URL da API (oficial: ${p.url_oficial || "—"})`}
          className="h-6 border-white/5 bg-bg-2/30 px-2 font-mono text-[10.5px] text-fg-2"
          spellCheck={false}
        />
        <p className="mt-0.5 px-1 text-[9.5px] text-fg-3/80">
          Deixe vazio para usar a URL oficial. Preencha só se usa proxy ou endpoint próprio.
        </p>
      </div>

      <div className="mt-1.5 flex items-center gap-2 text-[11px]">
        {teste && (
          <span className={teste.ok ? "text-emerald-300" : "text-red-300"}>
            {teste.ok ? "✓" : "✗"} {teste.msg}
          </span>
        )}
        {!teste && (
          <span className={cn("flex items-center gap-1", p.configurada ? "text-emerald-300" : "text-fg-3")}>
            <span className={cn("h-1.5 w-1.5 rounded-full", p.configurada ? "bg-emerald-400" : "bg-fg-3/40")} />
            {p.configurada ? `configurada ${p.previa}` : p.habilitado ? "sem chave — será ignorado" : "desligado"}
          </span>
        )}
      </div>
    </div>
  );
}

/** ⚠️ NOVO (23/09/2026): máquina já tem chaves no .env? 1 clique importa
    para a conta (sem sobrescrever as que o usuário já salvou). */
function ImportarGlobais({ onPronto }: { onPronto: (r: ResumoProvedores) => void }) {
  const [ocupado, setOcupado] = React.useState(false);
  const [msg, setMsg] = React.useState("");
  const importar = async () => {
    setOcupado(true);
    setMsg("");
    try {
      const r = await authApi.importarGlobais();
      onPronto(r.resumo);
      const n = r.importadas.length;
      setMsg(
        n > 0
          ? `✓ ${n} chave${n > 1 ? "s" : ""} importada${n > 1 ? "s" : ""} do .env — pode testar abaixo.`
          : "Nenhuma chave nova para importar (todas já configuradas ou .env vazio).",
      );
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "erro ao importar");
    } finally {
      setOcupado(false);
    }
  };
  return (
    <div className="mt-4 rounded-sm border border-neon/30 bg-neon/5 p-3">
      <p className="text-[12px] leading-relaxed text-fg-1">
        Este computador já tem chaves de API no arquivo <code className="font-mono text-neon">.env</code>.
      </p>
      <div className="mt-2 flex items-center gap-2">
        <Button variant="neon" size="sm" onClick={importar} disabled={ocupado}>
          {ocupado ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
          Importar chaves do .env (1 clique)
        </Button>
        {msg && <span className="text-[11.5px] text-emerald-300">{msg}</span>}
      </div>
    </div>
  );
}

export function ProvedoresDialog({ aberto, onFechar }: { aberto: boolean; onFechar: () => void }) {
  const { usuario } = useAuth();
  const [resumo, setResumo] = React.useState<ResumoProvedores | null>(null);
  const [erro, setErro] = React.useState("");

  React.useEffect(() => {
    if (!aberto || !usuario) return;
    setErro("");
    authApi.provedores()
      .then(setResumo)
      .catch((e) => setErro(e instanceof Error ? e.message : "erro ao carregar"));
  }, [aberto, usuario]);

  return (
    <AnimatePresence>
      {aberto && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[600] flex items-start justify-center overflow-y-auto bg-black/70 p-6 backdrop-blur-sm"
          onClick={onFechar}
        >
          <motion.div
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.25, ease: [0.2, 0.7, 0.2, 1] }}
            onClick={(e) => e.stopPropagation()}
            className="my-8 w-full max-w-[560px] rounded-sm border border-white/10 bg-bg-1 p-6 shadow-[0_24px_80px_-24px_rgba(0,0,0,0.85)]"
          >
            <div className="mb-1 flex items-start justify-between">
              <div>
                <h2 className="text-[15px] font-semibold text-fg-0">Chaves de API — bancos de mídia</h2>
                <p className="mt-0.5 text-[11.5px] text-fg-3">
                  Guardadas criptografadas na SUA conta. Pelo menos 1 banco com chave (ou grátis) é
                  preciso para a etapa 05 buscar mídia.
                </p>
              </div>
              <Button size="icon" variant="ghost" onClick={onFechar} aria-label="Fechar">
                <X className="h-4 w-4" />
              </Button>
            </div>

            {erro && (
              <p className="mt-3 rounded-sm border border-red-500/30 bg-red-500/10 px-3 py-2 text-[12px] text-red-300">
                {erro}
              </p>
            )}

            {resumo && !resumo.fixos.some((p) => p.configurada) && (
              <ImportarGlobais onPronto={setResumo} />
            )}

            {resumo && (
              <div className="mt-4 flex flex-col gap-2.5">
                {resumo.fixos.map((p) => (
                  <LinhaProvedor key={p.id} p={p} onSalvo={setResumo} />
                ))}
                <p className="mt-3 text-[11px] uppercase tracking-wide text-fg-3 font-mono">
                  bancos próprios (opcional)
                </p>
                {resumo.custom.map((p) => (
                  <LinhaProvedor
                    key={p.id}
                    p={p}
                    custom
                    onSalvo={setResumo}
                    onRemover={async (idx) => {
                      try {
                        setResumo(await authApi.removerCustom(idx));
                      } catch { /* silencioso */ }
                    }}
                  />
                ))}

                {/* ⚠️ 23/09/2026: slots próprios ILIMITADOS — adicionar quantos
                    bancos quiser, escolhendo qual engine de busca ele usa. */}
                <AddCustomForm onSalvo={setResumo} />
              </div>
            )}

            <div className="mt-5 flex justify-end">
              <Button variant="neon" onClick={onFechar}>Concluído</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** Formulário "Adicionar banco": nome livre + engine de busca. */
function AddCustomForm({ onSalvo }: { onSalvo: (r: ResumoProvedores) => void }) {
  const [tipo, setTipo] = React.useState("pexels");
  const [nome, setNome] = React.useState("");
  const [ocupado, setOcupado] = React.useState(false);

  const adicionar = async () => {
    setOcupado(true);
    try {
      onSalvo(await authApi.adicionarCustom(tipo, nome.trim()));
      setNome("");
    } catch { /* silencioso */ } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="rounded-sm border border-dashed border-white/15 bg-bg-2/20 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          placeholder="Nome do banco (ex.: Meu banco de vídeos)"
          className="h-8 min-w-[180px] flex-1 text-[12px]"
        />
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="h-8 rounded-sm border border-white/10 bg-bg-2 px-2 text-[12px] text-fg-1"
          aria-label="API que o banco usa"
        >
          {ENGINES.map((e) => (
            <option key={e.id} value={e.id}>usa API do {e.nome}</option>
          ))}
        </select>
        <Button size="sm" variant="outline" onClick={adicionar} disabled={ocupado}>
          {ocupado ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
          Adicionar banco
        </Button>
      </div>
      <p className="mt-1.5 text-[10.5px] text-fg-3">
        Quantos bancos quiser. Escolha qual API de busca ele usa — a chave do banco entra nessa engine.
      </p>
    </div>
  );
}
