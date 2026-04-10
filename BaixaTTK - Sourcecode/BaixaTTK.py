import tempfile
import shutil
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

FFMPEG_DIR = BASE_DIR / "Application" / "FFmpeg"

TEMP_DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "BaixaTTK_Temp"
TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

ICON_ICO_PATH = BASE_DIR / "Application" / "icon.ico"
ICON_PNG_PATH = BASE_DIR / "Application" / "icon.png"

MAX_DURATION_SECONDS = 3599

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BaixaTTK")
        self.root.resizable(False, False)
        self.root.geometry("560x300")
        self.center_window(560, 300)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_icon()

        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Cole o link abaixo")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value="")
        self.download_in_progress = False
        self.downloaded_file_path = None

        self.audio_btn = None
        self.video_btn = None
        self.back_btn = None
        self.paste_btn = None
        self.entry = None
        self.progressbar = None

        self.build_link_screen()

    def on_closing(self):
        if self.download_in_progress:
            if not messagebox.askyesno("Aviso", "Um download está em andamento. Tem certeza que deseja cancelar e fechar?"):
                return
        self.root.destroy()

    def setup_icon(self):
        try:
            if ICON_ICO_PATH.exists():
                self.root.iconbitmap(default=str(ICON_ICO_PATH))
        except tk.TclError:
            pass

        try:
            if ICON_PNG_PATH.exists():
                self._icon_img = tk.PhotoImage(file=str(ICON_PNG_PATH))
                self.root.iconphoto(True, self._icon_img)
            else:
                self._icon_img = None
        except tk.TclError:
            self._icon_img = None

    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_link_screen(self):
        self.clear()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="Cole o link do TikTok", font=("Arial", 16, "bold"))
        title.pack(pady=(0, 15))

        self.entry = tk.Entry(frame, textvariable=self.url_var, font=("Arial", 12), width=56)
        self.entry.pack(pady=(0, 10))
        self.entry.focus_set()
        self.entry.bind("<Return>", self.handle_enter_on_link_screen)

        status = tk.Label(frame, textvariable=self.status_var, font=("Arial", 10))
        status.pack(pady=(0, 8))

        self.paste_btn = tk.Button(frame, text="Baixar", width=14, command=self.handle_link_input)
        self.paste_btn.pack(pady=(0, 10))

        hint = tk.Label(frame, text="Depois de colar, pressione Enter ou clique em Baixar.", font=("Arial", 9), fg="gray")
        hint.pack(pady=(6, 0))

    def build_choice_screen(self):
        self.clear()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="Escolha o formato", font=("Arial", 16, "bold"))
        title.pack(pady=(0, 12))

        url_label = tk.Label(
            frame,
            text=self.url_var.get(),
            font=("Arial", 10),
            wraplength=500,
            justify="center",
        )
        url_label.pack(pady=(0, 16))

        buttons = tk.Frame(frame)
        buttons.pack(pady=(0, 10))

        self.audio_btn = tk.Button(
            buttons,
            text="Audio (OGG)",
            width=16,
            command=lambda: self.start_download("audio"),
        )
        self.audio_btn.grid(row=0, column=0, padx=10)

        self.video_btn = tk.Button(
            buttons,
            text="Video (MP4)",
            width=16,
            command=lambda: self.start_download("video"),
        )
        self.video_btn.grid(row=0, column=1, padx=10)

        self.back_btn = tk.Button(frame, text="Voltar", width=14, command=self.reset_to_link_screen)
        self.back_btn.pack(pady=(8, 12))

        progress_frame = tk.Frame(frame)
        progress_frame.pack(fill="x", pady=(8, 0))

        self.progressbar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_var,
            length=500,
        )
        self.progressbar.pack(pady=(0, 8))

        progress_text = tk.Label(progress_frame, textvariable=self.progress_text_var, font=("Arial", 10))
        progress_text.pack()

        self.progress_var.set(0)
        self.progress_text_var.set("Pronto para baixar")

    def handle_enter_on_link_screen(self, event=None):
        self.handle_link_input()

    def handle_link_input(self):
        if self.download_in_progress:
            return

        text = self.url_var.get().strip()

        if not text:
            try:
                clipboard_text = self.root.clipboard_get().strip()
            except tk.TclError:
                clipboard_text = ""

            if not clipboard_text:
                messagebox.showerror("Erro", "Cole um link do TikTok.")
                return

            text = clipboard_text
            self.url_var.set(text)

        if not self.is_tiktok_url(text):
            messagebox.showerror("Erro", "Link inválido do TikTok.")
            return

        self.build_choice_screen()

    def is_tiktok_url(self, url):
        text = url.strip().lower()
        return "tiktok" in text or "douyin" in text

    def normalize_url(self, url):
        text = url.strip()
        if "://" not in text:
            text = f"https://{text}"
        return text

    def reset_to_link_screen(self):
        if self.download_in_progress:
            return
        self.url_var.set("")
        self.status_var.set("Cole o link abaixo")
        self.build_link_screen()

    def set_buttons_state(self, state):
        widgets = [self.audio_btn, self.video_btn, self.back_btn, self.paste_btn, self.entry]
        for widget in widgets:
            if widget is not None:
                try:
                    widget.config(state=state)
                except tk.TclError:
                    pass

    def set_busy(self, busy: bool):
        self.download_in_progress = busy
        self.set_buttons_state("disabled" if busy else "normal")

    def start_download(self, kind):
        if self.download_in_progress:
            return

        url = self.url_var.get().strip()

        if not url or not self.is_tiktok_url(url):
            messagebox.showerror("Erro", "Cole um link válido do TikTok primeiro.")
            return

        self.set_busy(True)
        self.progress_var.set(0)
        self.progress_text_var.set("Verificando arquivo...")
        self.status_var.set("Baixando...")

        threading.Thread(
            target=self.download,
            args=(self.normalize_url(url), kind),
            daemon=True
        ).start()

    def progress_hook(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)

            if total and total > 0:
                percent = (downloaded / total) * 100
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                filename = d.get("filename", "")
                name = Path(filename).name if filename else "arquivo"
                text = f"{name}  •  {percent:.1f}%"
                if speed:
                    text += f"  •  {speed}"
                if eta:
                    text += f"  •  ETA {eta}"
                self.root.after(0, lambda p=percent, t=text: self.update_progress(p, t))
            else:
                filename = d.get("filename", "")
                name = Path(filename).name if filename else "arquivo"
                text = f"Baixando {name}..."
                self.root.after(0, lambda t=text: self.update_progress_indeterminate(t))

        elif d.get("status") == "finished":
            self.root.after(0, lambda: self.progress_text_var.set("Processando arquivo..."))

    def update_progress(self, percent, text):
        try:
            self.progressbar.stop()
        except tk.TclError:
            pass
        self.progressbar.config(mode="determinate")
        self.progress_var.set(max(0, min(100, percent)))
        self.progress_text_var.set(text)

    def update_progress_indeterminate(self, text):
        self.progressbar.config(mode="indeterminate")
        self.progressbar.start(10)
        self.progress_text_var.set(text)

    def get_duration_seconds(self, url):
        info_opts = {
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
        if FFMPEG_DIR.exists():
            info_opts["ffmpeg_location"] = str(FFMPEG_DIR)

        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            return info.get("duration") if isinstance(info, dict) else None
        except:
            return None

    def download(self, url, kind):
        try:
            duration = self.get_duration_seconds(url)
            if duration is not None and duration > MAX_DURATION_SECONDS:
                self.root.after(0, self.after_too_long)
                return

            common_opts = {
                "outtmpl": str(TEMP_DOWNLOAD_DIR / "%(title)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "progress_hooks": [self.progress_hook],
                "concurrent_fragment_downloads": 8,
                "continuedl": True,
                "retries": 3,
                "fragment_retries": 3,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            }

            if FFMPEG_DIR.exists():
                common_opts["ffmpeg_location"] = str(FFMPEG_DIR)

            if kind == "audio":
                opts = {
                    **common_opts,
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "vorbis",
                            "preferredquality": "192",
                        }
                    ],
                }
            else:
                opts = {
                    **common_opts,
                    "format": "best[ext=mp4]/best",
                    "merge_output_format": "mp4",
                }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if 'requested_downloads' in info:
                    self.downloaded_file_path = info['requested_downloads'][0]['filepath']
                else:
                    base_filepath = ydl.prepare_filename(info)
                    ext = ".ogg" if kind == "audio" else ".mp4"
                    self.downloaded_file_path = str(Path(base_filepath).with_suffix(ext))

            self.root.after(0, self.after_success)
        except Exception as e:
            self.root.after(0, lambda: self.after_error(str(e)))

    def ask_destination_folder(self):
        self.set_busy(False)

        if not self.downloaded_file_path or not Path(self.downloaded_file_path).exists():
            messagebox.showerror("Erro", "Arquivo não encontrado após o download.")
            self.reset_to_link_screen()
            return

        source = Path(self.downloaded_file_path)
        default_ext = source.suffix
        file_types = [("Audio OGG", "*.ogg")] if default_ext == ".ogg" else [("Video MP4", "*.mp4")]

        destination = filedialog.asksaveasfilename(
            title="Salvar arquivo como...",
            initialfile=source.name,
            defaultextension=default_ext,
            filetypes=file_types + [("Todos os arquivos", "*.*")]
        )

        if destination:
            try:
                shutil.move(str(source), destination)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")
        else:
            try:
                source.unlink()
            except:
                pass

        self.downloaded_file_path = None
        self.reset_to_link_screen()

    def after_too_long(self):
        if self.progressbar is not None:
            try:
                self.progressbar.stop()
            except tk.TclError:
                pass
        messagebox.showwarning("Aviso", "Esse arquivo é longo demais e não pode ser baixado.")
        self.set_busy(False)
        self.reset_to_link_screen()

    def after_success(self):
        if self.progressbar is not None:
            try:
                self.progressbar.stop()
            except tk.TclError:
                pass
        self.ask_destination_folder()

    def after_error(self, error_text):
        if self.progressbar is not None:
            try:
                self.progressbar.stop()
            except tk.TclError:
                pass
        messagebox.showerror("Erro", f"Ocorreu um erro durante o download:\n\n{error_text}")
        self.set_busy(False)
        self.reset_to_link_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()