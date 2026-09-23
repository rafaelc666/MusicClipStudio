# Relatório de Inventário — `MusicClipStudio/gui_clipes.py`

> **Escopo:** análise de leitura apenas. Nenhum arquivo do projeto foi modificado.
> **Data:** 2026-09-17
> **Alvo:** `D:\dev-projetos\MusicClipStudio\gui_clipes.py`
> **Linhas reais:** 1632 (não 1650) · **Tamanho:** 63.340 bytes
> **Arquivos correlatos:** `theme.py` (101 linhas), `ui_config.py` (362 linhas), `tests/test_clipes.py` (266 linhas)

---

## 0. TL;DR — o que você NÃO pode quebrar

1. **`self.btn_gerar` é criado DUAS VEZES** (`gui_clipes.py:116` e `gui_clipes.py:762`). A segunda atribuição sobrescreve a primeira. Depois de `_construir_ui()`, apenas o botão da etapa "Gerar" está acessível. `_gerar_clip` (`:1560`, `:1581`, `:1596`) atualiza **esse** botão — o da top bar fica órfão e nunca muda de estado.
2. **`StockMedia` é usado em `:1525` mas NUNCA é importado.** O módulo importa apenas `ClipConfig, load_config, save_config` de `config` e `StockDatabase` de `database` (`:22-25`). `_adicionar_arquivo_midia` levanta `NameError` ao adicionar qualquer arquivo. **Não é uma regressão de UI — é um bug pré-existente.** Não "conserte" trocando o nome sem verificar a origem do símbolo.
3. **`self._frames_passos = {}` é reatribuído em `_construir_conteudo_principal` (`:192`)** depois de já ter sido inicializado no `__init__` (`:50`). A ordem `_construir_ui → _construir_top_bar → _construir_sidebar_navegacao → _construir_conteudo_principal → _construir_painel_direito` é obrigatória: a sidebar chama `_mudar_passo("letra")` em `:177`, que já depende de `self._frames_passos` e `self._conteudo_passos` existirem.
4. **Acoplamento oculto de escrita cruzada:** `_criar_frame_audio` **insere dados** em `self.txt_music_prompt` (`:343`) e lê `self._config` — construtor de frame não é puramente visual.
5. **`_mostrar_passo` usa `frame.pack(in_=...)` (`:1080`)** enquanto `_exibir_resultados_automaticos`/`_exibir_resultados` usam `grid`/`pack` misturados. Se você trocar o gerenciador de geometria de um frame de etapa, precisa trocar também o `pack_forget()`/`pack(in_=)`.
6. **`_selecionar_midia` (`:1486`) compara `sel.id` apenas para `StockMedia`** — itens gerados por IA são dicts (`:1196`), que não têm `.id`. A mistura de tipos (dict vs StockMedia) na MESMA lista `self._midia_selecionada` é uma armadilha do modelo de dados, não da UI.
7. **Os testes NÃO importam o GUI.** (`grep` em `tests/` por `gui_clipes|GuiClipes|theme|Tema|ui_config` → zero resultados.) Renomear widgets é seguro para os testes, mas verifique a seção 6 para os contratos reais.

---

## 1. Inventário de widgets por etapa

Legenda: `[REFS]` = guardado em `self.*` e atualizado por outro método (crítico). `[LOCAL]` = criado e esquecido.

### 1.1 `_construir_top_bar()` — linhas 75–123

| Linha | Widget | Texto | Var | Geometria | command | Refs |
|---|---|---|---|---|---|---|
| 76 | `CTkFrame` | — | — | `grid(row=0, col=0, columnspan=3, sticky="ew")`, `grid_propagate(False)`, `height=52`, `fg=Tema.PAINEL` | — | `[LOCAL]` |
| 78 | `topbar.grid_columnconfigure(2, weight=1)` | — | — | — | — | — |
| 82 | `CTkFrame` logo_frame | — | — | `grid(row=0, col=0, padx=(16,8), pady=10, sticky="w")` | — | `[LOCAL]` |
| 85 | `CTkLabel` | `">_"` | — | `pack(side="left")` · color `Tema.NAV_ACTIVE` | — | `[LOCAL]` |
| 91 | `CTkLabel` | `" CLIPES MUSICAIS"` | — | `pack(side="left", padx=(4,0))` | — | `[LOCAL]` |
| 98 | `CTkLabel` | `"Novo clipe musical"` | — | `grid(row=0, col=1, padx=16, pady=10, sticky="w")` | — | `[LOCAL]` |
| 105 | `CTkFrame` btn_frame | — | — | `grid(row=0, col=2, padx=16, pady=10, sticky="e")` | — | `[LOCAL]` |
| 108 | `CTkButton` | `"APIs"` | — | `pack(side="left", padx=(0,8))`, w=80 h=30 | **`self._abrir_config_apis`** | `[LOCAL]` |
| **116** | **`CTkButton self.btn_gerar`** | `"Gerar"` | — | `pack(side="left")`, w=90 h=30 | **`self._gerar_clip`** | **`[REFS]` ⚠ sobrescrito em :762** |

> ⚠️ `self.btn_gerar` da linha 116 é **perdido**. Qualquer código que espere dois botões "Gerar" sincronizados vai falhar.

### 1.2 `_construir_sidebar_navegacao()` — linhas 125–177

| Linha | Widget | Texto | Var | Geometria | command | Refs |
|---|---|---|---|---|---|---|
| 126 | `CTkFrame` sidebar | — | — | `grid(row=1, col=0, sticky="nsew")`, `grid_propagate(False)`, `width=60`, `fg=Tema.NAV_BG` | — | `[LOCAL]` |
| 133 | `CTkLabel` | `">_"` | — | `pack(pady=(16,20))` | — | `[LOCAL]` |
| 140 | `CTkLabel` | `"PASSOS"` | — | `pack(pady=(0,8))` | — | `[LOCAL]` |
| **155-161** | `CTkButton` ×5 (loop) | `Letra/Audio/Imagens/Mídia/Gerar` | — | `pack(pady=2, padx=5)`, w=50 h=36 | **`lambda k=key: self._mudar_passo(k)`** | **`self._nav_btns[key]` `[REFS]`** |
| 166 | `CTkLabel` espaçador | `""` | — | `pack(expand=True)` | — | `[LOCAL]` |
| 169 | `CTkButton` | `"Config"` | — | `pack(pady=(0,16))`, w=40 h=40 | **`self._abrir_config_apis`** | `[LOCAL]` |
| **177** | **chamada direta** | — | — | `self._mudar_passo("letra")` | — | **ordem crítica** |

**`nav_items` bidirecional (`:146-152`):** as `key` aqui (`letra, audio, imagens, midia, gerar`) devem casar **exatamente** com as chaves de `self._frames_passos`, `self._passo_labels`, `self._nav_btns` e com `passos_ordem` em `_mudar_passo` (`:1050`). Renomear em um só lugar quebra 4 estruturas.

### 1.3 `_construir_conteudo_principal()` — linhas 179–199

| Linha | Ação | Detalhe |
|---|---|---|
| 180 | `self._conteudo_frame = CTkFrame` | `fg=Tema.FUNDO`, `grid(row=1, col=1, sticky="nsew")` |
| 183 | grid | `grid(row=1, col=1, sticky="nsew")` |
| 186 | chama `_construir_passos_indicator()` | antecede a criação dos frames |
| **189** | **`self._conteudo_passos = CTkFrame`** | `pack(fill="both", expand=True, padx=16, pady=(8,16))` — **container-pai de todos os 5 frames de etapa** |
| **192** | **`self._frames_passos = {}`** | ⚠ **reatribuição** (já existe em `:50`) |
| 193-197 | chama os 5 `_criar_frame_*` | **ordem fixa** letra→audio→imagens→midia→gerar |
| 199 | `self._mostrar_passo("letra")` | — |

### 1.4 `_construir_passos_indicator()` — linhas 201–245

| Linha | Widget | Texto | Geometria | Refs |
|---|---|---|---|---|
| 202 | `CTkFrame` indicator | — | `pack(fill="x")`, `pack_propagate(False)`, `height=48`, `fg=Tema.PAINEL` | `[LOCAL]` |
| 215 | `CTkFrame` frame (loop ×5) | — | `pack(side="left", padx=16, pady=8)` | `[LOCAL]` |
| 219 | `CTkLabel` icon_label | `f"{idx+1:02d}"` → `"01".."05"` | `pack(side="left", padx=(0,4))` | **`self._passo_labels[key]["icon"]` `[REFS]`** |
| 226 | `CTkFrame` text_frame | — | `pack(side="left")` | `[LOCAL]` |
| 229 | `CTkLabel` title | `Letra/Áudio/Imagens/Mídia/Gerar` | `pack(anchor="w")` | **`self._passo_labels[key]["title"]` `[REFS]`** |
| 236 | `CTkLabel` subtitle | `Em edição/Aguardando` | `pack(anchor="w")` | **`self._passo_labels[key]["subtitle"]` `[REFS]`** |

`passos` (`:206-212`) é uma **segunda cópia** da lista de chaves/labels/status. Está duplicada em relação a `nav_items` (`:146`) e `passos_ordem` (`:1050`) — três fontes de verdade.

### 1.5 `_criar_frame_letra()` — linhas 247–302

| Linha | Widget | Texto | Geometria | command |
|---|---|---|---|---|
| 248 | `CTkFrame` frame | — | `→ self._frames_passos["letra"]` | — |
| 251 | `CTkLabel` | `"ETAPA 01 · LETRA"` | `pack(anchor="w", pady=(0,4))` | — |
| 257 | `CTkLabel` | `"Letra da Música"` | `pack(anchor="w", pady=(0,4))` | — |
| 263 | `CTkLabel` | `"Cole ou digite a letra..."` | `pack(anchor="w", pady=(0,16))` | — |
| 270 | `CTkFrame` card | — | `pack(fill="both", expand=True)` | — |
| 273 | `CTkLabel` | `"TEXTO DA MÚSICA"` | `pack(anchor="w", padx=16, pady=(12,8))` | — |
| **279** | **`self.txt_letra`** `CTkTextbox` | vazio | `pack(fill="both", expand=True, padx=16, pady=(0,16))`, h=300 | **`[REFS]`** lido em `:1094-1095`, `:1211`, `:1235` |
| 287 | `CTkFrame` btn_frame | — | `pack(fill="x", padx=16, pady=(0,16))` | — |
| 290 | `CTkButton` | `"← Voltar"` | `pack(side="left")` w=100 h=32 | **`lambda: self._mudar_passo("imagens")`** ⚠ ver nota |
| 297 | `CTkButton` | `"Avançar →"` | `pack(side="right")` w=120 h=32 | **`lambda: self._mudar_passo("audio")`** |

> ⚠️ **"← Voltar" na etapa 1 aponta para "imagens"** (`:292`) — wrap-around intencional ou bug. Nenhum tratamento de borda em `_mudar_passo`.

### 1.6 `_criar_frame_audio()` — linhas 304–395

| Linha | Widget | Texto | Var | Geometria | command |
|---|---|---|---|---|---|
| 306 | `CTkFrame` | — | — | `→ self._frames_passos["audio"]` | — |
| 309/315/321 | `CTkLabel` ×3 | `"ETAPA 02 · ÁUDIO"` / `"Trilha Sonora"` / `"Configure e gere..."` | — | `pack(anchor="w")` | — |
| 327 | `CTkFrame` card | — | — | `pack(fill="both", expand=True)` | — |
| 331 | `CTkLabel` | `"PROMPT DA MÚSICA"` | — | `pack(anchor="w", padx=16, pady=(12,4))` | — |
| **337** | **`self.txt_music_prompt`** `CTkTextbox` | ← **insere `self._config.default_music_prompt` em `:343`** | — | `pack(fill="x", padx=16, pady=(0,8))`, h=80 | **`[REFS]`** lido em `:402` |
| 346 | `CTkLabel` | `"Duração da trilha (segundos)"` | — | `pack(anchor="w", padx=16, pady=(8,4))` | — |
| 352 | `self.var_music_duration = CTkIntVar` | valor `_config.default_music_duration` | ✔ | — | **`[REFS]`** |
| 353 | `CTkSlider` | from_=10 to=120 | `var_music_duration` | `pack(fill="x", padx=16, pady=(0,4))` | — |
| 359 | `CTkLabel` | textvariable=var_music_duration | ✔ | `pack(anchor="e", padx=16, pady=(0,8))` | — |
| **365** | **`self.lbl_trilha_status`** `CTkLabel` | `"Nenhuma trilha gerada..."` | — | `pack(anchor="w", padx=16, pady=(0,8))` | **`[REFS]`** `.configure` em `:409,425,432` |
| 373 | `CTkFrame` btn_frame | — | — | `pack(fill="x", padx=16, pady=(0,16))` | — |
| 376 | `CTkButton` | `"← Voltar"` | — | `pack(side="left")` | **`lambda: self._mudar_passo("letra")`** |
| 383 | `CTkButton` | `"Gerar Áudio"` | — | `pack(side="right")` | **`self._gerar_trilha_ace`** |
| 390 | `CTkButton` | `"Avançar →"` | — | `pack(side="right", padx=(0,8))` | **`lambda: self._mudar_passo("imagens")`** |

> ⚠️ **Dois botões empilhados em `side="right"`** (`:383` e `:390`) — ordem visual invertida em relação à ordem de criação.

### 1.7 `_criar_frame_imagens()` — linhas 442–586

Único frame que usa **`grid` internamente** (não `pack`).

| Linha | Widget | Texto | Var | Geometria | command |
|---|---|---|---|---|---|
| 444 | `CTkFrame` frame | — | — | `→ self._frames_passos["imagens"]` | — |
| 448 | `frame.grid_rowconfigure(3, weight=1)` | — | — | — | — |
| 449 | `frame.grid_columnconfigure(0, weight=1)` | — | — | — | — |
| 451 | `CTkLabel` | `"ETAPA 03 · IMAGENS"` | — | `grid(row=0, col=0, sticky="w", padx=20, pady=(10,0))` | — |
| 457 | `CTkLabel` | `"Buscar ou Gerar Imagens"` | — | `grid(row=1, col=0, sticky="w", padx=20, pady=(0,10))` | — |
| 464 | `CTkFrame` busca_card | — | — | `grid(row=2, col=0, sticky="ew", padx=20, pady=(0,10))` | — |
| 467 | `CTkFrame` busca_row | — | — | `pack(fill="x", padx=12, pady=8)` | — |
| 470 | `CTkButton` | `"Buscar Automaticamente"` | — | `pack(side="left")` w=200 h=32 | **`self._busca_automatica`** |
| **477** | **`self.lbl_auto_status`** | `""` | — | `pack(side="left", padx=(12,0))` | **`[REFS]`** `.configure` em `:1227,1242,1330,1333` |
| 484 | `CTkLabel` sep | `"│"` | — | `pack(side="left", padx=(16,16))` | — |
| 491 | `CTkLabel` | `"Prompt IA:"` | — | `pack(side="left")` | — |
| **497** | **`self.txt_prompt`** `CTkEntry` | placeholder `"Epic concert scene..."` + insert `:503` | — | `pack(side="left", padx=(6,8))` w=220 | **`[REFS]`** lido `:1136`, escrito `:1221-1222` |
| 506 | `CTkOptionMenu` mood | `[m.value for m in AgentMood]` | **`self.var_mood`** | `pack(side="left", padx=(0,4))` w=95 h=26 | — |
| 514 | `CTkOptionMenu` estilo | `[s.value for s in AgentStyle]` | **`self.var_estilo`** | `pack(side="left", padx=(0,8))` w=100 h=26 | — |
| 522 | `CTkButton` | `"Gerar IA"` | — | `pack(side="left")` w=70 h=28 | **`self._gerar_imagem_ia`** |
| 529 | `CTkButton` | `"Auto-prompt"` | — | `pack(side="left", padx=(6,0))` w=85 h=28 | **`self._auto_gerar_prompt`** |
| 537 | `CTkFrame` galeria_container | — | — | `grid(row=3, col=0, sticky="nsew", padx=20, pady=(0,10))` | — |
| 539-540 | `grid_rowconfigure(1,w=1)` / `grid_columnconfigure(0,w=1)` | — | — | — | — |
| 543 | `CTkFrame` galeria_header | — | — | `grid(row=0, col=0, sticky="ew", padx=12, pady=(10,0))` | — |
| 546 | `CTkLabel` | `"RESULTADOS"` | — | `pack(side="left")` | — |
| **552** | **`self.lbl_qtd_selecionadas`** | `"0 selecionados"` | — | `pack(side="right")` | **`[REFS]`** `.configure` em `:1505` |
| **559** | **`self._galeria_frame`** `CTkScrollableFrame` | — | — | `grid(row=1, col=0, sticky="nsew", padx=8, pady=(8,8))` | **`[REFS]`** populado `:1145`, `:1231`, `:1320`, `:1338` |
| 564 | `CTkLabel` empty-state | `"Clique em 'Buscar Automaticamente'..."` | — | `pack(expand=True, pady=40)` | — |
| 571 | `CTkFrame` btn_frame | — | — | `grid(row=4, col=0, sticky="ew", padx=20, pady=(0,10))` | — |
| 574 | `CTkButton` | `"← Voltar"` | — | `pack(side="left")` | **`lambda: self._mudar_passo("audio")`** |
| 581 | `CTkButton` | `"Avançar →"` | — | `pack(side="right")` | **`lambda: self._mudar_passo("midia")`** |

### 1.8 `_criar_frame_midia()` — linhas 588–683

| Linha | Widget | Texto | Var | Geometria | command |
|---|---|---|---|---|---|
| 589 | `CTkFrame` frame | — | — | `→ self._frames_passos["midia"]` | — |
| 592/598/604 | `CTkLabel` ×3 | `"ETAPA 04 · MÍDIA"` / `"Imagens e Vídeos"` / `"Busque imagens e vídeos..."` | — | `pack(anchor="w")` | — |
| 611 | `CTkFrame` card | — | — | `pack(fill="both", expand=True)` | — |
| 615 | `CTkFrame` search_frame | — | — | `pack(fill="x", padx=16, pady=(12,8))` | — |
| 618 | `CTkLabel` | `"Buscar mídia:"` | — | `pack(side="left", padx=(0,8))` | — |
| **624** | **`self.entry_search`** `CTkEntry` | placeholder `"Ex: concert, music, stage..."` | — | `pack(side="left", padx=(0,8))` w=300 | **`[REFS]`** lido `:1101` |
| 631 | `CTkButton` | `"Buscar"` | — | `pack(side="left")` w=100 h=32 | **`self._buscar_midia`** |
| **639** | **`self.var_provider`** `CTkStringVar` | value `self._config.stock_provider` | ✔ | — | **`[REFS]`** lido `:1106` |
| 640 | `CTkOptionMenu` provider | `["pexels","pixabay","unsplash","nasa","coverr","giphy","openverse"]` | `self.var_provider` | `pack(side="left", padx=(8,0))` w=120 | — |
| **649** | **`self._resultados_frame`** `CTkScrollableFrame` | — | — | `pack(fill="both", expand=True, padx=16, pady=(0,16))` | **`[REFS]`** limpo `:1110`, populado `:1114`, `:1346`, `:1350`, `:1358`, `:1365` |
| 654 | `CTkLabel` empty-state | `"Resultados da busca aparecerão aqui."` | — | `pack(expand=True, pady=40)` | — |
| 661 | `CTkFrame` btn_frame | — | — | `pack(fill="x", padx=16, pady=(0,16))` | — |
| 664 | `CTkButton` | `"← Voltar"` | — | `pack(side="left")` | **`lambda: self._mudar_passo("imagens")`** |
| 671 | `CTkButton` | `"+ Adicionar arquivo"` | — | `pack(side="left", padx=(8,0))` w=140 h=32 | **`self._adicionar_arquivo_midia`** ⚠ usa `StockMedia` não importado |
| 678 | `CTkButton` | `"Avançar →"` | — | `pack(side="right")` | **`lambda: self._mudar_passo("gerar")`** |

### 1.9 `_criar_frame_gerar()` — linhas 685–782

| Linha | Widget | Texto | Var | Geometria | command |
|---|---|---|---|---|---|
| 686 | `CTkFrame` frame | — | — | `→ self._frames_passos["gerar"]` | — |
| 689/695/701 | `CTkLabel` ×3 | `"ETAPA 05 · GERAR"` / `"Gerar Clipe"` / `"Revise as configurações..."` | — | `pack(anchor="w")` | — |
| 708 | `CTkFrame` card | — | — | `pack(fill="both", expand=True)` | — |
| 712 | `CTkFrame` config_frame | — | — | `pack(fill="x", padx=16, pady=(16,8))` | — |
| 716 | `CTkLabel` | `"Formato:"` | — | `pack(side="left", padx=(0,8))` | — |
| **722** | **`self.var_formato`** | `"9/16"` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 723 | `CTkOptionMenu` | `["9/16","16/9","3/4","4/3","1/1"]` | `self.var_formato` | `pack(side="left", padx=(0,16))` w=100 | — |
| 731 | `CTkLabel` | `"FPS:"` | — | `pack(side="left", padx=(0,8))` | — |
| **737** | **`self.var_fps`** | `"30"` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 738 | `CTkOptionMenu` | `["24","30","60"]` | `self.var_fps` | `pack(side="left")` w=80 | — |
| 746 | `CTkFrame` resumo_card | — | — | `pack(fill="x", padx=16, pady=(16,8))` | — |
| 749 | `CTkLabel` | `"RESUMO DO CLIPE"` | — | `pack(anchor="w", padx=12, pady=(8,4))` | — |
| 755 | `CTkLabel` **estático** | `"• Letra: Configurada\n• Áudio: Configurado\n• Mídia: Configurada"` | — | `pack(anchor="w", padx=12, pady=(0,8))` | — | ⚠ **nunca atualizado — 100% hardcoded** |
| **762** | **`self.btn_gerar`** `CTkButton` | `"GERAR CLIPE MUSICAL"` | — | `pack(anchor="center", pady=(16,16))` w=240 h=48 | **`self._gerar_clip`** | **`[REFS]` ⚠ SOBRESCREVE `:116`** |
| **772** | **`self.barra_progresso`** `CTkProgressBar` | — | — | `pack(fill="x", padx=16, pady=(0,8))`, `.set(0)`, h=6 | **`[REFS]`** `.set()` em `:1577` |
| **778** | **`self.lbl_status`** | `"Pronto para gerar"` | — | `pack(pady=(0,16))` | **`[REFS]`** `.configure` em `:1559,1583,1589,1598` |

### 1.10 `_construir_painel_direito()` — linhas 784–1035

| Linha | Widget | Texto | Var | Geometria | command |
|---|---|---|---|---|---|
| 785 | `CTkFrame` panel | — | — | `grid(row=1, col=2, sticky="nsew", padx=(1,0))`, `fg=Tema.PAINEL` | — |
| 788 | `CTkScrollableFrame` scroll | — | — | `pack(fill="both", expand=True, padx=8, pady=8)` | — |
| — | **LEGENDAS** | | | | |
| 792 | `CTkLabel` | `"LEGENDAS"` | — | `pack(anchor="w", pady=(0,8))` | — |
| **799** | **`self.var_lyrics_active`** | `_config.lyrics_active` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 800 | `CTkSwitch` | `"Mostrar letras"` | `var_lyrics_active` | `pack(anchor="w", pady=(0,8))` | — |
| 808 | `CTkLabel` | `"Posição:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **813** | **`self.var_lyrics_pos`** | `_config.lyrics_position` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 814 | `CTkOptionMenu` | `["top","center","bottom"]` | `var_lyrics_pos` | `pack(fill="x", pady=(0,8))` w=240 | — |
| 822 | `CTkLabel` | `"Tamanho da fonte:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **827** | **`self.var_font_size`** | `_config.lyrics_font_size` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 828 | `CTkSlider` | from_=24 to=96 | `var_font_size` | `pack(fill="x", pady=(0,4))` | — |
| 835 | separador | `CTkFrame` h=1 | — | `pack(fill="x", pady=8)` | — |
| — | **AGENTE DE IMAGENS** | | | | |
| 838 | `CTkLabel` | `"AGENTE DE IMAGENS"` | — | `pack(anchor="w", pady=(0,8))` | — |
| **844** | **`self.var_agent`** | `_config.agent_enabled` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 845 | `CTkSwitch` | `"Ativar agente IA"` | `var_agent` | `pack(anchor="w", pady=(0,8))` | — |
| 853 | `CTkLabel` | `"Estilo visual:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **858** | **`self.var_agent_style`** | `_config.agent_style` | ✔ | — | **`[REFS]`** ⚠ **lido por ninguém** |
| 859 | `CTkOptionMenu` | `["cinematic","documentary","music_video","artistic"]` | `var_agent_style` | `pack(fill="x", pady=(0,8))` w=240 | — |
| 867 | separador | — | — | `pack(fill="x", pady=8)` | — |
| — | **VÍDEO** | | | | |
| 870 | `CTkLabel` | `"VÍDEO"` | — | `pack(anchor="w", pady=(0,8))` | — |
| 877 | `CTkLabel` | `"Duração total (segundos):"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **882** | **`self.var_video_duration`** | `_config.default_music_duration` | ✔ | — | **`[REFS]`** lido `:1569` |
| 883 | `CTkSlider` | from_=10 to=180 | `var_video_duration` | `pack(fill="x", pady=(0,4))` | — |
| 889 | `CTkLabel` | textvariable | ✔ | `pack(anchor="e", pady=(0,8))` | — |
| 895 | `CTkLabel` | `"FPS:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **900** | **`self.var_video_fps`** | `str(_config.default_video_fps)` | ✔ | — | **`[REFS]`** lido `:1570` |
| 901 | `CTkOptionMenu` | `["24","25","30","60"]` | `var_video_fps` | `pack(fill="x", pady=(0,8))` w=240 | — |
| 909 | `CTkLabel` | `"Formato:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **914** | **`self.var_video_format`** | `_config.default_video_format` | ✔ | — | **`[REFS]`** lido `:1571` |
| 915 | `CTkOptionMenu` | `["9/16","16/9","1:1","4:5"]` | `var_video_format` | `pack(fill="x", pady=(0,8))` w=240 | — |
| 923 | separador | — | — | `pack(fill="x", pady=8)` | — |
| — | **EFEITOS** | | | | |
| 926 | `CTkLabel` | `"EFEITOS"` | — | `pack(anchor="w", pady=(0,8))` | — |
| 933 | `CTkLabel` | `"Efeito nas imagens:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **938** | **`self.var_effect`** | `_config.default_effect` | ✔ | — | **`[REFS]`** lido `:1572` |
| 939 | `CTkOptionMenu` | 17 valores (`zoom_in`…`corte`) `:940-947` | `var_effect` | `pack(fill="x", pady=(0,8))` w=240 | — |
| 954 | `CTkLabel` | `"Transição entre cenas:"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **959** | **`self.var_transition`** | `_config.default_transition` | ✔ | — | **`[REFS]`** lido `:1573` |
| 960 | `CTkOptionMenu` | 15 valores (`fade`…`zoom_reveal`) `:961-967` | `var_transition` | `pack(fill="x", pady=(0,8))` w=240 | — |
| 974 | `CTkLabel` | `"Duração por imagem (segundos):"` | — | `pack(anchor="w", pady=(0,4))` | — |
| **979** | **`self.var_effect_duration`** `DoubleVar` | `5.0` | ✔ | — | **`[REFS]`** lido `:1574` |
| 980 | `CTkSlider` | from_=2.0 to=15.0 | `var_effect_duration` | `pack(fill="x", pady=(0,4))` | — |
| 986 | `CTkLabel` | textvariable | ✔ | `pack(anchor="e", pady=(0,8))` | — |
| 992 | separador | — | — | `pack(fill="x", pady=8)` | — |
| — | **SAÍDA** | | | | |
| 995 | `CTkLabel` | `"SAÍDA"` | — | `pack(anchor="w", pady=(0,8))` | — |
| **1001** | **`self.var_output_dir`** | `_config.output_dir` | ✔ | — | **`[REFS]`** lido `:1549`, escrito `:1610` |
| 1003 | `CTkFrame` output_frame | — | — | `pack(fill="x", pady=(0,8))` | — |
| **1006** | **`self.entry_output`** `CTkEntry` | textvariable=`var_output_dir` | ✔ | `pack(side="left", fill="x", expand=True, padx=(0,4))` | **`[REFS]`** ⚠ **nunca lido diretamente** (só via var) |
| 1013 | `CTkButton` | `"..."` | — | `pack(side="right")` w=32 h=28 | **`self._escolher_pasta_saida`** |
| 1021 | separador | — | — | `pack(fill="x", pady=8)` | — |
| — | **LOG** | | | | |
| 1024 | `CTkLabel` | `"LOG"` | — | `pack(anchor="w", pady=(0,8))` | — |
| **1030** | **`self.log_box`** `CTkTextbox` | vazio | — | `pack(fill="x")`, h=200 | **`[REFS]`** `.insert`/`.see` em `:1622-1623` |

---

## 2. Inventário de atributos de instância (`self.*`)

### 2.1 Criados em `__init__` (linhas 42–55)

| Linha | Atributo | Tipo | Valor inicial | Classificação | Consumidores |
|---|---|---|---|---|---|
| 42 | `self._config` | `ClipConfig` | `load_config()` | **dado/config** | `:343,352,639,799,813,827,844,858,882,900,914,938,959,1001,1611` |
| 43 | `self._passo_atual` | `str` | `"letra"` | estado | escrito `:1042`; **nunca lido** |
| 44 | `self._db` | `StockDatabase` | — | dado | `:1124,1238,1247` |
| 45 | `self._agent` | `ClipAgent` | — | dado | `:1218` (`MOOD_QUERIES`) |
| 46 | `self._midia_selecionada` | `list` | `[]` | **estado crítico** | ver 2.3 |
| 47 | `self._imagens_geradas` | `list[dict]` | `[]` | estado | escrito `:1191`; **nunca lido** |
| 48 | `self._passo_labels` | `dict` | `{}` | **índice de widgets** | `:243-245` (escrita), `:1054-1068` (leitura) |
| 49 | `self._nav_btns` | `dict` | `{}` | **índice de widgets** | `:163` (escrita), `:1044-1048` (leitura) |
| 50 | `self._frames_passos` | `dict` | `{}` | **índice de widgets** ⚠ **reatribuído em `:192`** | `:249,307,445,590,687,1075-1080` |
| 51 | `self._conteudo_passos` | `CTkFrame\|None` | `None` | **widget** | `:189,1073,1080` |
| 52 | `self.var_mood` | `StringVar` | `"epic"` | dado/UI | `:509,1216` |
| 53 | `self.var_estilo` | `StringVar` | `"cinematic"` | dado/UI | `:517,1217` |
| 54 | `self._trilha_path` | `str\|None` | `None` | **estado crítico** | escrito `:424`, lido `:1575` |
| 55 | `self._trilha_gerando` | `bool` | `False` | lock lógico | `:399,408,422` |

### 2.2 Criados nos construtores de UI

| Linha | Atributo | Tipo | Classificação |
|---|---|---|---|
| 116, **762** | `self.btn_gerar` | `CTkButton` | **widget** ⚠ **duplicado** |
| 180 | `self._conteudo_frame` | `CTkFrame` | **widget** (pai do indicator + `_conteudo_passos`) |
| **192** | `self._frames_passos` | `dict` | **reatribuição destrutiva** |
| 189 | `self._conteudo_passos` | `CTkFrame` | **reatribuição** |
| 279 | `self.txt_letra` | `CTkTextbox` | **widget** |
| 337 | `self.txt_music_prompt` | `CTkTextbox` | **widget** |
| 352 | `self.var_music_duration` | `IntVar` | dado/UI |
| 365 | `self.lbl_trilha_status` | `CTkLabel` | **widget** |
| 477 | `self.lbl_auto_status` | `CTkLabel` | **widget** |
| 497 | `self.txt_prompt` | `CTkEntry` | **widget** |
| 552 | `self.lbl_qtd_selecionadas` | `CTkLabel` | **widget** |
| 559 | `self._galeria_frame` | `CTkScrollableFrame` | **widget** |
| 624 | `self.entry_search` | `CTkEntry` | **widget** |
| 639 | `self.var_provider` | `StringVar` | dado/UI |
| 649 | `self._resultados_frame` | `CTkScrollableFrame` | **widget** |
| 722 | `self.var_formato` | `StringVar` | dado/UI **órfão** |
| 737 | `self.var_fps` | `StringVar` | dado/UI **órfão** |
| **762** | `self.btn_gerar` | `CTkButton` | **widget** (vencedor) |
| 772 | `self.barra_progresso` | `CTkProgressBar` | **widget** |
| 778 | `self.lbl_status` | `CTkLabel` | **widget** |
| 799 | `self.var_lyrics_active` | `BooleanVar` | dado/UI **órfão** |
| 813 | `self.var_lyrics_pos` | `StringVar` | dado/UI **órfão** |
| 827 | `self.var_font_size` | `IntVar` | dado/UI **órfão** |
| 844 | `self.var_agent` | `BooleanVar` | dado/UI **órfão** |
| 858 | `self.var_agent_style` | `StringVar` | dado/UI **órfão** |
| 882 | `self.var_video_duration` | `IntVar` | dado/UI **usado** `:1569` |
| 900 | `self.var_video_fps` | `StringVar` | dado/UI **usado** `:1570` |
| 914 | `self.var_video_format` | `StringVar` | dado/UI **usado** `:1571` |
| 938 | `self.var_effect` | `StringVar` | dado/UI **usado** `:1572` |
| 959 | `self.var_transition` | `StringVar` | dado/UI **usado** `:1573` |
| 979 | `self.var_effect_duration` | `DoubleVar` | dado/UI **usado** `:1574` |
| 1001 | `self.var_output_dir` | `StringVar` | dado/UI **usado** `:1549,1610` |
| 1006 | `self.entry_output` | `CTkEntry` | widget **órfão direto** |
| 1030 | `self.log_box` | `CTkTextbox` | **widget** |

### 2.3 Inventário crítico: lista `self._midia_selecionada` (tipo misto ⚠)

| Linha | Operação | Tipo do elemento |
|---|---|---|
| 1196 | `.append({"type":"generated","prompt":...,"source":"ai"})` | **dict** |
| 1485 | `for i, sel in enumerate(...)` → `sel.id` | **assume objeto com `.id`** → ⚠ `AttributeError` se houver dict |
| 1488 | `.pop(i)` | — |
| 1496 | `.append(item)` | `StockMedia` |
| 1525-1538 | `.append(StockMedia(...))` | `StockMedia` ⚠ `NameError` (não importado) |
| 1545 | `if not self._midia_selecionada:` | — |
| 1506 | `len(self._midia_selecionada)` | — |
| 1567 | `midia_selecionada=self._midia_selecionada` | passado ao `gerar_clipe` |

> ⚠️ **Bug latente grave:** se o usuário clicar "Usar" numa imagem IA (`:1194`, insere **dict**) e depois clicar "Selecionar" em qualquer card (`:1485`), a linha `sel.id` levanta `AttributeError`. A UI não tem guarda de tipo.

---

## 3. Inventário de métodos

| # | Linha | Método / assinatura | O que faz | Chamado de |
|---|---|---|---|---|
| 1 | 31 | `__init__(self)` | Setup da janela, estado, chama `_construir_ui` | entrypoint `main()` |
| 2 | 63 | `_construir_ui(self)` | Config do grid raiz e ordem dos builders | `__init__:57` |
| 3 | 75 | `_construir_top_bar(self)` | Topbar: logo, título, botões APIs/Gerar | `_construir_ui:70` |
| 4 | 125 | `_construir_sidebar_navegacao(self)` | Sidebar 5 passos + Config; chama `_mudar_passo("letra")` | `_construir_ui:71` |
| 5 | 179 | `_construir_conteudo_principal(self)` | Cria `_conteudo_frame`, indicator, `_conteudo_passos`, os 5 frames | `_construir_ui:72` |
| 6 | 201 | `_construir_passos_indicator(self)` | Barra de 5 passos (icon/title/subtitle) | `_construir_conteudo_principal:186` |
| 7 | 247 | `_criar_frame_letra(self)` | Etapa 01 | `_construir_conteudo_principal:193` |
| 8 | 304 | `_criar_frame_audio(self)` | Etapa 02 | `:194` |
| 9 | **397** | `_gerar_trilha_ace(self)` | Gera trilha via `audio.gerar_trilha` em **thread**, `after(0,…)` p/ UI | **command** `:385` |
| 10 | 442 | `_criar_frame_imagens(self)` | Etapa 03 | `:195` |
| 11 | 588 | `_criar_frame_midia(self)` | Etapa 04 | `:196` |
| 12 | 685 | `_criar_frame_gerar(self)` | Etapa 05 | `:197` |
| 13 | 784 | `_construir_painel_direito(self)` | Painel scrollável: legendas, agente, vídeo, efeitos, saída, log | `_construir_ui:73` |
| 14 | **1041** | `_mudar_passo(self, passo: str)` | Atualiza `_passo_atual`, pinta `_nav_btns` e `_passo_labels`, chama `_mostrar_passo` | **command** `:157` (lambda), `:177`, `:292,299,378,392,576,583,666,680` |
| 15 | **1072** | `_mostrar_passo(self, passo: str)` | `pack_forget()` em todos e `pack(in_=…)` no ativo | `_mudar_passo:1070`, `_construir_conteudo_principal:199` |
| 16 | 1086 | `_carregar_letra_arquivo(self)` | Lê .txt e popula `txt_letra` | ⚠ **ÓRFÃO** — nenhum widget chama (verificado no repo) |
| 17 | **1100** | `_buscar_midia(self)` | Busca `_db.pesquisar` em **thread**; `after(0,_exibir_resultados)` | **command** `:633` |
| 18 | 1134 | `_gerar_imagem_ia(self)` | Cria card placeholder em `_galeria_frame` (sem IA real) | **command** `:524` |
| 19 | 1194 | `_usar_imagem_gerada(self, prompt, card_widget=None)` | Append **dict** em `_midia_selecionada`; pinta card | **command** lambda `:1177` |
| 20 | 1209 | `_auto_gerar_prompt(self)` | Gera prompt a partir da letra + `_agent.MOOD_QUERIES` | **command** `:531` |
| 21 | 1225 | `_busca_automatica(self)` | `_db.gerar_search_terms_letra` + `_db.busca_massiva` em **thread** | **command** `:472` |
| 22 | 1258 | `_extrair_queries(self, letra)` | Extrai queries via stopwords + `Counter`; usa `self._log` | ⚠ **ÓRFÃO** — nenhum caller (código morto, mas funcional) |
| 23 | 1318 | `_exibir_resultados_automaticos(self, resultados)` | Limpa `_galeria_frame`, cria grid de cards | `after(0,…)` em `:1254` |
| 24 | 1344 | `_exibir_resultados(self, resultado)` | Limpa `_resultados_frame`, cria grid de cards | `after(0,…)` em `:1128` |
| 25 | 1373 | `_criar_card_midia(self, parent, item, idx)` | Card 2-col com thumb, fonte, descrição, botão Selecionar | `:1342`, `:1369` |
| 26 | 1434 | `_carregar_thumbnail(self, parent, url, fallback_text="IMG")` | Baixa imagem em **thread**, `after(0,mostrar)` c/ `label.image=photo` | `:1397` |
| 27 | 1482 | `_selecionar_midia(self, item, card_widget=None)` | Toggle em `_midia_selecionada`; pinta card SUCESSO/CARTAO | **command** lambda `:1424` |
| 28 | 1502 | `_atualizar_contador_selecionadas(self)` | `lbl_qtd_selecionadas.configure(...)` c/ guarda `hasattr` | `:1207,1492,1500,1541` |
| 29 | 1509 | `_adicionar_arquivo_midia(self)` | `askopenfilenames` → cria `StockMedia` ⚠ **NameError** | **command** `:673` |
| 30 | **1543** | `_gerar_clip(self)` | Valida, chama `gerador.gerar_clipe` em **thread** c/ callbacks | **command** `:118` e `:764` |
| 31 | 1606 | `_escolher_pasta_saida(self)` | `askdirectory` → `var_output_dir.set` + `_config.output_dir` | **command** `:1015` |
| 32 | 1614 | `_abrir_config_apis(self)` | Abre `APIConfigUI(self).show()` | **command** `:110`, `:171` |
| 33 | **1621** | `_log(self, msg: str)` | `log_box.insert("end", …)` + `see("end")` | **muitos**: `:410,429,436,1096,1107,1130,1141,1192,1206,1223,1228,1239,1314,1371,1491,1499,1540,1558,1587,1597,1612` |
| — | 1626 | `main()` módulo | `GuiClipes().mainloop()` | `__main__` |

---

## 4. Acoplamento crítico

### 4.1 Widgets criados num método e mutados em OUTRO (não pode quebrar)

| Widget | Criado | Mutado em | Risco |
|---|---|---|---|
| `self.txt_letra` | `_criar_frame_letra:279` | `_carregar_letra_arquivo:1094-1095`, `_auto_gerar_prompt:1211`, `_busca_automatica:1235` | **lido com `hasattr`** — se removido, cai em `""` silenciosamente (`:1211,1235`) |
| `self.txt_music_prompt` | `_criar_frame_audio:337` | `_gerar_trilha_ace:402` | leitura direta, sem guarda |
| `self.lbl_trilha_status` | `_criar_frame_audio:365` | `_gerar_trilha_ace:409,425,432` | `configure` de dentro de closure `finalizar()` |
| `self.lbl_auto_status` | `_criar_frame_imagens:477` | `_busca_automatica:1227,1242`, `_exibir_resultados_automaticos:1330,1333` | `configure` de closure em thread |
| `self.txt_prompt` | `_criar_frame_imagens:497` | `_gerar_imagem_ia:1136`, `_auto_gerar_prompt:1221-1222` | leitura/escrita |
| `self._galeria_frame` | `_criar_frame_imagens:559` | `_gerar_imagem_ia:1145`, `_busca_automatica:1231`, `_exibir_resultados_automaticos:1320,1338` | `winfo_children()` + `destroy()` |
| `self.lbl_qtd_selecionadas` | `_criar_frame_imagens:552` | `_atualizar_contador_selecionadas:1505` | **única guarda `hasattr` do arquivo** (`:1504`) |
| `self.entry_search` | `_criar_frame_midia:624` | `_buscar_midia:1101` | leitura direta |
| `self._resultados_frame` | `_criar_frame_midia:649` | `_buscar_midia:1110,1114`, `_exibir_resultados:1346,1350,1358,1365` | `winfo_children()` + `destroy()` |
| `self.var_provider` | `_criar_frame_midia:639` | `_buscar_midia:1106` | — |
| `self.btn_gerar` | **`:116` e `:762`** | `_gerar_clip:1560,1581,1596` | ⚠ **duplicata** — muta só o vencedor |
| `self.barra_progresso` | `_criar_frame_gerar:772` | `_gerar_clip:1577` (via callback lambda `:1577`) | `set()` de dentro de thread |
| `self.lbl_status` | `_criar_frame_gerar:778` | `_gerar_clip:1559,1583,1589,1598` | `configure` de closures `reativar()`/`erro()` |
| `self.log_box` | `_construir_painel_direito:1030` | `_log:1622-1623` | **chamado por quase todos os métodos** — é o acoplamento mais difuso |
| `self._nav_btns[*]` | `_construir_sidebar_navegacao:163` | `_mudar_passo:1044-1048` | itera o dict |
| `self._passo_labels[*][*]` | `_construir_passos_indicator:243` | `_mudar_passo:1054-1068` | **itera dict de dicts de widgets** |
| `self._frames_passos[*]` | `_criar_frame_*:249,307,445,590,687` | `_mostrar_passo:1075-1080` | itera `.values()` + `pack_forget` |
| `self._conteudo_passos` | `_construir_conteudo_principal:189` | `_mostrar_passo:1073,1080` | guarda `if not … : return` |
| `self.var_video_*`, `var_effect*`, `var_transition`, `var_output_dir` | `_construir_painel_direito` | `_gerar_clip:1549,1569-1574` | **lidas da thread** (`gerar()`) ⚠ acesso Tk fora da main thread |

### 4.2 Iteração sobre coleções de widgets

- `_mudar_passo:1044` — `for key, btn in self._nav_btns.items()` → `configure`
- `_mudar_passo:1053-1068` — `for idx, key in enumerate(passos_ordem)` → `self._passo_labels.get(key)` → **3 `configure` por passo**
- `_mostrar_passo:1075` — `for frame in self._frames_passos.values(): frame.pack_forget()`
- `_buscar_midia:1110` / `_busca_automatica:1231` / `_exibir_resultados_automaticos:1320` / `_exibir_resultados:1346` — `for widget in ….winfo_children(): widget.destroy()`

> ⚠️ `passos_ordem` (`:1050`) é uma **quarta** cópia da lista de chaves. Se você renomear uma chave de frame, precisa atualizar: `nav_items` (`:147`), `passos` (`:207`), `passos_ordem` (`:1050`) e as 5 chaves de `self._frames_passos`.

### 4.3 `after()` / threads que tocam na UI

| Linha | Contexto | Toca |
|---|---|---|
| 438 | thread `gerar()` → `after(0, finalizar)` | `lbl_trilha_status`, `_trilha_path`, `_log` |
| 1128 | thread `buscar()` → `after(0, _exibir_resultados)` | `_resultados_frame` (reconstrói árvore) |
| 1130 | thread `buscar()` → `after(0, _log)` | `log_box` |
| 1242 | thread `buscar()` → `after(0, lbl_auto_status.configure)` | `lbl_auto_status` |
| 1254 | thread `buscar()` → `after(0, _exibir_resultados_automaticos)` | `_galeria_frame` |
| 1474 | thread `carregar()` → `after(0, mostrar)` | `parent` (cria label), `loading.destroy()` |
| 1478 | thread `carregar()` → `after(0, fallback)` | `loading.configure` |
| 1576 | callback_log → `after(0, _log)` | `log_box` |
| 1577 | **callback_prog → `after(0, barra_progresso.set)`** | ⚠ **lê `self.barra_progresso` e `self.var_video_*` de dentro da thread `gerar()`** |
| 1593 | thread `gerar()` → `after(0, reativar)` | `btn_gerar`, `lbl_status`, `_log` |
| 1602 | thread `gerar()` → `after(0, erro)` | `btn_gerar`, `lbl_status`, `_log` |

> ⚠️ **Padrão perigoso em `:1576-1577`:** os lambdas capturam `self.barra_progresso` por referência **dentro de `self.after`** — ok, pois `after` executa na main thread. Mas `self.var_video_duration.get()` etc. são chamados **antes** de entrar na thread (`:1569-1574`), então estão seguros por acidente. **Não mova essas leituras para dentro de `gerar()`.**
>
> ⚠️ **`_carregar_thumbnail` guarda `label.image = photo` (`:1471`)** — sem essa referência o GC destrói a imagem e o thumb fica branco. Se você reescrever, **preserve o atributo `.image` no widget**.

### 4.4 Dependências de ordem entre builders

```
__init__
 └─ _construir_ui (:63)
     ├─ grid config raiz (:64-68)
     ├─ _construir_top_bar          → cria self.btn_gerar (#1)
     ├─ _construir_sidebar_navegacao
     │    └─ :177 _mudar_passo("letra")   ⚠ EXIGE _frames_passos e _conteudo_passos
     │         └─ _mostrar_passo:1073  if not self._frames_passos or not self._conteudo_passos: return
     │                                   ↑ neste ponto ambos são {} / None → early return (seguro por acaso)
     ├─ _construir_conteudo_principal
     │    ├─ :186 _construir_passos_indicator  → popula _passo_labels
     │    ├─ :192 self._frames_passos = {}     ⚠ zera dict
     │    ├─ :193-197 _criar_frame_{letra,audio,imagens,midia,gerar}
     │    │      ⚠ _criar_frame_audio:343 LÊ self._config.default_music_prompt e ESCREVE no textbox
     │    └─ :199 _mostrar_passo("letra")
     └─ _construir_painel_direito    → cria as vars lidas por _gerar_clip
```

**Não existe reentrada de dependência de dados entre frames**, exceto:
- `_criar_frame_audio:343` insere `self._config.default_music_prompt` (leitura de config, escrita em widget próprio).
- `_criar_frame_imagens:503` insere a string literal `"Epic concert scene with dramatic lighting"` (default não vem da config — inconsistente com o padrão acima).

### 4.5 Contratos implícitos que a reescrita deve preservar

1. **Nomes de chave** `letra|audio|imagens|midia|gerar` consistentes em 6 estruturas (4 listas + 2 dicts).
2. **`_log(msg: str)`** deve existir e aceitar `str` — chamado por callbacks vindos do `gerador` via `after`.
3. **`_atualizar_contador_selecionadas`** deve tolerar `lbl_qtd_selecionadas` ausente (guarda `hasattr` em `:1504`). Não remova a guarda sem garantir criação prévia.
4. **`_mostrar_passo`** deve preservar semântica `pack_forget` + `pack(in_=parent)` se `_conteudo_passos` continuar sendo um container único.
5. **`self._trilha_path`** deve existir sempre (`None` por default) — `_gerar_clip:1575` o passa ao gerador sem checagem.
6. **`_selecionar_midia(item, card_widget)`** deve aceitar `card_widget=None` (chamada sempre com card, mas assinatura é pública).
7. **`self._midia_selecionada`** é consumido por `gerador.gerar_clipe` — a forma dos itens (dict vs `StockMedia`) importa para o backend.
8. **`_abrir_config_apis`** passa `self` como parent para `APIConfigUI` (`:1617`) — a janela principal deve continuar sendo um `tk` válido (é, via `ctk.CTk`).

---

## 5. Cores hardcoded (fora do `theme.py`)

### 5.1 Cores literais em `gui_clipes.py`

| Linha | Contexto | Valor | Ação sugerida |
|---|---|---|---|
| 82 | `CTkFrame` logo_frame | `"transparent"` | **não migrar** (pseudo-cor Tk) |
| 105 | `CTkFrame` btn_frame | `"transparent"` | não migrar |
| 158 | `CTkButton` fg_color (nav inativo) | `"transparent"` | não migrar |
| 166 | `CTkLabel` espaçador | `"transparent"` (fg_color) | não migrar |
| 172 | `CTkButton` Config | `"transparent"` | não migrar |
| 189 | `CTkFrame` `_conteudo_passos` | `"transparent"` | não migrar |
| 215 | `CTkFrame` (passo) | `"transparent"` | não migrar |
| 226 | `CTkFrame` text_frame | `"transparent"` | não migrar |
| 248,306,444,589,686 | frame de etapa | `"transparent"` | não migrar |
| 287,373,571,661,712 | btn_frame/config_frame | `"transparent"` | não migrar |
| 467 | busca_row | `"transparent"` | não migrar |
| 543 | galeria_header | `"transparent"` | não migrar |
| 615,1003 | search_frame / output_frame | `"transparent"` | não migrar |
| 788 | `CTkScrollableFrame` scroll | `"transparent"` | não migrar |
| 1048 | `_mudar_passo` `btn.configure(fg_color=…)` | **`"transparent"`** | não migrar (estado) |
| 1338,1365 | grid_frame | `"transparent"` | não migrar |
| 1150,1172 | img_frame / btn_frame | `"transparent"` (1172) | não migrar |

### 5.2 Valores de cor "reais" hardcoded em `gui_clipes.py`

**Nenhum.** ✅ Todas as cores não-transparentes em `gui_clipes.py` já usam `Tema.*`.

### 5.3 Strings de cor hardcoded em `ui_config.py` (fora do tema)

`ui_config.py` é `ttk`/`tk` puro e **não importa `Tema`**. Todas as cores aqui são nomes/ literais Tk:

| Linha | Valor | Contexto |
|---|---|---|
| 104 | `"gray"` | `pexels_status` foreground |
| 126 | `"gray"` | `pixabay_status` |
| 144 | `"gray"` | `unsplash_status` |
| 159 | `"gray"` | label informativa NASA |
| 165 | `"gray"` | `nasa_status` |
| 185 | `"gray"` | label informativa Coverr |
| 191 | `"gray"` | `coverr_status` |
| 206 | `"gray"` | label informativa Giphy |
| 212 | `"gray"` | `giphy_status` |
| 227 | `"gray"` | label informativa Openverse |
| 233 | `"gray"` | `openverse_status` |
| 318 | `"gray"` | `status_label.config(foreground="gray")` (testando) |
| 331 | `"green"` | `_update_status` sucesso |
| 333 | `"red"` | `_update_status` erro |
| 39 | `("Arial", 14, "bold")` | título (fonte hardcoded, não cor) |

**Total: 14 literais de cor em `ui_config.py`, 0 em `gui_clipes.py`.**

### 5.4 Observações sobre o tema

- `theme.py` **não é importado por nenhum outro módulo** além de `gui_clipes.py` (confirmado por grep). O `ui_config.py` usa `ttk` clássico e ignora o tema inteiro — se o redesign unificar a identidade visual, o `ui_config.py` precisa ser migrado de `ttk` para `ctk` (mudança de toolkit, não só de cor).
- Aliases a conhecer: `ACENTO_QUENTE`/`ACAO` = `PRIMARY`; `DESTAQUE` = `PRIMARY`; `SUCESSO` = `PRIMARY` = `#4ADE80`; `NAV_ACTIVE` = `DESTRUIVA` = `ERRO` = `#EF4444`; `CAMPO` = `CONTROLE` = `TEXTBOX_FUNDO` = `#16161F`; `HOVER` = `SECONDARY` = `#1E1E28`.
- `Tema.RAIO_CARD` (10) e `Tema.RAIO_BOTAO` (8) são usados, mas vários widgets usam `corner_radius` hardcoded `8`, `6`, `4` (`:464,537,560,650,1145,1150,1380,1386,1427`) — **inconsistência de forma**, não de cor.

---

## 6. O que os testes exigem

### 6.1 Fato confirmado

**`tests/test_clipes.py` NÃO importa nem referencia `gui_clipes`, `GuiClipes`, `theme.Tema` ou `ui_config`.** Grep em `tests/` retornou zero ocorrências para todos esses nomes.

**Consequência prática:** você pode renomear qualquer widget, método ou atributo privado de `GuiClipes` **sem quebrar nenhum teste**. Não há teste de UI no repositório.

### 6.2 Contratos que indiretamente tocam a UI

Embora o GUI não seja testado, os testes fixam **assinaturas de funções que o GUI chama**. Se a reescrita alterar essas chamadas, os testes continuam passando mas o app quebra em runtime.

| Teste | Linha (teste) | Contrato fixado | Chamada no GUI |
|---|---|---|---|
| `TestMontar.test_montar_clipe_assinatura` | 225-231 | `montar_clipe(project, audio_path, saida, …)` | — (não chamado no GUI) |
| `TestIntegrar.test_integrar_assinatura` | 235-241 | `integrar_clipe_audio(audio_path, imagens, saida, …)` | — |
| `TestConfig.test_default_config` | 40-47 | `ClipConfig` tem `base_dir, output_dir, default_music_duration=30, default_video_format="9/16", lyrics="", stock_provider="pexels"` | `:352,639,882,914,1001` |
| `TestConfig.test_config_to_dict` | 49-56 | `to_dict()` contém `output_dir, lyrics, stock_api_key, agent_enabled, moneyprinter_enabled` | — |
| `TestConfig.test_config_persistence` | 58-63 | `save_config(cfg)` → `load_config()` round-trip | `:42`, `ui_config:286` |
| `TestSchema.test_visual_element_defaults` | 104-108 | `MusicVisualElement(accent_color="#FFCC00")` | — |
| `TestDatabase.test_stock_media` | 252-259 | `StockMedia(id, url, width, height, source)` **kwargs nomeados** | ⚠ **GUI usa `StockMedia(id=…, url=…, thumbnail_url=…, width=0, height=0, source=…, media_type=…, category=…, tags=…, description=…, download_url=…)` em `:1525-1537`** |
| `TestDatabase.test_stock_search` | 261-263 | `StockSearch(query, provider, results, total)` | — |
| `TestAgent.*` | 137-170 | `ClipAgent()`, `.mood`, `.direcionar_imagem(beat)`, `.analisar(lyrics)`, `._detectar_mood(a,b,c)`, `.aplicar_cores()`, `AgentMood`, `AgentStyle` | ⚠ GUI usa **`self._agent.MOOD_QUERIES`** (`:1218`) — **atributo NÃO coberto por teste**; e `AgentMood(v)`, `AgentStyle(v)` (`:1216-1217`), `[m.value for m in AgentMood]` (`:508`) |
| `TestPresets.test_presets_nao_vazios` | 244-249 | `listar_presets()` → `{"trilhas": …, "narracao": …}` | — |
| `TestVersion` | 34-36 | `__version__ == "2.0.0"` | — |

### 6.3 Cobertura ausente que a reescrita pode explorar

Nenhum teste cobre: `generar.gerar_clipe`, `audio.gerar_trilha`, `db.pesquisar`, `db.buscar_massiva`, `db.gerar_search_terms_letra`, `db.testar_conexao`, nem nenhuma classe de `gui_clipes.py`/`ui_config.py`.

**Recomendação forte:** antes de reescrever, escreva testes de fumaça (`smoke tests`) que:
1. Instanciem `GuiClipes` (com `xvfb`/headless ou marcado como integração) e verifiquem que todos os `self.*` da seção 2.2 existem e não são `None`.
2. Verifiquem que `set(self._frames_passos) == set(self._passo_labels) == set(self._nav_btns) == {"letra","audio","imagens","midia","gerar"}`.
3. Verifiquem que `self.btn_gerar` é um único widget coerente (o bug da duplicata passaria a ser detectado).

---

## 7. Anexos

### 7.1 Bugs pré-existentes encontrados (não são de UI, mas você vai topar com eles)

| # | Linha | Bug | Severidade |
|---|---|---|---|
| B1 | 1525 | `StockMedia` usado sem import → `NameError` em `_adicionar_arquivo_midia` | **Alta** |
| B2 | 116 + 762 | `self.btn_gerar` criado 2× — o da topbar fica órfão e nunca é habilitado/desabilitado | Média |
| B3 | 1196 vs 1485 | Lista `_midia_selecionada` com tipo misto (dict/`StockMedia`) → `AttributeError` no toggle | **Alta** |
| B4 | 1671? — não; ver 8.1 | `self._passo_atual` escrito mas nunca lido | Baixa |
| B5 | 1225/1258 | `_extrair_queries` é código morto (nunca chamado); `_extrair_queries` também não é chamado por nada | Baixa |
| B6 | 1086 | `_carregar_letra_arquivo` é órfão — não há botão "Carregar arquivo" na etapa Letra | Média (funcionalidade perdida no redesign) |
| B7 | 755 | Label "RESUMO DO CLIPE" é estático — o resumo nunca reflete o estado real | Média |
| B8 | 292 | "← Voltar" da etapa 1 navega para "imagens" (wrap-around) | Baixa |
| B9 | 722/737 | `var_formato` e `var_fps` da etapa Gerar são duplicatas órfãs de `var_video_format`/`var_video_fps` do painel direito | Média |

> B9 é importante para o redesign: a etapa "Gerar" tem controles de Formato/FPS que **não fazem nada** (`_gerar_clip:1571-1572` lê as vars do painel direito). O usuário vê dois controles conflitantes.

### 7.2 Contagem de widgets por construtor

| Construtor | Frames/Labels/Buttons/etc. | Widgets globais |
|---|---|---|
| `_construir_top_bar` | 9 | 1 (`btn_gerar`) |
| `_construir_sidebar_navegacao` | 4 + 6 botões | 1 (`_nav_btns`) |
| `_construir_conteudo_principal` | 2 | 3 (`_conteudo_frame`, `_conteudo_passos`, `_frames_passos`) |
| `_construir_passos_indicator` | 16 (5 grupos × 3 + 5 frames) | 1 (`_passo_labels`) |
| `_criar_frame_letra` | 8 | 1 (`txt_letra`) |
| `_criar_frame_audio` | 14 | 3 (`txt_music_prompt`, `lbl_trilha_status`, `var_music_duration`) |
| `_criar_frame_imagens` | 19 | 5 (`lbl_auto_status`, `txt_prompt`, `lbl_qtd_selecionadas`, `_galeria_frame`, +2 vars) |
| `_criar_frame_midia` | 12 | 3 (`entry_search`, `_resultados_frame`, `var_provider`) |
| `_criar_frame_gerar` | 13 | 5 (`var_formato`, `var_fps`, `btn_gerar`, `barra_progresso`, `lbl_status`) |
| `_construir_painel_direito` | ~60 | 14 (`log_box`, `entry_output` + 12 vars) |
| **Total** | **~157** | **~37 atributos de UI** |

### 7.3 Mapa rápido de "variáveis órfãs" (candidatas a remoção ou correção)

| Var | Criada | Lida em produção? |
|---|---|---|
| `self.var_formato` | 722 | ❌ nunca |
| `self.var_fps` | 737 | ❌ nunca |
| `self.var_lyrics_active` | 799 | ❌ nunca |
| `self.var_lyrics_pos` | 813 | ❌ nunca |
| `self.var_font_size` | 827 | ❌ nunca |
| `self.var_agent` | 844 | ❌ nunca |
| `self.var_agent_style` | 858 | ❌ nunca |
| `self.entry_output` | 1006 | ❌ nunca (só via `var_output_dir`) |
| `self._imagens_geradas` | 1191 | ❌ nunca |
| `self._passo_atual` | 43/1042 | ❌ nunca |

> ⚠️ **Atenção:** "nunca lida" ≠ "removível". `var_lyrics_*` e `var_agent*` provavelmente seriam lidas por uma integração futura com `legendas.py`/`agent.py` que não existe. Confirme com o autor antes de apagar.

---

**Fim do relatório.**

---

## 8. STATUS DA CORREÇÃO (atualizado 2026-09-17)

Redesign da interface executado em `gui_clipes.py` (único arquivo de produção
alterado). `theme.py` foi estendido de forma **aditiva** (nada removido).

### 8.1 Bugs do relatório: RESOLVIDOS

| # | Bug | Status | Como foi resolvido |
|---|---|---|---|
| B1 | `StockMedia` usado sem import | ✅ Corrigido | Adicionado ao import de `database` |
| B2 | `btn_gerar` criado 2× (o da topbar órfão) | ✅ Corrigido | Referências guardadas (`_btn_gerar_topbar`, `_btn_gerar_passo5`) + helper `_definir_estado_gerar()` sincroniza os dois |
| B3 | `_midia_selecionada` misturava dict e `StockMedia` | ✅ Corrigido | Imagem de IA agora entra como `StockMedia(source="ai")`; toggle usa `getattr(item,"id")` |
| B6 | `_carregar_letra_arquivo` órfão | ✅ Corrigido | Virou o botão "Carregar arquivo" da etapa 1 |
| B7 | "RESUMO DO CLIPE" estático | ✅ Corrigido | `_atualizar_resumo_clipe()` lê o estado real |
| B8 | "← Voltar" da etapa 1 ia para "imagens" | ✅ Corrigido | Botão substituído por "Carregar arquivo" |
| B9 | `var_formato`/`var_fps` órãos na etapa 5 | ✅ Removidos | Fonte única passa a ser `var_video_format`/`var_video_fps` do painel direito |
| B4 | `_passo_atual` escrita, nunca lida | ⏸ Mantido | Agora lido (usado para saber passo atual); mantido de propósito |
| B5 | `_extrair_queries` código morto | ⏸ Mantido | Pode servir a integração futura |

### 8.2 Defeitos visuais: RESOLVIDOS

| Defeito | Antes | Depois |
|---|---|---|
| Sidebar estreita demais | 60px, ilegível | 196px, itens numerados 01–05 |
| Subtítulo do passo cortado | altura 48px, texto cortado ao meio | 72px, tudo visível |
| Logo `>_` duplicado | topbar + sidebar | só na sidebar |
| Campo de letra sem orientação | caixa vazia gigante | placeholder-guia cinza |
| Galeria vazia | uma linha de texto | estado vazio com ícone + instruções |
| Resumo mentia | texto fixo | estado real |
| Tipografia inconsistente | ~90 fontes hardcoded | 0 (`Tema.fonte()` + tokens) |

### 8.3 Variáveis intencionalmente NÃO removidas

Conforme o aviso da seção 7.3, `var_lyrics_active`, `var_lyrics_pos`,
`var_font_size`, `var_agent`, `var_agent_style` e `entry_output` foram
**mantidas** — são candidatas a uso futuro por `legendas.py`/`agent.py`.
Apenas `var_formato`/`var_fps` foram removidas, por serem duplicatas
comprovadas de `var_video_format`/`var_video_fps`.

### 8.4 Verificação

- `pytest tests/test_clipes.py` → **33/33 passando**
- `_req_tmp/testar_gui_abre.py` → abre, constrói e navega as 5 etapas
- `_req_tmp/testar_bugs_ui.py` → B1, B2, B3a, B3b, B6, B7, B8, B9 **todos OK**
- Comparativo visual: `_req_tmp/comparacao_antes_depois.png`

### 8.5 Nota de ambiente

O interpretador deste projeto é o **Python 3.12 do sistema**
(`C://Users//User//AppData//Local//Programs//Python//Python312//python.exe`).
O Python gerenciado pelo WorkBuddy **não** tem `customtkinter`/`pytest`.

---

## 9. FEATURE: FLUXO DE LEGENDA + INTERPRETAÇÃO EMOCIONAL

Implementado conforme a especificação do usuário:

> "receber um áudio de música e a letra da música, caso não tenha a letra
> ele deve usar o whisper para transcrever a letra e depois gerar e gravar
> as legendas no vídeo. antes de gravar deve ter a opção de editar a
> legenda. apenas se a letra não for inserida. [...] o agente que faz a
> busca das imagens e vídeos precisa saber interpretar a música."

### 9.1 Fluxo agora tem 6 etapas (era 5)

```
01 Letra  ->  02 Legenda  ->  03 Áudio  ->  04 Imagens
   ->  05 Mídia  ->  06 Gerar
```

A ordem virou **fonte única da verdade** em `GuiClipes.PASSOS_ORDEM`;
sidebar, indicador do topo, navegação Voltar/Avançar e o harness leem
todos a mesma lista (antes havia 3 listas duplicadas que podiam
divergir silenciosamente).

### 9.2 Módulos novos

| Arquivo | Papel |
|---|---|
| `interpretacao.py` | Traduz **metáfora → emoção → cena filmável** |
| `transcricao.py` | faster-whisper, segmentos com tempo, quebra de frases |
| `renderizador_legendas.py` | Desenha e queima as legendas nos frames |

### 9.3 O ponto central: interpretar, não traduzir

O defeito raiz estava em `agent.py`, que concatenava a linha crua da
letra na query de busca, e em `_detectar_mood`, que casava a palavra
solta `"heart"` → ROMANTIC. Resultado: **"coração partido" buscava
rosas e casais** — o oposto da intenção.

Agora:

```
"estou de coração partido"
   -> emoção: TRISTEZA (confiança 0.75)
   -> busca: "person crying alone in dark room"
              "tears streaming down face close up"
              "silhouette sitting by rainy window"
```

Nenhum termo literal (`heart`, `broken`, `coracao`) aparece na query.
Isso está travado por teste em `TestInterpretacaoEmocional` e
`TestBuscaEmocionalIntegrada`.

### 9.4 Ordem de precedência da busca

`StockDatabase.gerar_search_terms_letra()` passou a tentar, nesta ordem:

1. **Camada emocional** (local, determinística) — caminho correto
2. **LLM (Gemini)** — quando configurado
3. **Heurística de frequência** — último recurso

A camada emocional vem **primeiro de propósito**: no caminho antigo a
heurística de frequência elegia justamente as palavras metafóricas
(era assim que "coracao" virava termo de busca).

### 9.5 Legendas: quando aparecem

| Situação | Comportamento |
|---|---|
| Letra digitada | Etapa 2 mostra as linhas com **tempo estimado** para revisão |
| Sem letra | Botão **"Transcrever do áudio"** roda o Whisper |
| Após transcrever | `quebrar_em_frases()` fatia segmentos longos do Whisper |

O Whisper agrupa vários versos num segmento (medido: 3 versos num
único bloco de 7s). `quebrar_em_frases(max_segundos=5.0)` divide por
frase e distribui o tempo por peso de palavras, mantendo os trechos
**contíguos** (sem buraco nem sobreposição) — também travado por teste.

### 9.6 Gravação no vídeo

`gerar_clipe()` ganhou `legendas=` e `salvar_srt=`. As legendas são
queimadas **depois do áudio**, para o clipe já ter a duração definitiva
(evita SRT com tempos além do vídeo). Legendas órfãs são descartadas com
aviso. Falha na legenda **não derruba o vídeo** — a legenda é acessória
e o vídeo já custou minutos para montar. O `.srt` sai ao lado do `.mp4`.

Renderização por Pillow, não `TextClip`/ImageMagick: o ImageMagick
costuma faltar no Windows e quebraria no meio do render. Verificado com
acentuação completa (`ç ã õ á é í ó ú â ê ô à`), travessão e quebra
automática de linha.

### 9.7 Verificação

- `pytest tests/test_clipes.py` → **62/62 passando** (eram 33)
- `_req_tmp/testar_gui_abre.py` → 6 etapas, round-trip de tempo,
  clamp de inversão, `PASSOS_ORDEM == NAV_ITEMS`
- Render real de ponta a ponta com legenda queimada e frame extraído
  do `.mp4` confirmando o texto na tela
- Transcrição real (`small`, áudio de 10.3s): 2 segmentos → 4 linhas,
  CUDA float16 → fallback CPU int8 exercitado

### 9.8 Pendências conhecidas

- **Revisar emoções não cobertas:** linhas como "quando a noite cai
  sobre a cidade" e "eu ainda escuto a tua voz" retornam MELANCOLIA com
  confiança 0.10 (neutro). Funciona como *fallback* visual neutro, mas se
  o usuário quiser precisão nelas, o léxico precisa de mais entradas.
- **Modelo `tiny` do Whisper:** o cache estava corrompido (arquivos de
  0 byte) e foi removido. `small` (padrão) e `large-v3` estão íntegros.

---

## 10. FEATURE: CÁLCULO DE CLIPES PELA MÚSICA

**Pedido (2026-09-17):** *"o código precisa aprender a calcular, encaixar
a quantidade de imagens e vídeos de acordo com a música."*

### 10.1 O defeito que isto corrige

`gerador.py` fazia:

```python
duracao_por_clip = duracao_total / max(len(clips), 1)
```

Três consequências, todas visíveis no resultado final:

1. **Todo clipe durou o mesmo tempo.** A música não tinha voz nenhuma na
   decisão — o número de mídias escolhidas na tela mandava.
2. **O corte caía no meio da palavra.** Cortes em intervalo fixo não têm
   relação com onde a frase termina.
3. **A conta nunca "encaixava".** Sobrava ou faltava mídia, e o vídeo
   ficava mais curto ou mais longo que a música.

### 10.2 Arquitetura nova — 3 módulos, cada um com uma responsabilidade

| Módulo | Responde | Depende de |
|---|---|---|
| `analise_audio.py` | Onde estão as batidas e a energia | librosa |
| `planejador.py` | **Quantos clipes a música pede** e qual mídia em cada um | analise_audio |
| `descricao_musical.py` | O que a descrição livre do usuário significa | interpretacao |

O `planejador.py` só **calcula** — devolve um `PlanoClipe`. Quem baixa
mídia e renderiza é o `gerador.py`. Isso deixa o cálculo testável sem
tocar em rede nem em ffmpeg.

### 10.3 Como o plano é derivado (ordem de preferência)

```
1. FRASES   — tempos do Whisper; cada clipe cobre uma frase
              → o corte cai no silêncio depois da palavra
2. BATIDA   — grade de batidas do librosa (sem letra, ou por escolha)
3. FIXO     — divisão uniforme (fallback, sempre avisado na tela)
```

Se a letra não cobre a música inteira (intro instrumental, ou Whisper que
perdeu o final), a sobra é preenchida por uma grade que **começa colada no
fim da última frase** — nunca em 0, senão abriria buraco preto.

### 10.4 Regras confirmadas pelo usuário

| Pergunta | Decisão | Onde vive |
|---|---|---|
| Ritmo | Pela letra (frases) | `ConfigRitmo.modo` |
| Frase longa | Só fatia passando do máximo **com folga** | `max_por_clipe × (1 + tolerancia)` = 6×1.2 = **7.2s** |
| Sem letra | Cai para a batida | `slots_de_batida()` |
| Descrever a música | Campo livre + sugestões clicáveis | `descricao_musical.py` |
| Letra vs descrição | **Combinar sempre** — letra é o eixo | `combinar_cenas()` (2 letra : 1 descrição) |
| Descrever a música | Campo livre + sugestões clicáveis | `descricao_musical.py` |
| Repetição | Reciclar **embaralhando cada volta** | `reciclar_midias()` semente fixa |
| Efeito | **Pela natureza da mídia** | vídeo → `corte`; imagem → movimento pela energia |
| Alternância | Sugere pelo algoritmo, **sempre editável** | energia ≥ 0.5 prefere vídeo |

### 10.5 Verificação (evidência real, não suposição)

**a) Duração deixa de ser plana.** 30s com 5 frases de tamanhos diferentes:

| Antes (divisão cega) | Agora (pela letra) |
|---|---|
| 5.0 / 5.0 / 5.0 / 5.0 / 5.0 / 5.0 | **3.20 / 6.20 / 4.60 / 4.50 / 5.75 / 5.75** |

**b) Soma fecha com a música:** `3.2+6.2+4.6+4.5+5.75+5.75 = 30.0` ✔

**c) Render real de ponta a ponta** (3 imagens, 12s, frases 2/5/5s):
```
[IMAGE] [1/3] img1.jpg (+zoom_in, 2.0s)
[IMAGE] [2/3] img0.jpg (+zoom_out, 5.0s)
[IMAGE] [3/3] img2.jpg (+zoom_in_out, 5.0s)
ffprobe → 12.000000 s
```
Cada clipe com a **sua** duração e o **seu** efeito. O código antigo daria
4.0s para os três, com um efeito único.

**d) Buraco real encontrado e corrigido:** letra terminando em 19.0s com
grade de 5s começando em 0 fazia o primeiro slot extra cair em 20.0 e
**1s da música ficava sem imagem**. Corrigido com `_grade_uniforme(inicio, ...)`.
Cobertura agora é 90.0/90.0 sem buraco.

**e) BPM conferido contra verdade sintética:** metrônomo de 92 BPM →
detectado 92.3. A grade usou batidas reais (intervalos irregulares de
5.9 / 5.2 / 5.2s), não passo fixo.

**f) Testes:** `pytest tests/test_clipes.py` → **101/101** (eram 62).
Os 39 novos cobrem tolerância, reciclagem/embaralhamento, efeito por
natureza, energia→mídia, alinhamento do plano ao download e cobertura
sem buraco.

### 10.6 Painel na tela (etapa Mídia, coluna direita)

```
RITMO DO CORTE
  [ Pela letra (frases) ▾ ]     ← frases | batida | fixo
  Duração máxima por clipe (s)  —————●———  6.0
  Tolerância antes de fatiar (%) ———●————  20.0
  [ Batidas por troca de cena ▾ ]   4

MÚSICA (opcional)
  [ tribal com tambores e violão clássico ]
  Exemplos: · música para relaxar e dormir
            · tribal com tambores, pesado
            · solo de piano clássico, triste
  Entendi: tambor, violão · euforia · ritmo tribal

PREVISÃO
  18 clipe(s) · frases
  ~4.9s por clipe
  cobre 89s de 90s
  faltam 10 mídia(s) — 2 reciclagem(ns)
  [ Recalcular previsão ]
```

A previsão é calculada **antes** de gerar: o usuário descobre que faltam
10 mídias e que haverá 2 reciclagens sem esperar o render.

### 10.7 A descrição chega na busca

Não é campo decorativo. Em `_busca_automatica()`:

```
[SEARCH] Terms da letra: ...
[SEARCH] + descrição (tambor, violão · euforia · ritmo tribal): tribal drums, acoustic guitar
[SEARCH] 8 termo(s) no total
```

`termos_de_busca()` combina as cenas da letra com as da descrição na
proporção do peso (teto **0.6**, para a letra nunca ser ignorada). Cenas
internas em português são traduzidas para termos que o banco entende via
`ALIAS_BUSCA` (ex: `"hands drumming on djembe close up"` → `"tribal drums"`).

Conflito de clima entre letra e descrição é **avisado, não resolvido** —
as duas são combinadas e o usuário ajusta se não servir.

### 10.8 Pendências conhecidas

- `_normalizar_bpm` não corrige 184 (já está dentro da faixa 50–200, então
  o loop não dispara). Detecção real de 92 BPM funciona; fica como borda.
- Modo "batida" depende de `librosa` (instalado, 0.11.0). Sem ele o plano
  cai para "fixo" com aviso — nunca quebra.

## 11. FEATURE: LETRA EDITÁVEL + CORRETOR ORTOGRÁFICO

> Mandato do usuário: *"precisa deixar editar a letra pq o whisper
> transcreve com erros de ortografia ou pronuncia as vezes"*.
> Decisões: a legenda é a fonte da verdade; sugerir a correção pronta;
> avisar (não decidir) sobre a divergência etapa 01 × legenda.

O Whisper acerta a fonética e erra a grafia: ouve "voz" e escreve
"vois", ouve "coração" e escreve "corecao", ouve "razão" e escreve
"razao". Esses erros não eram problema até virarem **termos de busca**
no banco de mídia — o defeito concreto era corrigir "vois" na etapa 02
e a busca continuar procurando "vois" porque lia a etapa 01.

### 11.1 A legenda é a fonte da verdade

`GuiClipes._letra_oficial()` devolve a `_letra_da_legenda()` se houver
linhas; senão, a caixa da etapa 01. Todos os consumidores (busca,
resumo, prompt, validação de "gerar", conflito de clima) passaram a ler
`_letra_oficial()`. A caixa da etapa 01 vira **espelho**, editável mas
não autoritativa.

A etiqueta `_legenda_origem` distingue:

* `"transcricao"` — tempos REAIS do Whisper. `_sincronizar_legenda_com_letra`
  nunca sobrescreve, mesmo se a etapa 01 mudar (aqui a divergência é
  só avisada).
* `"letra"` — tempos estimados a partir da letra digitada. Se a etapa
  01 mudar, a legenda é remontada silenciosamente — os tempos ali não
  eram preciosos.
* `""` — sem linhas (estado vazio).

### 11.2 Aviso de divergência

`GuiClipes._lbl_divergencia` (em `barra`, segunda linha, começa com
`text=""` para não empurrar o layout). Mostrado quando
`_letra_diverge()` é True:

* origem `"transcricao"`: "A caixa da etapa 01 está diferente da
  legenda. A legenda é que vale — ela tem os tempos reais do áudio, e
  é ela que a busca já está usando."
* origem `"letra"`: "A caixa da etapa 01 mudou depois que a legenda
  foi montada. A busca está usando a legenda."

Junto ao aviso, o botão "Usar a legenda na etapa 01" copia a legenda
revisada para a caixa (`_espelhar_legenda_na_letra()`), deixando os
dois lugares consistentes.

### 11.3 Corretor ortográfico (`corretor_letra.py`)

Consta no `~5.2s` total (≈ 4s de construção do índice + ~1s de
verificação) contra >100s de `spylls.suggest()` direto. O dicionário
é carregado uma vez por instância (`GuiClipes._dic_pt`).

**3 serviços:**

1. `encontrar_suspeitas(texto, dicionario)` — lista palavras que o
   dicionário não conhece; ignora < 3 letras, ALL-CAPS, hifens.
2. `corrigir_texto(texto, aceitas)` — substituições palavra-inteira,
   preservando caixa inicial; comparação crua (não normalizada) para
   que troca de acento (`razao`→`razão`) não seja rejeitada como
   no-op.
3. `corrigir_por_fonetica(texto)` — auto-aceita correções em alta
   confiança (chave fonética bate **e** distância ≤ 2 **e** sem
   empate). Critério conservador: corromper o texto em silêncio é pior
   que não corrigir.

**Por que `voz` ganha de `vos` agora:**

* antes — `_forma_comparavel("correção")` colapsava o "rr" virando
  `"corecao"` idêntico ao input `corecao` → distância 0; e
  `correção` tinha mais flags no `.dic` que `coração` → escolhida
  como primeira sugestão.
* depois — `_forma_comparavel` parou de colapsar letra dobrada (isso é
  papel da `chave_fonetica`, que mede som). Agora `corecao` está a 1
  edição de `correção` **e** de `coração` — empate → marcado como
  ambíguo → usuário escolhe. Sem a etapa 03, "vos" (3 letras)
  ganhava de "voz" (4) por tie-break de tamanho; agora o desempate
  dentro do mesmo band usa o **paradigma morfológico** do `.dic`:
  `voz/BOVÌÚ` tem 5 flags (forma viva), `vos` (pronome arcaico)
  tem zero — `voz` ordena primeiro.

### 11.4 Card de ortografia na etapa 02

Em `GuiClipes._criar_frame_legenda`, layout reescrito:

| linha  | conteúdo                                |
|--------|-----------------------------------------|
| 0      | "ETAPA 02 · LEGENDA"                    |
| 1      | "Revisar Legenda"                       |
| 2      | barra (transcrever, status, revisar ort., divergência) |
| 3      | **card ORTOGRAFIA** (só após revisão)   |
| 4      | lista de linhas (weight=1)              |
| 5      | botões voltar / avançar                 |

O card (`_card_ortografia`) é oculto por padrão; só entra no grid em
`_mostrar_suspeitas()`. Dentro dele: status com contagem
("4 palavra(s) fora do dicionário · 2 com correção óbvia · 2 que só
você resolve") + "Aplicar as óbvias" + lista de chips com até 4
sugestões + "ignorar" por palavra.

Botões por linha de legenda:

* clicar em `voz` → aplica a troca via `corrigir_texto` na legenda
  E no espelho da etapa 01 (só se não há divergência — não passar
  por cima do que o usuário digitou na etapa 01);
* clicar em `ignorar` → adiciona à `_ignoradas`, próxima revisão não
  reclama.

### 11.5 Verificação

* `tests/test_clipes.py::TestCorretorLetra` (15 casos puros, sem
  dicionário): chave fonética, forma comparável, ranqueamento,
  detecção de empate, `corrigir_texto`.
* `TestCorretorComDicionario` (6 casos, pulam se sem dicionário):
  marca `vois`/`nacer`, NÃO marca `nacer` em texto limpo, auto-correção
  recusa ambíguo.
* `_req_tmp/testar_ortografia_gui.py` (30 asserções end-to-end):
  legenda como fonte, divergência, correção individual, espelho,
  proteção da transcrição, remontagem quando origem = "letra".

Total da suíte: 129 passing (era 106, +23).

### 11.6 Captura

`_req_tmp/capturar_ortografia.py` (reusa o WinAPI do
`testar_gui_abre.py` para forçar a janela a coordenadas reais).
Resultado em `_req_tmp/prints_orto/etapa_ortografia.png`.

### 11.7 Pendências conhecidas

- O corretor pede um dicionário Hunspell; sem o LibreOffice instalado
  (ou com o módulo `spylls` indisponível), a etapa 02 fica sem o card
  de ortografia mas o resto do fluxo continua intacto. Decisão
  deliberada: **clipe tem que sair mesmo sem corretor**.
- A captura de screenshot depende do WinAPI
  `GetParent(winfo_id)` + `SetForegroundWindow`; rodar a GUI em
  ambiente headless (sem janela visível) ainda devolve `(0, 0, 0, 0)`.
  Documentado na skill `customtkinter-ui-refactor`.

---

## 12. FEATURE: BUSCA DE MÍDIA — DIAGNÓSTICO E PREENCHIMENTO

> Data: 2026-09-17 · Origem: "por api os resultados são tão ruins" +
> "quando não houver imagens e vídeos de acordo ele pode gerar prompts"

### 12.1 O problema relatado

O usuário observou que a **busca manual** (digitar "rain" no site da
Pexels) funciona perfeitamente, mas a **busca por API** dentro do app
devolvia "quase sem vídeos e muitas imagens totalmente fora de contexto".

### 12.2 Causa 1 — `apenas_videos` era ignorado (`database.py`)

Em `_buscar_pexels` e `_buscar_pixabay`:

```python
# ERRADO — a segunda metade nunca importa quando buscar_fotos=True
buscar_fotos  = not apenas_videos or (apenas_fotos and apenas_videos)
buscar_videos = not apenas_fotos  or (apenas_fotos and apenas_videos)
```

Com a chamada histórica da GUI (`apenas_fotos=True, apenas_videos=True`),
as duas expressões resultavam `True`, o que "por acidente" funcionava.
Mas em qualquer chamada só-de-vídeo (`apenas_videos=True, apenas_fotos=False`)
o resultado era `buscar_videos=False` — **a busca por vídeo nunca acontecia**.

Medição (API real):
```
_buscar_pexels("rain", apenas_videos=True)  -> 15 fotos, 0 vídeos
endpoint Pexels /videos/search?query=rain   -> 7.612 vídeos disponíveis
```

**Correção** — tabela de decisão explícita e legível:
```python
apenas_um = apenas_fotos != apenas_videos
buscar_fotos  = (not apenas_um) or apenas_fotos
buscar_videos = (not apenas_um) or apenas_videos
```
Semântica: nenhum marcado → os dois; um marcado → só ele; os dois → os dois.

### 12.3 Causa 2 — o corte `[:max_results]` apagava os vídeos

`_buscar_*` coleta fotos primeiro e vídeos depois. `pesquisar()` cortava
a lista com `results[:max_results]`, então as fotos enchiam a cota e os
vídeos eram descartados — **mesmo com a Causa 1 já corrigida**.

Medição: `StockSearch.total=30` (15 fotos + 15 vídeos), `len(results)=15`,
todos `photo`.

**Correção** — `StockDatabase._intercalar_tipos()` alterna
vídeo/foto/vídeo/foto preservando a ordem de relevância interna de cada
tipo, de modo que ambos sobrevivam a qualquer cota.

### 12.4 Causa 3 — frases longas não são termos de busca (`encurtador_busca.py`)

`interpretacao.CENAS` descreve cenas como frases cinematográficas:

```
"empty apartment at night one lamp"
"single person alone in crowded street"
```

Ótimas como **prompt de IA**; péssimas como **query de stock**. Pexels e
Pixabay indexam conceitos de 2-3 palavras e fazem match por palavra
isolada, então uma frase de 5 palavras cai em match parcial nas palavras
genéricas (`person`, `empty`, `night`) — **é a origem das "imagens fora
de contexto"**.

**Correção** — `encurtador_busca.termo_curto()` escolhe o núcleo visual:
1. remove stopwords gramaticais (`a`, `of`, `in`, `by`...);
2. ancora no **primeiro substantivo** (modificadores fracos como
   `single`, `lone`, `empty`, `dark` não podem liderar o termo);
3. adiciona os últimos termos de conteúdo como contexto, preferindo
   não-modificadores;
4. limita a 3 palavras.

Aplicado em `StockDatabase._encurtar_para_busca()`, no ponto único de
saída de `_gerar_terms_letra_pura()` — cobre os três caminhos
(emocional, LLM e heurística). Os termos de tema já eram curtos e passam
intactos.

Resultado:
```
"empty apartment at night one lamp"      -> "apartment night lamp"
"single person alone in crowded street"  -> "person crowded street"
"lone figure on empty beach winter"      -> "figure beach winter"
```

### 12.5 Seletor de tipo de mídia (GUI)

Novo `CTkSegmentedButton` na barra da etapa 04, ao lado de
"Buscar Automaticamente": **Meio a meio · Mais vídeos · Mais fotos**
(`self.var_tipo_midia`, default "Meio a meio").

`_busca_automatica()` traduz o rótulo em flags:
```python
apenas_f = pref == "Mais fotos"
apenas_v = pref == "Mais vídeos"
```

Nota de tema: o texto do segmento usa `Tema.TEXTO_SOBRE_PRIMARIA` (escuro),
porque o segmento selecionado fica verde (`PRIMARY` `#4ADE80`) e o texto
claro padrão desaparecia sobre ele.

### 12.6 Preenchimento com prompts de IA (`preenchedor_prompts.py`)

Quando a busca rende menos que `MINIMO_MIDIA_SUFICIENTE = 6` itens, o
vídeo passaria a repetir mídia (reciclagem). Em vez disso,
`_oferecer_prompts_preenchimento()` mostra um card laranja na galeria com
prompts prontos.

- `gerar_prompts(bases, quantos, tipos)` alterna **image / video**;
- prompts de vídeo recebem movimento de câmera
  (`slow cinematic camera push in`, `aerial drone shot`, `slow pan left`);
- prompts de imagem recebem qualidade
  (`cinematic still, shallow depth of field`, `moody film photography, 35mm`);
- sufixo comum `no text, no watermark, no letters` (evita legenda queimada
  que o próprio app vai sobrepor);
- fonte de vocabulário: **tema** (`temas_musicais.TEMAS`) quando detectado,
  senão as cenas emocionais (`interpretacao.CENAS`);
- botão **"Usar prompt"** carrega o texto no campo de IA e o status pede
  "clique em Gerar IA".

### 12.7 Verificação

- `pytest tests/test_clipes.py -q` → **161 passando** (era 140; +21 novos).
- `TestEncurtadorBusca` (6), `TestPreenchedorPrompts` (5),
  `TestFlagsTipoMidia` (7), `TestModoParaFlags` (4).
- Captura: `_req_tmp/prints_preench/etapa04_fallback.png` mostra o
  segmentador e o card de prompts.
- End-to-end com letra real: Meio a meio → 50 vídeos + 50 fotos;
  Mais vídeos → 100 vídeos; Mais fotos → 100 fotos.

### 12.8 Armadilha registrada

`StockDatabase._cache` é indexado por
`f"{provider}:{query}:{apenas_fotos}:{apenas_videos}"`. Ao depurar as
flags, resultados **pré-correção** ficam cacheados e mascaram o conserto —
um teste mostrou `0 vídeos` mesmo após a correção. Sempre limpar
`db._cache` (ou usar query nova) ao revalidar mudanças de busca.
