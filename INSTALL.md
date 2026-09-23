# 📦 Instalação — MusicClipStudio

Guia completo para instalar e rodar pela primeira vez. Sem compilar nada,
sem Docker (mas funciona em Docker se você quiser).

## Pré-requisitos

| Ferramenta | Versão mínima | Como instalar |
|---|---|---|
| **Python** | 3.10 | https://www.python.org/downloads/ (Linux: já vem) |
| **Node.js** | 18 | https://nodejs.org (ou via gerenciador de pacotes) |
| **FFmpeg** | qualquer recente | `sudo pacman -S ffmpeg` / `sudo apt install ffmpeg` / `winget install ffmpeg` |
| **Chromium p/ Playwright** | — | instalado pelo comando abaixo (render das cenas) |

> Verifique: `python3 --version`, `node --version`, `ffmpeg -version`

## Instalação em 6 passos

```bash
# 1. Baixe o projeto (clone os DOIS repositórios, frontend é separado)
git clone https://github.com/SEU_USUARIO/MusicClipStudio.git
cd MusicClipStudio
git clone https://github.com/SEU_USUARIO/musicclipstudio-landing.git musicclipstudio-landing

# 2. Ambiente Python + dependências
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Chromium do Playwright (renderiza as cenas em frames)
playwright install chromium

# 4. Chaves de API (gratuitas — links e instruções na etapa 01 do app)
cp .env.example .env
nano .env                         # ou seu editor; preencha as que quiser

# 5. Frontend: dependências
cd musicclipstudio-landing
npm install
cd ..

# 6. Suba tudo
./RUN_WEB.sh                      # Windows: RUN_WEB.bat
# → Studio em http://127.0.0.1:3100/studio
```

## Primeiro uso dentro do app

1. **Crie sua conta** na tela de login (nome + senha de 8+ caracteres) —
   cada conta guarda as próprias chaves, criptografadas no seu computador.
2. **Etapa 01 · Chave API**: a tela mostra os 7 bancos, como criar a chave
   em cada um e um botão que abre o site oficial. Cole a chave no diálogo
   (ícone de chave no topo). *Mínimo: 1 banco configurado.*
3. Siga o wizard: **02 Letra** → **03 Áudio** → **04 Legenda** →
   **05 Imagens** (IA gera as cenas) → **06 Mídia** (busca nos bancos) →
   **07 Gerar** (MP4 final com a duração exata da música).

## Parar / reiniciar / logs

```bash
./PARAR_WEB.sh                    # derruba backend e frontend
tail -f /tmp/mcs_backend.log      # log do backend
tail -f /tmp/mcs_frontend.log     # log do frontend
```

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `backend ainda não respondeu` | dependência faltando | `pip install -r requirements.txt`; veja `/tmp/mcs_backend.log` |
| Busca de mídia vazia | nenhuma chave configurada | etapa 01 do app (ou `.env`) |
| Transcrição demora muito | 1º download do modelo Whisper (~460 MB) | aguarde; com `HF_TOKEN` no `.env` vai mais rápido |
| Render falha sem log | Chromium do Playwright ausente | `playwright install chromium` |
| Porta ocupada | outra instância rodando | `./PARAR_WEB.sh` e suba de novo |

## Desinstalar

Apague a pasta do projeto. Tudo (contas, chaves, projetos, clipes) vive dentro dela:
`output/` (dados), `database/` (cache de mídia), `venv/` (Python).

## Atualizar

```bash
git pull                          # na raiz e no musicclipstudio-landing
pip install -r requirements.txt   # se requirements mudou
cd musicclipstudio-landing && npm install && cd ..
rm -rf musicclipstudio-landing/.next   # força rebuild do frontend
./RUN_WEB.sh
```

## Segurança

Veja [SEGURANCA.md](SEGURANCA.md) — como suas chaves e senhas são guardadas,
o que o app envia (e não envia) para a internet.
