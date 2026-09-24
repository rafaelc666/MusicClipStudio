"""
Interface gráfica para configuração de APIs de mídia.

Permite ao usuário configurar chaves de API para Pexels, Pixabay e Unsplash,
habilitar/desabilitar provedores, testar conexões e salvar configurações.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from MusicClipStudio.config import ClipConfig, load_config, save_config
from MusicClipStudio.database import StockDatabase


class APIConfigUI:
    """Janela de configuração de APIs de mídia."""

    def __init__(self, parent=None):
        self.parent = parent
        self.config = load_config()
        self.db = StockDatabase(self.config)

        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Configuração de APIs de Mídia")
        self.window.geometry("600x500")
        self.window.resizable(False, False)

        self._create_widgets()
        self._load_config()

    def _create_widgets(self):
        """Cria os widgets da interface."""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(main_frame, text="Configuração de APIs de Mídia", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Notebook para abas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Aba Pexels
        pexels_frame = ttk.Frame(notebook, padding="10")
        notebook.add(pexels_frame, text="Pexels")
        self._create_pexels_tab(pexels_frame)

        # Aba Pixabay
        pixabay_frame = ttk.Frame(notebook, padding="10")
        notebook.add(pixabay_frame, text="Pixabay")
        self._create_pixabay_tab(pixabay_frame)

        # Aba Unsplash
        unsplash_frame = ttk.Frame(notebook, padding="10")
        notebook.add(unsplash_frame, text="Unsplash")
        self._create_unsplash_tab(unsplash_frame)

        # Aba NASA
        nasa_frame = ttk.Frame(notebook, padding="10")
        notebook.add(nasa_frame, text="NASA")
        self._create_nasa_tab(nasa_frame)

        # Aba Coverr
        coverr_frame = ttk.Frame(notebook, padding="10")
        notebook.add(coverr_frame, text="Coverr")
        self._create_coverr_tab(coverr_frame)

        # Aba Giphy
        giphy_frame = ttk.Frame(notebook, padding="10")
        notebook.add(giphy_frame, text="Giphy")
        self._create_giphy_tab(giphy_frame)

        # Aba Openverse
        openverse_frame = ttk.Frame(notebook, padding="10")
        notebook.add(openverse_frame, text="Openverse")
        self._create_openverse_tab(openverse_frame)

        # Aba IA de busca (⚠️ NOVO 24/09/2026)
        ia_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ia_frame, text="IA Busca")
        self._create_ia_tab(ia_frame)

        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Salvar", command=self._save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancelar", command=self.window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Testar Todas", command=self._test_all).pack(side=tk.LEFT)

    def _create_pexels_tab(self, parent):
        """Cria a aba de configuração do Pexels."""
        # Chave API
        ttk.Label(parent, text="Chave API:").pack(anchor=tk.W)
        self.pexels_key = ttk.Entry(parent, width=50)
        self.pexels_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.pexels_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.pexels_enabled).pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("pexels")).pack(pady=(10, 0))

        # Status
        self.pexels_status = ttk.Label(parent, text="", foreground="gray")
        self.pexels_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_pixabay_tab(self, parent):
        """Cria a aba de configuração do Pixabay."""
        # Chave API
        ttk.Label(parent, text="Chave API:").pack(anchor=tk.W)
        self.pixabay_key = ttk.Entry(parent, width=50)
        self.pixabay_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.pixabay_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.pixabay_enabled).pack(anchor=tk.W)

        # Buscar vídeos
        self.pixabay_videos = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Buscar vídeos", variable=self.pixabay_videos).pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("pixabay")).pack(pady=(10, 0))

        # Status
        self.pixabay_status = ttk.Label(parent, text="", foreground="gray")
        self.pixabay_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_unsplash_tab(self, parent):
        """Cria a aba de configuração do Unsplash."""
        # Chave API
        ttk.Label(parent, text="Chave API (Client-ID):").pack(anchor=tk.W)
        self.unsplash_key = ttk.Entry(parent, width=50)
        self.unsplash_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.unsplash_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.unsplash_enabled).pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("unsplash")).pack(pady=(10, 0))

        # Status
        self.unsplash_status = ttk.Label(parent, text="", foreground="gray")
        self.unsplash_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_nasa_tab(self, parent):
        """Cria a aba de configuração do NASA."""
        # Chave API
        ttk.Label(parent, text="Chave API (DEMO_KEY ou.nasa.gov):").pack(anchor=tk.W)
        self.nasa_key = ttk.Entry(parent, width=50)
        self.nasa_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.nasa_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.nasa_enabled).pack(anchor=tk.W)

        # Info
        ttk.Label(parent, text="Imagens e vídeos da NASA (images.nasa.gov)", foreground="gray").pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("nasa")).pack(pady=(10, 0))

        # Status
        self.nasa_status = ttk.Label(parent, text="", foreground="gray")
        self.nasa_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_coverr_tab(self, parent):
        """Cria a aba de configuração do Coverr."""
        # App ID
        ttk.Label(parent, text="App ID:").pack(anchor=tk.W)
        self.coverr_app_id = ttk.Entry(parent, width=50)
        self.coverr_app_id.pack(fill=tk.X, pady=(0, 10))

        # API Key
        ttk.Label(parent, text="API Key:").pack(anchor=tk.W)
        self.coverr_key = ttk.Entry(parent, width=50)
        self.coverr_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.coverr_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.coverr_enabled).pack(anchor=tk.W)

        # Info
        ttk.Label(parent, text="Vídeos gratuitos (coverr.co)", foreground="gray").pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("coverr")).pack(pady=(10, 0))

        # Status
        self.coverr_status = ttk.Label(parent, text="", foreground="gray")
        self.coverr_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_giphy_tab(self, parent):
        """Cria a aba de configuração do Giphy."""
        # API Key
        ttk.Label(parent, text="API Key:").pack(anchor=tk.W)
        self.giphy_key = ttk.Entry(parent, width=50)
        self.giphy_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.giphy_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.giphy_enabled).pack(anchor=tk.W)

        # Info
        ttk.Label(parent, text="GIFs animados (giphy.com)", foreground="gray").pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("giphy")).pack(pady=(10, 0))

        # Status
        self.giphy_status = ttk.Label(parent, text="", foreground="gray")
        self.giphy_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_openverse_tab(self, parent):
        """Cria a aba de configuração do Openverse."""
        # API Key
        ttk.Label(parent, text="API Key (v1):").pack(anchor=tk.W)
        self.openverse_key = ttk.Entry(parent, width=50)
        self.openverse_key.pack(fill=tk.X, pady=(0, 10))

        # Habilitado
        self.openverse_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.openverse_enabled).pack(anchor=tk.W)

        # Info
        ttk.Label(parent, text="Imagens e áudio (openverse.org - WordPress)", foreground="gray").pack(anchor=tk.W)

        # Botão testar
        ttk.Button(parent, text="Testar Conexão", command=lambda: self._test("openverse")).pack(pady=(10, 0))

        # Status
        self.openverse_status = ttk.Label(parent, text="", foreground="gray")
        self.openverse_status.pack(anchor=tk.W, pady=(5, 0))

    def _create_ia_tab(self, parent):
        """Aba da chave GENÉRICA de IA para a busca (⚠️ NOVO 24/09/2026).

        Uma única entrada aceita Google (AIza…), Groq (gsk_…), OpenRouter
        (sk-or-…) ou qualquer OpenAI-compatible (sk-…) — o provedor é
        detectado pelo prefixo. A IA só traduz a intenção da busca
        (letra/consulta PT → termos visuais EN); sem chave, a busca
        continua funcionando pelo caminho determinístico.
        """
        ttk.Label(parent, text="Chave de IA para pesquisa (opcional):").pack(anchor=tk.W)
        self.ia_key = ttk.Entry(parent, width=50)
        self.ia_key.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(parent, text="Modelo (vazio = default do provedor):").pack(anchor=tk.W)
        self.ia_model = ttk.Entry(parent, width=50)
        self.ia_model.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(parent, text="Base URL (só p/ OpenAI-compatible fora da lista):").pack(anchor=tk.W)
        self.ia_base = ttk.Entry(parent, width=50)
        self.ia_base.pack(fill=tk.X, pady=(0, 10))

        self.ia_enabled = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Habilitado", variable=self.ia_enabled).pack(anchor=tk.W)

        ttk.Label(
            parent,
            text="Aceita: AIza… (Gemini) · gsk_… (Groq) · sk-or-… (OpenRouter) · sk-… (genérico).\n"
                 "A IA não busca: gera os termos em inglês que os bancos entendem melhor.",
            foreground="gray",
        ).pack(anchor=tk.W)

        ttk.Button(parent, text="Testar IA", command=self._test_ia).pack(pady=(10, 0))

        self.ia_status = ttk.Label(parent, text="", foreground="gray")
        self.ia_status.pack(anchor=tk.W, pady=(5, 0))

    def _load_config(self):
        """Carrega a configuração atual."""
        self.pexels_key.insert(0, self.config.stock_pexels_api_key)
        self.pexels_enabled.set(self.config.stock_pexels_enabled)

        self.pixabay_key.insert(0, self.config.stock_pixabay_api_key)
        self.pixabay_enabled.set(self.config.stock_pixabay_enabled)
        self.pixabay_videos.set(self.config.stock_pixabay_videos)

        self.unsplash_key.insert(0, self.config.stock_unsplash_api_key)
        self.unsplash_enabled.set(self.config.stock_unsplash_enabled)

        self.nasa_key.insert(0, self.config.stock_nasa_api_key)
        self.nasa_enabled.set(self.config.stock_nasa_enabled)

        self.coverr_app_id.insert(0, self.config.stock_coverr_app_id)
        self.coverr_key.insert(0, self.config.stock_coverr_api_key)
        self.coverr_enabled.set(self.config.stock_coverr_enabled)

        self.giphy_key.insert(0, self.config.stock_giphy_api_key)
        self.giphy_enabled.set(self.config.stock_giphy_enabled)

        self.openverse_key.insert(0, self.config.stock_openverse_api_key)
        self.openverse_enabled.set(self.config.stock_openverse_enabled)

        self.ia_key.insert(0, self.config.stock_ia_api_key)
        self.ia_model.insert(0, self.config.stock_ia_model)
        self.ia_base.insert(0, self.config.stock_ia_base_url)
        self.ia_enabled.set(self.config.stock_ia_enabled)

    def _save(self):
        """Salva a configuração."""
        self.config.stock_pexels_api_key = self.pexels_key.get().strip()
        self.config.stock_pexels_enabled = self.pexels_enabled.get()

        self.config.stock_pixabay_api_key = self.pixabay_key.get().strip()
        self.config.stock_pixabay_enabled = self.pixabay_enabled.get()
        self.config.stock_pixabay_videos = self.pixabay_videos.get()

        self.config.stock_unsplash_api_key = self.unsplash_key.get().strip()
        self.config.stock_unsplash_enabled = self.unsplash_enabled.get()

        self.config.stock_nasa_api_key = self.nasa_key.get().strip()
        self.config.stock_nasa_enabled = self.nasa_enabled.get()

        self.config.stock_coverr_app_id = self.coverr_app_id.get().strip()
        self.config.stock_coverr_api_key = self.coverr_key.get().strip()
        self.config.stock_coverr_enabled = self.coverr_enabled.get()

        self.config.stock_giphy_api_key = self.giphy_key.get().strip()
        self.config.stock_giphy_enabled = self.giphy_enabled.get()

        self.config.stock_openverse_api_key = self.openverse_key.get().strip()
        self.config.stock_openverse_enabled = self.openverse_enabled.get()

        self.config.stock_ia_api_key = self.ia_key.get().strip()
        self.config.stock_ia_model = self.ia_model.get().strip()
        self.config.stock_ia_base_url = self.ia_base.get().strip()
        self.config.stock_ia_enabled = self.ia_enabled.get()

        save_config(self.config)
        messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
        self.window.destroy()

    def _test(self, provider: str):
        """Testa a conexão com um provedor."""
        # Atualizar chave antes de testar
        if provider == "pexels":
            self.config.stock_pexels_api_key = self.pexels_key.get().strip()
            status_label = self.pexels_status
        elif provider == "pixabay":
            self.config.stock_pixabay_api_key = self.pixabay_key.get().strip()
            status_label = self.pixabay_status
        elif provider == "unsplash":
            self.config.stock_unsplash_api_key = self.unsplash_key.get().strip()
            status_label = self.unsplash_status
        elif provider == "nasa":
            self.config.stock_nasa_api_key = self.nasa_key.get().strip()
            status_label = self.nasa_status
        elif provider == "coverr":
            self.config.stock_coverr_app_id = self.coverr_app_id.get().strip()
            self.config.stock_coverr_api_key = self.coverr_key.get().strip()
            status_label = self.coverr_status
        elif provider == "giphy":
            self.config.stock_giphy_api_key = self.giphy_key.get().strip()
            status_label = self.giphy_status
        elif provider == "openverse":
            self.config.stock_openverse_api_key = self.openverse_key.get().strip()
            status_label = self.openverse_status
        else:
            return

        status_label.config(text="Testando...", foreground="gray")
        self.window.update()

        def test_in_thread():
            result = self.db.testar_conexao(provider)
            self.window.after(0, lambda: self._update_status(status_label, result))

        thread = threading.Thread(target=test_in_thread, daemon=True)
        thread.start()

    def _update_status(self, label, result):
        """Atualiza o label de status."""
        if result["sucesso"]:
            label.config(text=f"✓ Conectado ({result['resultados']} resultados)", foreground="green")
        else:
            label.config(text=f"✗ Erro: {result['erro']}", foreground="red")

    def _test_ia(self):
        """Testa a chave genérica de IA (detecção + 1 chamada real)."""
        from MusicClipStudio import ia_busca

        chave = self.ia_key.get().strip()
        provedor = ia_busca.detectar_provedor(chave)
        if not chave:
            self.ia_status.config(text="sem chave informada", foreground="gray")
            return
        if not provedor:
            self.ia_status.config(
                text="✗ prefixo não reconhecido (AIza…/gsk_…/sk-or-…/sk-…)",
                foreground="red")
            return

        self.ia_status.config(
            text=f"Testando {provedor}…", foreground="gray")
        self.window.update()
        modelo = self.ia_model.get().strip()
        base = self.ia_base.get().strip()

        def test_in_thread():
            r = ia_busca.testar(chave, modelo=modelo, base_url=base)
            if r["ok"]:
                txt = f"✓ {r['provedor']} · {r['modelo']} · {r['amostra']}"
                cor = "green"
            else:
                txt = f"✗ {r.get('provedor', '')}: {r['erro']}"
                cor = "red"
            self.window.after(0, lambda: self.ia_status.config(text=txt, foreground=cor))

        threading.Thread(target=test_in_thread, daemon=True).start()

    def _test_all(self):
        """Testa todos os provedores habilitados."""
        self._test("pexels")
        self._test("pixabay")
        self._test("unsplash")
        self._test("nasa")
        self._test("coverr")
        self._test("giphy")
        self._test("openverse")

    def show(self):
        """Mostra a janela."""
        if self.parent:
            self.window.transient(self.parent)
            self.window.grab_set()
        self.window.mainloop()


def abrir_configuracao(parent=None):
    """Abre a janela de configuração de APIs."""
    app = APIConfigUI(parent)
    app.show()
    return app.config


if __name__ == "__main__":
    app = APIConfigUI()
    app.show()
