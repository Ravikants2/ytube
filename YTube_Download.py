import io
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from urllib.request import urlopen
from PIL import Image
import customtkinter as ctk
import yt_dlp

# Initialize CustomTkinter Theme
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")


class ModernYouTubeDownloader(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("Modern YouTube Studio & Downloader")
    self.geometry("850x700")
    self.minsize(800, 650)

    # Variables
    self.url_var = ctk.StringVar()
    self.save_path = ctk.StringVar(value=os.getcwd())
    self.quality_var = ctk.StringVar(value="1080p (.mp4)")
    self.embed_thumb_var = ctk.BooleanVar(value=True)

    self.thumbnail_image = None
    self.ansi_escape = re.compile(r"\x1b\[[0-9;]*m")

    self.create_widgets()

  def create_widgets(self):
    # Main Layout Grid
    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(2, weight=1)

    # 1. Header Title
    title_label = ctk.CTkLabel(
        self,
        text="YouTube .MP4 Studio Downloader",
        font=ctk.CTkFont(size=20, weight="bold"),
    )
    title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

    # 2. URL Input Card
    url_card = ctk.CTkFrame(self)
    url_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
    url_card.grid_columnconfigure(0, weight=1)

    self.url_entry = ctk.CTkEntry(
        url_card,
        textvariable=self.url_var,
        placeholder_text="Paste YouTube URL here...",
        height=40,
        font=ctk.CTkFont(size=13),
    )
    self.url_entry.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

    fetch_btn = ctk.CTkButton(
        url_card,
        text="Fetch Info",
        command=self.fetch_info_thread,
        width=120,
        height=40,
    )
    fetch_btn.grid(row=0, column=1, padx=(0, 15), pady=15)

    # 3. Content Middle Split (Preview + Options)
    mid_frame = ctk.CTkFrame(self, fg_color="transparent")
    mid_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
    mid_frame.grid_columnconfigure(1, weight=1)
    mid_frame.grid_rowconfigure(0, weight=1)

    # Left: Thumbnail Snapshot Box
    self.thumb_card = ctk.CTkFrame(mid_frame, width=240)
    self.thumb_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
    self.thumb_card.grid_propagate(False)

    self.thumb_label = ctk.CTkLabel(
        self.thumb_card,
        text="No Preview\nAvailable",
        text_color="gray",
        font=ctk.CTkFont(size=12),
    )
    self.thumb_label.pack(expand=True, fill="both", padx=10, pady=10)

    # Right: Metadata & Settings Card
    settings_card = ctk.CTkFrame(mid_frame)
    settings_card.grid(row=0, column=1, sticky="nsew")
    settings_card.grid_columnconfigure(0, weight=1)

    # Title & Duration labels
    self.title_label = ctk.CTkLabel(
        settings_card,
        text="Title: Waiting for URL...",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w",
        wraplength=420,
    )
    self.title_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

    self.duration_label = ctk.CTkLabel(
        settings_card,
        text="Duration: --:--",
        font=ctk.CTkFont(size=12),
        anchor="w",
    )
    self.duration_label.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

    # Save Folder Selection
    folder_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
    folder_frame.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
    folder_frame.grid_columnconfigure(0, weight=1)

    self.path_entry = ctk.CTkEntry(
        folder_frame, textvariable=self.save_path, height=35
    )
    self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    ctk.CTkButton(
        folder_frame, text="Browse", command=self.browse_directory, width=90
    ).grid(row=0, column=1)

    # Quality Selector Dropdown
    qual_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
    qual_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew")
    qual_frame.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(qual_frame, text="Resolution:").grid(
        row=0, column=0, sticky="w", padx=(0, 10)
    )
    qualities = [
        "Best Available Quality (.mp4)",
        "1080p HD (.mp4)",
        "720p HD (.mp4)",
        "480p SD (.mp4)",
        "Audio Only (.mp4 / m4a)",
    ]
    self.qual_dropdown = ctk.CTkComboBox(
        qual_frame, variable=self.quality_var, values=qualities, height=35
    )
    self.qual_dropdown.grid(row=0, column=1, sticky="ew")

    # Embed Thumbnail Checkbox
    self.embed_chk = ctk.CTkCheckBox(
        settings_card, text="Embed Thumbnail into File", variable=self.embed_thumb_var
    )
    self.embed_chk.grid(row=4, column=0, padx=15, pady=10, sticky="w")

    # 4. Bottom Action Frame (Progress Bar & Button)
    bottom_card = ctk.CTkFrame(self)
    bottom_card.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
    bottom_card.grid_columnconfigure(0, weight=1)

    # Progress stats row
    stats_frame = ctk.CTkFrame(bottom_card, fg_color="transparent")
    stats_frame.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
    stats_frame.grid_columnconfigure(0, weight=1)

    self.status_label = ctk.CTkLabel(
        stats_frame, text="Ready", font=ctk.CTkFont(size=11), text_color="gray"
    )
    self.status_label.grid(row=0, column=0, sticky="w")

    self.percent_label = ctk.CTkLabel(
        stats_frame,
        text="0.0%",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color="#1f538d",
    )
    self.percent_label.grid(row=0, column=1, sticky="e")

    # Progress Bar
    self.progress_bar = ctk.CTkProgressBar(bottom_card, height=12)
    self.progress_bar.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
    self.progress_bar.set(0.0)

    # Download Button
    self.download_btn = ctk.CTkButton(
        bottom_card,
        text="Start .MP4 Download",
        command=self.start_download_thread,
        height=45,
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    self.download_btn.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")

  def clean_ansi(self, text):
    return self.ansi_escape.sub("", text)

  def browse_directory(self):
    dir_path = filedialog.askdirectory()
    if dir_path:
      self.save_path.set(dir_path)

  def fetch_info_thread(self):
    url = self.url_var.get().strip()
    if not url:
      messagebox.showerror("Error", "Please enter a valid YouTube URL.")
      return
    self.status_label.configure(text="Fetching video metadata...")
    threading.Thread(
        target=self.fetch_metadata_task, args=(url,), daemon=True
    ).start()

  def fetch_metadata_task(self, url):
    try:
      with yt_dlp.YoutubeDL({"skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "Unknown Title")
        duration = info.get("duration", 0)
        mins, secs = divmod(duration, 60)
        thumb_url = info.get("thumbnail", "")

        self.after(
            0,
            lambda: self.title_label.configure(text=f"Title: {title}"),
        )
        self.after(
            0,
            lambda: self.duration_label.configure(
                text=f"Duration: {int(mins)}m {int(secs)}s"
            ),
        )
        self.after(
            0, lambda: self.status_label.configure(text="Metadata loaded.")
        )

        if thumb_url:
          self.load_thumbnail(thumb_url)
    except Exception as e:
      self.after(
          0,
          lambda: messagebox.showerror(
              "Error", f"Failed to fetch metadata:\n{e}"
          ),
      )
      self.after(
          0, lambda: self.status_label.configure(text="Metadata fetch failed.")
      )

  def load_thumbnail(self, url):
    try:
      with urlopen(url) as u:
        raw = u.read()
      im = Image.open(io.BytesIO(raw))
      ctk_img = ctk.CTkImage(light_image=im, dark_image=im, size=(210, 120))
      self.after(0, lambda: self.thumb_label.configure(text="", image=ctk_img))
      self.thumb_label.image = ctk_img  # Keep reference
    except Exception as e:
      print(f"Thumbnail error: {e}")

  def get_ydl_options(self):
    quality = self.quality_var.get()
    outtmpl = os.path.join(self.save_path.get(), "%(title)s.%(ext)s")

    if "Audio Only" in quality:
      format_str = "bestaudio[ext=m4a]/bestaudio/best"
      postprocessors = [{
          "key": "FFmpegExtractAudio",
          "preferredcodec": "m4a",
      }]
    else:
      if "1080p" in quality:
        format_str = (
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"
        )
      elif "720p" in quality:
        format_str = (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"
        )
      elif "480p" in quality:
        format_str = (
            "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"
        )
      else:
        format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

      postprocessors = []
      if self.embed_thumb_var.get():
        postprocessors.append({"key": "EmbedThumbnail"})

    return {
        "format": format_str,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "postprocessors": postprocessors,
        "progress_hooks": [self.progress_hook],
    }

  def progress_hook(self, d):
    if d["status"] == "downloading":
      p_str = self.clean_ansi(d.get("_percent_str", "0.0%")).strip()
      speed = self.clean_ansi(d.get("_speed_str", "Unknown speed")).strip()
      eta = self.clean_ansi(d.get("_eta_str", "Unknown time")).strip()

      try:
        val = float(p_str.replace("%", "")) / 100.0
      except ValueError:
        val = 0.0

      self.after(0, lambda: self.progress_bar.set(val))
      self.after(0, lambda: self.percent_label.configure(text=p_str))
      self.after(
          0,
          lambda: self.status_label.configure(
              text=f"Downloading... Speed: {speed} | ETA: {eta}"
          ),
      )
    elif d["status"] == "finished":
      self.after(
          0,
          lambda: self.status_label.configure(
              text="Merging tracks & saving as .mp4..."
          ),
      )

  def start_download_thread(self):
    url = self.url_var.get().strip()
    if not url:
      messagebox.showerror("Error", "Please enter a valid YouTube URL.")
      return

    self.download_btn.configure(state="disabled")
    self.progress_bar.set(0.0)

    threading.Thread(
        target=self.run_download_task, args=(url,), daemon=True
    ).start()

  def run_download_task(self, url):
    try:
      ydl_opts = self.get_ydl_options()
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

      self.after(
          0,
          lambda: messagebox.showinfo(
              "Success", "Video downloaded successfully as .mp4!"
          ),
      )
      self.after(
          0, lambda: self.status_label.configure(text="Download complete!")
      )
    except Exception as e:
      self.after(
          0, lambda: messagebox.showerror("Error", f"Download failed:\n{e}")
      )
      self.after(
          0, lambda: self.status_label.configure(text="Download failed.")
      )
    finally:
      self.after(0, lambda: self.download_btn.configure(state="normal"))


if __name__ == "__main__":
  app = ModernYouTubeDownloader()
  app.mainloop()