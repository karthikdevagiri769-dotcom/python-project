import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk, ImageOps
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ---------------------------------------------------------------
# Folder where THIS script lives (media files are searched here)
# ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
AUDIO_EXTS = (".m4a", ".mp3", ".wav", ".aac", ".ogg", ".wma", ".flac", ".mp4", ".m4b", ".opus")
SKIP_EXTS = (".py", ".pyc", ".txt", ".md") + AUDIO_EXTS

# Colours
LIGHT = "#ffe4ec"
PINK = "#d81b60"
BLACK = "#000000"
RED = "#ff1e1e"
YELLOW = "#ffd60a"
WHITE = "#ffffff"

FONT = "Segoe UI"


# ---------------------------------------------------------------
# File detection
# ---------------------------------------------------------------
def list_files():
    try:
        names = sorted(os.listdir(BASE_DIR))
    except OSError:
        return []
    return [n for n in names if os.path.isfile(os.path.join(BASE_DIR, n))]


def rakhi_first(names):
    """Files with 'rakhi' in the name come first."""
    return sorted(names, key=lambda n: (0 if "rakhi" in n.lower() else 1, n.lower()))


def find_image():
    """Return (path, PIL image) for the first file Pillow can open."""
    files = list_files()
    by_ext = [n for n in files if n.lower().endswith(IMAGE_EXTS)]
    others = [n for n in files
              if n not in by_ext and not n.lower().endswith(SKIP_EXTS)]
    for name in rakhi_first(by_ext) + rakhi_first(others):
        path = os.path.join(BASE_DIR, name)
        try:
            img = Image.open(path)
            img.load()  # forces real decoding; fails if not a real image
            return path, img
        except Exception:
            continue
    return None, None


def find_audio():
    files = list_files()
    audio = [n for n in files if n.lower().endswith(AUDIO_EXTS)]
    if audio:
        return os.path.join(BASE_DIR, rakhi_first(audio)[0])
    return None


# ---------------------------------------------------------------
# The application
# ---------------------------------------------------------------
class RakhiApp:
    def __init__(self, root):
        self.root = root
        self.token = 0          # used to cancel pending animations
        self.frame = None
        self.boy = ""
        self.girl = ""
        self.photo = None
        self.song_status = None

        root.title("💘 Rakhi Match-O-Meter 💘")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.win_w = min(900, sw - 40)
        self.win_h = min(820, sh - 90)
        x = (sw - self.win_w) // 2
        y = max(0, (sh - self.win_h) // 2 - 20)
        root.geometry(f"{self.win_w}x{self.win_h}+{x}+{y}")
        root.minsize(700, 600)
        root.bind("<Escape>", lambda e: self.close())

        self.image_path, self.pil_image = find_image()
        self.audio_path = find_audio()
        self.photo = self.make_photo()

        self.build_main()
        self.root.after(300, self.startup_check)

    # ---------- helpers ----------
    def startup_check(self):
        problems = []
        if not self.image_path:
            problems.append("• No readable image found (.png / .jpg / .jpeg / .webp).")
        if not self.audio_path:
            problems.append("• No audio file found (.m4a / .mp3 / .wav).")
        if problems:
            found = ", ".join(list_files()) or "(nothing)"
            messagebox.showwarning(
                "Missing files",
                "\n".join(problems)
                + f"\n\nI looked in this folder:\n{BASE_DIR}"
                + f"\n\nFiles I can see there:\n{found}"
                + "\n\nPut your image and song in that folder and restart.")

    def make_photo(self):
        """Resize the image to fit the reveal screen."""
        if self.pil_image is None:
            return None
        try:
            img = self.pil_image
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            img = img.convert("RGB")
            max_w = self.win_w - 80
            max_h = max(200, self.win_h - 400)
            scale = min(max_w / img.width, max_h / img.height)
            new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            resample = getattr(Image, "Resampling", Image).LANCZOS
            img = img.resize(new_size, resample)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def new_frame(self, bg):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = tk.Frame(self.root, bg=bg)
        self.frame.pack(fill="both", expand=True)
        self.root.configure(bg=bg)
        return self.frame

    def later(self, token, ms, fn):
        """Run fn after ms, but only if the reveal hasn't been cancelled."""
        def run():
            if token == self.token:
                fn()
        self.root.after(ms, run)

    def close(self):
        self.root.destroy()

    # ---------- main screen ----------
    def build_main(self):
        self.token += 1
        f = self.new_frame(LIGHT)

        tk.Label(f, text="💘 Match-O-Meter 💘", bg=LIGHT, fg=PINK,
                 font=(FONT, 36, "bold")).pack(pady=(40, 5))
        tk.Label(f, text="Enter two names and discover the shocking truth...",
                 bg=LIGHT, fg="#555555", font=(FONT, 15)).pack(pady=(0, 30))

        tk.Label(f, text="Boy's Name", bg=LIGHT, fg="#333333",
                 font=(FONT, 16, "bold")).pack()
        self.boy_entry = self.make_entry(f)
        self.boy_entry.pack(pady=(5, 20), ipady=8)

        tk.Label(f, text="Girl's Name", bg=LIGHT, fg="#333333",
                 font=(FONT, 16, "bold")).pack()
        self.girl_entry = self.make_entry(f)
        self.girl_entry.pack(pady=(5, 30), ipady=8)

        self.boy_entry.bind("<Return>", lambda e: self.girl_entry.focus_set())
        self.girl_entry.bind("<Return>", lambda e: self.start_reveal())

        tk.Button(f, text="🔥 REVEAL 🔥", font=(FONT, 24, "bold"),
                  bg="#d90429", fg=WHITE, activebackground="#ef233c",
                  activeforeground=WHITE, relief="flat", cursor="hand2",
                  padx=30, pady=10, command=self.start_reveal).pack(pady=10)

        tk.Button(f, text="✖ Close", font=(FONT, 13), bg="#bbbbbb",
                  fg="#222222", relief="flat", cursor="hand2",
                  padx=15, pady=4, command=self.close).pack(pady=(25, 5))

        status = []
        status.append("🖼 Image: " + (os.path.basename(self.image_path)
                                     if self.image_path else "NOT FOUND"))
        status.append("🎵 Song: " + (os.path.basename(self.audio_path)
                                     if self.audio_path else "NOT FOUND"))
        tk.Label(f, text="     ".join(status), bg=LIGHT, fg="#777777",
                 font=(FONT, 10)).pack(side="bottom", pady=10)

        self.boy_entry.focus_set()

    def make_entry(self, parent):
        return tk.Entry(parent, font=(FONT, 20), justify="center", width=22,
                        relief="flat", bd=0, highlightthickness=2,
                        highlightbackground=PINK, highlightcolor=PINK)

    # ---------- validation ----------
    def start_reveal(self):
        boy = self.boy_entry.get().strip()
        girl = self.girl_entry.get().strip()
        if not boy and not girl:
            messagebox.showwarning("Oops", "Please enter both names!")
            self.boy_entry.focus_set()
            return
        if not boy:
            messagebox.showwarning("Oops", "Please enter the Boy's Name!")
            self.boy_entry.focus_set()
            return
        if not girl:
            messagebox.showwarning("Oops", "Please enter the Girl's Name!")
            self.girl_entry.focus_set()
            return
        self.boy, self.girl = boy, girl
        self.show_loading()

    # ---------- suspense screen ----------
    def show_loading(self):
        self.token += 1
        f = self.new_frame(BLACK)

        self.loading_label = tk.Label(f, text="", bg=BLACK, fg=WHITE,
                                      font=(FONT, 28, "bold"),
                                      wraplength=self.win_w - 60)
        self.loading_label.pack(expand=True, pady=(0, 10))

        self.bar = tk.Canvas(f, width=420, height=22, bg="#222222",
                             highlightthickness=0)
        self.bar.pack(pady=(0, 120))
        self.bar_fill = self.bar.create_rectangle(0, 0, 0, 22, fill=RED, width=0)

        self.messages = [
            "🔮 Consulting the stars...",
            "💌 Reading secret diaries...",
            "👀 Checking suspicious glances...",
            "🚨 MATCH FOUND...",
        ]
        self.loading_tick(0, self.token)

    def loading_tick(self, step, token):
        if token != self.token:
            return
        if step >= len(self.messages):
            self.show_reveal()
            return
        self.loading_label.config(text=self.messages[step])
        self.bar.coords(self.bar_fill, 0, 0, 420 * (step + 1) / len(self.messages), 22)
        self.root.after(500, lambda: self.loading_tick(step + 1, token))

    # ---------- dramatic reveal ----------
    def show_reveal(self):
        self.token += 1
        token = self.token
        f = self.new_frame(BLACK)

        # Bottom button bar (packed first so it always stays visible)
        bar = tk.Frame(f, bg=BLACK)
        bar.pack(side="bottom", fill="x", pady=(0, 15))
        self.song_status = tk.Label(bar, text="", bg=BLACK, fg="#999999",
                                    font=(FONT, 10))
        self.song_status.pack(pady=(0, 6))
        row = tk.Frame(bar, bg=BLACK)
        row.pack()
        self.small_button(row, "▶ PLAY SONG", "#1db954",
                          lambda: self.play_song(auto=False)).pack(side="left", padx=8)
        self.small_button(row, "🔁 AGAIN", "#444444",
                          self.go_home).pack(side="left", padx=8)
        self.small_button(row, "✖ CLOSE", "#b00020",
                          self.close).pack(side="left", padx=8)

        # Stage 1: heading + song
        tk.Label(f, text="🚨 WAIT... WHAT?! 🚨", bg=BLACK, fg=RED,
                 font=(FONT, 36, "bold")).pack(pady=(25, 10))
        self.later(token, 300, lambda: self.play_song(auto=True))

        # Stage 2: names
        def show_names():
            text = f"{self.boy}  ❤️  {self.girl}"
            size = 36 if len(text) <= 22 else 28 if len(text) <= 36 else 22
            tk.Label(f, text=text, bg=BLACK, fg=WHITE,
                     font=(FONT, size, "bold"), justify="center",
                     wraplength=self.win_w - 60).pack(pady=8)
        self.later(token, 900, show_names)

        # Stage 3: image
        def show_image():
            if self.photo is not None:
                tk.Label(f, image=self.photo, bg=BLACK).pack(pady=8)
            else:
                tk.Label(f, text="[ Rakhi image missing or unreadable ]",
                         bg=BLACK, fg=RED, font=(FONT, 16)).pack(pady=30)
        self.later(token, 1700, show_image)

        # Stage 4: funny message
        def show_message():
            tk.Label(f, text="👀 You two look suspiciously good together 😂\n"
                             "💀 Don't kill the messenger!",
                     bg=BLACK, fg=YELLOW, font=(FONT, 20, "bold"),
                     justify="center", wraplength=self.win_w - 60).pack(pady=10)
        self.later(token, 2500, show_message)

    def small_button(self, parent, text, bg, cmd):
        return tk.Button(parent, text=text, font=(FONT, 14, "bold"), bg=bg,
                         fg=WHITE, activebackground=bg, activeforeground=WHITE,
                         relief="flat", cursor="hand2", padx=14, pady=6,
                         command=cmd)

    def go_home(self):
        self.build_main()

    # ---------- audio ----------
    def play_song(self, auto=False):
        if not self.audio_path:
            msg = "No audio file found in the folder."
            self.set_song_status("⚠ " + msg)
            if not auto:
                messagebox.showwarning("No song", msg + f"\n\nFolder:\n{BASE_DIR}")
            return
        try:
            if os.name == "nt":
                os.startfile(self.audio_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.audio_path])
            else:
                subprocess.Popen(["xdg-open", self.audio_path])
            self.set_song_status("🎵 Song opened in your media player")
            # The media player may pop up on top; bring our window back.
            self.root.after(1200, self.bring_to_front)
            self.root.after(2800, self.bring_to_front)
        except Exception as e:
            self.set_song_status("⚠ Couldn't autoplay - click ▶ PLAY SONG")
            if not auto:
                messagebox.showerror("Can't play song",
                                     f"Couldn't open the audio file:\n{e}")

    def set_song_status(self, text):
        try:
            if self.song_status is not None and self.song_status.winfo_exists():
                self.song_status.config(text=text)
        except tk.TclError:
            pass

    def bring_to_front(self):
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(300, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except tk.TclError:
            pass


# ---------------------------------------------------------------
# Start the program
# ---------------------------------------------------------------
def main():
    root = tk.Tk()
    if not PIL_OK:
        messagebox.showerror(
            "Pillow is missing",
            "Pillow is not installed.\n\nOpen Command Prompt and run:\n\n"
            "python -m pip install Pillow\n\nThen run this program again.")
        root.destroy()
        return
    RakhiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()