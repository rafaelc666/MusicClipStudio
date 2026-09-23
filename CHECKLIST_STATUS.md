# Checklist de Status — MusicClipStudio

> Atualizado: 2026-09-23 (sessão Manjaro/Linux)

## Legenda

- [x] **Pronto** — pode testar
- [~] **Em andamento** — funciona mas precisa de refinamento
- [ ] **Pendente** — não iniciado ou bloqueado
- [!] **Com bug conhecido** — funciona parcialmente

---

## 0. VERSÃO WEB (backend FastAPI 8300 + frontend Next 3100)

> Estado de 2026-09-23. Ambiente Linux (Manjaro) reconfigurado e validado.

### Ambiente & Infra

| # | Item | Status | Nota |
|---|------|--------|------|
| 0.1 | Stack sobe no Manjaro (`./RUN_WEB.sh` / `./PARAR_WEB.sh`) | [x] | Backend 8300 + frontend 3100 desanexados (duplo-fork) |
| 0.2 | venv Python 3.14 completo (fastapi, moviepy, playwright, whisper, librosa, pytest) | [x] | 155 testes passando, 6 skipped |
| 0.3 | Frontend com binários Linux (Next 16 + SWC) | [x] | node_modules reinstalado; tsc limpo |
| 0.4 | Chromium do Playwright + render HTML→MP4 h264 | [x] | Comprovado com render real 540×960 |
| 0.5 | Chaves de API fora do código (`.env` + `config.py` lê env) | [x] | `.env.example` para novos usuários; `.gitignore` completo |
| 0.6 | Atalho na Área de Trabalho (abre Studio, sobe stack se preciso) | [x] | `MusicClipStudio.desktop` validado |

### Wizard Web — Fluxo

| # | Item | Status | Nota |
|---|------|--------|------|
| 0.7 | Etapa 02: cartão ÚNICO do áudio (player + Trocar + Excluir) | [x] | Antes: 2 cartões duplicados + "Continuar" redundante |
| 0.8 | Etapa 02: exclusão definitiva do áudio | [x] | Arquivo excluído não volta no banner "reanexar" |
| 0.9 | Etapa 02: caixa de bancos de música gratuitos | [x] | YouTube Audio Library, FMA, Pixabay, Incompetech, Chosic |
| 0.10 | Etapa 04: "Gerar cenas da letra com IA" (real, lê a letra) | [x] | Backend `/api/imagens/gerar-prompts` |
| 0.11 | Etapa 04: TEMA VISUAL LIVRE (campo de texto) | [x] | Qualifica todas as queries ("chuva lenta" etc.) |
| 0.12 | Etapa 05: busca ACUMULATIVA com dedup | [x] | Antes: "Buscar tudo" repetia a auto-busca e nada mudava |
| 0.13 | Etapa 05: temas rápidos (Chuva, Natureza, Dança, Cidade…) | [x] | Um clique = multi-busca e acumula |
| 0.14 | Etapa 05: chips de cenas com dedup ("termo ×N") | [x] | 112 beats não viram mais 100 chips repetidos |
| 0.15 | Etapa 05: "Ir para gerar" duplicado removido | [x] | Rodapé do wizard é a navegação única |
| 0.16 | Preview lateral rotulado "Ilustrativo — não é o vídeo final" | [x] | Selo DEMO; animação mantida |
| 0.17 | Render com legendas (queima ASS/force_style) | [x] | Bug `self` em @staticmethod corrigido (23/09) |
| 0.18 | Limpeza dos vídeos intermediários após gerar | [x] | Só o final fica em `output/clipes/` |

### Agente de Cenas (qualidade dos prompts)

| # | Item | Status | Nota |
|---|------|--------|------|
| 0.19 | Tema musical detectado da letra alimenta as queries | [x] | Antes: 4 queries fixas do mood ("dark city" ×112) |
| 0.20 | Tema Gospel/Worship criado (faltava) | [x] | Cruz, luz, adoração; estetica "golden light" |
| 0.21 | API devolve `tema`/`tema_nome` para a UI | [x] | Toast mostra o tema detectado |
| 0.22 | Estética por gênero nos demais temas (rock, jazz…) | [ ] | Campo `estetica` só no gospel por enquanto |

### Login & Chaves por Usuário

| # | Item | Status | Nota |
|---|------|--------|------|
| 0.23 | `auth_store.py` (contas PBKDF2 + sessões + chaves Fernet) | [x] | Banco `output/usuarios.db` |
| 0.24 | Endpoints `/api/auth/*` e `/api/provedores/*` no main.py | [x] | Registrar/login/logout/eu + chaves/testar/habilitar — testados via HTTP |
| 0.25 | Tela de login + sessão no header (usuário + Sair) | [x] | LoginGate no shell; F5 mantém sessão; testado no navegador |
| 0.26 | Dialog "Configurar provedores" | [x] | 7 bancos fixos + bancos PRÓPRIOS ILIMITADOS (adicionar/remover/renomear, escolhe a API de busca; chave testada contra a API real) |
| 0.26b | Busca da etapa 05 usa as chaves do usuário logado | [x] | `load_config()` + `dataclasses.replace` por request; sem login cai no .env |
| 0.27 | Freemium/planos | [ ] | **Decisão do usuário: só FREE por enquanto** |
| 0.27b | Intro de abertura (splash animado em código) | [x] | Equalizer neon + wordmark; 1× por sessão, clique pula; validada no navegador |

### Pendências conhecidas

| # | Item | Status | Nota |
|---|------|--------|------|
| 0.28 | Bugs de tela reportados pelo usuário | [!] | "Vou ajustar isso outra hora" — aguardando descrição/prints |
| 0.29 | Dicionário pt-BR embutido (sem LibreOffice) | [ ] | Copiar `_req_tmp/teste_spylls/` → `assets/dict/` |
| 0.30 | Teste de performance com vídeo 4K real | [ ] | Do handoff 18/09 |
| 0.31 | BPM 184 não normalizado | [ ] | Edge case documentado, não crítico |

---

## 1. Interface Gráfica (GUI)

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 1.1 | Janela abre sem erro | [x] | `python -m pytest tests/test_clipes.py -q` (129 passando) |
| 1.2 | Navegação entre 6 etapas | [x] | Clicar nos passos na sidebar (01..06) |
| 1.3 | Sidebar redimensionada (196px) | [x] | Visual — labels legíveis, item ativo destacado |
| 1.4 | Indicador de passos (72px, não cortado) | [x] | Visual — subtítulo "Em edição" visível |
| 1.5 | Painel direito com scroll | [x] | Scrollar até "Transição entre cenas" — não corta |
| 1.6 | Placeholder na caixa de letra | [x] | Clicar no campo — placeholder some; sair vazio — volta |
| 1.7 | Botão "Carregar arquivo" (.txt) | [x] | Selecionar arquivo .txt — texto aparece no campo |
| 1.8 | Resumo dinâmico na etapa Gerar | [x] | Preencher letra + selecionar mídia → resumo atualiza |

## 2. Correção Ortográfica (Etapa 02)

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 2.1 | Transcrição Whisper → legenda | [x] | Botão "Transcrever do áudio" (precisa de áudio) |
| 2.2 | Legenda editável (tempos + texto) | [x] | Clicar em qualquer campo de tempo/texto e editar |
| 2.3 | **Revisar ortografia** | [x] | Botão "Revisar ortografia" — detecta erros do Whisper |
| 2.4 | Sugestões clicáveis por palavra | [x] | Clicar em `voz` para corrigir `vois` |
| 2.5 | "Aplicar as óbvias" (auto-correção) | [x] | Botão aplica `razão`, `nascer` sem ambiguidade |
| 2.6 | "Ignorar" palavra | [x] | Botão "ignorar" — palavra não reaparece na próxima revisão |
| 2.7 | Legenda = fonte da verdade | [x] | Corrigir na etapa 02 → busca (etapa 05) usa a correção |
| 2.8 | Aviso de divergência etapa 01 × 02 | [x] | Editar etapa 01 depois da legenda → aviso laranja aparece |
| 2.9 | "Usar a legenda na etapa 01" | [x] | Botão copia legenda revisada para a caixa da etapa 01 |
| 2.10 | Proteção da transcrição (tempos reais) | [x] | Editar etapa 01 NÃO apaga a legenda com tempos do Whisper |

## 3. Cálculo de Clipes pela Música (Etapa 05)

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 3.1 | Modo "Pela letra (frases)" | [x] | Selecionar no menu — corta nas quebras da letra |
| 3.2 | Modo "Pela batida da música" | [x] | Precisa de áudio + librosa — detecta BPM |
| 3.3 | Modo "Duração fixa" | [x] | Todos os clipes com o mesmo tempo |
| 3.4 | Previsão de quantos clipes | [x] | Painel direito mostra "N clipes · modo · cobre Xs de Ys" |
| 3.5 | Aviso de mídias faltando | [x] | Selecionar poucas mídias → "faltam N mídia(s)" |
| 3.6 | Efeito por natureza da mídia | [x] | Vídeo = corte direto; imagem = zoom/pan conforme energia |
| 3.7 | Descrição musical na busca | [x] | Preencher "tribal com tambores" → aparece nos search terms |

## 4. Busca de Mídia (Etapa 04/05)

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 4.1 | Busca automática por termos da letra | [x] | Botão "Buscar mídia automática" — gera terms da letra |
| 4.2 | Busca manual por query | [x] | Digitar "nature sunset" + Enter |
| 4.3 | Resultados do Pexels | [x] | Precisa de API key configurada em config_ia.json |
| 4.4 | Resultados do Pixabay | [x] | Precisa de API key configurada |
| 4.5 | Seleção de mídia (clique) | [x] | Clicar no card — borda verde + contador atualiza |
| 4.6 | Download de mídia selecionada | [x] | Botão "Gerar" → baixa e renderiza |
| 4.7 | **Busca temática (sem letra)** | [x] | Digitar "mantra tibetano" ou "432Hz" na descrição → busca por tema |
| 4.8 | **Vídeos aparecem na busca** | [x] | Buscar → status mostra "N vídeo, N foto". Antes: sempre 0 vídeo |
| 4.9 | **Termos curtos p/ API** | [x] | Log `[SEARCH]` mostra termos de 2-3 palavras, não frases longas |
| 4.10 | **Seletor Meio a meio / Mais vídeos / Mais fotos** | [x] | Segmento ao lado de "Buscar Automaticamente" |
| 4.11 | **Prompts de preenchimento quando falta mídia** | [x] | Busca com < 6 resultados → card laranja com prompts IMAGEM/VÍDEO |
| 4.12 | "Usar prompt" envia para o campo de IA | [x] | Clicar em "Usar prompt" → preenche o campo IA + pede "Gerar IA" |

## 5. Geração do Clipe (Etapa 06)

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 5.1 | Validação (letra + mídia + áudio) | [x] | Tentar gerar sem letra → aviso |
| 5.2 | Render com legendas | [x] | Gerar com legenda editada → texto aparece no vídeo |
| 5.3 | Render com efeitos por slot | [x] | Cada clipe com efeito próprio (zoom, pan, fade) |
| 5.4 | Render com transições | [x] | Menu "Transição entre cenas" |
| 5.5 | Progresso em tempo real | [x] | Barra de progresso + log ao vivo |
| 5.6 | Salvamento automático (timestamp) | [x] | Vídeo salvo em output/clipe_YYYYMMDD_HHMMSS.mp4 |

## 6. Áudio / Trilha (Etapa 03)

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 6.1 | Geração ACE-Step | [x] | Botão "Gerar trilha" — demora ~1-2 min |
| 6.2 | Upload de áudio próprio | [x] | Botão de upload na etapa 03 |
| 6.3 | Duração ajustável (10-120s) | [x] | Slider na etapa 03 |
| 6.4 | **TTS / Narração** | [ ] | **PROIBIDO — nunca tocar** |

## 7. Configurações

| # | Funcionalidade | Status | Como Testar |
|---|----------------|--------|-------------|
| 7.1 | API keys (Pexels, Pixabay, Gemini) | [x] | Botão "APIs" na topbar → diálogo de config |
| 7.2 | Tema visual (escuro) | [x] | Visual — tema Elton Studio V2 aplicado |
| 7.3 | Diretório de saída | [x] | Botão "..." ao lado do campo de saída |

---

## Problemas Conhecidos / Próximos Passos

### DIAGNÓSTICO: por que a busca por API rendia tão mal (2026-09-17)

A pergunta era: *"na busca manual não há problemas... mas por API não entendo
por que os resultados são tão ruins"*. A causa eram **três defeitos somados**,
todos encontrados com medição na API real (não por inspeção):

**1. O parâmetro `apenas_videos` era IGNORADO (bug grave).**
Em `_buscar_pexels`/`_buscar_pixabay`, a condição era
`buscar_videos = not apenas_fotos or (apenas_fotos and apenas_videos)`.
Como `buscar_fotos` era True, a segunda metade nunca importava — o
`apenas_videos` era descartado. Resultado: **nenhuma busca retornava vídeo.**

> Medido: `_buscar_pexels("rain", apenas_videos=True)` → 15 fotos, **0 vídeos**.
> O endpoint do Pexels devolve 7.612 vídeos para "rain" — o problema era nosso.

**2. O corte `[:max_results]` descartava TODOS os vídeos.**
As fotos são coletadas antes dos vídeos e concatenadas na ordem crua. Com
cota de 15 e 15 fotos + 15 vídeos, as fotos enchiam a cota e o corte
eliminava os 15 vídeos — mesmo depois de corrigir o item 1.

> Medido: `total=30` (15+15) mas `results=15`, todos fotos.
> Correção: `_intercalar_tipos()` alterna vídeo/foto/vídeo/foto antes do corte.

**3. As frases de busca eram longas demais para a API.**
A camada emocional mandava frases de 5 palavras
(`"empty apartment at night one lamp"`). Pexels/Pixabay indexam conceitos
de 2-3 palavras e fazem match por palavra isolada, então a API caía em
match parcial nas palavras genéricas ("person", "empty", "night") — **essa
é a origem das "imagens totalmente fora de contexto"**.

> Comparativo: `"walk"`/`"night city"` (humano) → resultados relevantes;
> frase de 5 palavras → match difuso e irrelevante.
> Correção: `encurtador_busca.termo_curto()` reduz a cena ao núcleo visual
> (`"empty apartment at night one lamp"` → `"apartment night lamp"`),
> mantendo a frase completa como base de prompt de IA.

**Resultado medido (letra real, 5 termos):**

| Modo | Antes | Depois |
|------|-------|--------|
| Meio a meio | 100 fotos, **0 vídeos** | 50 fotos, **50 vídeos** |
| Mais vídeos | — | **100 vídeos** |
| Mais fotos | — | **100 fotos** |

### Prioridade ALTA (usuário pediu)

1. **Busca temática para músicas sem letra** [x]
   - Módulo `temas_musicais.py` com 11 temas: classica, mantra, frequencia,
     arabe, meditacao, eletronica, jazz, rock, hiphop, country, infantil
   - Cada tema tem 10-14 termos de busca em inglês, testados para retornar
     resultados relevantes no Pexels/Pixabay
   - Temas que ignoram letra (mantra, frequencia, arabe): a busca vai só
     pelos termos do tema, não tenta extrair palavras da letra
   - Temas que combinam (jazz, rock, classica): termos do tema + letra
   - Detectado automaticamente na descrição da música (campo "MÚSICA")
   - Exemplos clicáveis na GUI: "mantra tibetano", "432Hz", "árabe com oud"

2. **Mais vídeos, menos imagens fora de contexto** [x]
   - Os 3 defeitos acima explicam 100% da reclamação e estão corrigidos
   - `encurtador_busca.py` — frases longas viram termos de 2-3 palavras
   - `_intercalar_tipos()` — garante que vídeo sobreviva ao corte
   - Flags de tipo de mídia corrigidas nos dois provedores
   - Novo seletor **Meio a meio / Mais vídeos / Mais fotos** na GUI

3. **Preenchimento com prompts quando falta mídia** [x]
   - `preenchedor_prompts.py` — gera prompts de IMAGEM e de VÍDEO a partir
     do tema (se houver) ou das cenas emocionais
   - Dispara quando a busca rende < 6 itens (`MINIMO_MIDIA_SUFICIENTE`)
   - Card laranja na galeria lista os prompts, alternando imagem/vídeo
   - "Usar prompt" carrega o texto no campo de IA, pronto para "Gerar IA"
   - Os prompts incluem movimento de câmera (push in, pan, drone) para vídeo
     e qualidade (cinematic still, 35mm) para imagem


### Prioridade MÉDIA

3. **Dicionário pt-BR embutido** [ ]
   - Hoje depende do LibreOffice estar instalado
   - Já existe cópia em `_req_tmp/teste_spylls/`
   - **Status:** Pendente — copiar para `assets/dict/` e ajustar caminho

4. **BPM 184 não é normalizado** [ ]
   - `_normalizar_bpm(184)` não faz nada (já está dentro da faixa 50-200)
   - É um edge case documentado, não crítico
   - **Status:** Documentado, não prioritário

### Prioridade BAIXA

5. **Mais templates de vídeo** [ ]
   - Hoje só existe `vox_editorial.html`
   - **Status:** Não solicitado pelo usuário

---

## Como Testar o Que Está Pronto

### Teste rápido (2 minutos)
```bash
cd D:\dev-projetos\MusicClipStudio
python -m pytest tests/test_clipes.py -q
```
→ Esperado: `129 passed`

### Teste da GUI (5 minutos)
```bash
python _req_tmp/testar_gui_abre.py
python _req_tmp/testar_ortografia_gui.py
```
→ Esperado: todas as conferências passam

### Teste end-to-end (manual)
1. Abrir o programa: `python -m MusicClipStudio.gui_clipes`
2. Etapa 01: colar uma letra com erros (ex: "eu ainda escuto a tua vois")
3. Etapa 02: clicar "Revisar ortografia" → ver sugestões → clicar em `voz`
4. Etapa 03: gerar trilha ou fazer upload de áudio
5. Etapa 04/05: clicar "Buscar mídia automática" → selecionar resultados
6. Etapa 06: clicar "Gerar" → acompanhar progresso

---

## Registro de Mudanças Recentes

| Data | O que mudou |
|------|-------------|
| 2026-09-17 | **Corretor ortográfico** — detecta erros do Whisper, sugere correções, aplica na legenda e na busca |
| 2026-09-17 | **Legenda = fonte da verdade** — busca usa a legenda revisada, não a etapa 01 |
| 2026-09-17 | **Aviso de divergência** — avisa quando etapa 01 e legenda não batem |
| 2026-09-17 | **Busca temática** — 11 temas (mantra, 432Hz, árabe, clássica, etc.) com termos em inglês |
| 2026-09-17 | **Cálculo de clipes pela música** — plano com durações por slot, efeitos por slot, sem buracos |
| 2026-09-17 | **Descrição musical na busca** — "tribal com tambores" vira termo de busca |
| 2026-09-17 | **Interface redesenhada** — sidebar 196px, indicador 72px, placeholder, resumo dinâmico |
