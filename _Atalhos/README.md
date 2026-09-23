# Pasta de Atalhos · MusicClipStudio WEB

Esta pasta contém os arquivos de atalho para você colocar na sua **Área de Trabalho (Desktop)**.

## 🚀 2 cliques para instalar

1. Abra esta pasta no Explorador de Arquivos
2. **Duplo clique em `INSTALAR_atalho_na_Desktop.bat`**
   - (Autorize qualquer aviso do Windows)
   - Ele pergunta se você quer sobrescrever (caso já exista)
3. Pronto — sua Desktop agora tem dois atalhos:

| Atalho na Desktop | O que faz |
|---|---|
| 🎵 **`MusicClipStudio WEB.bat`** | **Lançador principal** → liga backend + frontend + abre Studio no navegador |
| 🧭 **`MusicClipStudio Studio (Web).url`** | **Acesso rápido** → só abre o Studio (use se a stack **já estiver rodando**) |

---

## 🔧 Arquivos desta pasta (referência)

| Arquivo | Propósito |
|---|---|
| `MusicClipStudio_WEB.bat` | Lançador que vai para a Desktop |
| `INSTALAR_atalho_na_Desktop.bat` | Instala o atalho acima via cmd do Windows (simples) |
| `_instalar_atalhos.py` | Mesmo que acima, mas em Python (mais robusto, fallback para casos de encoding) |

---

## ✋ Se o instalador automático NÃO funcionar (caso raro)

**Faça manualmente em 2 segundos:**
1. Clique com o botão direito em **`MusicClipStudio_WEB.bat`**
2. Clique em **Enviar para → Área de Trabalho (criar atalho)**
3. (opcional) Renomeie o atalho na sua Desktop para **`MusicClipStudio WEB`**

---

## 💡 Dicas

- A primeira vez que você rodar o atalho, o Next.js compila os arquivos. Demora ~8 segundos (Turbopack acelera muito nas próximas vezes).
- Para **desligar tudo**, basta fechar as **2 janelas CMD** que ficam abertas em segundo plano.
- Quer que a stack inicie sozinha quando você ligar o Windows? Coloque um atalho do `MusicClipStudio_WEB.bat` dentro de `shell:startup` (tecla Win+R e cole isso).
