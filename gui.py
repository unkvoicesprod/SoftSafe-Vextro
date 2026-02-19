import os
import queue
import threading
import tkinter as tk
import webbrowser
import sys
from tkinter import filedialog, messagebox, scrolledtext, ttk

from backend import (
    baixar_audio,
    baixar_playlist_audio,
    baixar_playlist_video,
    baixar_video,
    info_video,
    salvar_thumbnail,
    validar_pasta,
    validar_url,
)
from splash import SplashScreen


def set_app_icon(root):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    icon_png = os.path.join(base_dir, 'ico.png')
    icon_ico = os.path.join(base_dir, 'ico.ico')
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SoftSafe.Vextro.3.0')
        except Exception:
            pass
 
    try:
        if os.path.isfile(icon_png):
            root._app_icon = tk.PhotoImage(file=icon_png)
            root.iconphoto(True, root._app_icon)
    except Exception:
        pass

    # No Windows, iconbitmap com .ico costuma refletir melhor no título/taskbar.
    try:
        if os.name == 'nt':
            if not os.path.isfile(icon_ico) and os.path.isfile(icon_png):
                try:
                    import importlib
                    pil_image = importlib.import_module('PIL.Image')
                    pil_image.open(icon_png).save(icon_ico, format='ICO')
                except Exception:
                    pass
            if os.path.isfile(icon_ico):
                root.iconbitmap(icon_ico)
    except Exception:
        pass


class UnkvDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title('SoftSafe Vextro 3.0')
        set_app_icon(self.root)
        self.root.geometry('800x580')
        self.root.minsize(800, 580)
        self.root.maxsize(800, 580)
        self._center_window(self.root, 800, 580)


        self.log_queue = queue.Queue()
        self.em_execucao = False
        self.log_file_path = os.path.join(os.path.dirname(__file__), 'download_logs.txt')
        self.theme_mode = 'light'
        self.log_text = None

        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w', encoding='utf-8') as _:
                pass

        self._setup_style()
        self._build_ui()
        self._processar_fila_eventos()

    def _setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._apply_theme()

    def _center_window(self, window, width, height):
        window.update_idletasks()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = int((sw - width) / 2)
        y = int((sh - height) / 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def _build_ui(self):
        self.container = ttk.Frame(self.root, style='Card.TFrame', padding=18)
        self.container.pack(fill='both', expand=True, padx=18, pady=18)

        def _load_png_scaled(path, size):
            if not os.path.isfile(path):
                return None
            try:
                from PIL import Image, ImageTk
                img = Image.open(path).convert('RGBA')
                resample = getattr(getattr(Image, 'Resampling', Image), 'LANCZOS', None)
                if resample is None:
                    resample = getattr(Image, 'LANCZOS', None)
                if resample is None:
                    resample = getattr(Image, 'BICUBIC', 3)
                img = img.resize((size, size), resample)
                return ImageTk.PhotoImage(img)
            except Exception:
                try:
                    img = tk.PhotoImage(file=path)
                    w, h = img.width(), img.height()
                    if w <= 0 or h <= 0:
                        return img
                    scale = max(w // size, h // size, 1)
                    return img.subsample(int(scale))
                except Exception:
                    return None

        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
        icon_png = os.path.join(base_dir, 'ico.png')
        self.icon_large = None
        if os.path.isfile(icon_png):
            try:
                self.icon_large = _load_png_scaled(icon_png, 50)
            except Exception:
                self.icon_large = None

        if self.icon_large:
            ttk.Label(self.container, image=self.icon_large, style='Flat.TLabel').grid(
                row=0, column=0, sticky='w', padx=(0, 10), pady=(0, 14)
            )

        ttk.Label(self.container, text='SoftSafe Vextro 3.0',
                  style='Title.TLabel').grid(
            row=0, column=1, columnspan=2, sticky='w', pady=(0, 14)
        )

        self.top_actions = ttk.Frame(self.container, style='Card.TFrame')
        self.top_actions.grid(row=0, column=3, sticky='e', pady=(0, 14))
        self.support_link = ttk.Label(
            self.top_actions,
            text='Apoie o projeto',
            style='Link.TLabel',
            cursor='hand2',
        )
        self.support_link.pack(side='left', padx=(0, 8))
        self.support_link.bind('<Button-1>', self.abrir_link_apoiador)

        exit_png = os.path.join(base_dir, 'exit.png')
        self.exit_icon = _load_png_scaled(exit_png, 18)
        if self.exit_icon:
            self.btn_exit = ttk.Button(
                self.top_actions,
                image=self.exit_icon,
                style='GhostNoBorder.TButton',
                command=self.fechar_programa,
            )
        else:
            self.btn_exit = ttk.Button(
                self.top_actions,
                text='Fechar',
                style='GhostNoBorder.TButton',
                command=self.fechar_programa,
            )
        self.btn_exit.pack(side='left')

        ttk.Label(self.container, text='URL do YouTube', style='Flat.TLabel').grid(row=1, column=0, sticky='w')
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self.container, textvariable=self.url_var, style='Flat.TEntry')
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky='ew', padx=(0, 8), pady=(2, 10))
        ttk.Button(self.container, text='Colar link', style='Flat.TButton', command=self.colar_link).grid(row=2, column=2, sticky='ew', padx=(0, 8))
        ttk.Button(self.container, text='Buscar info', style='Ghost.TButton', command=self.buscar_info).grid(row=2, column=3, sticky='ew')

        ttk.Label(self.container, text='Pasta de destino', style='Flat.TLabel').grid(row=3, column=0, sticky='w')
        self.destino_var = tk.StringVar(value=os.path.expanduser('~'))
        self.destino_entry = ttk.Entry(self.container, textvariable=self.destino_var, style='Flat.TEntry')
        self.destino_entry.grid(row=4, column=0, columnspan=3, sticky='ew', padx=(0, 8), pady=(2, 10))
        ttk.Button(self.container, text='Escolher pasta', style='Ghost.TButton', command=self.escolher_pasta).grid(row=4, column=3, sticky='ew')

        ttk.Label(self.container, text='Tipo de download', style='Flat.TLabel').grid(row=5, column=0, sticky='w')
        self.tipo_var = tk.StringVar(value='Video')
        self.tipo_combo = ttk.Combobox(
            self.container,
            textvariable=self.tipo_var,
            state='readonly',
            values=['Video', 'Audio', 'Playlist Video', 'Playlist Audio'],
            style='FlatNoBg.TCombobox',
        )
        self.tipo_combo.grid(row=6, column=0, sticky='ew', pady=(2, 10))
        self.tipo_combo.bind('<<ComboboxSelected>>', lambda _: self.atualizar_campos())

        ttk.Label(self.container, text='Qualidade video', style='Flat.TLabel').grid(row=5, column=1, sticky='w')
        self.qualidade_video_var = tk.StringVar(value='best')
        self.qualidade_video_combo = ttk.Combobox(
            self.container,
            textvariable=self.qualidade_video_var,
            values=['best', '2160', '1440', '1080', '720', '480', '360'],
            style='Flat.TCombobox',
        )
        self.qualidade_video_combo.grid(row=6, column=1, sticky='ew', pady=(2, 10))

        ttk.Label(self.container, text='Formato video', style='Flat.TLabel').grid(row=5, column=2, sticky='w')
        self.formato_video_var = tk.StringVar(value='mp4')
        self.formato_video_combo = ttk.Combobox(
            self.container,
            textvariable=self.formato_video_var,
            values=['mp4', 'mkv', 'webm'],
            style='FlatNoBg.TCombobox',
        )
        self.formato_video_combo.grid(row=6, column=2, sticky='ew', pady=(2, 10))

        ttk.Label(self.container, text='Itens playlist', style='Flat.TLabel').grid(row=5, column=3, sticky='w')
        self.itens_var = tk.StringVar(value='all')
        self.itens_entry = ttk.Entry(self.container, textvariable=self.itens_var, style='Flat.TEntry')
        self.itens_entry.grid(row=6, column=3, sticky='ew', pady=(2, 10))

        ttk.Label(self.container, text='Formato audio', style='Flat.TLabel').grid(row=7, column=0, sticky='w')
        self.formato_audio_var = tk.StringVar(value='mp3')
        self.formato_audio_combo = ttk.Combobox(
            self.container,
            textvariable=self.formato_audio_var,
            values=['mp3', 'm4a', 'best'],
            style='Flat.TCombobox',
        )
        self.formato_audio_combo.grid(row=8, column=0, sticky='ew', pady=(2, 10))

        ttk.Label(self.container, text='Qualidade audio (0-9)', style='Flat.TLabel').grid(row=7, column=1, sticky='w')
        self.qualidade_audio_var = tk.StringVar(value='0')
        self.qualidade_audio_combo = ttk.Combobox(
            self.container,
            textvariable=self.qualidade_audio_var,
            values=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
            style='Flat.TCombobox',
        )
        self.qualidade_audio_combo.grid(row=8, column=1, sticky='ew', pady=(2, 10))

        self.info_titulo_var = tk.StringVar(value='Titulo: -')
        self.info_tamanho_var = tk.StringVar(value='Tamanho: -')
        self.info_thumb_var = tk.StringVar(value='Thumbnail: -')
        ttk.Label(self.container, textvariable=self.info_titulo_var, style='Flat.TLabel').grid(row=9, column=0, columnspan=4, sticky='w', pady=(4, 0))
        ttk.Label(self.container, textvariable=self.info_tamanho_var, style='Flat.TLabel').grid(row=10, column=0, columnspan=4, sticky='w')
        ttk.Label(self.container, textvariable=self.info_thumb_var, style='Flat.TLabel').grid(row=11, column=0, columnspan=4, sticky='w')

        botoes = ttk.Frame(self.container, style='Card.TFrame')
        botoes.grid(row=12, column=0, columnspan=4, sticky='ew', pady=(10, 8))
        botoes.columnconfigure(0, weight=1)
        botoes.columnconfigure(1, weight=2)
        botoes.columnconfigure(2, weight=1)
        botoes.columnconfigure(3, weight=1)
        self.btn_baixar = ttk.Button(botoes, text='Iniciar download', style='Flat.TButton', command=self.iniciar_download)
        self.btn_baixar.grid(row=0, column=0, sticky='ew', padx=(0, 6))
        self.btn_cancelar = ttk.Button(botoes, text='Cancelar', style='Danger.TButton', command=self.cancelar_download)
        self.btn_cancelar.grid(row=0, column=1, sticky='ew', padx=(6, 6))
        self.btn_logs = ttk.Button(botoes, text='Logs', style='Ghost.TButton', command=self.mostrar_menu_logs)
        self.btn_logs.grid(row=0, column=2, sticky='ew', padx=(6, 6))
        self.btn_theme = ttk.Button(botoes, text='Tema: Light', style='Ghost.TButton', command=self.toggle_theme)
        self.btn_theme.grid(row=0, column=3, sticky='ew', padx=(6, 0))
        self.menu_logs = tk.Menu(self.root, tearoff=0)
        self.menu_logs.add_command(label='Abrir arquivo', command=self.abrir_arquivo_log)
        self.menu_logs.add_command(label='Limpar', command=self.limpar_log)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_label_var = tk.StringVar(value='Progresso: 0%')
        self.progressbar = ttk.Progressbar(self.container, style='Main.Horizontal.TProgressbar', mode='determinate', maximum=100.0, variable=self.progress_var)
        self.progressbar.grid(row=13, column=0, columnspan=4, sticky='ew')
        ttk.Label(self.container, textvariable=self.progress_label_var, style='Flat.TLabel').grid(row=14, column=0, columnspan=4, sticky='w', pady=(4, 6))

        self.status_var = tk.StringVar(value='Pronto')
        ttk.Label(self.container, textvariable=self.status_var, style='Status.TLabel').grid(row=15, column=0, columnspan=4, sticky='w', pady=(0, 8))

        for idx in range(4):
            self.container.columnconfigure(idx, weight=1)
        self._apply_theme()
        self.atualizar_campos()

    def _apply_theme(self):
        themes = {
            'light': {
                'root_bg': '#f4f6f8',
                'card_bg': '#ffffff',
                'text': '#1f2937',
                'title': '#111827',
                'status': '#2563eb',
                'primary': '#2563eb',
                'primary_active': '#1d4ed8',
                'primary_disabled': '#93c5fd',
                'danger': '#dc2626',
                'danger_active': '#b91c1c',
                'danger_disabled': '#fca5a5',
                'ghost_bg': '#e5e7eb',
                'ghost_active': '#d1d5db',
                'input_bg': '#f9fafb',
                'input_border': '#4d4d4d',
                'prog_trough': '#e5e7eb',
                'log_bg': '#0b1220',
                'log_fg': '#d1fae5',
                'menu_bg': '#ffffff',
                'menu_fg': '#111827',
            },
            'dark': {
                'root_bg': '#0f172a',
                'card_bg': '#111827',
                'text': '#cbd5e1',
                'title': '#f8fafc',
                'status': '#60a5fa',
                'primary': '#3b82f6',
                'primary_active': '#2563eb',
                'primary_disabled': '#1d4ed8',
                'danger': '#ef4444',
                'danger_active': '#dc2626',
                'danger_disabled': '#fca5a5',
                'ghost_bg': '#1f2937',
                'ghost_active': '#374151',
                'input_bg': '#111827',
                'input_border': '#bfbfbf',
                'prog_trough': '#1f2937',
                'log_bg': '#020617',
                'log_fg': '#a7f3d0',
                'menu_bg': '#111827',
                'menu_fg': '#e5e7eb',
            },
        }
        c = themes[self.theme_mode]
        self.root.configure(bg=c['root_bg'])
        self.style.configure('Card.TFrame', background=c['card_bg'])
        self.style.configure('Flat.TLabel', background=c['card_bg'], foreground=c['text'], font=('Segoe UI', 10))
        self.style.configure('Title.TLabel', background=c['card_bg'], foreground=c['title'], font=('Segoe UI Semibold', 14))
        self.style.configure('Status.TLabel', background=c['card_bg'], foreground=c['status'], font=('Segoe UI', 10, 'bold'))
        self.style.configure('Flat.TButton', background=c['primary'], foreground='#ffffff', borderwidth=0, relief='flat', padding=8)
        self.style.map('Flat.TButton', background=[('active', c['primary_active']), ('disabled', c['primary_disabled'])], foreground=[('disabled', '#e5e7eb')])
        self.style.configure('Danger.TButton', background=c['danger'], foreground='#ffffff', borderwidth=0, relief='flat', padding=8)
        self.style.map('Danger.TButton', background=[('active', c['danger_active']), ('disabled', c['danger_disabled'])], foreground=[('disabled', '#fee2e2')])
        self.style.configure('Ghost.TButton', background=c['card_bg'], foreground=c['text'], borderwidth=1, relief='solid', padding=8)
        self.style.map('Ghost.TButton', background=[('active', c['card_bg'])])
        self.style.configure('GhostNoBorder.TButton', background=c['card_bg'], foreground=c['text'], borderwidth=0, relief='flat', padding=8)
        self.style.map('GhostNoBorder.TButton', background=[('active', c['card_bg'])])
        self.style.configure('Flat.TEntry', fieldbackground=c['card_bg'], bordercolor=c['input_border'], lightcolor=c['input_border'], darkcolor=c['input_border'], foreground=c['text'], padding=6, borderwidth=1, relief='solid')
        self.style.configure('Flat.TCombobox', fieldbackground=c['card_bg'], background=c['card_bg'], bordercolor=c['input_border'], lightcolor=c['input_border'], darkcolor=c['input_border'], foreground=c['text'], padding=6, borderwidth=1, relief='solid')
        self.style.configure('FlatNoBg.TCombobox', fieldbackground=c['card_bg'], background=c['card_bg'], bordercolor=c['input_border'], lightcolor=c['input_border'], darkcolor=c['input_border'], foreground=c['text'], padding=6, borderwidth=1, relief='solid')
        self.style.map(
            'FlatNoBg.TCombobox',
            fieldbackground=[('readonly', c['card_bg']), ('disabled', c['card_bg'])],
            background=[('readonly', c['card_bg']), ('disabled', c['card_bg'])],
            foreground=[('readonly', c['text']), ('disabled', c['text'])],
        )
        self.style.configure('Main.Horizontal.TProgressbar', troughcolor=c['prog_trough'], background=c['primary'], bordercolor=c['prog_trough'], lightcolor=c['primary'], darkcolor=c['primary'])
        self.style.configure('Link.TLabel', background=c['card_bg'], foreground='#1d4ed8' if self.theme_mode == 'light' else '#93c5fd', font=('Segoe UI', 9, 'underline'))

        if self.log_text is not None:
            self.log_text.configure(bg=c['log_bg'], fg=c['log_fg'], insertbackground=c['log_fg'])
        if hasattr(self, 'menu_logs'):
            self.menu_logs.configure(bg=c['menu_bg'], fg=c['menu_fg'], activebackground=c['ghost_active'], activeforeground=c['menu_fg'])
        if hasattr(self, 'btn_theme'):
            self.btn_theme.configure(text='Tema: Light' if self.theme_mode == 'light' else 'Tema: Dark')

        # Remove o fundo das opcoes do Combobox (lista de itens).
        try:
            self.root.option_add('*TButton.cursor', 'hand2')
            self.root.option_add('*TCombobox*Listbox.background', c['card_bg'])
            self.root.option_add('*TCombobox*Listbox.foreground', c['text'])
            self.root.option_add('*TCombobox*Listbox.selectBackground', c['card_bg'])
            self.root.option_add('*TCombobox*Listbox.selectForeground', c['text'])
            self.root.option_add('*TCombobox*Listbox.highlightThickness', 1)
            self.root.option_add('*TCombobox*Listbox.borderWidth', 1)
        except Exception:
            pass

    def toggle_theme(self):
        self.theme_mode = 'dark' if self.theme_mode == 'light' else 'light'
        self._apply_theme()

    def abrir_link_apoiador(self, _event=None):
        webbrowser.open('https://www.paypal.com/ncp/payment/984SMG97UGV6N', new=2)

    def fechar_programa(self):
        self.root.destroy()

    def colar_link(self):
        try:
            texto = self.root.clipboard_get().strip()
        except tk.TclError:
            texto = ''
        if texto:
            self.url_var.set(texto)
            self.url_entry.focus_set()
            self.url_entry.icursor('end')

    def _enqueue_log(self, mensagem):
        self.log_queue.put(('log', mensagem))

    def _enqueue_progress(self, percentual):
        self.log_queue.put(('progress', percentual))

    def _processar_fila_eventos(self):
        while not self.log_queue.empty():
            kind, payload = self.log_queue.get_nowait()
            if kind == 'log':
                texto = str(payload)
                if self.log_text is not None:
                    self.log_text.insert('end', texto + '\n')
                    self.log_text.see('end')
                with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(texto + '\n')
            elif kind == 'progress':
                valor = max(0.0, min(100.0, float(payload)))
                self.progress_var.set(valor)
                self.progress_label_var.set(f'Progresso: {valor:.1f}%')
        self.root.after(120, self._processar_fila_eventos)

    def set_status(self, texto):
        self.status_var.set(texto)

    def set_progress(self, valor=0.0):
        self.progress_var.set(valor)
        self.progress_label_var.set(f'Progresso: {valor:.1f}%')

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(initialdir=self.destino_var.get() or os.path.expanduser('~'))
        if pasta:
            self.destino_var.set(pasta)

    def limpar_log(self):
        if self.log_text is not None:
            self.log_text.delete('1.0', 'end')
        with open(self.log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write('')

    def cancelar_download(self):
        if not self.em_execucao:
            return
        self._enqueue_log('Cancelamento solicitado pelo usuario.')
        self.set_status('Cancelamento solicitado (aguarde finalizar).')
        messagebox.showinfo('Cancelar', 'Cancelamento solicitado. Aguarde a finalizacao do download atual.')

    def mostrar_menu_logs(self):
        x = self.btn_logs.winfo_rootx()
        y = self.btn_logs.winfo_rooty() + self.btn_logs.winfo_height()
        self.menu_logs.tk_popup(x, y)

    def abrir_arquivo_log(self):
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w', encoding='utf-8') as _:
                pass
        os.startfile(self.log_file_path)

    def atualizar_campos(self):
        tipo = self.tipo_var.get()
        is_video = tipo == 'Video'
        is_audio = tipo == 'Audio'
        is_pl_video = tipo == 'Playlist Video'
        is_pl_audio = tipo == 'Playlist Audio'

        self.qualidade_video_combo.configure(state='normal' if is_video or is_pl_video else 'disabled')
        self.formato_video_combo.configure(state='readonly' if is_video else 'disabled')
        self.itens_entry.configure(state='normal' if is_pl_video or is_pl_audio else 'disabled')
        self.formato_audio_combo.configure(state='readonly' if is_audio or is_pl_audio else 'disabled')
        self.qualidade_audio_combo.configure(state='readonly' if is_audio or is_pl_audio else 'disabled')

    def buscar_info(self):
        url = self.url_var.get().strip()
        if not validar_url(url):
            messagebox.showerror('Erro', 'URL invalida. Use um link youtube.com ou youtu.be')
            return
        self.set_status('Buscando informacoes...')
        self._enqueue_log('Buscando informacoes do link...')
        info = info_video(url)
        if not info['ok']:
            self.set_status('Falha ao buscar info')
            self._enqueue_log(f"Erro: {info['erro']}")
            messagebox.showerror('Erro', f"Falha ao obter informacoes:\n{info['erro']}")
            return

        self.info_titulo_var.set(f"Titulo: {info['titulo']}")
        self.info_tamanho_var.set(f"Tamanho: {info['tamanho']}")
        self.info_thumb_var.set(f"Thumbnail: {info['thumbnail'] or '-'}")
        self.set_status('Informacoes carregadas')
        self._enqueue_log('Informacoes carregadas com sucesso.')

    def iniciar_download(self):
        if self.em_execucao:
            return

        url = self.url_var.get().strip()
        destino = self.destino_var.get().strip()
        if not validar_url(url):
            messagebox.showerror('Erro', 'URL invalida.')
            return
        if not validar_pasta(destino):
            messagebox.showerror('Erro', 'Pasta de destino invalida ou inexistente.')
            return

        self.em_execucao = True
        self.btn_baixar.configure(state='disabled')
        self.set_status('Preparando download...')
        self.set_progress(0.0)
        t = threading.Thread(target=self._executar_download, daemon=True)
        t.start()

    def _executar_download(self):
        url = self.url_var.get().strip()
        destino = self.destino_var.get().strip()
        tipo = self.tipo_var.get()
        qualidade_video = self.qualidade_video_var.get().strip() or 'best'
        formato_video = self.formato_video_var.get().strip() or 'mp4'
        itens = self.itens_var.get().strip() or 'all'
        formato_audio = self.formato_audio_var.get().strip() or 'mp3'
        qualidade_audio = self.qualidade_audio_var.get().strip() or '0'

        self._enqueue_log(f"Modo selecionado: {tipo}")
        info = info_video(url)
        if not info['ok']:
            self._enqueue_log(f"Nao foi possivel obter info antes do download: {info['erro']}")
            titulo = None
            thumb = None
        else:
            titulo = info['titulo']
            thumb = info['thumbnail']
            self._enqueue_log(f"Midia: {titulo} | {info['tamanho']}")

        if tipo in ('Audio', 'Playlist Video', 'Playlist Audio') and thumb and titulo:
            salvar_thumbnail(thumb, destino, titulo, self._enqueue_log)

        if formato_audio == 'mp3' and tipo in ('Audio', 'Playlist Audio'):
            self._enqueue_log('Nota: conversao para mp3 requer FFmpeg instalado e no PATH.')

        if tipo == 'Video':
            sucesso, erro = baixar_video(url, destino, qualidade_video, formato_video, self._enqueue_log, self._enqueue_progress)
        elif tipo == 'Audio':
            sucesso, erro = baixar_audio(url, destino, formato_audio, qualidade_audio, self._enqueue_log, self._enqueue_progress)
        elif tipo == 'Playlist Video':
            sucesso, erro = baixar_playlist_video(url, destino, qualidade_video, itens, self._enqueue_log, self._enqueue_progress)
        else:
            sucesso, erro = baixar_playlist_audio(url, destino, formato_audio, qualidade_audio, itens, self._enqueue_log, self._enqueue_progress)

        def finalizar():
            if sucesso:
                self.set_status('Download concluido')
                self.set_progress(100.0)
                self._enqueue_log('Concluido com sucesso.')
                messagebox.showinfo('Sucesso', 'Download concluido com sucesso.')
                abrir_pasta = messagebox.askyesno('Abrir pasta', f'Deseja abrir a pasta de download?\n{destino}')
                if abrir_pasta:
                    os.startfile(destino)
            else:
                self.set_status('Falha no download')
                self._enqueue_log(f"Erro: {erro}")
                messagebox.showerror('Erro', f"Falha no download:\n{erro}")
            self.em_execucao = False
            self.btn_baixar.configure(state='normal')

        self.root.after(0, finalizar)


def _show_splash_then_app(root):
    splash = SplashScreen(root)
    root.update_idletasks()
    root.update()

    def close_splash_and_start():
        if splash.winfo_exists():
            splash.close()
        UnkvDownloaderApp(root)
        root.deiconify()

    root.after(5000, close_splash_and_start)


def main():
    root = tk.Tk()
    set_app_icon(root)
    root.withdraw()
    _show_splash_then_app(root)
    root.mainloop()


if __name__ == '__main__':
    main()
