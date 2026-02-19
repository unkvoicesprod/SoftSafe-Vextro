import os
import sys
import tkinter as tk
from tkinter import ttk


class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        try:
            if hasattr(parent, '_app_icon'):
                self.iconphoto(True, parent._app_icon)
        except Exception:
            pass
        self.configure(bg='#0f172a')
        self.geometry(self._center_geometry(560, 460))
        self.deiconify()
        self.lift()
        self.focus_force()

        frame = tk.Frame(self, bg='#0f172a', bd=0)
        frame.pack(fill='both', expand=True, padx=18, pady=18)

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
                self.icon_large = _load_png_scaled(icon_png, 96)
            except Exception:
                self.icon_large = None

        if self.icon_large:
            tk.Label(
                frame,
                image=self.icon_large,
                bg='#0f172a',
            ).pack(anchor='w', pady=(4, 8))

        tk.Label(
            frame,
            text='SoftSafe Vextro',
            bg='#0f172a',
            fg='#e2e8f0',
            font=('Segoe UI Semibold', 22),
        ).pack(anchor='w', pady=(8, 6))

        tk.Label(
            frame,
            text='Software gratuito para baixar videos, audios e playlists de videos e audios do YouTube.',
            bg='#0f172a',
            fg='#93c5fd',
            font=('Segoe UI', 10),
        ).pack(anchor='w', pady=(20, 20))

        tk.Label(
            frame,
            text='author: Francisco Armando Chico\nEmpresa: SoftSafe\nLançamento: 2026\nVersão: 3.0',
            justify='left',
            bg='#0f172a',
            fg='#cbd5e1',
            font=('Segoe UI', 11),
        ).pack(anchor='w')

        pb_style = ttk.Style(self)
        pb_style.theme_use('clam')
        pb_style.configure(
            'Splash.Horizontal.TProgressbar',
            troughcolor='#1e293b',
            background='#38bdf8',
            bordercolor='#1e293b',
            lightcolor='#38bdf8',
            darkcolor='#38bdf8',
        )
        self.pb = ttk.Progressbar(
            frame,
            mode='determinate',
            maximum=100,
            style='Splash.Horizontal.TProgressbar',
            length=520,
        )
        self.pb.pack(side='bottom', pady=(20, 6))

        self._progress_value = 0
        self._progress_job = None
        self._animate_progress()

        # Permite dispensar a splash e evita percepcao de travamento.
        self.bind('<Escape>', lambda _e: self.close())
        self.bind('<Button-1>', lambda _e: self.close())

    def _center_geometry(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = int((sw - w) / 2)
        y = int((sh - h) / 2)
        return f'{w}x{h}+{x}+{y}'

    def _animate_progress(self):
        if not self.winfo_exists():
            return
        self._progress_value = (self._progress_value + 3) % 101
        self.pb['value'] = self._progress_value
        self._progress_job = self.after(40, self._animate_progress)

    def close(self):
        try:
            if self._progress_job is not None:
                self.after_cancel(self._progress_job)
                self._progress_job = None
        except Exception:
            pass
        if self.winfo_exists():
            self.destroy()
