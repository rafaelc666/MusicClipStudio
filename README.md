# 🎬 MusicClipStudio WEB

Transforme sua música pronta em um **clipe musical completo** — com cenas escolhidas por IA a partir da letra, mídia de bancos gratuitos (Pexels, Pixabay, Unsplash, NASA, Coverr, Giphy, Openverse), legendas sincronizadas por Whisper e render final MP4.

> A música é a **entrada** (o app não gera música). O resto — cenas, mídia, legenda, render — é com o Studio.

## ✨ Destaques

- **Wizard de 7 etapas**: 01 Chaves de API → 02 Letra → 03 Áudio → 04 Legenda → 05 Imagens (IA) → 06 Mídia → 07 Gerar
- **Multiusuário local**: cada conta guarda as próprias chaves criptografadas (Fernet) — nada sai do seu computador
- **Bancos ilimitados**: adicione quantos bancos próprios quiser, com endpoint de API customizável por banco
- **Busca multi-banco**: a galeria mistura resultados de **todos** os bancos ligados
- **Cenas inteligentes**: a IA lê a letra, detecta o tema (gospel, rock, dança…) e gera uma cena por beat
- **Legendas**: transcrição automática (Whisper) com editor de linhas, adicionar/remover frases
- **Render**: MP4 na proporção que você escolher (9:16, 16:9, 1:1…), com duração exata da música
- **Intro animada**, temas rápidos de busca, preview ilustrativo ao vivo

## 🚀 Como rodar

Requisitos: **Python 3.10+**, **Node 18+**, **FFmpeg** instalado.

```bash
# 1. Backend (FastAPI na porta 8300)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # e preencha com as suas chaves (gratuitas)

# 2. Frontend (Next.js na porta 3100)
cd musicclipstudio-landing
npm install

# 3. Subir tudo
./RUN_WEB.sh                    # Windows: RUN_WEB.bat
# → Studio em http://127.0.0.1:3100/studio
```

Na primeira execução, crie sua conta na tela de login e configure pelo menos 1 banco
de mídia na **etapa 01** (a tela traz o link de cada site e explica como criar a chave).

## 🔑 Chaves de API

O `.env` nunca é commitado; dentro do app cada usuário também pode colar as chaves
próprias (criptografadas no banco local, `output/usuarios.db`).

**Mídia — fotos e vídeos** (todas gratuitas):

| Banco | Onde criar |
|---|---|
| Pexels | https://www.pexels.com/api/ |
| Pixabay | https://pixabay.com/api/docs/ |
| Unsplash | https://unsplash.com/developers |
| NASA Images | https://api.nasa.gov/ |
| Coverr | https://coverr.co |
| Giphy | https://developers.giphy.com/ |
| Openverse | https://api.openverse.org/ |

**Áudio — trilha** (opcional: a etapa 03 funciona sem ela):

| Serviço | O que dá | Onde criar |
|---|---|---|
| Epidemic Sound | música, com licença comercial | https://developers.epidemicsound.com/docs/ |

> ⚠️ **Nem tudo aqui é grátis.** O Epidemic Sound **não** é chave grátis: é a
> *Partner API*, que exige acordo de parceria, e a licença comercial segue o
> contrato. E o **Pixabay não serve música pela API** (só fotos e vídeos,
> confirmado em 24/09/2026): música lá é download manual no site.

## 🧪 Testes

```bash
./venv/bin/python -m pytest tests/ -q     # suíte do motor/backend
cd musicclipstudio-landing && npx tsc --noEmit
```

## 🏗️ Arquitetura

```
musicclipstudio-landing/   Next.js (wizard, dashboard, preview)
backend/app/main.py        FastAPI (letra, áudio, legenda, mídia, jobs de render)
scene_engine/              beats, prompts, render HTML→MP4 (FFmpeg)
agent.py                   agente de cenas (letra → prompts por beat)
temas_musicais.py          catálogo de temas (gospel, rock, dança…) com estética
database.py                clientes dos bancos de mídia (7 APIs)
backend/app/auth_store.py  contas + chaves criptografadas por usuário
engine.py                  orquestração do clipe
```

## 📄 Licença

MIT — veja [LICENSE](LICENSE).
