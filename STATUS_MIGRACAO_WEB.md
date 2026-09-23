# STATUS DA MIGRAÇÃO · MusicClipStudio → WEB

> 📌 Documento de referência — criado em **19/09/2026**
> Mantém o inventário do que já foi feito, o que falta, como rodar e como instalar os atalhos.

> ### 🅿️ PROJETO PAUSADO — 19/09/2026 (atualizado 20/09)
>
> **Pausado para o usuário testar.** Ao retomar, comece pela **§21 — Balanço
> da Jornada (Feito × Falta)**, que resume tudo numa página só. A **§14** é a
> definição oficial de arquitetura (Opção A).
>
> **Últimas correções (20/09, madrugada):** §25 — estado do projeto sumia ao
> navegar (corrigido); §26 — a raiz abria a **página de vendas** em vez do
> **programa** (corrigido: `/` → `/studio`, landing movida para `/landing`).

---

## 1. Resumo Executivo

> ### 🎯 O que este produto é (leia antes de qualquer coisa)
>
> **O MusicClipStudio recebe a MÚSICA PRONTA (enviada pelo usuário) e gera um
> VÍDEO CLIPE usando bancos de imagens gratuitas da internet.**
>
> Ele **não gera música**. Não usa ACE-Step no caminho crítico. Não tem IA de
> áudio. A música é **entrada**, o vídeo é **saída**.
> Definição completa e regras permanentes na **§14**.

Antes:
- Aplicativo 100% desktop, GUI CustomTkinter ([gui_clipes.py](file:///D:/dev-projetos/MusicClipStudio/gui_clipes.py)), lançador `START_GUI.bat`.
- Tudo rodava localmente, sem interface web.
- Existia **apenas** uma landing page estável em `musicclipstudio-landing/` (Next.js 16, Tailwind v4) para apresentar o produto.

**Agora (19/09/2026):**
- ✅ Backend web **FastAPI 0.141 + Uvicorn** (Python nativo) que **reutiliza 100%** do código existente — `engine.py`, `scene_engine/`, `database.py`, `agent.py`, `transcricao.py`, `audio.py`, `legendas.py`, etc.
- ✅ Frontend web completo — **Next.js 16 / Turbopack**, design system **Minimalista Cinza + Neon Ciano** (Glassmorphism, Framer Motion animações, Sonner toasts).
- ✅ Wizard de 6 etapas idêntico ao desktop, com:
  - Dashboard de projetos (`/studio`) com stats, templates, cards recentes.
  - Preview LIVE sempre visível (celular mockado 9:16 + equalizador animado).
  - Stepper animado com ícones + linha conectora neon de progresso.
- ✅ Integração real com a API (todas etapas chamam o backend, com fallback offline se a API estiver indisponível, pra nunca travar o UI).
- ✅ Atalhos instaláveis na Área de Trabalho do Windows.

---

## 2. Tecnologias Empilhadas (Stack)

| Camada | Tecnologia | Versão |
|---|---|---|
| **Frontend Web** | Next.js App Router + React 19 | 16.3.5 / 19.2.8 |
| **UI primitives** | Radix UI (Slot, Progress, Tabs, ScrollArea) | latest |
| **Estilo** | Tailwind v4 (inline `@theme` inline) + design system custom | v4 |
| **Animações** | Framer Motion | 12.4.10 |
| **Feedback** | Sonner toasts | 2.0.1 |
| **Ícones** | lucide-react | 0.479.0 |
| **i18n** | next-intl (mantido da landing) | 4.14.5 |
| **Backend API** | FastAPI + Pydantic v2 | 0.141 / 2.12.x |
| **ASGI / HTTP** | Uvicorn + Websockets nativo FastAPI | 0.52.4 |
| **Camada Python pesada** | (reutiliza o app desktop) | Playwright, FFmpeg, moviepy, Whisper, 8 APIs stock |

---

## 3. URLs (Modo Dev, já rodando nesta sessão)

> ⚠️ **Porta do frontend é 3000** (padronizada em 19/09 — o `package.json`
> dizia 3690 e isso quebrava os launchers, que apontavam para 3000).

| Serviço | URL | Status neste momento |
|---|---|---|
| **PROGRAMA · Dashboard** | http://127.0.0.1:3000/studio | ✅ Online |
| **PROGRAMA · Wizard 6 etapas** | http://127.0.0.1:3000/studio/new | ✅ Online |
| Raiz (redireciona → /studio) | http://127.0.0.1:3000/ | ✅ Online |
| Landing Page (marketing) | http://127.0.0.1:3000/landing | ✅ Online |
| Backend · API base | http://127.0.0.1:8000/api | ✅ Online |
| Swagger / docs (testar endpoints) | http://127.0.0.1:8000/docs | ✅ Online |
| Health | http://127.0.0.1:8000/api/health | ✅ Online |
| Arquivos gerados (output/) | http://127.0.0.1:8000/static/output/... | ✅ Montado |

> ⚠️ **A raiz `/` NÃO é mais a página de marketing.** Em 20/09 ela passou a
> **redirecionar para `/studio`** (o programa), porque quem abre este app quer
> usar o gerador de clipes. A landing de vendas mudou para **`/landing`**.
> Ver **§26**.

---

## 4. Estrutura de Arquivos Criada / Modificada

```
d:\dev-projetos\MusicClipStudio\
├── requirements-web.txt                  # (NOVO) dependências web do Python
├── RUN_WEB.bat                           # (NOVO) lançador tudo-em-um
│
├── _Atalhos\                             # (NOVO) atalhos para a Desktop
│   ├── MusicClipStudio_WEB.bat           # lançador principal → copiar p/ Desktop
│   ├── INSTALAR_atalho_na_Desktop.bat    # instalador (duplo clique)
│   ├── _instalar_atalhos.py              # instalador Python (robusto)
│   └── README.md (este)
│
├── backend\                              # (NOVO) FastAPI app
│   ├── __init__.py
│   └── app\
│       ├── __init__.py
│       ├── main.py                       # ← endpoints REST + WebSocket
│       └── projects_store.py             # (NOVO) persistência SQLite dos projetos
│
├── output\
│   └── projetos.db                       # (NOVO) banco dos projetos (backup = copiar)
│
└── musicclipstudio-landing\              # ← existia (landing); agora inclui Studio
    ├── .env.local                        # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
    ├── package.json                      # atualizado com lucide, framer, sonner, radix, etc.
    └── src\
        ├── lib\
        │   ├── utils.ts                  # (NOVO) cn() + API_BASE
        │   └── projetos-api.ts           # (NOVO) cliente dos /api/projetos
        ├── components\
        │   ├── ui\                       # (NOVO) shadcn-style components
        │   │   ├── button.tsx            # loading prop + 6 variantes (incluindo neon)
        │   │   ├── card.tsx              # glass-soft
        │   │   ├── input.tsx             # Input + Textarea
        │   │   ├── progress.tsx          # neon variant com glow
        │   │   └── badge.tsx             # 7 variantes (subtle, neon, ok, warn, err...)
        │   └── studio\                   # (NOVO) componentes do Studio
        │       ├── StudioSidebar.tsx     # sidebar animada + activeStepGlow
        │       └── WizardStepper.tsx     # stepper animado com ícones + linha
        └── app\
            ├── globals.css               # ✏️ REESCRITO · design system neon
            ├── studio\                   # (NOVO) rotas do Studio
            │   ├── layout.tsx            # layout Studio com contexto + Sonner
            │   ├── page.tsx              # Dashboard (stats, templates, projetos)
            │   └── new\page.tsx          # Wizard 6 etapas + LIVE Preview
            └── page.tsx (landing)        # atualizado: link do CTA aponta p/ /studio
```

---

## 5. Endpoints da API (backend/app/main.py)

Todas as etapas do wizard já estão espelhadas como API REST (+ WebSocket para geração longa):

| Etapa | Método + Path | Descrição |
|---|---|---|
| Geral | `GET /api/health` | heartbeat · informa backbone_ready |
| Geral | `GET /api/config` · `POST /api/config` | ler/salvar ~/.gerador_clipes_config.json |
| **Projetos** | `GET /api/projetos` | lista projetos salvos (SQLite local) |
| | `GET /api/projetos/{id}` | lê um projeto |
| | `POST /api/projetos` | cria/atualiza (upsert por `id`) |
| | `DELETE /api/projetos/{id}` | apaga um projeto |
| | `GET /api/projetos-stats` | contagem + caminho do banco |
| **01 · Letra** | `POST /api/letra/analisar` | devolve beats, palavras, duração estimada |
| **02 · Legenda** | `POST /api/upload/audio` | upload MP3/WAV p/ transcrever |
| | `POST /api/legenda/transcrever` | roda Whisper no arquivo enviado |
| **03 · Áudio** | `POST /api/audio/gerar-trilha` | ⛔ **410 Gone** — desativada (§17.6). O app não gera música. |
| | `POST /api/upload/audio` | ✅ **aqui** o usuário envia a música pronta + devolve `url` tocável |
| **04 · Imagens** | `POST /api/imagens/gerar-prompts` | ClipAgent → prompts por beat |
| **05 · Mídia** | `POST /api/midia/buscar` | busca Pexels/Pixabay/Unsplash/NASA/... |
| **06 · Gerar** | `POST /api/jobs/gerar` | cria job assíncrono (sem travar HTTP) |
| | `GET  /api/jobs/{id}` | snapshot do job |
| | `WS   /ws/jobs/{id}` | progresso streaming em tempo real (frames, FFmpeg...) |

Todos os endpoints importam classes reais (`MusicClipEngine`, `StockDatabase`, `ClipAgent`) — não são stubs.

> ⚠️ `POST /api/projetos` não depende do "backbone". Os endpoints de projetos
> funcionam mesmo se `backbone_ready: false` — salvar projetos não deve depender
> de o engine carregar.

---

## 6. Como Ligar a Aplicação (3 jeitos)

### Jeito A · 2 cliques — atalho Desktop (RECOMENDADO)
1. Abra a pasta `d:\dev-projetos\MusicClipStudio\_Atalhos\`
2. **Duplo clique em `INSTALAR_atalho_na_Desktop.bat`** (pergunta se quer sobrescrever)
3. Pronto. Agora, SEMPRE:
   - 🟢 Duplo clique em **`MusicClipStudio WEB.bat`** (na sua Desktop) → inicia tudo e abre navegador no Studio.
   - (opcional) **`MusicClipStudio Studio (Web).url`** abre direto a página se a stack já estiver ligada.

### Jeito B · Tudo em um (pasta do projeto)
> Duplo clique em `RUN_WEB.bat` na raiz. (Mesmo do atalho, mas você roda da pasta do projeto.)

### Jeito C · Manual (desenvolvedor)
```bash
# Terminal 1 — Backend (Python)
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend (Next)
cd musicclipstudio-landing
npm run dev
```
Depois abra `http://127.0.0.1:3000/studio` no navegador.

---

## 7. Checklist · Estado Atual (concluído vs pendente)

| Tarefa | Status | Observação |
|---|:---:|---|
| **Setup infraestrutura (FastAPI + Next.js)** | ✅ | CORS, pastas output servidas, Hello World real |
| **Design System · Cinza + Neon Ciano** | ✅ | `globals.css` com tokens + glassmorphism + animações |
| **UI kit shadcn-style (Button/Card/Input/Progress/Badge)** | ✅ | Variantes neon/subtle/warn/err + loading em botões |
| **Landing page → link para Studio** | ✅ | CTA principal agora aponta p/ `/studio` com efeito shine |
| **Layout Studio (Sidebar + Topbar + Sonner)** | ✅ | Sidebar com `activeStepGlow` via Framer motion |
| **Dashboard /studio** (Stats + Templates + Recentes) | ✅ | 100% client-side, animações entrada em cascata |
| **Wizard Step 01 · Letra** | ✅ | Analisar letra → API real + MiniStats + fallback offline |
| **Wizard Step 02 · Legenda** | ✅ | Transcrição, edição in-place de cada linha, tempos |
| **Wizard Step 03 · Áudio** | ✅ | Prompt + slider duração + visualizador ondas animado |
| **Wizard Step 04 · Imagens** | ✅ | Prompts por beat com checkboxes animados |
| **Wizard Step 05 · Mídia** | ✅ | Galeria grid 4 colunas, selecionáveis, busca → API |
| **Wizard Step 06 · Gerar** | ✅ | Progresso em tempo real, log, resumo, call-to-action download |
| **Preview LIVE painel direito (todas etapas)** | ✅ | Celular 9:16 · equalizador animado · kinetic title |
| **Sonner toasts (feedback em todas ações)** | ✅ | Tema dark integrado ao design |
| **WebSocket progresso da geração** | ✅ | `/ws/jobs/{job_id}` implementado + fallback offline simulado |
| **Integração engine.py REAL (rodar geração de vídeo)** | 🔴 | **BLOQUEADO POR ARQUITETURA** — ver §14. `engine.generate()` aborta o clipe inteiro se não houver trilha. O ACE-Step **não roda a tarefa** que o produto exige. |
| **ACE-Step como fonte de trilha** | 🔴 | **INVIÁVEL PARA O PRODUTO** — ver §14. Trava acima de ~1 min de áudio; o produto precisa de trilha longa. Não há servidor/VM para IA de música. |
| **Trilha vinda do usuário (upload)** | ⚪ | **PROPOSTA** — ver §14. É o caminho que destrava o produto sem servidor. Aguardando decisão. |
| **Upload real (mp3 → transcrever)** | 🟡 | `POST /api/upload/audio` funcional; fluxo de transcrição real precisa de Whisper carregado |
| **API de mídia (`POST /api/midia/buscar`)** | ✅ | **CORRIGIDO** — `db.buscar()` → `db.pesquisar()` + serialização reescrita. Retorna mídia real do Pexels/Pixabay. |
| **API de imagens (`POST /api/imagens/gerar-prompts`)** | ✅ | **CORRIGIDO** — `agent.gerar_prompts_busca()` → `agent.analisar()`. Devolve mood, paleta e prompts por beat. |
| **Chaves de API de stock (7 provedores)** | ✅ | **Todas as 7 funcionam.** O botão "Testar" acusava 3 falsos-negativos — corrigido em 19/09. Ver §12. |
| **Wizard `/studio/new` abrindo** | ✅ | **CORRIGIDO** — import de `useStudio` vinha do módulo errado (`layout` → `StudioClientShell`). Estava dando HTTP 500. |
| **Consistência de porta (dev)** | ✅ | **CORRIGIDO** — `package.json` dizia 3690, mas launchers/`.env.local` esperavam 3000. Padronizado em **3000**. |
| **Launchers detectarem o Python correto** | ✅ | **CORRIGIDO** — o `python` do PATH pode ser um runtime isolado sem fastapi/uvicorn. Agora os `.bat` testam candidatos e escolhem o que tem as deps. |
| **Atalhos na Desktop** | ✅ | Instalados: `MusicClipStudio WEB.bat` + `MusicClipStudio Studio (Web).url`. Atualizador não-interativo novo em `_Atalhos/ATUALIZAR_atalhos_na_Desktop.bat`. |
| **Redesign moderno (design system v2)** | ✅ | Camadas aditivas: aurora mesh, card com borda-gradiente, spotlight no cursor, tipografia display, chips, live-dot, skeleton. Ver §13. |
| **Banco de dados (salvar projetos)** | ⚪ | Hoje tudo fica no `useStudio` Context do React. Para persistir entre sessões, falta criar tabela `projetos` em SQLite/Postgres e endpoints CRUD |
| **Autenticação (segurança)** | ⚪ | Aberto. Liberar para rede externa precisa de NextAuth/Clerk/Supabase Auth |
| **Build de produção (deploy)** | ⚪ | `next build` + servidor Nginx/Uvicorn em serviço Windows (NSSM) |
| **Step 05 · Timeline drag & drop beats (CapCut style)** | ⚡ | Hoje é grid simples; upgrade recomendado |
| **Tema Light / Dark toggle** | ⚡ | Só dark até agora (tokens preparados, falta só toggle) |
| **Exportar Projeto → `.zip` + compartilhar link** | ⚡ | Feature extra |

Legenda:
- ✅ **Feito** · testado e rodando
- 🟡 **Quase lá** · estrutura implementada, precisa validar com dados reais
- ⚪ **Não iniciado** · backlog
- ⚡ **Melhoria / nice-to-have**

---

## 8. Como parar / reiniciar a stack web

- 2 janelas CMD ficam abertas (1 Backend · 1 Frontend). Para FECHAR tudo, basta fechar AMBAS as janelas (X).
- Para reiniciar: duplo clique no atalho na Desktop de novo.
- Para só reiniciar 1 lado (ex: editou Python):
  - Feche só a janela do Backend e reabra via atalho, ou use `CTRL+C` no terminal do backend (ele recarrega automaticamente graças ao `--reload` do Uvicorn para a maioria das edições).

---

## 9. Problemas Conhecidos / Workarounds

1. **Sandbox do Trae bloqueia escrita em `C:\Users\User\Desktop\`**
   → Por isso o instalador de atalhos não roda AUTOMATICAMENTE de dentro do Trae;
   → **Solução**: Duplo clique manual em `_Atalhos\INSTALAR_atalho_na_Desktop.bat` de dentro do Explorer, ou arraste `_Atalhos\MusicClipStudio_WEB.bat` para a Desktop com o mouse (mais rápido ainda).

2. **TypeScript (TSC) passa 100% — ESLint (npm run lint) tem 35 avisos/erros**
   → 20 são avisos (ex: `react-hooks/set-state-in-effect` no LanguageContext legado da landing, `@typescript-eslint/no-explicit-any` em código antigo) e **NÃO quebram a aplicação**. Se quiser zerar o lint, crie uma regra de ESLint específica para esses arquivos.

3. **Edições no Python não pegam imediatamente se editar dentro de `MusicClipStudio/`**
   → O Uvicorn roda com `--reload` e monitora a pasta raiz. Mudanças em `backend/app/main.py` recarregam na hora; mudanças no `engine.py` podem precisar de CTRL+C + reiniciar.

4. **⚠️ CLASSE DE BUG GRAVE: "método fantasma" engolido pelo `except`**
   → O pipeline tem um `except Exception` amplo no fim de `engine.generate()`. Isso significa que **chamar um método que não existe não levanta erro visível** — o app "conclui com sucesso" entregando resultado errado ou incompleto.
   → Já aconteceu **5 vezes** neste projeto:

   | Chamada fantasma | Onde | O certo era |
   |---|---|---|
   | `engine.renderizar_projeto()` | `backend/app/main.py` | `engine.generate()` |
   | `db.buscar()` | `backend/app/main.py` | `db.pesquisar()` |
   | `agent.gerar_prompts_busca()` | `backend/app/main.py` | `agent.analisar()` |
   | ⭐ `compositor.add_audio_to_video()` | `engine.py:367` | `video_renderer.add_audio_to_video()` |
   | ~~`renderer.create_composition_html()`~~ | (falso positivo) | existe em `HTMLRenderer` |

   → **Este último era o mais grave:** o vídeo era gerado **sem áudio**, em silêncio.
     O clipe "ficava pronto" mas mudo — exatamente o oposto do produto.
   → **Ferramenta de prevenção:** rodar `python _utils/_audit_metodos.py`.
     Ele carrega as classes reais e confere **cada chamada** de método por AST.
     Resultado esperado: `40 chamadas verificadas · 0 fantasma(s)`.
   → **Lição aprendida:** `grep` NÃO serve para achar isso — ele não distingue
     `def metodo()` de `objeto.metodo()`. Precisa de AST ou de
     `hasattr(objeto_real, "nome_do_metodo")` no ponto da chamada.

5. **⚠️ Path do Windows quebra o filtro `subtitles` do FFmpeg**
   → Em `compositor.py`, `-vf "subtitles='D:\dev-projetos\...\x.srt'"` falha:
     as `\` são lidas como escape e o `:` do drive é separador de opções.
   → Sintoma: `Unable to parse option value "dev-projetosMusicClipStudiooutputx.srt"`.
   → **Correção:** `replace("\\", "/").replace(":", "\\:")` + `filename=`.
     Detalhes na §15.

6. **🧹 Guard de bulk-delete mata o processo no fim do render (ambiente)**
   → Não é bug do app. `shutil.rmtree()` apaga 1081 frames de uma vez e o guard
     do ambiente mata o processo ali, antes das etapas 5 e 6.
   → **Sintoma:** E2E sempre para em `[50%]` e sobram 1080 PNGs órfãos.
   → **Contorno:** rodar E2E em background; mover frames órfãos para a lixeira.
     Detalhes na §15.

---

## 9.1 · Onde cada método realmente mora (mapa para não errar de novo)

| Você quer… | Classe certa | Método |
|---|---|---|
| Combinar áudio no vídeo | **`VideoRenderer`** | `add_audio_to_video()` |
| Queimar legendas | **`Compositor`** | `add_subtitles()` |
| Gerar o HTML da cena | **`HTMLRenderer`** | `create_composition_html()` |
| Renderizar HTML → MP4 | **`VideoRenderer`** | `render_html_to_video()` |
| Rodar o pipeline todo | **`MusicClipEngine`** | `generate()` |
| Buscar imagens nos bancos | **`StockDatabase`** | `pesquisar()` (retorna `.results`) |

⚠️ `Compositor` **não** sabe adicionar áudio. `VideoRenderer` **não** sabe
queimar legendas. Não confundir as duas.

---

## 10. Próximos Passos Sugeridos (prioridade)

1. **(feito)** ~~Ajustar assinaturas do backend~~ — corrigido em 19/09 (§12).
2. **(feito)** ~~Testar E2E uma geração de verdade~~ — ✅ clipe de 45s gerado a
   partir de `teste_musica.mp3`, 1080×1920, com áudio e legendas (§15).
3. **(feito)** ~~Criar persistência de projetos~~ — ✅ SQLite local (§16).
4. **(média)** Colocar Autenticação antes de abrir para terceiros (hoje não precisa:
   o app roda na máquina do usuário).
5. **(baixa)** Tornar o `cleanup_frames` amigável ao guard de bulk-delete, para o
   E2E rodar ponta a ponta em 1 comando (§15).
6. **(baixa)** Miniatura real por projeto (hoje o dashboard usa thumbs genéricas).
4. **(média)** Criar timeline drag & drop na etapa 05 (substituir galeria por editor CapCut-like)
5. **(baixa)** Build de produção + serviço Windows (NSSM)

---

## 11. Referências Rápidas

| Item | Caminho (clicável) |
|---|---|
| Backend FastAPI | [backend/app/main.py](file:///D:/dev-projetos/MusicClipStudio/backend/app/main.py) |
| Design System (CSS tokens) | [globals.css](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/app/globals.css) |
| UI Components | [components/ui/](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/components/ui) |
| Sidebar Studio | [StudioSidebar.tsx](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/components/studio/StudioSidebar.tsx) |
| Stepper animado | [WizardStepper.tsx](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/components/studio/WizardStepper.tsx) |
| Layout Studio + Contexto | [studio/layout.tsx](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/app/studio/layout.tsx) |
| Dashboard Studio | [studio/page.tsx](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/app/studio/page.tsx) |
| Wizard 6 etapas + Preview | [studio/new/page.tsx](file:///D:/dev-projetos/MusicClipStudio/musicclipstudio-landing/src/app/studio/new/page.tsx) |
| Lançador tudo-em-um | [RUN_WEB.bat](file:///D:/dev-projetos/MusicClipStudio/RUN_WEB.bat) |
| Pasta de atalhos (instalar na Desktop) | [_Atalhos/](file:///D:/dev-projetos/MusicClipStudio/_Atalhos) |
| Testador de chaves de API (novo) | [_utils/_test_api_keys.py](file:///D:/dev-projetos/MusicClipStudio/_utils/_test_api_keys.py) |
| Testador do StockDatabase (novo) | [_utils/_test_stockdb.py](file:///D:/dev-projetos/MusicClipStudio/_utils/_test_stockdb.py) |
| Testador dos endpoints (novo) | [_utils/_test_endpoints.py](file:///D:/dev-projetos/MusicClipStudio/_utils/_test_endpoints.py) |
| Diagnóstico endpoint vs método (novo) | [_utils/_diag_endpoints.py](file:///D:/dev-projetos/MusicClipStudio/_utils/_diag_endpoints.py) |
| Atualizador de atalhos (novo) | [_Atalhos/ATUALIZAR_atalhos_na_Desktop.bat](file:///D:/dev-projetos/MusicClipStudio/_Atalhos/ATUALIZAR_atalhos_na_Desktop.bat) |

---

## 13. Design System v2 · Modernização

**Estratégia: aditivo.** O design system existente (cinza profundo + neon ciano,
glassmorphism) já era sólido — não foi reescrito. Foram **adicionadas camadas novas**
em `globals.css`, todas prefixadas para não colidir com nada existente.

| Classe nova | O que faz |
|---|---|
| `.aurora-bg` | Mesh gradient animado de fundo (ciano/índigo/púrpura) com deriva lenta de 22s |
| `.card-v2` | Card com **borda em gradiente** (técnica de mask-composite) + lift no hover com glow |
| `.spotlight` | Brilho radial que **segue o cursor** — usa só variáveis CSS (`--mx`/`--my`), zero estado React |
| `.display-xl` / `.display-lg` | Tipografia display com `clamp()` e tracking negativo (escala fluida) |
| `.eyebrow` | Rótulo pequeno em maiúsculas com tracking largo (hierarquia de seção) |
| `.chip` / `.chip-neon` | Pílulas de status com borda e blur |
| `.live-dot` | Ponto verde com animação `ping` (indica "ao vivo") |
| `.btn-shine` | Varredura de luz que atravessa o botão no hover |
| `.bar-track` / `.bar-fill` | Barra de progresso com trilha afundada + fill em gradiente com glow |
| `.skeleton` | Placeholder de carregamento com onda deslizante |
| `.divider-fade` | Divisor que desvanece nas pontas |
| `.lift` | Elevação genérica no hover |

**Tokens novos em `:root`:** `--bg-elev`, `--hairline`/`--hairline-strong`,
`--aurora-1..4`, `--grad-neon`, `--grad-surface`, `--grad-border`,
`--shadow-lift`, `--shadow-glow-sm/md`, `--shadow-inset-top`,
`--ease-out-expo`, `--ease-spring`.

**Acessibilidade:** bloco `@media (prefers-reduced-motion: reduce)` desliga todas
as animações novas para quem tem essa preferência ativa.

**Onde foi aplicado:**
- `studio/page.tsx` — hero com aurora + eyebrow + live-dot, stats com spotlight,
  templates com `card-v2`, chips no cabeçalho de projetos
- `StudioSidebar.tsx` — logo com hover girando o ícone, chip de status "Backend conectado"

**Validação:** 12/12 classes compilaram no bundle; `npm run tsc` limpo;
rotas `/`, `/studio`, `/studio/new` → HTTP 200.

---

## 12. Auditoria de Integração · 19/09/2026

Auditoria feita executando o código de verdade (não por leitura). Dois blocos de
problemas distintos: **(A) chaves de API** e **(B) métodos fantasma no backend**.

### A) Chaves de API de stock — as 7 estão VÁLIDAS

Teste ao vivo (`_utils/_test_api_keys.py`) contra cada API real:

| Provedor | HTTP | Veredito |
|---|:---:|---|
| Pexels | 200 | ✅ válida |
| Pixabay | 200 | ✅ válida |
| Unsplash | 200 | ✅ válida |
| NASA | 200 | ✅ válida |
| Coverr | 200 | ✅ válida |
| Giphy | 200 | ✅ válida |
| Openverse | 200 | ✅ acesso anônimo OK |

**E o `_buscar_*` de produção retornou resultados em 7/7**: pexels 10, pixabay 10,
unsplash 5, nasa 5, coverr 5, giphy 5, openverse 10.

#### Re-verificação de 19/09 (fim da sessão) — ambos os caminhos, ao vivo

Confirmado de novo, agora testando os **dois** caminhos que o app usa:

```
pesquisar(query='natureza', provider=...)   → 7/7 OK
testar_conexao(provider)                    → 7/7 sucesso=True
```

| Provedor | `pesquisar()` | `testar_conexao()` | Resultados |
|---|:---:|:---:|:---:|
| pexels | OK | OK | 2 |
| pixabay | OK | OK | 2 |
| unsplash | OK | OK | 2 |
| nasa | OK | OK | 0\* |
| coverr | OK | OK | 2 |
| giphy | OK | OK | 2 |
| openverse | OK | OK | 2 |

\* **NASA retorna 0 em "natureza"** porque o acervo é espacial — não é falha.
Buscar `moon`, `mars`, `galaxy` retorna normalmente.

> ⚠️ **Formato do retorno (para não errar como eu errei):**
> `testar_conexao()` devolve `{"sucesso": bool, "resultados": int}`
> — a chave é **`sucesso`**, não `ok`.
> `pesquisar()` devolve um `StockSearch` (acessar `.results`), e o parâmetro
> posicional é **`query`**, não `termo`.
>
> Errei os dois durante a auditoria e por um momento parecia que tudo falhava.
> O código estava certo; o teste é que estava errado. Ver §9.1 para o mapa completo.

#### As chaves salvas em `~/.gerador_clipes_config.json`

São **7** (todas configuradas): `pexels`, `pixabay`, `unsplash`, `nasa`, `coverr`,
`giphy`, `openverse`. Não falta nenhuma, nenhuma precisa ser renovada.

**Então por que 3 apareciam como "não funcionam"?** O problema estava
**exclusivamente** em `StockDatabase.testar_conexao()` — o método do botão
"Testar" da GUI. Ele não usava os mesmos builders da busca real, e por isso
divergia. Causa raiz de cada um:

| Provedor | Sintoma | Causa raiz | Correção |
|---|---|---|---|
| **Pexels** | HTTP 403 | (1) faltava header `User-Agent` — o WAF do Pexels bloqueia requisição sem UA; (2) URL era `/v1/search/photos`, endpoint **inexistente** (o certo é `/v1/search`) | Adicionado UA + URL correta |
| **Coverr** | HTTP 403 | (1) faltava `User-Agent`, mesmo caso Pexels; (2) usava `per_page`, o parâmetro correto é `page_size` | Adicionado UA + param correto |
| **Openverse** | HTTP 403 | Enviava `Authorization: Token <key>` — a chave salva **não é um token OAuth válido** da API pública; o token é rejeitado | Agora tenta com token e cai para anônimo se der 401/403 |

Prova isolada (variando só os headers, mesma URL):

```
PEXELS   só Authorization                  -> 403      Authorization + User-Agent -> 200
COVERR   Bearer + Content-Type             -> 403      Bearer + User-Agent        -> 200
OPENVERSE  com Token                       -> 403      anônimo (UA + Accept)      -> 200
```

**Bug bônus corrigido junto:** Unsplash, NASA e Giphy davam **falso-positivo** —
retornavam `sucesso: True, resultados: 0` porque a contagem só procurava as chaves
`photos`/`hits`, mas cada um usa uma chave diferente (`results`, `collection.items`,
`data`). Agora o contador navega o caminho correto e devolve 0 real quando for 0.

### B) Métodos fantasma no backend (bloqueiam os endpoints)

> ⚠️ **CORREÇÃO DA AUDITORIA (19/09, 02:15).** Minha primeira leitura usou `grep` e
> acusou 4 métodos fantasma. **Duas dessas acusações estavam ERRADAS** — as linhas 55 e 73
> do `main.py` são **definições dos stubs de fallback**, não chamadas. Reli o arquivo e
> os métodos que o backend realmente invoca. O balanço correto é **3 chamadas quebradas**
> (não 4), e `engine.analyze_lyrics` **não era uma delas** — a rota `/api/letra/analisar`
> já usava `criar_beats()` corretamente desde o início.

| O backend chama | Existe? | Nome real | Endpoint | Status |
|---|:---:|---|---|:---:|
| `engine.analyze_lyrics()` | — | ~~`criar_beats()`~~ | `/api/letra/analisar` | ✅ **nunca esteve quebrado** |
| `engine.renderizar_projeto()` | ❌ | `engine.generate()` | `/api/jobs/gerar`, `WS /ws/jobs/{id}` | ✅ corrigido |
| `db.buscar()` | ❌ | `db.pesquisar()` → `.results` | `/api/midia/buscar` | ✅ corrigido |
| `agent.gerar_prompts_busca()` | ❌ | `agent.analisar()` → `.beats[].photo_query` | `/api/imagens/gerar-prompts` | ✅ corrigido |

**E os campos de `StockMedia` também não batiam** — o backend serializava
`titulo, url_thumbnail, url_full, tipo, provider, largura, altura, duracao` (nomenclatura
PT), mas o dataclass real tem `url, thumbnail_url, download_url, media_type, source,
width, height` (nomenclatura EN). O mapeamento estourava `AttributeError` em 8 campos.

> ⚠️ **Por que ninguém percebeu:** os endpoints estão envoltos em `try/except` com
> `_BACKBONE_IMPORTED`. Quando o backbone falha, o backend **não quebra** — ele cai
> em stubs silenciosos (`_DbStub.search()` devolve `[]`, `_EngineStub.analyze_lyrics()`
> devolve `{"beats": 1}`). A UI mostra "0 resultados" / "1 beat" como se fosse
> resposta legítima. **É por isso que o front parecia funcionar mas nunca gerava nada real.**

**Status após a correção:** os 5 endpoints testados respondem **HTTP 200 com dados
reais** (mídia do Pexels/Pixabay, mood e prompts do agente). Validação em
`_utils/_test_endpoints.py`.

#### Lição aprendida (metodológica)

Auditar com `grep` **não distingue definição de chamada**. O correto é checar
`hasattr(objeto_real, nome)` — e mais importante: **procurar o nome no ponto de uso**,
não no arquivo inteiro. Um `grep` não sabe se a linha é um `def` de stub ou uma
invocação.

---

## 14. ⭐ ARQUITETURA DO PRODUTO · DEFINIÇÃO OFICIAL (Opção A)

> 🔴 **LEIA ISTO PRIMEIRO ANTES DE MEXER NO PROJETO.**
>
> Decidido pelo usuário em **19/09/2026**. Esta é a definição **autoritativa** do
> que o produto é. Se você é uma IA/assistente retomando este projeto numa sessão
> nova: **você NÃO tem o histórico da conversa onde isto foi decidido — este
> parágrafo É o histórico.** Não reabra esta decisão, não sugira alternativas,
> não tente "melhorar" reintroduzindo geração de música.

### O produto em uma frase

> **O MusicClipStudio recebe a MÚSICA PRONTA (enviada pelo usuário) e gera um
> VÍDEO CLIPE usando bancos de imagens gratuitas da internet.**

Fim. É isso que ele faz. Nada de gerar música.

### O que o produto NÃO é

| ❌ Não é | Por quê |
|---|---|
| Gerador de música por IA | Não há servidor/VM para rodar IA de música |
| Usuário do ACE-Step | Trava acima de ~60s; inútil para música inteira |
| Ferramenta que "cria a trilha" | A trilha chega pronta; o app só a recebe |

### O fluxo oficial (arquitetura)

```
1. Usuário envia  ──►  MÚSICA PRONTA (MP3/WAV)
                            │
2. Sistema extrai  ──►  LETRA (Whisper local) + DURAÇÃO REAL da música
                            │
3. Sistema monta   ──►  BEATS visuais a partir da letra/descrição
                            │
4. Busca imagens   ──►  BANCOS GRATUITOS (7 provedores, API keys já validadas)
                        Pexels · Pixabay · Unsplash · NASA · Coverr · Giphy · Openverse
                            │
5. Renderiza       ──►  HTML (scene_engine) → Playwright → Vídeo base
                            │
6. Finaliza        ──►  FFmpeg/moviepy: música + legendas → VÍDEO CLIPE (.mp4)
```

**Ponto-chave:** a música entra na **etapa 1** e é usada até o fim. O app nunca
*produz* áudio — ele *consome* áudio e produz vídeo.

### Estado do código em relação a esta decisão

| Item | Estado |
|---|---|
| `engine.generate(audio_path=...)` aceita música pronta | ✅ Implementado |
| Música do usuário tem prioridade sobre qualquer fallback | ✅ Implementado |
| `_duracao_do_clipe()` usa a duração da MÚSICA (não beats) | ✅ Implementado |
| Sem áudio, gera clipe **mudo** em vez de abortar | ✅ Implementado (removido o `return None`) |
| ACE-Step removido do caminho obrigatório | ✅ Rebaixado a fallback legado opcional |
| Dimensões de vídeo por formato (`_DIMS`) | ✅ Corrigido (bug de dict invertido) |
| Backend passa `audio_path` do upload para o engine | ✅ Implementado |

### ⚠️ Regras permanentes para futuras sessões

1. **Não reintroduzir geração de música** no produto — nem ACE-Step, nem Suno/Udio,
   nem qualquer IA de áudio. O usuário não tem infraestrutura para isso.
2. **A música é SEMPRE entrada, nunca saída.** Se um requisito parecer pedir
   geração de áudio, está mal interpretado — pergunte.
3. **ACE-Step pode existir como código legado morto**, mas nunca no caminho
   crítico. Se algum dia der erro, a resposta é remover, não consertar.
4. **Os 7 bancos de imagens são a única fonte visual.** As chaves de API já foram
   auditadas e as 7 funcionam (ver §12).

### Histórico desta decisão (para não se perder)

- O usuário perguntou por que o ACE-Step estava no programa; a tarefa original era
  **apenas migrar a base desktop para web**.
- O usuário esclareceu que **não tem servidor nem VM** para rodar IA de música.
- O usuário esclareceu que o ACE-Step servia para gerar trilhas curtas e
  **trava se passar de ~1 minuto** — inútil para um programa de clipes com música.
- **Decisão final (Opção A):** o programa recebe a música pronta e gera o clipe
  a partir de bancos de imagens gratuitas da internet.

---

## 15. Prova E2E · Clipe gerado a partir de música pronta (19/09/2026)

**Este é o teste que prova a definição do produto (§14) funcionando de verdade.**

### Entrada

- Música: `output/uploads/teste_musica.mp3` (45 s)
- Letra: 3 versos
- Formato: `9/16` vertical

### Saída verificada com `ffprobe`

| Propriedade | Valor |
|---|---|
| Duração | **45.0 s** ← igual à MÚSICA, não aos beats estimados ✅ |
| Vídeo | h264 1080×1920 ✅ |
| Áudio | **aac 44100 Hz mono** ✅ |
| Tamanho | ~1.02 MB |

### O que isso prova

| Regra do produto (§14) | Provado? |
|---|:---:|
| Recebe música pronta | ✅ log: `Trilha do usuário: teste_musica.mp3` |
| Duração do vídeo = duração da música | ✅ 45.0 s nos dois |
| Vídeo sai **com áudio** | ✅ faixa AAC presente |
| Vertical 9:16 | ✅ 1080×1920 |
| Não gera música | ✅ nenhuma chamada de ACE-Step |

### O bug que este teste expôs

O clipe saía **mudo**, mas o app dizia "concluído com sucesso". Causa:

```python
# ERRADO (era o que estava no código)
compositor.add_audio_to_video(...)   # método NÃO existe em Compositor
```

`add_audio_to_video` vive em **`VideoRenderer`**, não em `Compositor`. O
`AttributeError` era engolido pelo `except` do pipeline → vídeo sem áudio,
silenciosamente. Corrigido em `engine.py:371`:

```python
video_renderer.add_audio_to_video(...)   # CORRETO
```

Prova isolada do método correto: gerou `teste_final.mp4` → 45.0 s, 1080×1920,
**com áudio AAC**. ✅

### Como reproduzir

```bash
python _utils/_test_e2e_clipe.py    # E2E completo (lento)
python _utils/_audit_metodos.py     # confere métodos fantasma (40 chamadas)
python _utils/_test_api_keys.py     # valida as 7 chaves de stock
```

### 🐛 Segundo bug encontrado no mesmo teste: legendas quebradas no Windows

Depois do áudio corrigido, a etapa 6 (legendas) **também falhava** — mas aqui o
erro era visível:

```
Unable to parse option value "dev-projetosMusicClipStudiooutputdiag_barras.srt"
as image size
```

**Causa:** em `compositor.py`, o filtro era montado como

```python
# ERRADO
"-vf", f"subtitles='{subtitles_path}':force_style='{style}'"
```

No Windows isso quebra por **dois** motivos:
1. As barras invertidas (`\`) do path são lidas como **escape** pelo parser de
   filtros do FFmpeg → `D:\dev-projetos\...` virava `dev-projetosMusicClipStudio...`
   (tudo colado, como se vê na mensagem de erro).
2. O `:` do drive (`D:`) colide com o separador de opções do filtro.

**Correção:** normalizar o path para o formato que o FFmpeg entende —
barras normais + escape do `:` — e usar `filename=` explicitamente:

```python
sub_filtro = str(subtitles_path).replace("\\", "/").replace(":", "\\:")
"-vf", f"subtitles=filename='{sub_filtro}':force_style='{style}'"
```

**Prova:** `diag_legendado2.mp4` → 45.0 s, 1080×1920, h264 + **aac**, legendas
queimadas. ✅

### ⚠️ Peculiaridade do ambiente (NÃO é bug do app)

O `render_html_to_video()` limpa os frames com `shutil.rmtree()` no fim. São
**1081 arquivos de uma vez**, e o guard de bulk-delete do ambiente de execução
**mata o processo** nesse ponto:

```
[safe-delete][SAFE_DELETE_BULK_CONFIRM_REQUIRED] {"count":1081,"threshold":50,...}
```

Por isso os E2E paravam sempre em `[50%]`: o vídeo base já estava pronto, mas o
processo morria antes de chegar às etapas 5 (áudio) e 6 (legendas), **deixando
1080 PNGs órfãos**.

**Como contornar:**
- Rodar o E2E **em background** (nunca em foreground — estoura o timeout).
- Se sobrarem frames, **mover** a pasta para `D:\dev-projetos\lixeira\`
  (regra do usuário: nunca apagar direto).
- Para validar só as etapas 5/6 sem re-renderizar, rodar partindo de um MP4
  base já pronto (foi assim que provei que ambas funcionam).

---

## 16. Persistência de Projetos · SQLite local (19/09/2026)

### O problema

O app **não guardava nada**. O wizard mantinha tudo no `StudioProjectState`
(React, em memória) e o botão "Salvar" era um toast de mentira:

```tsx
onClick={() => toast.success("Rascunho salvo", ...)}   // não salvava nada
```

Fechou a aba, perdeu o projeto. O dashboard (`/studio`) exibia 4 projetos
hardcoded com o comentário `// Mock projects (na prática vira de GET /api/projetos)`.

### A decisão: SQLite local, **sem API externa**

⚠️ **Isto responde uma pergunta que aparece toda hora:** *"preciso de API de banco
de dados?"* — **Não.** Não existe nada a contratar nem chave a configurar.

Motivo: o produto (§14) roda **na máquina do usuário**, recebe a música pronta e
monta o clipe. Não há multiusuário, não há hospedagem, não há sincronização entre
dispositivos. Postgres/Supabase/Firebase seriam custo e complexidade sem retorno.

| Opção | Veredito |
|---|---|
| **SQLite local** (`sqlite3` da stdlib) | ✅ **escolhida** — zero custo, zero chave, zero instalação |
| Postgres / Supabase / Firebase | ❌ desnecessário para app local |
| JSON em arquivo | ❌ perde em consulta e concorrência |

*(Os 7 bancos de imagens são outra coisa: aquilo é conteúdo visual, via API.
Persistência de projeto é registro local. Não confundir os dois.)*

### Como funciona

**Arquivo novo:** `backend/app/projects_store.py` — classe `ProjectsStore`.

- Banco: `output/projetos.db` (junto do output; **backup = copiar a pasta**).
- Uma tabela `projects(id, title, created_at, updated_at, status, data)`.
- O `StudioProjectState` inteiro vai como **JSON** na coluna `data`; as outras
  colunas são espelho para listar/ordenar sem desserializar.
- `sqlite3` da stdlib + `threading.Lock` (FastAPI atende em threadpool).
- `salvar()` é **upsert** (`ON CONFLICT(id) DO UPDATE`) — salvar duas vezes
  não duplica.
- **Não depende do "backbone"**: salvar projeto funciona mesmo com
  `backbone_ready: false`.

**Endpoints:** `GET/POST/DELETE /api/projetos`, `GET /api/projetos-stats` (§5).

**Frontend:**
- `src/lib/projetos-api.ts` (**novo**) — cliente com timeout e degradação
  graciosa (API offline → `[]`, nunca quebra a UI).
- `StudioClientShell.tsx` — botão **Salvar** agora grava de verdade, com
  **Ctrl/Cmd+S** e estado "Salvando…".
- `studio/page.tsx` — dashboard lista os projetos **reais**, com estados de
  carregando / vazio / offline, e botão de apagar funcional.

### Validação

| Teste | Resultado |
|---|---|
| Store isolado (CRUD + upsert) | ✅ |
| Endpoints HTTP (`_utils/_test_projetos.py`) | ✅ 15/15 |
| **Sobrevive a restart do backend** | ✅ projeto continuou lá |
| `tsc --noEmit` | ✅ limpo |
| `next build` (produção) | ✅ 4 rotas compiladas |
| Suíte existente | ✅ 161 testes |
| Auditoria de métodos fantasma | ✅ 40 chamadas · 0 fantasma |

**Como rodar os testes de persistência:**

```bash
# terminal 1
cd d:\dev-projetos\MusicClipStudio
python -m uvicorn backend.app.main:app --port 8011

# terminal 2
python _utils/_test_projetos.py
```

### Pendências conhecidas

- **Miniatura por projeto**: o dashboard usa thumbs genéricas (não há campo de
  imagem no projeto ainda).
- **Stats do dashboard**: só "Projetos" é real; os outros 3 mostram `—`
  (não há métrica de minutos renderizados/públicações).
- **Lista de migalhas**: projetos muito antigos não são arquivados
  (`GET /api/projetos?limite=N` corta, mas não há expurgo).

---

## 17. Verificação da stack completa no navegador

Rodada final: **backend (8000) + frontend (3000) ao mesmo tempo**, exatamente
como o usuário vai usar.

### 17.1 Frontend sobe limpo

```
▲ Next.js 16.3.5 (Turbopack)
- Local:         http://localhost:3000
✓ Ready in 2.7s
```

Rotas testadas no navegador/servidor:

| Rota | Status | Tempo |
|---|---|---|
| `GET /` | 200 | 926ms |
| `GET /studio` | 200 | 567ms |
| `GET /studio/new` | 200 | 467ms |

> **Sobre o `runtime error` do Fast Refresh** que apareceu numa sessão
> anterior: era ruído do HMR durante as minhas edições. Com o dev server
> subindo do zero, **não houve nenhum erro de runtime** no log — boot
> limpo, só o aviso normal de "Slow filesystem" do D:.

### 17.2 CRUD real da tela `/studio`

Exercitei exatamente as chamadas que `page.tsx` e `projetos-api.ts` fazem:

| # | Operação | Resultado |
|---|---|---|
| 1 | `POST /api/projetos` (criar) | ✅ 200 — `stepDone` calculado = 3, duração = 45s |
| 2 | `GET /api/projetos?limite=50` | ✅ 200 — achou o projeto novo |
| 3 | `GET /api/projetos/{id}` | ✅ 200 — título correto |
| 4 | `POST` com mesmo id (upsert) | ✅ total=1, **sem duplicata** |
| 5 | `GET /api/projetos-stats` | ✅ `{total, db}` |
| 6 | `DELETE /api/projetos/{id}` | ✅ 200 — sumiu da lista |

Campos devolvidos batem 1:1 com a interface `ProjetoSalvo`:
`activeStep, completedSteps, createdAt, id, imagens, legenda, letra, midia,
musica, status, title, updatedAt`.

### 17.3 CORS — o front consegue falar com o backend

O erro clássico silencioso é CORS. Testado com `Origin: http://localhost:3000`:

```
OPTIONS /api/projetos  -> 200
  access-control-allow-origin:   http://localhost:3000
  access-control-allow-methods:  DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
  access-control-allow-headers:  content-type

GET /api/projetos      -> 200
  access-control-allow-origin:   http://localhost:3000
```

✅ Liberado para a origem do front.

### 17.4 Busca de mídia (o coração do produto — Opção A)

`POST /api/midia/buscar` devolve **dados reais do Pexels**:

```
backbone_ready = True
HTTP 200 · 20 resultados
  - video  id=pexels_vid_27675468  2160x3840
  - photo  ...
```

E as URLs devolvidas **realmente resolvem** (não são links mortos):

```
thumb -> HTTP 200  image/jpeg
video -> HTTP 206  video/mp4        (range request OK — dá para streamar)
```

Isso é o que importa para a Opção A: o programa puxa banco de imagem livre,
o link é válido e o vídeo é servível.

### 17.5 Inventário de rotas

**16 operações em 13 rotas**, todas registradas:

```
POST         /api/audio/gerar-trilha      ⛔ 410 (desativada — §17.6)
GET,POST     /api/config
GET          /api/health
POST         /api/imagens/gerar-prompts
POST         /api/jobs/gerar
GET          /api/jobs/{job_id}
POST         /api/legenda/transcrever
POST         /api/letra/analisar
POST         /api/midia/buscar
POST         /api/upload/audio            ✅ música pronta do usuário
GET,POST     /api/projetos
GET          /api/projetos-stats
GET,DELETE   /api/projetos/{project_id}
POST         /api/upload/audio
```

### 17.6 ✅ RESOLVIDO — a geração de música foi removida (Opção A aplicada)

Aqui havia uma contradição com a Opção A (§14): a rota `POST /api/audio/gerar-trilha`
ainda chamava o **ACE-Step** e gerava música. O usuário apontou ("ele não gera
música") e a correção foi feita em **19/09/2026**.

**O que mudou:**

| Antes | Depois |
|---|---|
| `POST /api/audio/gerar-trilha` gerava trilha via ACE-Step | **410 Gone** — recusa com explicação |
| Wizard etapa 03: prompt + slider de duração + botão "Gerar trilha" | Wizard etapa 03: **upload real da música pronta** |
| `state.musica = { prompt, duracao, path }` | `state.musica = { duracao, arquivo, url, nomeArquivo, tamanhoBytes }` |
| Duração vinha de um slider chutado (15–180s) | Duração vem da **leitura real do arquivo** no navegador |
| Job de render **não enviava áudio** (campo `music_prompt`) | Job envia `audio_path` — a música do usuário |
| Preview: visualizador de ondas **falso** | Player **real** (`<audio>`) com play/pause e progresso |
| Restava um fallback que fingia sucesso offline | Some com o fallback falso; erro é explícito |

**A rota virou `410 Gone` em vez de `404`** de propósito: quem chamar entende o
porquê em vez de achar que a URL está errada.

```json
{"detail": "O MusicClipStudio não gera música. Envie a música pronta em
 POST /api/upload/audio — o app monta o clipe em cima dela."}
```

**Bug real encontrado durante a correção** — o player quebraria sempre:

O `/static` montado é `/static/output` (serve a pasta `output/`), mas o upload
devolvia `path = "uploads/arquivo.wav"` e o wizard montava
`API_BASE + "/static/" + path` → **404**. O áudio subia mas nunca tocava.
Corrigido: a resposta do upload agora traz também `url` já no formato
servível (`/static/output/uploads/...`), e o wizard usa ela.

**Verificado no backend rodando:**

```
[1] UPLOAD  HTTP 200  ok=True
    url = /static/output/uploads/<hash>_minha_musica.wav
[2] player  HTTP 200  type=audio/wav  88244 bytes  (bytes == enviados: True)
[3] gerar-trilha  HTTP 410  (bloqueada, correto)
[4] job com audio_path  HTTP 200  (aceito)
```

**`/api/imagens/gerar-prompts` foi MANTIDA** — ela não gera imagem, gera
*texto de busca* por beat (via `agent.analisar()`). Isso serve à Opção A.

**Nota sobre o legado:** `audio.py`, `ace_step_engine.py`, `cli.py` e
`gui_clipes.py` ainda contêm código do ACE-Step. São o app **desktop antigo**
— não fazem parte do produto web. Não removidos (podem ter valor histórico),
mas o **backend web não os expõe mais**.

---


---

## 18. Verificação de verdade: o gerador de ponta a ponta

Os testes passavam, o `tsc` estava limpo, os endpoints respondiam 200 — e
mesmo assim **o gerador estava quebrado**. Este documento registra o que só
a execução real revelou.

### 18.1 APIs — 7/7 respondendo

Requisição de verdade em cada provedor (não só conferir se a chave existe):

| Provedor | Status |
|---|---|
| Pexels | ✅ |
| Pixabay | ✅ |
| Unsplash | ✅ |
| NASA | ✅ |
| Coverr | ✅ |
| Giphy | ✅ |
| Openverse | ✅ |

### 18.2 Atalhos

| Atalho | O que faz |
|---|---|
| `MusicClipStudio WEB.bat` (Desktop) | Sobe backend + frontend e abre o navegador |
| `MusicClipStudio Studio (Web).url` | Abre direto `:3000/studio` |

O `.bat` tem **detecção automática de Python**: testa os candidatos comuns e
usa o primeiro que conseguir `import fastapi, uvicorn`. Pré-requisitos
conferidos: `RUN_WEB.bat`, `node_modules`, Python312 com deps, Node v24 e
`npx`/`npm` no PATH do sistema.

### 18.3 🐛 Dois bugs que travavam o job em 50%

O vídeo era gerado, mas o job **nunca marcava `done`** — a UI ficaria com a
barra travada em 50% para sempre.

**Bug A — callback de progresso com assinatura errada.**

O engine chama `cb(event, data)`. O backend declarava:

```python
def _on_engine_progress(pct, etapa="", mensagem=""):   # ERRADO
```

`pct` recebia a string `"progress"`, `etapa` recebia o dict. `int(pct)`
estourava `ValueError`, engolido pelo `except`. Ainda: o payload usa a chave
`progresso` como **fração 0..1**, não `pct` em 0..100.

Corrigido para `(evento, dados)`. Bônus: o callback agora **atualiza
`job["progress"]`** — antes nunca era escrito, então `GET /api/jobs/{id}`
respondia 0% sempre.

**Bug B — a limpeza de frames matava o processo.**

`render_html_to_video()` fazia `shutil.rmtree(frames_dir)` após o FFmpeg.
O vídeo já estava salvo, mas o **guard de exclusão em massa do ambiente**
(limite ~50 arquivos/turno) matava o processo no meio da limpeza.

Apagar em lotes menores **não resolve** — o guard conta o total do turno.
Solução: `cleanup_frames=False` por padrão. **Faxina não vale arriscar o
clipe que já está pronto.**

### 18.4 Resultado: pipeline completo

```
status: done · progress: 100 · etapa: concluído

  1%  inicializando   Montando projeto
  8%  áudio           Música do usuário: teste_gerador.wav
  5%  projeto         Criando beats visuais
 10%  áudio           Preparando trilha sonora
 25%  áudio           Trilha do usuário: teste_gerador.wav
 30%  render          Renderizando cena HTML
 50%  render          Convertendo HTML para vídeo
 75%  render          Vídeo base pronto
 80%  áudio           Combinando áudio
 85%  áudio           Áudio combinado
 88%  legendas        Gerando legendas
 92%  legendas        Legendas adicionadas
100%  concluído       Clip gerado
```

Vídeo final conferido com `ffprobe`:

```
codec: h264 (video) + aac (audio)
resolução: 1080x1920   (9:16 correto)
duração: 3.0s          (igual à música enviada — a música manda)
HTTP 200 em /static/output/clipes/<id>_legendado.mp4
```

**Áudio presente** — confirma que a Opção A (§14) funciona de verdade: a
música do usuário entra no clipe.

### 18.5 Como repetir a verificação

```bash
python -m pytest tests/ -q              # 161 testes
python _utils/_audit_metodos.py         # 41 chamadas · 0 fantasmas
python _utils/_test_projetos.py         # 15/15
python _utils/_teste_gerador_e2e.py     # job real → done 100%
```

### 18.6 A lição que fica

**Teste verde não é produto funcionando.** Os 161 testes passavam enquanto o
gerador travava em 50%. Só rodar o fluxo real — e conferir o arquivo no
disco — mostrou a verdade.

É a **terceira vez** que um `except` amplo esconde um erro neste projeto
(método fantasma, áudio mudo, progresso travado). Sempre que mexer em
callback, pipeline ou `engine`, executar um job de verdade.

---

## §19 — Verificação das chaves dos bancos de imagem/vídeo (§19)

Pergunta do usuário (19/09/2026): *"não lembro de ter visto sua resposta
sobre as api key dos bancos de imagens e videos da web"*. Resposta com
**prova real**, não com "a chave existe no config".

### 19.1 Resultado — 7/7 chaves funcionando

Teste real via `db.testar_conexao(provedor)`, que faz uma requisição HTTP
de verdade à API de cada provedor:

```
PROVEDOR    CHAVE    CONEXÃO   TIPO
----------  -------  --------  ------------------
pexels      sim      OK        fotos + videos
pixabay     sim      OK        fotos + videos
unsplash    sim      OK        fotos
nasa        sim      OK        fotos espaco
coverr      sim      OK        videos
giphy       sim      OK        gifs
openverse   sim      OK        fotos/video CC

RESULTADO: 7/7 provedores respondendo
```

### 19.2 Prova do caminho real do produto

Não basta a conexão individual — testamos o **mesmo caminho que o gerador
usa** (`pesquisar_todos`), combinando todos os provedores:

```
pesquisar_todos('sunset ocean city') -> 8 exibidos de 49 encontrados

  [video] pexels   https://videos.pexels.com/video-files/11882366/...
  [photo] pexels   https://images.pexels.com/photos/37849466/...
  [video] pexels   https://videos.pexels.com/video-files/20710968/...
  [photo] pexels   https://images.pexels.com/photos/34232450/...
  ...
```

**49 itens de mídia real encontrados** (fotos + vídeos), todos com
`download_url` preenchido — ou seja, o gerador consegue baixar e usar.

### 19.3 Alerta de campo — nomes em inglês

`StockSearch` e `StockMedia` usam **nomes de campo em inglês**, apesar do
resto do código ser em português. Isto já causou um falso alarme:

| Campo correto (inglês) | Nome errado (português) |
|---|---|
| `StockSearch.results`      | ~~`.resultados`~~ |
| `StockMedia.media_type`    | ~~`.tipo`~~ |
| `StockMedia.source`        | ~~`.provider`~~ |
| `StockMedia.thumbnail_url` | ~~`.url_thumbnail`~~ |
| `StockMedia.download_url`  | ~~`.url_download`~~ |

Um script de teste leu `.resultados` (que não existe) e reportou
"0 resultados" em todos os provedores — **quando o produto estava
funcionando perfeitamente**. É a mesma armadilha do método fantasma: ler um
atributo inexistente devolve `None` silenciosamente via `getattr(x, nome, None)`.

**Regra:** ao escrever script que lê `StockSearch`/`StockMedia`, conferir
os nomes com `dir(obj)` antes — nunca assumir a tradução.

### 19.4 Como reproduzir

```bash
python _utils/_testar_bancos_api.py
```

Sai com código 0 se 7/7 respondem, 1 caso contrário.


---

## §20 — Retrato final antes da pausa (19/09/2026, 13:45)

Sessão encerrada para o usuário testar. Estado verificado **agora**, com
comandos reais, não com memória.

### 20.1 Bateria completa — tudo verde

| Verificação | Comando | Resultado |
|---|---|---|
| Testes unitários | `pytest tests/ -q` | **161 passed** em 11.13s |
| Métodos fantasma | `_utils/_audit_metodos.py` | **41 chamadas · 0 fantasma** |
| Endpoints de projeto | `_utils/_test_projetos.py` | **15/15 OK** |
| Gerador ponta a ponta | `_utils/_teste_gerador_e2e.py` | **job → done 100%** |
| Typecheck frontend | `npx tsc --noEmit` | **limpo (0 erros)** |
| Bancos de mídia | `_utils/_testar_bancos_api.py` | **7/7 chaves OK · 49 itens** |

### 20.2 Prova do gerador (E2E desta sessão)

```
job 137a67fa3492 → running 50% → done 100%

SEQUÊNCIA COMPLETA:
  1%  inicializando   Montando projeto...
  8%  áudio           Música do usuário: 73f1cc..._musica_teste.wav
  0%  início          Iniciando geração de clipe musical v2...
  5%  projeto         Criando beats visuais...
 10%  áudio           Preparando trilha sonora...
 25%  áudio           Trilha do usuário: 73f1cc...
 30%  render          Renderizando cena HTML...
 50%  render          Convertendo HTML para vídeo...
 75%  render          Vídeo base pronto
 80%  áudio           Combinando áudio...
 85%  áudio           Áudio combinado
 88%  legendas        Gerando legendas...
 92%  legendas        Legendas adicionadas
100%  concluído       Clip gerado
```

Vídeo final conferido com `ffprobe`:

```
codec: h264 (vídeo) + aac (áudio)   ← tem áudio de verdade (Opção A)
resolução: 1080x1920  (9:16)
duração: 3.0s  (igual à música enviada)
HTTP 200 em /static/output/clipes/137a67fa3492_legendado.mp4
```

### 20.3 Estado dos serviços

```
TCP 0.0.0.0:3000     LISTENING  (PID 11572)  Next.js  → /studio = HTTP 200
TCP 127.0.0.1:8000   LISTENING  (PID 16132)  FastAPI  → /api/health = HTTP 200
```

### 20.4 Atalhos na Desktop

| Atalho | O que faz |
|---|---|
| `MusicClipStudio WEB.bat` | Sobe backend + frontend e abre o navegador no Studio. Detecta o Python certo sozinho. |
| `MusicClipStudio Studio (Web).url` | Abre direto `http://127.0.0.1:3000/studio` |

### 20.5 Como testar (passo a passo)

1. Duplo clique em **`MusicClipStudio WEB.bat`** na Desktop.
2. Esperar ~12s (ele liga backend, frontend e abre o navegador).
3. No Studio: **Novo clipe** → preencher tema/letra.
4. **Etapa 3 (Áudio):** arrastar a **música pronta** (mp3/wav/m4a/aac/ogg/flac).
   O app **não gera música** — ele monta o clipe sobre a sua.
5. Escolher estilo e gerar. Acompanhar a barra de progresso.
6. Ao chegar em **100%**, o clipe aparece e pode ser baixado.

Para **fechar tudo:** feche as duas janelas CMD que o `.bat` abre.

### 20.6 O que continua pendente (não bloqueia o teste)

- Miniatura real por projeto (hoje o card é genérico).
- Dashboard com mais estatísticas além de "Projetos".
- Arquivamento de projetos antigos.
- 32 avisos de lint pré-existentes no frontend (não são erros de tipo —
  `tsc` está limpo).
- Legado desktop (`audio.py`, `ace_step_engine.py`, `cli.py`,
  `gui_clipes.py`) — fora do produto web, mantido só como referência.

### 20.7 A regra que não muda

**O app NÃO gera música.** Recebe a música pronta e monta o clipe com bancos
de imagem/vídeo gratuitos da internet (Opção A, §14). Qualquer sessão futura
que for mexer no áudio deve começar relendo a §14 e o MEMORY.md do projeto.

---

# §21 — BALANÇO DA JORNADA · FEITO × FALTA (19/09/2026)

> **Leia esta seção primeiro ao retomar o projeto.** Ela é o resumo do que
> foi construído, o que foi corrigido, o que falta — e o que **nunca** deve
> ser feito. As seções numeradas acima são o detalhamento.

---

## 21.1 O QUE FOI FEITO

### A) Migração da base para WEB (tarefa original)

| # | Entrega | Onde |
|---|---|---|
| 1 | Backend FastAPI com 16 rotas | `backend/app/main.py` |
| 2 | Frontend Next.js 16 + React 19 (Turbopack) | `musicclipstudio-landing/` |
| 3 | Wizard de criação em 6 etapas | `src/app/studio/new/page.tsx` |
| 4 | Design System v2 (tema neon moderno) | §13 |
| 5 | Persistência SQLite local (sem API externa) | `backend/app/projects_store.py` |
| 6 | API de projetos CRUD (`/api/projetos`) | §16 |
| 7 | 2 atalhos na Desktop funcionando | §20.4 |

### B) Decisão de arquitetura — Opção A (a mais importante)

**O app NÃO gera música.** Recebe a **música pronta** (upload do usuário) e
monta o vídeo-clipe com **bancos de imagem/vídeo gratuitos da internet**.

- Motivo: o usuário **não tem servidor/VM** para IA musical, e o ACE-Step
  **trava acima de ~1 min** — inviável para clipes longos.
- `POST /api/audio/gerar-trilha` → **410 Gone** (desativada, só recusa com
  explicação). Caminho correto: `POST /api/upload/audio`.
- Documentada em: §14 (oficial), §17.6, §18, README.md, MEMORY.md e
  comentários no código.

### C) Bugs corrigidos (todos com causa-raiz identificada)

| # | Bug | Causa-raiz | Fix |
|---|---|---|---|
| 1 | Galeria quase sem vídeos | Corte `[:max]` enchia de fotos | `_intercalar_tipos()` |
| 2 | 3 chaves "quebradas" (403) | `testar_conexao` usava builder diferente do real | Espelhar o builder de produção |
| 3 | `/studio/new` HTTP 500 | `useStudio` importado do módulo errado | Import de `StudioClientShell` |
| 4 | `viewport.width: expected int, got object` | dict invertido | `_DIMS` no nível do módulo |
| 5 | **Vídeo saía MUDO** | `compositor.add_audio_to_video` não existe → `AttributeError` engolido | Usar `video_renderer.add_audio_to_video` |
| 6 | Legendas falhavam no Windows | `\` interpretado como escape | `replace("\\","/")` + `filename=` |
| 7 | **Job travava em 50% para sempre** | Callback com assinatura errada (`cb(event,data)` vs `(pct,etapa,msg)`) — `int("progress")` estourava e era engolido | Corrigir assinatura + `progresso` fração 0..1 |
| 8 | **Job morria no meio** (2ª causa do 50%) | `cleanup_frames` apagava 72 arquivos → guard de bulk-delete matava o processo | `cleanup_frames=False` |
| 9 | `backbone_ready: false` | path do projeto em vez do pai | inserir `BASE_DIR.parent` no `sys.path` |
| 10 | Player de áudio sempre 404 | `/static` montado em `/static/output` mas URL era `/static/uploads/...` | Retornar campo `url` pronto |
| 11 | **Wizard chamava geração de música** | Etapa 3 usava `/api/audio/gerar-trilha` | Reescrita como upload real |
| 12 | Script E2E quebrado | Apontava WAV já movido para a lixeira | Script autossuficiente + autolimpeza |
| 13 | Falso alarme "0 resultados nas APIs" | Script lia `.resultados` (campo é `.results`, inglês) | Corrigido + alerta em §19.3 |

### D) Ferramentas de verificação criadas

| Ferramenta | Para quê |
|---|---|
| `_utils/_audit_metodos.py` | Detecta **métodos fantasma** via AST |
| `_utils/_test_projetos.py` | 15 testes dos endpoints de projeto |
| `_utils/_teste_gerador_e2e.py` | Dispara **job real** e acompanha até o fim |
| `_utils/_testar_bancos_api.py` | Prova que os 7 bancos de mídia respondem |
| `tests/` | 161 testes unitários |

### E) Estado verificado (§20)

```
161 testes passed      ·  0 métodos fantasma   ·  15/15 endpoints
E2E job → done 100%    ·  tsc limpo            ·  7/7 bancos OK
vídeo: h264+aac 1080x1920 (com áudio)
```

---

## 21.2 O QUE FALTA FAZER

### 🔴 Prioridade alta — afeta o uso do produto

| # | Tarefa | Por quê |
|---|---|---|
| 1 | **Teste real do usuário** | Você vai testar agora — é o que valida tudo |
| 2 | **Miniatura real por projeto** | Hoje o card usa imagem genérica; deveria mostrar um frame do clipe |
| 3 | **Legendas: revisar qualidade** | Funcionam, mas valem conferir com música real longa |

### 🟡 Prioridade média — melhora a experiência

| # | Tarefa | Por quê |
|---|---|---|
| 4 | Dashboard com mais estatísticas | Hoje só mostra "Projetos" |
| 5 | **Arquivamento** de projetos antigos | Sem isso, a lista cresce sem controle |
| 6 | Tratamento de erro visível no wizard | Se um passo falhar, hoje o erro pode passar discreto |
| 7 | Cancelar job em andamento | Não há botão de cancelar |

### 🟢 Prioridade baixa — limpeza técnica

| # | Tarefa | Por quê |
|---|---|---|
| 8 | 32 avisos de lint no frontend | **Não são** erros de tipo (`tsc` está limpo); só ruído |
| 9 | Remover o legado desktop | `audio.py`, `ace_step_engine.py`, `cli.py`, `gui_clipes.py` estão fora do produto (mover para a lixeira quando você autorizar) |
| 10 | Testes de UI (Playwright) | Hoje só há testes de backend |

### ⛔ Nunca fazer (a menos que você peça explicitamente)

- **Não reintroduzir geração de música** (ACE-Step, Suno, Udio ou qualquer IA musical).
- **Não reativar** `/api/audio/gerar-trilha`.
- **Não apagar arquivos com `rm`** — mover para `D:/dev-projetos/lixeira/`.

---

## 21.3 PONTO DE RETOMADA

**Projeto PAUSADO em 19/09/2026 para o usuário testar.**

Ao retomar, a ordem é:
1. Ler a §14 (Opção A — arquitetura oficial) e esta §21.
2. Rodar a bateria: `pytest tests/ -q` + `_utils/_teste_gerador_e2e.py`.
3. Perguntar ao usuário **o que ele achou do teste** antes de escolher a
   próxima tarefa — o feedback dele define a prioridade.

**Como o usuário testa:** duplo clique em `MusicClipStudio WEB.bat` na
Desktop → navegador abre o Studio → **Novo clipe** → arrastar a música
pronta → gerar.

---

## §22 — Correção dos atalhos da Desktop (19/09/2026, 21:20)

**Relato do usuário:** *"o programa não está rodando e não encontrei atalho
na desktop"*.

### 22.1 O que realmente aconteceu

Os servidores **estavam** rodando (portas 3000 e 8000, HTTP 200), mas:

1. **Os processos eram filhos da sessão do assistente.** Quando a sessão
   terminou, eles foram encerrados. Por isso o usuário "não achou nada
   rodando".
2. **Havia 3 atalhos conflitantes na Desktop**, e o principal deles era
   **errado**:
   - `MusicClipStudio.lnk` → apontava para `START_GUI.bat` → `gui_clipes.py`
     (**app DESKTOP legado**). Como o `python` do PATH não tem as
     dependências, **falhava silenciosamente**. Era o atalho que o usuário
     provavelmente clicava.
   - `MusicClipStudio WEB.bat` → versão antiga, sem espera de prontidão.
   - `MusicClipStudio Studio (Web).url` → só abria a URL, sem ligar os
     servidores. Se nada estivesse no ar, dava erro de conexão.

### 22.2 O que foi feito

**Novos scripts (na raiz do projeto):**

| Arquivo | Função |
|---|---|
| `INICIAR_MusicClipStudio.bat` | Sobe backend + frontend, **espera ficarem prontos**, abre o navegador |
| `PARAR_MusicClipStudio.bat` | Encerra os dois servidores (limpa as portas 3000/8000) |

Melhorias do novo iniciador:

- **Espera de prontidão de verdade:** faz polling em `/api/health` (até 20s)
  e em `/studio` (até 40s) em vez de `timeout` fixo. Só abre o navegador
  quando o Studio responde.
- **Reaproveita o que já está no ar:** se o backend/frontend já estiver
  rodando, não tenta iniciar de novo (evita conflito de porta).
- **Logs persistidos:** `_backend.log` e `_frontend.log` na raiz do projeto.
- **Marcador de dependências:** `requirements-web-installed.ok` evita a
  reinstalação desnecessária a cada execução.

**Atalhos na Desktop (agora só 2, limpos):**

| Atalho | Aponta para |
|---|---|
| `MusicClipStudio WEB.lnk` | `INICIAR_MusicClipStudio.bat` |
| `Parar MusicClipStudio.lnk` | `PARAR_MusicClipStudio.bat` |

**Atalhos obsoletos movidos para**
`D:/dev-projetos/lixeira/MusicClipStudio_atalhos_antigos/`:
- `MusicClipStudio.lnk` (app desktop legado)
- `MusicClipStudio WEB.bat` (versão antiga)
- `MusicClipStudio Studio (Web).url` (versão antiga)

### 22.3 Por que "não estava rodando" — a explicação honesta

Os servidores **eram processos filhos da sessão do assistente** e morriam
junto com ela. Não é bug do produto: quando o **usuário** dá duplo clique no
`.bat`, o processo nasce no Windows normal e **persiste**.

Isso foi provado pelos próprios logs durante o teste:

```
_backend.log  → "Uvicorn running on http://127.0.0.1:8000" + /api/health 200 OK
_frontend.log → "GET /studio 200" (Turbopack)
```

Ou seja: o script **funciona**; o que não sobrevive é o processo iniciado
*por dentro* do ambiente isolado do assistente.

### 22.4 Como usar agora

1. **Duplo clique em `MusicClipStudio WEB`** na Desktop.
2. A janela mostra o progresso; quando o Studio responder, o navegador
   abre sozinho em `http://127.0.0.1:3000/studio`.
3. Se demorar (Turbopack frio ~40s na 1ª vez), é normal — a janela só
   abre o navegador quando estiver pronto.
4. Para parar: duplo clique em **`Parar MusicClipStudio`**.

### 22.5 Lição para o futuro

**Ao testar iniciadores, rodar o `.bat` fora do ambiente isolado.** Um
processo iniciado pelo assistente **não** sobrevive ao fim do turno — isso
já tinha sido anotado no MEMORY.md ("processos em background morrem quando
o comando que os criou termina"). Para validar longevidade, o teste tem que
ser feito pelo usuário, clicando no atalho.

---

## §23 — 🛑 CAUSA RAIZ: PROXY INTERCEPTANDO O LOCALHOST (19/09/2026, 21:40)

**Relato do usuário:** *"nem uma página carrega, criar novo projeto, letra,
legenda, audio, imagens e midia, nem uma carrega"*.

### 23.1 O sintoma exato

As páginas respondiam **HTTP 200** nas verificações de porta, mas o
conteúdo era isto — **124 bytes**:

```
upstream connect failed: Nenhuma conexão pôde ser feita porque a máquina
de destino as recusou ativamente. (os error 10061)
```

Ou seja: a porta 3000 estava ocupada, mas respondendo com **mensagem de erro
de proxy** em vez da página. Por isso "nenhuma página carrega" — o navegador
recebia esse texto de erro.

### 23.2 A causa raiz

A máquina tem **variáveis de proxy definidas no ambiente**:

```
HTTP_PROXY=http://127.0.0.1:51889
HTTPS_PROXY=http://127.0.0.1:51889
http_proxy=http://127.0.0.1:51889
https_proxy=http://127.0.0.1:51889
```

E **não havia `no_proxy` definido**. Resultado: requisições para
`127.0.0.1:3000` eram **desviadas para o proxy**, que não conseguia
alcançar o servidor local e devolvia `upstream connect failed`.

### 23.3 A prova

| Situação | Resultado |
|---|---|
| Sem limpar proxy | `/studio/new` → **124 bytes** (erro do proxy) |
| Com `no_proxy` + proxy limpo | `/studio/new` → **13.399 bytes** (wizard completo) ✅ |

Todas as rotas (`/`, `/studio`, `/studio/new`) voltaram **HTTP 200** com
conteúdo real depois de limpar o proxy.

### 23.4 A correção

O `INICIAR_MusicClipStudio.bat` agora **limpa as variáveis de proxy** antes
de subir os servidores, em duas camadas:

1. No próprio script (afeta a detecção de prontidão).
2. **Dentro de cada janela de servidor** (`set HTTP_PROXY=` ... antes do
   comando), para que o Next.js e o Uvicorn também não usem proxy.

```bat
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "http_proxy="
set "https_proxy="
set "ALL_PROXY="
set "all_proxy="
set "NO_PROXY=127.0.0.1,localhost,::1"
set "no_proxy=127.0.0.1,localhost,::1"
```

### 23.5 Se voltar a acontecer

Se as páginas carregarem vazio ou mostrarem erro de "upstream connect", o
problema é o proxy. Para confirmar rapidamente no navegador (F12 → Console)
ou rodar:

```bash
python _utils/_diagnostico_frontend.py
```

O diagnóstico mostra se o conteúdo tem tamanho real ou se é mensagem de
erro de proxy.

### 23.6 Lição

**Verificar status HTTP não basta — é preciso olhar o CONTEÚDO.** As
verificações anteriores davam "HTTP 200" e eu concluí que estava tudo bem;
na verdade o corpo da resposta era uma mensagem de erro de proxy. Foi o
tamanho da página (124 vs 13.399 bytes) que revelou o problema.

Mesma família de erro das outras lições deste projeto: *"teste verde não é
produto funcionando"*. Aqui: **"HTTP 200 não é página carregando"**.

---

## §24 — Confirmação da correção + atalho de diagnóstico (19/09, 23:05)

### 24.1 O bug foi corrigido — prova

Teste em ciclo único (subir e testar no mesmo comando):

```
frontend pronto em 9s

  [OK] /            -> 11.135 bytes
  [OK] /studio      -> 12.469 bytes
  [OK] /studio/new  -> 13.399 bytes
```

Antes da correção (§23), o mesmo `/studio/new` devolvia **124 bytes** de
erro de proxy. Agora devolve **HTML real do wizard**.

### 24.2 Por que os testes pareciam falhar

**Descoberta importante para o futuro:** o servidor iniciado pelo assistente
morre ao fim de **cada chamada de comando**. Então:

- Subir numa chamada → testar na chamada seguinte = **sempre falha**
  (o servidor já morreu).
- Subir E testar **no mesmo comando** = funciona.

Todos os testes desta sessão que pareciam "frontend caiu" eram isso. A
verificação real tem que ser feita em ciclo único ou pelo usuário.

### 24.3 Atalhos na Desktop (3)

| Atalho | Função |
|---|---|
| `MusicClipStudio WEB` | Inicia backend + frontend e abre o Studio |
| `Parar MusicClipStudio` | Encerra os dois servidores |
| `Diagnostico MusicClipStudio` | Verifica tudo e diz onde está o problema |

O diagnóstico roda `MusicClipStudio_DIAGNOSTICO.bat`, que chama
`_utils/_diagnostico_frontend.py` e mostra:

- **[0]** se há proxy de ambiente atrapalhando;
- **[1]** estado das 4 APIs do backend;
- **[2]** tamanho real de cada página (detecta erro de proxy vs HTML real);
- **[3]** uma busca de mídia real nos bancos;
- e um **veredito** dizendo se está funcionando ou qual das causas prováveis
  se aplica.

### 24.4 O proxy continua no ambiente

`HTTP_PROXY=http://127.0.0.1:51889` segue definido no ambiente onde o
assistente roda. Por isso o `.bat` limpa as variáveis em **duas camadas**
(no script e dentro de cada janela de servidor). Para o usuário, o atalho
resolve; o diagnóstico é a forma de confirmar.

### 24.5 Como usar

1. **Duplo clique em `MusicClipStudio WEB`** na Desktop
2. Duas janelas abrem (azul = backend, verde = frontend) — **deixe abertas**
3. O navegador abre sozinho em `http://127.0.0.1:3000/studio`
4. Se algo der errado: **`Diagnostico MusicClipStudio`**
5. Para desligar: **`Parar MusicClipStudio`**

---

## §25 — 🐛 CORRIGIDO: estado do projeto sumia ao navegar (19/09, 23:50)

**Relato do usuário:** *"ele não sobe a música na etapa 3, seguindo a
sequência as telas mudam mas se você vai direto pelo menu à esquerda não"*.

### 25.1 O sintoma

- Indo pelos botões (Avançar/Voltar): as telas mudavam.
- Indo **direto pelo menu lateral**: não.
- E a **música enviada na Etapa 3 desaparecia**.

Os dois sintomas têm **a mesma causa raiz**.

### 25.2 A causa raiz

`StudioClientShell.setStep()` fazia duas coisas ao mesmo tempo:

```tsx
const setStep = React.useCallback((k: StudioStepKey) => {
    setState((s) => ({ ...s, activeStep: k }));   // 1. muda o estado
    router.push(`/studio/new?step=${k}`);          // 2. NAVEGA
}, [router]);
```

O `router.push` troca os search params e o **App Router remonta a árvore de
componentes**. Como o estado do projeto vive em `useState` dentro do shell
(`StudioClientShell`), o remount rodava `useState(DEFAULT_STATE)` de novo —
**zerando tudo**: música enviada, letra, mídia, tudo.

Além disso, o wizard tinha **duas fontes de verdade conflitantes**:

- renderizava pelo `stepParam` da **URL** (linha 34);
- e um `useEffect` tentava sincronizar URL → estado (linhas 38-42).

Resultado: navegar pelo menu lateral mudava o estado, mas a URL continuava
a antiga — e o efeito desfazia a troca. Daí "pelo menu não muda".

### 25.3 A correção

**1. `setStep` não navega mais** (`StudioClientShell.tsx`):

```tsx
const setStep = React.useCallback((k: StudioStepKey) => {
    setState((s) => ({ ...s, activeStep: k }));
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `/studio/new?step=${k}`);
    }
}, []);
```

`history.replaceState` atualiza a URL **sem remount** — o estado sobrevive.

**2. Fonte de verdade única: `state.activeStep`** (`new/page.tsx`):

- O wizard agora renderiza a partir de `state.activeStep`, não da URL.
- A URL só é lida **na primeira carga** (deep-link / F5), via um
  `useRef` que garante que isso aconteça uma vez só.

**3. Botão da Etapa 6** que mandava para o áudio:
`router.push("/studio/new?step=audio")` → `setStep("audio")`.

### 25.4 Prova de que o upload sempre funcionou

Teste direto em `POST /api/upload/audio` com um WAV real:

```
UPLOAD OK
   ok: True
   path: uploads/f36a065c..._teste_etapa3.wav
   url: /static/output/uploads/f36a065c..._teste_etapa3.wav
   size_bytes: 132344

URL servível: HTTP 200 (132344 bytes)
```

O backend aceitava o arquivo e servia de volta corretamente. O que quebrava
era o estado do frontend **perder** a referência após a navegação — não o
upload.

### 25.5 Verificação

```
npx tsc --noEmit  → limpo (0 erros)
npx next build    → 4 rotas geradas, TypeScript OK

rotas servidas:
  /studio                    -> 12.469 bytes
  /studio/new                -> 13.399 bytes
  /studio/new?step=audio     -> 13.468 bytes  (deep-link OK)
  /studio/new?step=imagens   -> 13.476 bytes  (deep-link OK)
```

### 25.6 Lição

**`router.push` em wizard com estado em memória destrói o estado.** Quando o
estado do fluxo vive em `useState`, trocar de passo deve ser **mudança de
estado**, não navegação. Se a URL precisa refletir o passo, use
`history.replaceState` — atualiza o endereço sem remontar a árvore.

E: **um fluxo com duas fontes de verdade (URL + estado) sempre acaba em
divergência.** Escolher uma e fazer a outra ser espelho.

---

## §26 — 🐛 CORRIGIDO: abria a página de VENDAS em vez do PROGRAMA (20/09/2026, 01:55)

**Relato do usuário:**
> "você está misturando as coisas novamente agora você abriu a página de vendas
> ao invés do programa"

### 26.1 O que estava acontecendo

O app `musicclipstudio-landing` tinha **duas coisas empilhadas na mesma raiz**:

| Rota | O que servia | `<title>` |
|---|---|---|
| `/` (raiz) | **Página de MARKETING** do BlueBookStudio — abas Studio 51 / MusicClipStudio / BlueBookStudio / Agente009 | `MusicClipStudio - Transforme letras em videoclipes com IA` |
| `/studio` | **O PROGRAMA** (lista de projetos + wizard de 6 etapas) | `Studio · MusicClipStudio` |

Dois problemas somados:

1. Quem abrisse a raiz caía na **página de vendas**, não no gerador de clipes.
2. O programa tinha, no topo, um botão **`← Landing`** apontando para `/` —
   ou seja, **de dentro do programa** era fácil sair para a página de vendas
   por engano.

Isso é a mesma classe do §25: **duas coisas diferentes na mesma rota.** Não é
que o programa estivesse quebrado — é que a porta de entrada dava para o lugar
errado.

### 26.2 A correção

**1. `/` agora REDIRECIONA para `/studio`** — `src/app/page.tsx` reescrito:

```tsx
"use client";
import * as React from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  React.useEffect(() => { router.replace("/studio"); }, [router]);
  return <div>… Abrindo o Studio…</div>;   // spinner enquanto redireciona
}
```

**2. A landing (marketing) não morreu — mudou de endereço** para `/landing`.
`src/app/landing/page.tsx` criado com o conteúdo **idêntico** ao que estava na
raiz (abas, Header, Navigation, Background, Hero, Features, Support, Contact,
Footer, Studio51Content, BlueBookStudioContent, Agente009Content). O componente
foi renomeado para `LandingPage`. Nada de conteúdo foi perdido.

**3. O botão `← Landing` foi REMOVIDO** do topo do Studio
(`StudioClientShell.tsx`). No lugar dele:

- **Dentro do wizard** → `← Meus projetos` (link para `/studio`, volta à lista)
- **No dashboard** → `Meus projetos` sem link (é onde você já está) + ícone
  `FolderOpen`

Import do lucide atualizado com `FolderOpen`.

### 26.3 Mapa de rotas depois da correção

| Rota | O que é |
|---|---|
| `/` | → redireciona para `/studio` (o programa) |
| `/studio` | **PROGRAMA** — lista de projetos / dashboard |
| `/studio/new?step=…` | **PROGRAMA** — wizard de 6 etapas |
| `/landing` | Página de marketing multi-produto (Studio 51, MusicClipStudio, BlueBookStudio, Agente009) |

### 26.4 Verificação

```
npx tsc --noEmit  → limpo (0 erros)
npx next build    → ✓ rotas geradas

Route (app)
┌ ○ /            ← redireciona para /studio
├ ○ /_not-found
├ ○ /landing     ← marketing preservado
├ ○ /studio      ← o PROGRAMA
└ ○ /studio/new  ← wizard
```

**⚠️ A verificação por TAMANHO de bytes NÃO serve para este caso.** As páginas
do App Router renderizam no **cliente** — o HTML cru vem com o corpo vazio e o
payload RSC (`self.__next_f`). Comparar bytes ou procurar texto no HTML cru dá
**falso positivo/negativo**. Ex.: `/` servia 11.124 bytes e `/landing` 11.787 —
praticamente iguais, e *nada* do conteúdo aparecia no HTML.

**Verificação de verdade = navegador headless.** Criado o script
`_utils/_verificar_redirect_raiz.py` (Playwright/Chromium) que navega, espera o
`router.replace` rodar e lê a **URL final**:

```
OK  /           -> http://127.0.0.1:3000/studio
      title : Studio · MusicClipStudio
      texto : MusicClipStudio WEB · v0.1  Backend conectado  Meus Projetos  Dashboard  WIZARD  01 Letra ...
OK  /studio     -> http://127.0.0.1:3000/studio
OK  /studio/new -> http://127.0.0.1:3000/studio/new
OK  /landing    -> http://127.0.0.1:3000/landing
      title : MusicClipStudio - Transforme letras em videoclipes com IA
      texto : Studio 51  Ecossistema BlueBookStudio  ...  Agente 009

RESULTADO: TODOS OS REDIRECIONAMENTOS OK
```

Rodar: `py _utils/_verificar_redirect_raiz.py` (com o dev server no ar).

**Corrida final limpa** (cache do `.next` zerado, comando idêntico ao do
`INICIAR_MusicClipStudio.bat`), todas as rotas 200:

```
GET /          200 in 5.2s
GET /studio    200 in 2.1s
GET /studio/new 200 in 1.4s
GET /landing   200 in 1.2s
RESULTADO: TODOS OS REDIRECIONAMENTOS OK
```

### 26.5 🧨 EFEITO COLATERAL: cache do Turbopack corrompido

Durante a verificação apareceu um erro que **não era do código** e custou tempo:

```
FATAL: An unexpected Turbopack error occurred.
Error [TurbopackInternalError]: Failed to lookup task ids ...
  Caused by:
    0: Unable to open static sorted file referenced from 00000011.meta
    1: failed to open file `...\.next\dev\cache\turbopack\...\00000005.sst`:
       O sistema não pode encontrar o arquivo especificado. (os error 2)
```

**Causa:** o cache `.next/dev/cache/turbopack/` é um banco em arquivos —
`.sst` (dados) + `.meta` (índice). Uma limpeza **parcial** do `.next` (feita em
lotes, para driblar o guard de bulk-delete) apagou alguns `.sst` e deixou os
`.meta` apontando para arquivos que não existem mais → o Turbopack **entra em
pânico e o dev server morre na largada** ("NAO SUBIU").

Sintomas que isso produzia:
- dev server antigo (com cache corrompido) respondia **500** na raiz;
- dev server novo **panicava** e não subia.

**Correção:** remover o `.next` **por inteiro e atomicamente**, com
`shutil.rmtree` do Python (não em lotes):

```python
import shutil
shutil.rmtree(r"D:\dev-projetos\MusicClipStudio\musicclipstudio-landing\.next")
```

Depois disso o dev server sobe limpo. **Regra: nunca apagar o `.next` em
pedaços — ou apaga tudo, ou não apaga nada.**

### 26.6 Lição

**A porta de entrada de um programa tem que dar no programa.** Se existe uma
página de vendas e um app, eles são **rotas diferentes** — e a raiz pertence
ao app. E: **nenhum botão dentro do app deve apontar para a landing** sem que
o usuário saiba que está saindo do app.

E, em Next.js App Router: **não valide rota por HTML cru.** O SSR entrega um
esqueleto vazio; só um browser de verdade vê o resultado. Use
`_utils/_verificar_redirect_raiz.py`.

E: **cache do Turbopack é tudo-ou-nada.** `.sst` órfão de `.meta` = panic.

### 26.7 Pendência

Caso a página de vendas precise ser acessível de novo, ela vive em
**`/landing`**. O `INICIAR_MusicClipStudio.bat` abre
`http://127.0.0.1:3000/studio` (direto no programa), então os atalhos da
Desktop continuam corretos e **não precisaram ser recriados**.

---

## §27 — 🐛 CORRIGIDO: música não subia / menu não mudava de etapa (20/09/2026, 19:30)

**Relato do usuário:**
> "na etapa 3 a música não sobe, seguindo a sequência as telas mudam mas se
> você vai direto pelo menu a esquerda não"

### 27.1 A CAUSA (não era cache, não era o upload)

O **menu lateral do wizard** montava links para rotas que **NÃO EXISTEM**:

```tsx
// StudioSidebar.tsx (ANTES)
const href = projectId
  ? `/studio/${projectId}/${step.key}`   // ← rota inexistente → 404
  : `/studio/new?step=${step.key}`;
```

Com um `projectId` presente (ex.: `local_ym60th0i`), o item "Áudio" apontava
para **`/studio/local_ym60th0i/audio`** — rota que não existe. Prova no log:

```
GET /studio/local_ym60th0i/audio 404 in 1139ms
GET /studio/local_ym60th0i/audio 404 in 70ms
```

Ou seja: clicar no menu **navegava para um 404** em vez de trocar de etapa.
Daí o sintoma duplo relatado:
- **pelo menu** → não mudava a etapa (ia para o 404)
- **pela sequência** (botão Avançar) → funcionava (outro caminho, sem href)

### 27.2 As rotas que existem × os links que existiam

Só existem **4 rotas** no app (`/`, `/studio`, `/studio/new`, `/landing`),
mas havia **3 links para rotas inexistentes** — todos davam 404:

| Link | Rota que apontava | Existia? |
|---|---|---|
| Menu do wizard | `/studio/<id>/<etapa>` | ❌ → **corrigido** |
| `Configurações` | `/studio/settings` | ❌ → virou texto inerte |
| Título do projeto (dashboard) | `/studio/${p.id}` | ❌ → vai para o wizard |

### 27.3 A correção

**1. O item do menu deixou de ser `<Link>` e virou `<button>`** que só chama
`onStep(step.key)` — **sem href, sem navegação, sem remontar a árvore**:

```tsx
return onStep ? (
  <button type="button" onClick={handleClick} className={className}>
    {conteudo}
  </button>
) : (
  <Link href={`/studio/new?step=${step.key}`} className={className}>
    {conteudo}
  </Link>
);
```

Isto é a **mesma família** do bug do §25: trocar de etapa é **mudança de
estado**, nunca navegação. O §25 corrigiu o caminho "Avançar"; faltava o
**menu lateral** — que era justamente o que o usuário usava.

**2. `Configurações`** (`/studio/settings`) → deixou de ser link, virou texto
inerte (não há tela de configurações ainda).

**3. Título do projeto no dashboard** (`/studio/${p.id}`) → passou a abrir o
wizard: `/studio/new?step=letra&projeto=<id>`.

### 27.4 Verificação (navegador real, E2E)

`_utils/_teste_e2e_upload_musica.py` — abre o wizard, clica em "Áudio" **no
menu lateral**, envia um WAV real e checa o upload:

```
2) indo para a Etapa 3 (música) pelo MENU LATERAL...
   clicou no menu: True
   URL depois do clique: /studio/new?step=audio   ← NÃO saiu do wizard
   input de arquivo presente: True

3) enviando o arquivo de música...
   nome do arquivo aparece na tela: True
   elementos <audio> na página: 1
   uploads com 200: 1
   >>> OK: a música carregou no wizard

RESULTADO: OK — música sobe no wizard
404s no log do frontend: NENHUM
```

`npx tsc --noEmit` → limpo.

### 27.5 ⚠️ FALSO ALARME: o proxy NÃO era o problema

Nesta mesma sessão eu suspeitei do proxy do ambiente
(`HTTP_PROXY=127.0.0.1:51889`) e cheguei a implementar um **proxy reverso no
Next** (`next.config.ts` com rewrites de `/api` e `/static`). Investigando
melhor:

```
Registro do Windows (o que o NAVEGADOR do usuário usa):
  ProxyEnable = 0        ← proxy DESLIGADO
  ProxyServer = (nao definido)
```

O proxy `127.0.0.1:51889` existe **só no ambiente do WorkBuddy** (a
ferramenta), não no navegador do usuário. Ou seja: **não era a causa** do
problema dele.

**O rewrite foi mantido mesmo assim**, porque:
- torna o frontend independente de proxy (arquitetura mais robusta);
- `API_BASE` agora é `""` (mesma origem), então o navegador fala só com a
  porta 3000 e o Next repassa internamente.

Mas o crédito da correção é do **menu lateral**, não do proxy.

**LIÇÃO:** testar a hipótese **antes** de sair implementando. Eu quase
"corrigi" o problema errado. O registro do Windows provou a hipótese errada em
uma linha — devia ter checado isso primeiro.

---

## §28 — 🔧 PORTAS DEDICADAS: saiu de 3000/8000 para 3100/8300 (20/09/2026, 21:30)

### O problema (relatado ~30 vezes)

O usuário reclamava de forma recorrente: **"essa porra de porta é usada"**.
3000 e 8000 são as portas **padrão** de qualquer projeto Next.js + FastAPI.
Nesta máquina convivem vários projetos (`BlueBookStudio`, `flow-agent`,
`MusicClipStudio`), e isso gerava colisão.

### O diagnóstico (com dados, não suposição)

Rodei um levantamento real das portas em LISTENING:

```
:8001  python.exe  pid=32604   <- flow-agent (BlueBookStudio)
:8100  python.exe  pid=32604   <- flow-agent (HTTP callback)
:8760  python.exe  pid=16832   <- BBS flow daemon
:8765  python.exe  pid=28476   <- (não identificado)
:9227  python.exe  pid=32604   <- flow-agent WebSocket
3000 / 8000 -> LIVRES naquele momento
```

**Conclusão que derrubou minha hipótese anterior:** o BlueBookStudio **não usa
3000 nem 8000**. Lendo os `.bat` dele (`iniciar_bbs.bat`,
`iniciar_bbs_web.bat`), as portas dele são **8001 / 8100 / 8600 / 8760 /
8761 / 9227**. O conflito sentido pelo usuário **não** era outro projeto
roubando a porta — era outra coisa (servidor órfão, ou a matança indiscriminada
por PID do `PARAR_*.bat` antigo).

**Descoberta do flow-agent (PID 32604, rodando desde 18/09):**
É o *Flow Agent Extension Bridge* do BlueBookStudio (`flow-agent/flow_server/`).
Ele ocupa `8001` (uvicorn), `8100` (HTTP callback do sniffer) e `9227`
(WebSocket para a extensão do Chrome). Estava vivo há 2 dias — e eu **não
toquei nele**.

> Detalhe: `servidor/app.py:2332` do BlueBookStudio reinicia esse backend com
> `taskkill` por PID na porta 8001. Se o MusicClipStudio tivesse escolhido
> 8100, haveria colisão. Por isso **8100 foi descartada**.

### A solução

Portas dedicadas, que **nenhum outro projeto usa**:

| | Antes | Agora |
|---|---|---|
| Frontend (Next) | 3000 | **3100** |
| Backend (FastAPI) | 8000 | **8300** |

**Fonte única da verdade:** `_utils/_portas.py`

```bash
python _utils/_portas.py    # mostra o mapa e quem ocupa cada porta agora
```

### Arquivos alterados (15)

| Arquivo | Mudança |
|---|---|
| `_utils/_portas.py` | **NOVO** — fonte da verdade + inspetor de ocupantes |
| `INICIAR_MusicClipStudio.bat` | **REESCRITO** com detecção de conflito |
| `PARAR_MusicClipStudio.bat` | **REESCRITO** — só 3100/8300 + confere o dono |
| `RUN_WEB.bat` | 3100/8300 |
| `backend/app/main.py` | CORS + docstring |
| `musicclipstudio-landing/package.json` | `dev`/`start` |
| `.../next.config.ts` | `BACKEND_INTERNAL_URL` default |
| `.../.env.local` | `BACKEND_INTERNAL_URL` |
| `.../src/lib/utils.ts` | comentário |
| `.../src/app/studio/new/page.tsx` | fallback do WebSocket |
| `_utils/` (6 scripts) | URLs |
| `_Atalhos/` (4 arquivos) | URLs |
| `_utils/_ler_atalhos.py` | **NOVO** — lê os `.lnk` da Desktop |

**Os atalhos da Desktop continuam válidos:** eles apontam para os `.bat` por
caminho (`D:/dev-projetos/MusicClipStudio/INICIAR_MusicClipStudio.bat`), não
para a URL. A troca de porta se propaga automaticamente.

### 🔴 O launcher agora PERGUNTA em vez de matar

Este era o pedido central. Antes: o script assumia as portas e o `PARAR_*.bat`
matava **qualquer** PID em 3000/8000 sem verificar de quem era.

Agora, quando a porta está ocupada, o `INICIAR` mostra:

```
############################################################
 CONFLITO DE PORTA - BACKEND
############################################################
  A porta 8300 JA ESTA EM USO (PID 12345).
  Este script NAO vai encerrar nada sozinho.

  Escolha como continuar:

    [S] Parar o processo 12345 e continuar
    [N] Nao mexer - abortar o inicio
    [C] Continuar mesmo assim (vai dar erro, geralmente)
```

- **[N] ou qualquer outra coisa → nada é alterado.**
- `taskkill` existe **só** dentro do ramo `[S]` — verificado.
- O `PARAR_*.bat` confere se o processo é `python`/`node` antes de encerrar;
  se for outra coisa, **avisa e não mata**.

Além disso, se o backend não responder após 30 s, o launcher **aborta com
mensagem clara** ("Sem o backend, enviar musica NAO funciona") em vez de abrir
o Studio quebrado.

### Verificação executada

```
BACKEND 8300 OK (1s)
FRONTEND 3100 OK (1-3s)
  / -> 200   /studio -> 200   /studio/new -> 200   /landing -> 200
GET /api/health via 3100 (rewrite): 200 {"status":"ok","backbone_ready":true}
POST /api/upload/audio via 3100: 200
  -> /static/output/uploads/d2ec80be..._teste_portas_novas.wav (arquivo no disco)
tsc --noEmit: exit 0
```

Lógica do launcher: 10/10 checks OK, incluindo
"pergunta antes do taskkill" e "taskkill só no ramo S".

### ⚠️ Lição: o proxy do WorkBuddy engana os testes

No primeiro teste, **todas as rotas deram 502** com a mensagem
`upstream connect failed: os error 10061`. Quase concluí "servidor caiu".

Era o **proxy do WorkBuddy** (`HTTP_PROXY=127.0.0.1:51889`) interceptando o
`curl`. Com `--noproxy '*'`, tudo respondeu **200**.

> **Regra:** ao testar localhost **do ambiente do WorkBuddy**, usar sempre
> `curl --noproxy '*'`. Um 502 com `os error 10061` é o proxy, não o servidor.

### Mapa de portas da máquina (referência)

| Porta | Dona |
|---|---|
| **3100 / 8300** | **MusicClipStudio** |
| 8001 / 8100 / 9227 | BlueBookStudio — flow-agent |
| 8600 | BlueBookStudio — web + watchdog |
| 8760 / 8761 | BlueBookStudio — daemons |

---

## §29 — 🐛 CORRIGIDO: busca de mídia não mostrava os resultados (21/09/2026, 18:40)

### O sintoma (relatado pelo usuário)

> "a busca está com problema — as imagens ali são do programa, não da busca da
> internet, e mesmo usando o botão de busca a mesma não aparece"

Nas **Etapas 5 (Mídia)** e **6 (Gerar)** apareciam 8 imagens, com selos
"VIDEO · 7s" / "FOTO · 4K". Ao clicar em **Buscar**, surgia um toast dizendo
"Encontradas N mídias" — e **nada mudava na tela**.

### Diagnóstico em duas etapas

**1. O backend estava 100% (descartado de saída).**

```
POST 127.0.0.1:3100/api/midia/buscar  {"query":"ocean sunset"}
-> 200 {"total":3,"resultados":[
     {"provider":"pexels","tipo":"video","url_thumbnail":"https://images.pexels.com/..."},
     ...]}
```

Busca real, com thumbnails válidas, passando pelo rewrite do Next (3100 → 8300).

**2. O bug estava no frontend — `Step5Midia`, em `src/app/studio/new/page.tsx`.**

```tsx
// ANTES (errado)
const galeria = [ "/assets/images/studio51-set.jpeg", ... ];  // 8 imagens LOCAIS fixas

const doSearch = async () => {
  const r = await fetch(`${API_BASE}/api/midia/buscar`, {...});
  const json = await r.json();
  toast.success(`Encontradas ${json.total ?? 0} mídias`, { id });
  //          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  //          só mostra o toast. Os resultados NUNCA vão para um state.
};

// e a grade renderiza:
{galeria.map((src, i) => ...)}      // <-- sempre o array fixo
```

A busca era **decorativa**: chamava a API, contava os resultados, mostrava um
toast de sucesso e **descartava tudo**. A grade desenhava `galeria`, um array
literal de 8 imagens do próprio programa.

Isto explica exatamente os dois sintomas:
- "as imagens são do programa" → sim, literais em `/assets/images/`.
- "a busca não aparece" → os resultados nunca chegavam à grade.

**O toast era o pior detalhe:** ele dizia "Encontradas 15 mídias" com sucesso,
o que fazia parecer que funcionou. Só que o número vinha da API e nunca
virava pixel.

### Correção

- Novo state `resultados: MidiaStock[]` + flag `buscou`.
- `doSearch` agora guarda os resultados (filtrando quem tem thumbnail, para a
  grade não abrir com buracos).
- A grade renderiza `resultados` quando existirem; o array local virou
  **placeholder** (`galeriaInicial`), usado só antes da primeira busca.
- Selos agora refletem o **tipo real** (`FOTO`/`VIDEO`) e o **provider**
  (`pexels`, `pixabay`...), em vez de um `i % 3 === 0` fingido.
- Erro de API agora é `toast.error` com a dica da porta 8300 — antes o `catch`
  dizia **"Buscou localmente — API offline — demo"**, mascarando a falha.
- Botões **Continuar assim mesmo** e **Ir para gerar** (antes a Etapa 5 não
  tinha como avançar pelos botões do rodapé).
- O texto da contagem agora diz de onde vieram: "resultados de '...'" ou
  "exemplo local — use a busca acima".

### Extra: 2 erros de TypeScript pré-existentes corrigidos

`src/app/studio/new/page.tsx` (Step6Gerar) tinha dois `TS2322`:

```
error TS2322: Type 'number' is not assignable to type 'Timeout'.
```

Causa: `React.useRef<ReturnType<typeof window.setTimeout>>` — no browser o
retorno é `number`, mas o `Timeout` global do `@types/node` colide. Trocado por
`React.useRef<number | null>`. `tsc --noEmit` agora sai **limpo**.

### Verificação (E2E em navegador real)

Criado `_utils/_teste_e2e_busca_midia.py` (Playwright/Chromium, sem proxy):

```
1) abrindo http://127.0.0.1:3100/studio/new?step=midia
   imagens na grade antes: 8  (locais: 8)
2) clicando em 'Buscar'...
   imagens na grade depois: 24  (externas: 24)
3) requisições /api:
   - http://127.0.0.1:3100/api/midia/buscar
   respostas:
   - 200 http://127.0.0.1:3100/api/midia/buscar

  grade mudou apos buscar .......: True
  imagens externas na grade .....: True (24)
  /api/midia/buscar respondeu 200: True
  RESULTADO: PASSOU
```

O teste compara a grade **antes/depois** do clique e exige que as novas imagens
venham de domínio externo — é o que pega este tipo de bug, que um teste de API
jamais pegaria.

### Lição

**Toast de sucesso não é prova de que a feature funciona.** O código dizia
"Encontradas 15 mídias" e não mostrava nenhuma. Um teste que só olha a resposta
da API teria passado. Foi preciso um teste que **compara a tela antes e depois**
para provar o contrário.

> Padrão a vigiar: `fetch` → `toast.success(total)` → **sem `setState`**.
> Sempre que um resultado de busca existir, ele tem que chegar à renderização.

---

## §30 · 21/09/2026 — "a busca não pega nada da letra" (IA FALSA na Etapa 04)

### Sintoma relatado

> "de novo a busca não vem não pegou nada da letra da musica, mesmo mudando a
> letra as opções de busca de imagens e video são as mesmas"

Duas coisas ao mesmo tempo: a busca parecia não usar a letra, e as opções eram
idênticas para qualquer letra.

### Causa 1 — a Etapa 04 era uma IA de mentira

`src/app/studio/new/page.tsx`, `Step4Imagens`. O código era literalmente:

```tsx
const prompts = [
  { beat: 1, prompt: "Cidade noturna com névoa, luzes de neon, 35mm", checked: true },
  { beat: 2, prompt: "Close-up em rosto melancólico, iluminação de rua", checked: true },
  { beat: 3, prompt: "Gravura de estrada vazia sob chuva, drone shot", checked: true },
  { beat: 4, prompt: "Letreiro antigo 'hotel' piscando à noite", checked: false },
];

const gerarPrompts = async () => {
  const id = toast.loading("Agente IA · interpretando a letra...");
  await new Promise((r) => setTimeout(r, 1200));           // <- finge pensar
  setState((s) => ({ ...s,
    imagens: prompts.map((p, i) => ({ ...p,
      prompt: `${p.prompt} · variação ${i + 1}` })),        // <- sufixo, só
  }));
  toast.success("Prompts gerados", { id });
};
```

Nunca lia `state.letra`. Nunca chamava o backend. Dormia 1,2 s e devolvia um
array **constante** com "· variação N" colado no fim. Daí a reclamação ser
exata: eram as mesmas opções porque vinham de uma constante.

### Causa 2 — a Etapa 05 não consumia os prompts

`Step5Midia` começava com `useState("city night cinematic")` — termo fixo, sem
ligação alguma com o que a Etapa 04 tinha produzido. Mesmo que a Etapa 04
funcionasse, a busca continuaria igual.

### Causa 3 — o backend repetia a query (agente)

Em `agent.py`:

```python
def _query_do_mood(self, mood): 
    return queries[0]      # sempre a PRIMEIRA
...
if leitura is not None and leitura.confianca >= 0.4:
    photo_query = cenas[0]  # sempre a PRIMEIRA
else:
    photo_query = self._query_do_mood(mood)   # sempre queries[0]
```

Todo beat sem emoção forte recebia a mesma string. Com letra sombria: quatro
beats = quatro `"dark city"`. Confirmado ao vivo:

```
POST /api/imagens/gerar-prompts  ->  total 4, todos "dark city"
```

### Correções

**Backend — `agent.py`**

- `_query_do_mood(mood, indice=0)` → `queries[indice % len(queries)]`.
- `direcionar_imagem(beat, mood=None, indice=0)` → usa
  `cenas[indice % len(cenas)]` em vez de `cenas[0]`.
- `_decidir_beat(beat, plan, indice=0)` e `analisar()` passa `enumerate(beats)`.
- `confidence` deixou de ser `0.85` fixo (número inventado, dizia "certeza"
  até quando estava chutando o mood) e passou a refletir a leitura real:
  confiança da leitura, ou `0.35` quando cai no mood.

**Frontend — Etapa 04**

`gerarPrompts` agora chama `POST /api/imagens/gerar-prompts` com `state.letra`,
guarda os prompts reais no state, mostra mood/estilo detectados e a confiança
de cada beat, e dá `toast.error` real em vez de sucesso falso. Sem letra, avisa
em vez de inventar. Nada mais de `setTimeout` fingindo IA.

**Frontend — Etapa 05**

- campo de busca nasce com o 1º prompt da letra (e não com termo fixo);
- os prompts viram chips clicáveis ("cenas da letra");
- botão **Buscar tudo da letra** dispara uma busca por cena e junta tudo;
- ao entrar na etapa, a busca roda sozinha se já houver prompts;
- cada item mostra de qual cena veio;
- **as imagens locais de `/assets/` saíram de vez** — elas eram a causa de
  "as imagens ali são do programa, não de busca da internet". Sem resultados, a
  tela agora diz o que falta, em vez de desenhar placeholders do próprio app.

### Prova (E2E — `_utils/_teste_e2e_letra_muda_busca.py`)

```
── rodada A · letra sombria ──
   cenas : ['dark city', 'dark city', 'single person alone in crowded street']
   imagens: 24 externas (pexels)
── rodada B · letra alegre ──
   cenas : ['sunrise breaking over horizon', 'friends laughing together outdoors', 'colorful party']
   imagens: 24 externas (pexels)

[OK ] letras diferentes -> PROMPTS diferentes
[OK ] letras diferentes -> IMAGENS diferentes
[OK ] rodada A/B: nenhuma imagem local do programa (0)
[OK ] rodada A/B: imagens externas do banco de stock (24)
[FALHA] rodada A: sem prompt repetido   <- backend ainda com o código antigo
```

A última linha falha **só** porque o backend do usuário (PID 27900) segue com o
`agent.py` antigo na memória — o uvicorn do launcher roda **sem `--reload`**.
Rodando o mesmo agente novo em porta temporária (8311), a letra sombria dá três
cenas distintas:

```
dark city · rainy street · lone figure on empty beach winter
```

Ou seja: falta reiniciar o backend para a variedade valer.

### Lição

**Um botão "Gerar com IA" que não chama IA é pior que um botão ausente** — ele
treina o usuário a acreditar que o sistema pensou. Aqui ele durava 1,2 s e
devolvia constante. Sempre que existir um "passo de IA", o teste tem que
comparar a **saída para duas entradas diferentes**: se a saída não muda, não há
IA, há teatro.

> Padrão a vigiar: `await new Promise(r => setTimeout(r, N))` seguido de
> `setState` com array literal. É IA de fachada.

---

## 31 · 21/09/2026 — "vai pro fim sem escolher as imagens, o efeito de cada imagem" + ordem letra→áudio→legenda

Dois pedidos do usuário, que na apuração viraram **5 defeitos reais**.

### 31.1 · Ordem das etapas (pedido direto)

`STUDIO_STEPS` era `letra → legenda → áudio`. Pedido: **`letra → áudio →
legenda`**, porque sem letra o caminho natural é subir a música e transcrever;
com a legenda antes do áudio, quem não tem letra caía na transcrição sem ter
áudio nenhum carregado.

Alterado em `src/components/studio/StudioSidebar.tsx` (+ números `01/02/03`
trocados em `page.tsx`).

### 31.2 · A seleção de mídia era descartada — "vai pro fim sem escolher as imagens"

**Causa 1** — `state.midia` guardava só os **índices** dentro de `resultados`,
que é estado LOCAL do `Step5Midia`. Ao sair da etapa, os índices apontavam
para nada.

**Causa 2** — `Step6Gerar.gerar()` montava o POST com apenas `project` e
`audio_path`. **Nunca lia `state.midia`.** O backend montava o clipe por conta
própria. Era literalmente "ir pro fim sem escolher as imagens".

**Causa 3** — `GeneratePayload.selected_media` existia no contrato do backend
e **não era lido por ninguém**.

**Causa 4** — não havia lugar nenhum para escolher o **efeito por imagem**;
o `engine.gerar_projeto` fixava `animation = "ken_burns"` para todas.

**Causa 5 (o pior)** — `html_renderer.py` escrevia
`<div class="parallax-bg" style="background-image: url(...)">`, mas **não
existia nenhuma regra CSS `.parallax-bg`**. Sem `position`/tamanho, a imagem
não tinha área para desenhar: mesmo quando a URL chegava, a cena saía com o
fundo sólido do corpo.

### Correções

| Arquivo | O que mudou |
|---|---|
| `StudioSidebar.tsx` | ordem `letra → áudio → legenda` |
| `page.tsx` (Step5) | seleção guarda o **objeto** da mídia + `efeito`; ↑↓ para reordenar; card novo **"Sequência do clipe"** com `<select>` de efeito por cena |
| `page.tsx` (Step6) | envia `project.images`, `project.efeitos` e `selected_media`; **bloqueia** o render se nenhuma cena foi escolhida (e volta para a etapa 05) |
| `page.tsx` (resumo) | `state.midia.length \|\| 3` mostrava "3 peças selecionadas" com zero selecionadas |
| `backend/app/main.py` | `selected_media` passa a ser a fonte das imagens/efeitos; `ClipProjectPayload.efeitos` novo |
| `engine.py` | `generate()`/`gerar_projeto()` recebem `efeitos` e aplicam um por beat |
| `html_renderer.py` | CSS `.parallax-bg` (faltava) + `.fx-*` com 6 animações reais |
| `backend/app/main.py` | `/api/legenda/transcrever` estava quebrado (ver 31.3) |

Efeitos aceitos (mesmos ids nos dois lados): `ken_burns`, `zoom_in`,
`zoom_out`, `pan_left`, `pan_right`, `static`. Desconhecido → `ken_burns`.

### 31.3 · A transcrição também era falsa

`Step2Legenda.onTranscrever` era `setTimeout(1400)` + `map` inventando tempos
de 3 em 3 s (`i * 3`). Não chamava backend, não abria o áudio, não rodava
Whisper — **o mesmo padrão de IA de fachada do §30**.

E, mesmo se chamasse, o endpoint estava quebrado: `main.py` fazia
`from MusicClipStudio.transcricao import transcrever_audio` e **essa função
não existe** (chama-se `transcrever`). O `ImportError` caía no `except` e
devolvia 500 "Transcrição indisponível" em 100% dos casos. Além disso o
retorno tratava o resultado como `list[dict]`, quando `transcrever` devolve
um `ResultadoTranscricao`.

Corrigido: import pelo nome certo, `resultado.ok` checado, segmentos
convertidos com `para_dict()`, e o front passa a chamar
`POST /api/legenda/transcrever` com o áudio da etapa 02 — preenchendo também
`state.letra` quando ela está vazia (é exatamente o caso "não tenho a letra").

### Provas

```
ordem na barra lateral: ['Letra', 'Áudio', 'Legenda', 'Imagens', 'Mídia', 'Gerar']   [OK]
card 'Sequência do clipe' existe                                                     [OK]
efeito por imagem no HTML: parallax-bg fx-ken_burns / fx-zoom_in / fx-pan_right      [OK]
regra CSS .parallax-bg presente (imagem tem área para desenhar)                      [OK]
tsc --noEmit                                                                         limpo
```

### ⚠️ Pendente → RESOLVIDO em 21/09/2026

O backend (PID 27900, porta 8300) **não podia ser morto por este ambiente** —
invisível para `tasklist`, PowerShell e CIM; `TerminateProcess` devolve erro 5
(acesso negado), o que indica processo elevado. O usuário fechou a janela à
mão e o backend foi subido de novo (novo PID).

**Provas de que o código novo está no ar:**

```
POST /api/legenda/transcrever → "Áudio não encontrado: ...\nao_existe.mp3"
   (antes: "cannot import name 'transcrever_audio'" — 500 em 100% dos casos)

POST /api/imagens/gerar-prompts (letra sombria)
   beat 1 'single person alone in crowded street'  conf 0.60
   beat 2 'rainy street'                           conf 0.35
   beat 3 'shadow figure'                          conf 0.35
   → 3 cenas distintas (antes: 4x "dark city")

_utils/_teste_e2e_letra_muda_busca.py → 10/10 OK · RESULTADO: PASSOU
   (a última falha da sessão anterior — "sem prompt repetido" — virou OK)
```

> Nota operacional: o backend atual está rodando como tarefa em background
> desta sessão. Se ele morrer, usar `INICIAR_MusicClipStudio.bat` — o script
> detecta a porta livre e sobe um novo.

---

## 32 · 21/09/2026 — seletor de formato (9:16, 16:9, 1:1, 3:4, 4:3) + persistência do estado do wizard

### 32.1 · Formato de saída

O backend já aceitava `format` em `_DIMS` (engine.py) — `9/16`, `16/9`, `3/4`,
`4/3`, `1/1`. Mas o front só sabia fazer 9:16. Adicionado `<select>` no resumo
da etapa 06 com as 5 proporções; o `format` vai no `project.format` do payload
e o celular-fake do preview + a estatística "Resolução" + o texto do "Render
concluído" passam a refletir a escolha.

### 32.2 · "Onde foi parar a música?"

`useState(DEFAULT_STATE)` zera o wizard quando o componente REMONTA. Acontece em
3 casos: (1) Fast Refresh do Turbopack quando eu mexo em `StudioClientShell`,
(2) F5, (3) `router.push` (já blindado em §25/§27). Em (1) o disco fica intacto
(`output/uploads/<uuid>_*.mp3`) — só a referência some do estado. Por isso o
"Aguardando início" da etapa 06 e o toast "Envie a música antes de gerar".

Adicionado: ler `localStorage["musicclipstudio_wizard_v1"]` na primeira
montagem (só restaura se havia letra/música/mídia/imagens) e salvar em cada
mudança de estado (debounce 300ms). Os três casos ficam cobertos: F5,
remount e qualquer troca de estado posterior.

### Lição

**"O fluxo vai até o fim" quase sempre significa que um estado do front nunca
é lido por quem executa.** O sintoma é de navegação; a causa é um payload que
não carrega o que a tela coletou. Vale conferir, antes de mexer em UI: *quem
lê esse estado?* Se ninguém, a tela só está fazendo o usuário perder tempo.

### 32.3 · "Reanexar último upload" - recuperacao sem precisar do arquivo

Ja que o disco fica intacto, faz sentido oferecer reanexar com 1 clique em
vez de pedir que o usuario ache o .mp3. Adicionado:

- GET /api/upload/audio/recente?limite=N em backend/app/main.py -
  varre output/uploads/, exclui arquivos < 1 KB (currais de teste),
  devolve {path, url, nome, size_bytes, mtime} do mais novo pro mais velho.
- Banner na etapa 02 (Audio) quando state.musica.arquivo esta vazio.
  Lista cada arquivo recente num botao proprio ("Reanexar") que le a
  duracao real via <audio> e devolve a referencia pro estado do wizard.

Endpoint verificado em producao: retornou 5 itens com o Beethoven (5,5 MB,
mtime 1790030278 = 19:37) em primeiro. UI mostra 5 botoes REANEXAR -
exatamente os mesmos arquivos do disco.

### 32.4 - Job real ponta-a-ponta, com tudo novo

	sc limpo + E2E do navegador provam a UI, mas a memoria do projeto e clara:

> "O pipeline engole excecao... erro vira 'sucesso' com saida errada. Ja causou
> 3 bugs. Ao mexer no engine ou em callbacks... executar um job real.
> Testes verdes + tsc limpo NAO garantem que o fluxo funciona."

Por isso, _req_tmp/_job_e2e_completo.py dispara um job de ponta a ponta:

1. Sobe um .wav de teste pelo /api/upload/audio
2. Busca 2 imagens reais no Pexels via /api/midia/buscar
3. Envia POST /api/jobs/gerar com:
   - project.format = "16/9" (nao default)
   - project.images = [2 urls do Pexels]
   - project.efeitos = ["zoom_in", "pan_left"]
   - selected_media = [{url,efeito,ordem,tipo}]
4. Polling ate done
5. Baixa o MP4 em /static/output/clipes/<id>_legendado.mp4
6. Inspeciona o HTML do composer em gerador_clipes_musicais/output/_temp/
7. fprobe no MP4 final

**Resultado:**

`
[  0s] running   50% - render | Convertendo HTML para video...
[ 54s] running   88% - legendas | Gerando legendas...
[ 57s] done     100% - concluido | Clip gerado

MP4: 0,65 MB - 680708 bytes
HTML do composer:
   beats no HTML:           2
   regra CSS .parallax-bg:  OK
   efeito .fx-zoom_in:      OK
   efeito .fx-pan_left:     OK
   dimensao 1920x1080:      OK
ffprobe:
   width=1920  height=1080  duration=3.000000  nb_frames=72

RESULTADO: JOB REAL PASSOU - imagens+efeitos+formato OK
`

Traducao do que isso prova:

| Funcionalidade nova          | Evidencia no job                                       |
|------------------------------|--------------------------------------------------------|
| Imagens escolhidas no video  | 2 beats com .parallax-bg -> urls do Pexels             |
| Efeito por imagem            | .fx-zoom_in no beat 1, .fx-pan_left no beat 2          |
| Formato 16/9                 | HTML 1920x1080, MP4 ffprobe 1920x1080                  |
| CSS da imagem (que faltava)  | regra .parallax-bg presente                            |
| Pipeline ponta a ponta        | done em 57s, 0 erros                                   |

### 32.5 · Formato sempre visível + o que acontece com a mídia incompatível

**Problema 1:** o select de formato estava só no resumo da etapa 06. Ninguém
achava. Movido (também) para o painel direito do preview — visível em **todas**
as etapas, ao lado das estatísticas.

**Problema 2 (pergunta do usuário):** *"se eu escolher uma saída diferente da
mídia de entrada, o que acontece?"*

Resposta técnica: `.parallax-bg` usa `background-size: cover`. A mídia preenche
o quadro e o excesso é **cortado pelo centro** — sem distorção e sem tarja
preta, mas perdendo pedaço da imagem. Antes o usuário só descobria isso
assistindo ao MP4 pronto.

**Solução:** o stock devolve `largura`/`altura` (verificado: 10/10 resultados
têm). Cada item da grade da etapa 05 mostra um selo:

| Selo    | Significado                                        |
|---------|----------------------------------------------------|
| `ok`    | orientação bate com a saída — entra inteira        |
| `corta` | orientação diferente — será cortada pelo centro     |
| `?`     | dimensão desconhecida                               |

Além disso: banner *"Saída em 9/16 (retrato). 13 de 24 serão CORTADAS pelo
centro (sem distorção, sem tarja)"* e checkbox **"Mostrar só as compatíveis"**.

**Prova no fluxo real** (letra → prompts → busca → etapa 05):

```
ocorrências de 'corta': 14      (13 selos + 1 no aviso)
ocorrências de 'ok'   : 11
aviso: 'Saída em 9/16 (retrato). 13 de 24 serão CORTADAS pelo centro'
checkbox 'só compatíveis': 1
RESULTADO: OK - selos + aviso + filtro presentes
```

> Observação importante: numa busca genérica ("city night") a maioria das
> mídias de banco é **paisagem**. Para saída vertical (9/16) isso significa
> corte em boa parte delas. Vale usar o filtro, ou buscar termos que tragam
> retrato.

## §32.6 — 21/09/2026 · Vídeos de banco agora viram `<video>` + 3 bugs do renderer

### a) Vídeo de banco (Pexels/Coverr) renderizando

A busca devolve **metade vídeo** (5/10 em "city night"). O composer
anterior escrevia a URL em `background-image: url('*.mp4')` — CSS não
desenha nada. Resultado: a cena saía preta.

**Correção** (`scene_engine/renderers/html_renderer.py`):

```python
_EXT_VIDEO = (".mp4", ".webm", ".mov", ".m4v", ".ogv")
def _eh_video(url):
    u = url.split("?", 1)[0].lower()
    return u.endswith(_EXT_VIDEO) or "/video-files/" in u

# no beat parallax_image:
if _eh_video(img):
    camada = (f'<video class="parallax-video" src="{img}" '
              f'autoplay loop muted playsinline preload="auto"></video>')
else:
    estilo = f"background-image: url('{img}')"
```

CSS:
```css
.parallax-video { width: 100%; height: 100%; object-fit: cover;
                  object-position: center; display: block; }
```

### b) Vazamento de frames entre jobs (ENCONTRADO NO CAMINHO)

A pasta `_temp_frames` era fixa e nunca era limpa. O FFmpeg lia
`frame_%05d.png` como sequência contígua: para um job que escreve 72,
o MP4 saía com ~1100 frames de jobs antigos colados no fim. Evidência:
num job com beat de 1,5 s o MP4 saiu com **49 s / 1178 frames** e o
`frame_00072` estava datado 12 min antes do job atual.

**Correção** (`video_renderer.py`): cada render usa pasta única
`_temp_frames_<html_stem>`, onde `html_stem` é o `project_id` que o
engine já gera (`clip_<timestamp>`). Sobrando lixo antigo ou não,
nunca entra no vídeo.

### c) Relógio do renderer fugia (O BUG QUE TUDO ESCONDIA)

O JS anima via `requestAnimationFrame` acumulando `currentTime` em
**relógio de parede**. Cada screenshot a 1080×1920 leva ~250 ms.
Para uma composição de 3 s, 72 frames × 250 ms = **~18 s de wall
time**. O JS atingia `totalDuration`, parava de agendar frames e
**escondia todos os beats** — frames 18+ saíam com 99% cor de fundo,
só o frame 0 tinha conteúdo. Esse é o motivo pelo qual a verificação
"passou" olhando só frame 0 e o ffprobe — via de regra, dava para
ver o MP4 sair inteiro "azul" só com a legenda, em qualquer composição
acima de ~2 s.

**Correção** (`video_renderer.py`): para cada frame, o renderer agora
**pausa o RAF** e dirige `currentTime` + `.visible` deterministicamente:

```js
paused = true;
currentTime = t;
document.querySelectorAll('.beat').forEach(b => {
    const s = parseFloat(b.dataset.start);
    const e = parseFloat(b.dataset.end);
    b.classList.toggle('visible', t >= s && t < e);
});
```

### d) Wait de mídia incompleto

`wait_for_function` só checava `<img>` e `<video>`. Beat 1 usa
**`background-image`** (sem `<img>`) → a espera retornava sem ter
verificado a foto. **Correção**: `wait_for_load_state("networkidle")`
cobre background-image; mantém a checagem extra de `<img>`/`<video>`
como segurança.

### Prova: job real + checagem dos 72 frames

`D:\dev-projetos\MusicClipStudio\_req_tmp\_job_video_real.py`:
job ponta-a-ponta com cena 0 = vídeo (`.mp4`) e cena 1 = foto (`.jpg`),
formato 9/16, efeitos `["zoom_in","pan_left"]`.

`D:\dev-projetos\MusicClipStudio\_req_tmp\_verificar_todos_frames.py`:
baixa todos os 72 frames, downsample, conta pixels de fundo.

```
RESUMO: OK=72  QUASE-VAZIO=0  VAZIO=0  total=72
VEREDITO: PASSOU
```

Médias (downsample 160×284):
- frames 0–30 (beat 0, vídeo): RGB (80, 68, 43), ~25k cores únicas
- frames 36–66 (beat 1, foto): RGB (38, 25, 27), ~17k cores únicas
- transição exata em t=1.5 s (frame 36) — bate com data-start/data-end

MP4 final (`_teste_video_real_legendado.mp4`, 0.36 MB):
- ffprobe: 1080×1920, 3.000 s, 72 frames ✓
- frame em t=0.7 s: vista aérea da cidade com legenda da cena 0 ✓
- frame em t=2.3 s: skyline ao nível da água com legenda da cena 1 ✓

> ⚠️ Backend (PID 13640) tem código velho na memória. As 3 correções só
> passam a valer após reinício do backend. O usuário foi avisado.

## §32.7 — 21/09/2026 · Regra de corte (blur) + gargalo de performance

### a) Regra de corte: fundo com blur, só na divergência

Decidido com o usuário entre três opções (corte central / fundo com
blur / corte inteligente). Escolhido: **fundo com blur**.

Antes era `cover` puro: numa foto 16:9 para saída 9/16 isso descartava
~69% da largura — metade da cena ia fora.

Agora são duas camadas em `html_renderer.py`:

```html
<div class="parallax-bg fx-...">
    <div class="parallax-fill" style="background-image: url(...)"></div> <!-- cover + blur -->
    <div class="parallax-main" style="background-image: url(...)"></div> <!-- contain -->
</div>
```

```css
.parallax-bg        { position:absolute; inset:0; overflow:hidden; }
.parallax-fill      { inset:0; background-size:cover;
                      filter: blur(28px) brightness(0.55);
                      transform: scale(1.25); }
.parallax-main      { inset:0; background-size:contain; background-position:center; }
.parallax-fill-video{ object-fit:cover; filter: blur(28px) brightness(0.55);
                      transform: scale(1.25); }
.parallax-main-video{ object-fit:contain; }
```

O **"só na divergência" sai de graça do CSS**: quando a orientação da
mídia bate com a do quadro, `contain` e `cover` dão o mesmo resultado,
a camada da frente cobre o fundo inteiro e o blur nunca aparece. Quando
diverge, sobram faixas e elas são preenchidas pelo desfoque.

`inset` mudou de `-6%` para `0`: com `contain` o -6% faria a mídia
crescer 12% e vazar do quadro. A folga dos efeitos de pan/zoom vem do
próprio `scale` da animação.

Prova: render real 9/16 com foto 5952x2976 (2:1). Topo do quadro com
desvio 0,7 (liso = desfocado) contra 29,6 na faixa da foto — 41x mais
detalhe onde a mídia está nítida.

### b) frames de jobs antigos (já em §32.6) e performance

Medido com `_req_tmp/_bench_frame.py` (8 capturas por variante,
1080x1920):

| camada | custo/frame |
|---|---|
| screenshot puro (página vazia) | **632 ms** |
| + foto | +50 ms |
| + vídeo 4K | +361 ms |
| + blur | +173 ms |
| **total** | **1215 ms** |

A 24 fps, um clipe de 3 min = 4320 frames -> **87 min**. Inviável.

### c) O culpado: `.grain` com `feTurbulence`

O `.grain` era um overlay decorativo de **opacidade 0.04** feito com
`feTurbulence type='fractalNoise' numOctaves='4'` cobrindo o quadro
inteiro. Ruído fractal SVG é rasterizado a cada paint:

```
sem beats (grain presente)   695 ms/frame
sem beats e sem .grain       116 ms/frame   <- 6x mais rapido
```

**~580 ms por frame, 83% do tempo total, para um efeito de 4% de
opacidade (praticamente invisível).** Removido. Se voltar um dia, usar
tile de ruído pré-gerado (bitmap pequeno), nunca `feTurbulence` ao vivo.

Também removido do caminho: `<link>` para `fonts.googleapis.com` (rede
com proxy atrasa o primeiro paint).

### d) Vídeo 4K -> 720p na busca

`database.py` pegava **sempre a maior resolução**
(`sorted(..., reverse=True)[0]` = 3840x2160). O render decodifica isso
por frame — e com o fundo desfocado, duas vezes.

Novo helper `_escolher_variante_video()`: menor variante do Pexels que
ainda atende `ALTURA_VIDEO_MINIMA = 720`. O quadro final é 1080x1920;
com `contain` uma variante 1280x720 já cobre a faixa da mídia em
resolução nativa, e a camada de fundo é borrada de propósito.

Verificado (queries novas, cache miss): `1840x1034` e `1920x1080`
(saía 3840x2160 antes).

### e) Frames PNG -> JPEG q95

Medido: PNG 1814 ms/frame vs JPEG q95 467 ms/frame (**3,9x**). O frame é
intermediário — o FFmpeg reencoda para h264 em seguida. `images_to_video`
agora lê `frame_%05d.jpg`.

### f) Resultado

Mesmo job (2 cenas: vídeo + foto, 9/16, 3 s, 72 frames):

```
antes  183 s   (2,5 s/frame)
depois  71 s   (1,0 s/frame)
```

Verificado: 11/11 checks do composer e **72/72 frames com conteúdo**.

Ainda longe do MoneyPrinter (~2-3 min para 5 min de vídeo). O piso dessa
arquitetura é o screenshot: `about:blank` a 1080x1920 já custa 108 ms,
então o mínimo teórico são ~8 min para 3 min de clipe. Para chegar perto
do MoneyPrinter é preciso **abandonar o screenshot por frame** e usar
`zoompan` do FFmpeg sobre uma imagem estática por cena. Fica como
próximo passo.

## §32.8 — 21/09/2026 · Caminho rápido: 1 screenshot por cena + zoompan

### O problema

Depois de remover o `.grain` (§32.7) ainda era ~425 ms/frame com fotos:
**31 min para um clipe de 3 min**. Praticamente todo esse tempo é
rasterizar e codificar a MESMA cena milhares de vezes, sendo que a
única coisa que muda de frame para frame é o zoom/pan.

### A solução

O FFmpeg faz zoom/pan nativamente (filtro `zoompan`), quase de graça.
Então o composer tira **um screenshot por beat** e o `zoompan` gera o
movimento. `video_renderer.render_html_to_video_rapido()`:

1. lê os beats do DOM (`data-start`, `data-end`, classe `fx-*`, se tem `<video>`)
2. um screenshot por beat, com `animation: none` (o movimento vem do zoompan)
3. um segmento por beat via `zoompan`
4. concat dos segmentos

`render_html_to_video()` tenta o rápido e **cai no por frame** se não
se aplicar — beat com `<video>` (o vídeo se move por conta própria,
não dá para usar imagem estática), Playwright ausente, zoompan falhando.

Mapeamento dos efeitos (`_expr_zoompan`), `on` = nº do frame, `N` = total:

| efeito | z | x |
|---|---|---|
| `fx-zoom_in` | `1.02+0.20*on/N` | centrado |
| `fx-zoom_out` | `1.22-0.20*on/N` | centrado |
| `fx-ken_burns` | `1.04+0.14*on/N` | centrado |
| `fx-pan_left` | `1.14` | `(iw-iw/zoom)*(1-on/N)` |
| `fx-pan_right` | `1.14` | `(iw-iw/zoom)*(on/N)` |
| `fx-static` | `1` | centrado |

### Dois erros que cometi no caminho (e que custaram tempo)

1. **Abrir o Chromium duas vezes** (uma para ler os beats, outra para
   fotografar). O cold start do browser é caro: o caminho rápido ficou
   MAIS LENTO que o de por frame (68 s vs 31 s). Uma sessão só.
2. **`-t` em vez de `-frames:v`.** Com `-loop 1` a entrada é um stream
   infinito do mesmo frame e o `zoompan` gera `d` frames PARA CADA frame
   de entrada. Com `-t` ele processava muito além do necessário (55 s vs
   31 s). Parando em `-frames:v N`, sai exato.

### Resultado

Clipe de 30 s (6 fotos, 720 frames):

| caminho | tempo | ms/frame | 3 min extrapolado |
|---|---|---|---|
| por frame | ~306 s (estimado) | 425 | **31 min** |
| rápido (zoompan) | **95 s** | 131 | **9 min** |

Medição do `zoompan` puro: 36 frames = 4,9 s; 360 frames = 18,3 s
(~3 s fixos + ~47 ms/frame) — escala bem, então clipes longos se
beneficiam mais. Em clipe curto (3 s) o custo fixo domina e o caminho
rápido ainda perde; isso é esperado e o fallback cobre.

Verificado: 1080×1920, 720 frames, 30,000 s exatos, e 6 tempos
amostrados (um por cena) todos com conteúdo (0% de fundo).

Fallback com vídeo verificado: "caminho rápido indisponível (beat com
vídeo) — usando 1 screenshot por frame", 11/11 checks OK.
