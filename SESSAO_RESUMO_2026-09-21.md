# MusicClipStudio — Resumo da Sessão (2026-09-21)

## O que foi investigado e corrigido

### 1. Performance — Bug de geração lenta (5min para 3s de vídeo)

**Causa identificada:** O `wait_for_function` no `video_renderer.py` esperava por `readyState >= 3` de vídeos 4K do Pexels com timeout de 20s. Vídeos 4K nunca alcançam esse estado em tempo hábil no Chromium, então o `wait_for_function` timeoutava e o código continuava, mas o overhead de 20s por renderização explodia o tempo total.

**Correção aplicada (`scene_engine/renderers/video_renderer.py`):**
- `timeout=20000` → `timeout=2000` na chamada do `wait_for_function` (linha 103)
- Adicionado comentário explicativo sobre o motivo

**Otimização CAPTURE_SCALE (já existia no código, confirmada via medição):**
- `VideoRenderer.CAPTURE_SCALE = 0.5` — captura em 540×960 (metade da resolução final)
- FFmpeg faz upscale via `scale=1080:1920:flags=lanczos` no `images_to_video()`
- Ganho medido: ~0.46x (1.2x no HTML simples, mais no HTML real com muitas camadas)

**Resultado esperado:**
- 720 frames (30s áudio, 24fps): ~1.6min (antes ~2.15min só no Chromium)
- + correção do timeout: ganho adicional ~20s por render

### 2. Limpeza de lixo — 3.7GB recuperados

**Local:** `gerador_clipes_musicais/output/_temp/`
**O que tinha:** 4361 frames PNG/JPG de renders antigos (antes e depois da correção de 21/09/2026) em 10 pastas `_temp_frames*`
**Ação:** Apagados todos os PNG/JPG, mantidos 27 HTMLs
**Resultado:** 3.7GB → ~500KB

### 3. Segurança — API keys no config.py

**Problema:** 7 chaves de API hardcoded no `config.py`:
- Pexels, Pixabay, Unsplash, NASA, Coverr, Giphy, Openverse

**Ação pendente:** Extrair para env vars com fallback para os valores atuais (para não quebrar dev local). O usuário indicou que cada um que usar coloca a sua própria — então o ideal é ler de `os.getenv()` com default vazio e deixar o usuário configurar.

### 4. .gitignore faltando na raiz

**Ação pendente:** Criar `.gitignore` na raiz ignorando `__pycache__/`, `*.pyc`, `.env`, `output/clipes/`, `gerador_clipes_musicais/output/_temp/`, etc.

---

## Estado atual do MusicClipStudio

### Componentes funcionais

| Componente | Status | Observação |
|---|---|---|
| Backend (uvicorn, porta 8300) | ✅ Online | `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8300` |
| Frontend (npx next dev, porta 3100) | ✅ Online | `cd musicclipstudio-landing && npx next dev --hostname 127.0.0.1 --port 3100` |
| Engine de geração (engine.py) | ✅ Funcional | Pipeline completo: beats → HTML → vídeo → áudio + legendas |
| Database (database.py) | ✅ Funcional | Busca multi-provedor com 7 chaves |
| Scene engine (render HTML→vídeo) | ✅ Funcional | Playwright + FFmpeg |
| Configuração (config.py) | ⚠️ Requer ajuste | Chaves hardcoded — ver seguridad |

### Como subir (comandos diretos que funcionam)

```bash
# Backend (janela 1)
cd D:\dev-projetos\MusicClipStudio
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8300

# Frontend (janela 2)
cd D:\dev-projetos\MusicClipStudio\musicclipstudio-landing
npx next dev --hostname 127.0.0.1 --port 3100
```

Rota do studio: `http://127.0.0.1:3100/studio`

### O que NÃO foi feito (pendências)

1. **Revisão de segurança completa** — extrair API keys para env vars + criar `.gitignore`
2. **Banco de dados de login/senhas** — tabela `users` + `usage` no SQLite
3. **Controle freemium/premium** — limite de gerações por plano
4. **Testar a correção de performance com vídeo 4K real** — teste feito com demo.html, confirmação com vídeo Pexels real pendente

---

## Arquivos modificados nesta sessão

- `scene_engine/renderers/video_renderer.py` — timeout do `wait_for_function` de 20s → 2s

## Arquivos que EXISTS EM VIROLUÇÃO (read-only, não modificados)

- `config.py` — com 7 API keys hardcoded (segurança pendente)
- `engine.py` — motor principal
- `gerador.py` — moviepy fallback
- `gui_clipes.py` — GUI CustomTkinter (desktop, não utilizado no fluxo web)
- `backend/app/main.py` — FastAPI backend
- `backend/app/projects_store.py` — SQLite de projetos
- `musicclipstudio-landing/` — Next.js frontend
- `database.py` — busca de mídia stock
- `batcher.py` — geração em lote

---

## Notas para sessão futura

1. **Performance:** a correção do timeout parece ser o principal ganho. Confirmação com vídeo 4K real recomendada. A otimização CAPTURE_SCALE já estava no código e foi confirmada via medição.

2. **Segurança:** prioridade alta — as 7 chaves estão expostas. O usuário quer que cada um coloque a sua, então extrair para `os.getenv()` com fallback vazio é o caminho.

3. **Freemium/Premium:** o `projects_store.py` já usa SQLite. Criar `users_store.py` com tabelas `users` e `usage` seria o próximo passo lógico. O backend FastAPI já tem estrutura de endpoints para estender.

4. **Processos:** há muitos processos orphaned (node.exe e python.exe) na máquina. Recomenda-se limpar periodicamente ou usar o script de parada (`PARAR_MusicClipStudio.bat` se existir) para não acumular.

---

## Atualização 22/09 — Vídeo todo azul CORRIGIDO

**Causa:** o frontend mandava pro render a `url_preview` do Pexels, que era a **PÁGINA** do site
(pexels.com/photo/...), não o arquivo. `background-image` com página não desenha: a camada ficava
transparente e aparecia o fundo do tema VOX (`#1A1A2E`) = clipe 100% azul, sem mídia nenhuma.
As mudanças de performance de 21/09 NÃO foram a causa (estavam certas).

**Correções (3):**
1. `page.tsx` (~1308): mídia escolhida agora usa `url_full || video_url || url_thumbnail` (arquivo real).
2. `backend/app/main.py` `/api/midia/buscar`: `url_preview` agora aponta pro arquivo (`download_url or url`).
3. `backend/app/main.py` job de geração: GUARDA que rejeita payload com URL que não seja arquivo de
   mídia direto (.jpg/.png/.mp4/...), com erro claro — nunca mais MP4 azul silencioso.

**Provas:** busca real devolve 6/6 arquivos diretos (images.pexels.com/*.jpeg, videos.pexels.com/*.mp4);
payload com página → job falha com mensagem clara; job com 2 fotos reais → MP4 gerado com a mídia
visível (frames 10/40 com variância ~5.100, não fundo plano). Saída: output/clipes/649f0df6d8cb_legendado.mp4.
Backend 8300 reiniciado com o código novo. Frontend Next (dev) pega o TSX no reload.

## Atualização 22/09 (2) — Filtros de busca na etapa 05
- **Tipo de mídia na BUSCA**: seletor Ambos / Só fotos / Só vídeos na barra de busca. Backend: `SearchMediaPayload.apenas_fotos/apenas_videos` → `db.pesquisar()` (que já filtrava por API, mas a tela nunca expunha).
- **Orientação compatível na BUSCA**: checkbox "Só na orientação da saída" — formato 9/16 traz retrato, 16/9 traz paisagem (mídia sem dimensão sempre passa). Complementa o selo "corta" e o filtro de exibição que já existiam.
- Ambos os filtros valem pra busca manual, por cena da letra e "buscar tudo".
- PROVA: busca `city night` com apenas_fotos → 8/8 photo; apenas_videos → 8/8 video. tsc --noEmit limpo; backend 8300 reiniciado.
- Sugestão de formatos aceita pelo dono: manter 9/16 e 16/9 como padrão; 1/1, 3/4 e 4/3 já suportados pelo motor caso algum dia precise — nada novo adicionado.

## Atualização 22/09 (4) — Correção do filtro de orientação
- **Filtro de orientação agora é da ENTRADA**, escolhido na mão na busca (Qualquer / Retrato / Paisagem / Quadrado) — não herdava mais da saída (que só se decide na geração). Formato de saída continua no mesmo lugar (etapa 06/painel).

## Atualização 22/09 (5) — Estilo da legenda (etapa 03)
- **UI**: painel "estilo da legenda" na etapa 03 — cor do texto, cor do contorno, fonte (Montserrat/Inter/Arial/Verdana/Georgia/Courier), tamanho (24–96px), contorno (0–6px), posição (baixo/centro/topo), negrito + pré-visualização WYSIWYG + restaurar padrão.
- **Persistência**: `legendaEstilo` no StudioProjectState (salvo no projeto via salvarProjeto/ProjetoSalvo).
- **Pipeline**: payload `project.legenda_estilo` → `engine.generate(legenda_estilo=...)` → `Compositor.add_subtitles(estilo=...)` → `_estilo_para_force_style()` converte #RRGGBB → &HBBGGRR (ASS), posição via Alignment (2/5/8) e MarginV.
- **PROVA REAL**: job com #FFD700, Verdana 72, negrito, contorno 4, centro → MP4 gerado com a legenda amarela gigante queimada NO CENTRO (16,3 0e pixels amarelos na faixa central; screenshot anexado em _req_tmp/_prova_legenda.png).
- tsc --noEmit limpo; backend 8300 reiniciado.

## Atualização 22/09 (6) — Sincronia de legendas com tempos reais (Whisper)
- `subtitle_lines` (payload) agora é LIDO: backend converte em `legendas` → `engine._srt_de_legendas()` gera o SRT com os tempos do Whisper (etapa 03) em vez de dividir a letra em blocos iguais. Sem transcrição, cai no comportamento antigo.
- Frontend manda `subtitle_lines` do estado `legenda` (linhas com inicio/fim/texto).
- Teste unitário do helper OK (ordenação, descarte de inválidas); tsc limpo; backend reiniciado.

## Atualização 22/09 (7) — Itens restantes da legenda
- **Preview fidedigno**: LivePreviewPanel agora usa o estilo escolhido na etapa 03 (cor, fonte, tamanho, contorno, negrito) e respeita a posição (topo/centro/baixo). Antes era estilo fixo.
- **Fontes garantidas**: Montserrat e Inter baixadas pra fonts/ do projeto (OFL, uso comercial ok). Compositor injeta FontFile= no force_style quando a fonte não é do sistema — não depende mais de fontes instaladas no Windows. Prova: render de teste com Montserrat desenhou texto (4.827 px brancos).
- **Botão .SRT funcional**: exporta o SRT com tempos reais da transcrição (ou distribuído pela duração da música) direto do navegador.
- **Revisar ortografia funcional**: limpa espaços duplicados, pontuação colada e minúscula pós-frase; informa quantas linhas ajustou.
- tsc --noEmit limpo. Jobs persistidos: NÃO feito (dono dispensou).
