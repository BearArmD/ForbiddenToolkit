"""
ForbiddenToolkit.py -- Forbidden Cheese Development
Swiss-army CTF and security utility tool.

Tabs:
  1. Encode / Decode  -- Base64, Base32, Hex, URL, ROT13, Binary (stdlib)
  2. Hash ID          -- Identify hash types (pip install hashid)
  3. Strings          -- Extract printable strings from any file (stdlib)
  4. Exif             -- Dump file metadata (ExifTool external)

Dependencies:
    pip install hashid Pillow opencv-python pygame

Audio files (generate with ForbiddenReader, place in same folder as script):
    BGM.wav        -- looping ambient, plays at low volume always
    welcome.wav    -- plays on every launch after splash
    results.wav    -- plays when results are returned
    nomatch.wav    -- plays when nothing is found
    error.wav      -- plays when something breaks

Run:
    python ForbiddenToolkit.py
"""

import tkinter as tk
from tkinter import filedialog, ttk
import base64
import os
import sys
import re
import time
import string
import subprocess
import threading
import configparser
from urllib.parse import quote, unquote

# ── APP DIRECTORY ─────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "fk_config.ini")

# ── FC COLOUR PALETTE ─────────────────────────────────────────────────────────
DARK_BG  = "#1a1a2e"
PANEL_BG = "#16213e"
ACCENT   = "#e94560"
BTN_FG   = "#dde1e7"
TEXT_BG  = "#0f3460"
TEXT_FG  = "#e0e0e0"
STS_BG   = "#0d0d1a"
STS_FG   = "#bbbbbb"

LOGO_HEIGHT = 40
BGM_VOLUME    = 0.30
SPEECH_VOLUME = 0.87

# ── EXIFTOOL CANDIDATES ───────────────────────────────────────────────────────
EXIFTOOL_CANDIDATES = [
    os.path.join(APP_DIR, "ExifTool", "ExifTool.exe"),
    "exiftool",
    r"C:\Windows\exiftool.exe",
    r"C:\Program Files\ExifTool\exiftool.exe",
    r"C:\Users\b3ar\AppData\Local\Programs\ExifTool\ExifTool.exe",
]

def find_exiftool():
    for c in EXIFTOOL_CANDIDATES:
        try:
            r = subprocess.run([c, "-ver"], capture_output=True, timeout=5,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0:
                return c
        except Exception:
            pass
    return None

# ── CONFIG ────────────────────────────────────────────────────────────────────

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE, encoding="utf-8")
    p = cfg["paths"] if "paths" in cfg else {}
    s = cfg["state"] if "state" in cfg else {}
    return {
        "logo_path":    p.get("logo_path",    ""),
        "splash_video": p.get("splash_video", ""),
        "splash_audio": p.get("splash_audio", ""),
        "exiftool":     p.get("exiftool",     ""),
        "bgm_wav":      p.get("bgm_wav",      os.path.join(APP_DIR, "BGM.wav")),
        "welcome_wav":  p.get("welcome_wav",  os.path.join(APP_DIR, "welcome.wav")),
        "results_wav":  p.get("results_wav",  os.path.join(APP_DIR, "results.wav")),
        "nomatch_wav":  p.get("nomatch_wav",  os.path.join(APP_DIR, "nomatch.wav")),
        "error_wav":    p.get("error_wav",    os.path.join(APP_DIR, "error.wav")),
        "first_run":    s.get("first_run",    "True") == "True",
    }

def save_config(d):
    cfg = configparser.ConfigParser()
    cfg["paths"] = {
        "logo_path":    d.get("logo_path",    ""),
        "splash_video": d.get("splash_video", ""),
        "splash_audio": d.get("splash_audio", ""),
        "exiftool":     d.get("exiftool",     ""),
        "bgm_wav":      d.get("bgm_wav",      ""),
        "welcome_wav":  d.get("welcome_wav",  ""),
        "results_wav":  d.get("results_wav",  ""),
        "nomatch_wav":  d.get("nomatch_wav",  ""),
        "error_wav":    d.get("error_wav",    ""),
    }
    cfg["state"] = {"first_run": str(d.get("first_run", False))}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cfg.write(f)

# ── GLOBALS ───────────────────────────────────────────────────────────────────
cfg        = {}
root       = None
status_var = None
notebook   = None
_bgm_ch    = None
_speech_ch = None

# ══════════════════════════════════════════════════════════════════════════════
# AUDIO SYSTEM -- pygame dual-channel
# Channel 0 = BGM (looping, low volume)
# Channel 1 = speech (full volume, plays on top)
# ══════════════════════════════════════════════════════════════════════════════

_sound_cache = {}   # pre-loaded pygame Sound objects

def audio_init():
    global _bgm_ch, _speech_ch
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(2)
        _bgm_ch    = pygame.mixer.Channel(0)
        _speech_ch = pygame.mixer.Channel(1)
        _bgm_ch.set_volume(BGM_VOLUME)
        _speech_ch.set_volume(SPEECH_VOLUME)
    except Exception:
        _bgm_ch = None
        _speech_ch = None

def preload_sounds():
    """Load all WAV files into memory in a background thread so playback is instant."""
    keys = ["bgm_wav", "welcome_wav", "results_wav", "nomatch_wav", "error_wav"]
    try:
        import pygame
        for key in keys:
            path = cfg.get(key, "")
            if path and os.path.isfile(path) and key not in _sound_cache:
                try:
                    _sound_cache[key] = pygame.mixer.Sound(path)
                except Exception:
                    pass
    except Exception:
        pass

def bgm_start():
    if _bgm_ch is None:
        return
    path = cfg.get("bgm_wav", "")
    if not path or not os.path.isfile(path):
        return
    try:
        sound = _sound_cache.get("bgm_wav")
        if sound is None:
            import pygame
            sound = pygame.mixer.Sound(path)
            _sound_cache["bgm_wav"] = sound
        _bgm_ch.play(sound, loops=-1)
        _bgm_ch.set_volume(BGM_VOLUME)
    except Exception:
        pass

def bgm_pause():
    if _bgm_ch:
        try: _bgm_ch.pause()
        except Exception: pass

def bgm_resume():
    if _bgm_ch:
        try: _bgm_ch.unpause()
        except Exception: pass

def bgm_stop():
    if _bgm_ch:
        try: _bgm_ch.stop()
        except Exception: pass

def play_speech(wav_key):
    """Play a speech WAV on channel 1 using pre-cached Sound object."""
    if _speech_ch is None:
        return
    def _play():
        try:
            sound = _sound_cache.get(wav_key)
            if sound is None:
                path = cfg.get(wav_key, "")
                if not path or not os.path.isfile(path):
                    return
                import pygame
                sound = pygame.mixer.Sound(path)
                _sound_cache[wav_key] = sound
            _speech_ch.play(sound)
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
# SPLASH
# ══════════════════════════════════════════════════════════════════════════════

def show_splash():
    vid = cfg.get("splash_video", "")
    aud = cfg.get("splash_audio", "")
    if not vid or not os.path.isfile(vid):
        return
    try:
        import cv2
        from PIL import Image, ImageTk
    except ImportError:
        return

    cap = cv2.VideoCapture(vid)
    if not cap.isOpened():
        return

    bgm_pause()

    fps     = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_s = 1.0 / fps
    root.update()
    win_w = root.winfo_width()
    win_h = root.winfo_height()

    overlay = tk.Canvas(root, bg="black", highlightthickness=0)
    overlay.place(x=0, y=0, relwidth=1, relheight=1)
    placeholder = ImageTk.PhotoImage(Image.new("RGB", (win_w, win_h), (0, 0, 0)))
    image_id = overlay.create_image(0, 0, anchor="nw", image=placeholder)
    root.update()

    skipped = [False]
    def skip(_=None): skipped[0] = True
    overlay.bind("<Button-1>", skip)
    root.bind("<KeyPress>", skip)

    if aud and os.path.isfile(aud):
        import winsound
        threading.Thread(
            target=lambda: winsound.PlaySound(aud, winsound.SND_FILENAME),
            daemon=True).start()

    photo_ref = [placeholder]
    try:
        while not skipped[0]:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                break
            resized = cv2.resize(frame, (win_w, win_h), interpolation=cv2.INTER_LINEAR)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            photo_ref[0] = ImageTk.PhotoImage(Image.fromarray(rgb))
            overlay.itemconfig(image_id, image=photo_ref[0])
            root.update()
            spent = time.time() - t0
            if frame_s - spent > 0:
                time.sleep(frame_s - spent)
    except Exception:
        pass

    cap.release()
    root.unbind("<KeyPress>")
    overlay.destroy()
    root.update()
    bgm_resume()

# ══════════════════════════════════════════════════════════════════════════════
# SHARED UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def set_status(msg):
    if status_var:
        status_var.set(msg)

def mkbtn(parent, label, cmd, bg=PANEL_BG, fg=BTN_FG, w=10, bold=False):
    font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
    return tk.Button(parent, text=label, command=cmd, width=w,
                     font=font, relief="flat", bg=bg, fg=fg,
                     activebackground="#2e2e50", activeforeground=fg,
                     cursor="hand2", padx=4)

def load_logo(path, height):
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        ratio = height / img.height
        img = img.resize((int(img.width * ratio), height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def make_textbox(parent, height=8, readonly=False):
    frm = tk.Frame(parent, bg=DARK_BG)
    sb  = tk.Scrollbar(frm, bg=PANEL_BG, troughcolor=DARK_BG, relief="flat")
    sb.pack(side="right", fill="y")
    txt = tk.Text(frm, wrap="word", height=height,
                  font=("Consolas", 10), yscrollcommand=sb.set,
                  relief="flat", bd=0, padx=10, pady=8,
                  bg=TEXT_BG, fg=TEXT_FG,
                  insertbackground="white",
                  selectbackground=ACCENT,
                  state="disabled" if readonly else "normal")
    txt.pack(fill="both", expand=True)
    sb.config(command=txt.yview)
    return frm, txt

def txt_set(widget, content):
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", content)
    widget.config(state="disabled")

def lbl(parent, text, bold=False, fg=BTN_FG):
    font = ("Segoe UI", 9, "bold") if bold else ("Segoe UI", 9)
    return tk.Label(parent, text=text, font=font, fg=fg, bg=DARK_BG, anchor="w")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 -- ENCODE / DECODE
# ══════════════════════════════════════════════════════════════════════════════

ENCODE_MODES = [
    "Base64  encode", "Base64  decode",
    "Base32  encode", "Base32  decode",
    "Hex     encode", "Hex     decode",
    "URL     encode", "URL     decode",
    "ROT13",
    "Binary  encode", "Binary  decode",
]

def _do_encode(mode, text):
    try:
        b = text.encode("utf-8")
        if mode == "Base64  encode":  return base64.b64encode(b).decode()
        if mode == "Base64  decode":  return base64.b64decode(text.strip()).decode("utf-8", errors="replace")
        if mode == "Base32  encode":  return base64.b32encode(b).decode()
        if mode == "Base32  decode":  return base64.b32decode(text.strip().upper()).decode("utf-8", errors="replace")
        if mode == "Hex     encode":  return b.hex()
        if mode == "Hex     decode":  return bytes.fromhex(re.sub(r"\s","",text)).decode("utf-8", errors="replace")
        if mode == "URL     encode":  return quote(text)
        if mode == "URL     decode":  return unquote(text)
        if mode == "ROT13":
            return ''.join(
                chr((ord(c)-(ord('A') if c.isupper() else ord('a'))+13)%26
                    +(ord('A') if c.isupper() else ord('a')))
                if c.isalpha() else c for c in text)
        if mode == "Binary  encode":
            return ' '.join(f"{x:08b}" for x in b)
        if mode == "Binary  decode":
            bits = re.sub(r"\s","",text)
            return ''.join(chr(int(bits[i:i+8],2)) for i in range(0,len(bits),8))
    except Exception as e:
        return f"ERROR: {e}"
    return "Unknown mode"

def _auto_detect(text):
    t = text.strip()
    # Binary
    tb = re.sub(r"\s","",t)
    if re.match(r"^[01]+$",tb) and len(tb)%8==0 and len(tb)>=8:
        try:
            r=''.join(chr(int(tb[i:i+8],2)) for i in range(0,len(tb),8))
            if r.isprintable(): return "Binary", r
        except Exception: pass
    # Hex
    th = re.sub(r"\s","",t)
    if re.match(r"^[0-9A-Fa-f]+$",th) and len(th)%2==0 and len(th)>=4:
        try:
            r=bytes.fromhex(th).decode("utf-8",errors="replace")
            if r.isprintable(): return "Hex", r
        except Exception: pass
    # Base32
    tb32=re.sub(r"\s","",t).upper()
    if re.match(r"^[A-Z2-7]+=*$",tb32) and len(tb32)%8==0 and len(tb32)>=8:
        try:
            r=base64.b32decode(tb32).decode("utf-8",errors="replace")
            if r.isprintable(): return "Base32", r
        except Exception: pass
    # Base64
    tb64=re.sub(r"\s","",t)
    if re.match(r"^[A-Za-z0-9+/]*={0,2}$",tb64) and len(tb64)%4==0 and len(tb64)>=4:
        try:
            r=base64.b64decode(tb64).decode("utf-8",errors="replace")
            if r.isprintable(): return "Base64", r
        except Exception: pass
    # URL
    if re.search(r"%[0-9A-Fa-f]{2}",t):
        try:
            r=unquote(t)
            if r!=t: return "URL encoded", r
        except Exception: pass
    # ROT13 excluded from auto detect -- too ambiguous, false positives common.
    # User is directed to the manual dropdown.
    return None, ("Could not auto-detect encoding.\n\n"
                  "Tips:\n"
                  "  - If input looks like shifted letters, try ROT13 in the dropdown.\n"
                  "  - For mixed content (letters + numbers + symbols), use manual mode.\n"
                  "  - Paste only the encoded portion with no extra text.")

def build_encode_tab(parent):
    frm = tk.Frame(parent, bg=DARK_BG, padx=12, pady=8)
    frm.pack(fill="both", expand=True)
    lbl(frm,"Input",bold=True).pack(anchor="w")
    frm_in, txt_in = make_textbox(frm, height=7)
    frm_in.pack(fill="both", expand=True, pady=(2,6))
    ctrl = tk.Frame(frm, bg=DARK_BG)
    ctrl.pack(fill="x", pady=4)
    mode_var = tk.StringVar(value=ENCODE_MODES[0])
    lbl(ctrl,"Operation:").pack(side="left")
    menu = tk.OptionMenu(ctrl, mode_var, *ENCODE_MODES)
    menu.config(bg=PANEL_BG, fg=BTN_FG, relief="flat", highlightthickness=0,
                activebackground="#2e2e50", activeforeground=BTN_FG,
                font=("Segoe UI",9), width=18)
    menu["menu"].config(bg=PANEL_BG, fg=BTN_FG, font=("Segoe UI",9),
                        activebackground=ACCENT, activeforeground="white")
    menu.pack(side="left", padx=8)
    frm_out, txt_out = make_textbox(frm, height=7, readonly=True)

    def run():
        text = txt_in.get("1.0",tk.END).strip()
        if not text:
            set_status("Encode/Decode: nothing to process.")
            return
        mode = mode_var.get()
        result = _do_encode(mode, text)
        txt_set(txt_out, result)
        if result.startswith("ERROR"):
            play_speech("error_wav")
            set_status("Encode/Decode: error.")
        else:
            play_speech("results_wav")
            set_status(f"Encode/Decode: {mode.strip()} complete.")

    def auto_detect():
        text = txt_in.get("1.0",tk.END).strip()
        if not text:
            set_status("Auto Detect: paste something first.")
            return
        detected, result = _auto_detect(text)
        txt_set(txt_out, result)
        if detected:
            play_speech("results_wav")
            set_status(f"Auto Detect: identified as {detected}.")
        else:
            play_speech("nomatch_wav")
            set_status("Auto Detect: no encoding matched.")

    def copy_out():
        out = txt_out.get("1.0",tk.END).strip()
        if out:
            root.clipboard_clear()
            root.clipboard_append(out)
            set_status("Copied to clipboard.")

    def clear():
        txt_in.delete("1.0",tk.END)
        txt_set(txt_out,"")
        set_status("Cleared.")

    btn_row = tk.Frame(ctrl, bg=DARK_BG)
    btn_row.pack(side="right")
    mkbtn(btn_row,"Auto Detect",auto_detect,bg="#16213e",fg="#39ff14",w=11).pack(side="left",padx=4)
    mkbtn(btn_row,"  Run  ",run,bg=ACCENT,fg="white",bold=True,w=8).pack(side="left",padx=4)
    mkbtn(btn_row,"Copy",copy_out,w=6).pack(side="left",padx=4)
    mkbtn(btn_row,"Clear",clear,w=6).pack(side="left",padx=4)
    lbl(frm,"Output",bold=True).pack(anchor="w",pady=(4,0))
    frm_out.pack(fill="both", expand=True, pady=(2,0))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 -- HASH ID
# ══════════════════════════════════════════════════════════════════════════════

def _identify_hash(hash_str):
    try:
        import hashid as hmod
        hi = hmod.HashID()
        results = list(hi.identifyHash(hash_str))
        if not results:
            return None, "No hash types matched.\n\nPaste only the hash with no extra spaces."
        lines=[]
        for r in results[:15]:
            name=getattr(r,"name",str(r))
            hc=getattr(r,"hashcat",None)
            jtr=getattr(r,"john",None)
            parts=[f"  {name}"]
            if hc:  parts.append(f"  Hashcat: {hc}")
            if jtr: parts.append(f"  John: {jtr}")
            lines.append('\n'.join(parts))
        return len(results), '\n\n'.join(lines)
    except ImportError:
        return None, "ERROR: hashid not installed.\nRun: pip install hashid"
    except Exception as e:
        return None, f"ERROR: {e}"

def build_hash_tab(parent):
    frm = tk.Frame(parent, bg=DARK_BG, padx=12, pady=8)
    frm.pack(fill="both", expand=True)
    lbl(frm,"Paste hash string below",bold=True).pack(anchor="w")
    frm_in, txt_in = make_textbox(frm, height=4)
    frm_in.pack(fill="x", pady=(2,6))
    ctrl = tk.Frame(frm, bg=DARK_BG)
    ctrl.pack(fill="x", pady=4)
    frm_out, txt_out = make_textbox(frm, height=14, readonly=True)

    def run():
        h = txt_in.get("1.0",tk.END).strip().split("\n")[0].strip()
        if not h:
            set_status("Hash ID: paste a hash first.")
            return
        set_status("Hash ID: identifying...")
        root.update_idletasks()
        count, result = _identify_hash(h)
        txt_set(txt_out, result)
        if count:
            play_speech("results_wav")
            set_status(f"Hash ID: {count} type(s) matched.")
        elif "ERROR" in result:
            play_speech("error_wav")
            set_status("Hash ID: error.")
        else:
            play_speech("nomatch_wav")
            set_status("Hash ID: no matches.")

    def clear():
        txt_in.delete("1.0",tk.END)
        txt_set(txt_out,"")
        set_status("Cleared.")

    mkbtn(ctrl,"  Identify  ",run,bg=ACCENT,fg="white",bold=True,w=12).pack(side="left")
    mkbtn(ctrl,"Clear",clear,w=7).pack(side="left",padx=8)
    tk.Label(ctrl,text="Hashcat & John modes shown where available",
             font=("Segoe UI",8),fg="#555",bg=DARK_BG).pack(side="left",padx=8)
    lbl(frm,"Results",bold=True).pack(anchor="w",pady=(8,0))
    frm_out.pack(fill="both", expand=True, pady=(2,0))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 -- STRINGS
# ══════════════════════════════════════════════════════════════════════════════

def _extract_strings(path, min_len=4):
    printable = set(string.printable)-set('\t\n\r\x0b\x0c')
    results, current = [], []
    try:
        with open(path,"rb") as f:
            data=f.read()
        for byte in data:
            ch=chr(byte)
            if ch in printable:
                current.append(ch)
            else:
                if len(current)>=min_len:
                    results.append(''.join(current))
                current=[]
        if len(current)>=min_len:
            results.append(''.join(current))
    except Exception as e:
        return None, f"ERROR reading file: {e}"
    return results, None

def build_strings_tab(parent):
    frm = tk.Frame(parent, bg=DARK_BG, padx=12, pady=8)
    frm.pack(fill="both", expand=True)
    ctrl = tk.Frame(frm, bg=DARK_BG)
    ctrl.pack(fill="x", pady=(0,6))
    file_var = tk.StringVar(value="No file loaded")
    tk.Label(ctrl, textvariable=file_var, font=("Segoe UI",9),
             fg="#888", bg=DARK_BG, anchor="w").pack(side="left",fill="x",expand=True)
    min_row = tk.Frame(ctrl, bg=DARK_BG)
    min_row.pack(side="right")
    tk.Label(min_row,text="Min length:",font=("Segoe UI",9),fg=BTN_FG,bg=DARK_BG).pack(side="left")
    min_var = tk.IntVar(value=4)
    tk.Spinbox(min_row,from_=3,to=20,textvariable=min_var,width=4,
               bg=TEXT_BG,fg=TEXT_FG,buttonbackground=PANEL_BG,
               relief="flat",font=("Segoe UI",9)).pack(side="left",padx=4)
    filter_row = tk.Frame(frm, bg=DARK_BG)
    filter_row.pack(fill="x", pady=2)
    tk.Label(filter_row,text="Filter:",font=("Segoe UI",9),fg=BTN_FG,bg=DARK_BG).pack(side="left")
    filter_var = tk.StringVar()
    tk.Entry(filter_row,textvariable=filter_var,font=("Segoe UI",9),
             bg=TEXT_BG,fg=TEXT_FG,insertbackground="white",
             relief="flat",width=30).pack(side="left",padx=6)
    frm_out, txt_out = make_textbox(frm, height=15, readonly=True)
    all_strings=[None]
    last_path=[None]

    def apply_filter(*_):
        if all_strings[0] is None: return
        term=filter_var.get().lower()
        filtered=[s for s in all_strings[0] if term in s.lower()] if term else all_strings[0]
        txt_set(txt_out,'\n'.join(filtered))
        set_status(f"Strings: showing {len(filtered)} of {len(all_strings[0])}.")

    filter_var.trace_add("write",apply_filter)

    def _run_extraction(path):
        file_var.set(os.path.basename(path))
        set_status(f"Strings: extracting...")
        root.update_idletasks()
        results, err = _extract_strings(path, min_var.get())
        if err:
            txt_set(txt_out, err)
            play_speech("error_wav")
            set_status("Strings: read error.")
            return
        all_strings[0]=results
        filter_var.set("")
        txt_set(txt_out,'\n'.join(results))
        play_speech("results_wav")
        set_status(f"Strings: {len(results)} extracted.")

    def load_and_run():
        path=filedialog.askopenfilename(title="Select file",
                                        filetypes=[("All files","*.*")])
        if not path: return
        last_path[0]=path
        _run_extraction(path)

    def rescan():
        if last_path[0] is None:
            set_status("Strings: load a file first.")
            return
        _run_extraction(last_path[0])

    def save_out():
        content=txt_out.get("1.0",tk.END).strip()
        if not content:
            set_status("Nothing to save.")
            return
        path=filedialog.asksaveasfilename(defaultextension=".txt",
                                          filetypes=[("Text file","*.txt")])
        if path:
            with open(path,"w",encoding="utf-8",errors="replace") as f:
                f.write(content)
            set_status(f"Saved: {os.path.basename(path)}")

    btn_row=tk.Frame(frm,bg=DARK_BG)
    btn_row.pack(fill="x",pady=(2,4))
    mkbtn(btn_row,"  Load File  ",load_and_run,bg=ACCENT,fg="white",bold=True,w=14).pack(side="left")
    mkbtn(btn_row,"Rescan",rescan,w=8).pack(side="left",padx=4)
    mkbtn(btn_row,"Save TXT",save_out,w=10).pack(side="left",padx=8)
    frm_out.pack(fill="both",expand=True,pady=(2,0))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 -- EXIF
# ══════════════════════════════════════════════════════════════════════════════

def _run_exiftool(exe, file_path):
    try:
        r=subprocess.run([exe,file_path],capture_output=True,timeout=30,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        out=r.stdout.decode("utf-8",errors="replace").strip()
        err=r.stderr.decode("utf-8",errors="replace").strip()
        if r.returncode!=0: return None, f"ExifTool error:\n{err}"
        return out or "No metadata found.", None
    except FileNotFoundError:
        return None,("ExifTool not found.\n\nClick Browse to locate ExifTool.exe\n"
                     "or: winget install OliverBetz.ExifTool")
    except subprocess.TimeoutExpired:
        return None,"ExifTool timed out."
    except Exception as e:
        return None,f"ERROR: {e}"

def build_exif_tab(parent):
    frm = tk.Frame(parent, bg=DARK_BG, padx=12, pady=8)
    frm.pack(fill="both", expand=True)
    exif_row=tk.Frame(frm,bg=DARK_BG)
    exif_row.pack(fill="x",pady=(0,4))
    tk.Label(exif_row,text="ExifTool:",font=("Segoe UI",9),fg=BTN_FG,bg=DARK_BG).pack(side="left")
    exiftool_var=tk.StringVar(value=cfg.get("exiftool","") or find_exiftool() or "not found")
    tk.Label(exif_row,textvariable=exiftool_var,font=("Consolas",8),
             fg="#888",bg=DARK_BG,anchor="w").pack(side="left",padx=6,fill="x",expand=True)

    def browse_exiftool():
        path=filedialog.askopenfilename(title="Locate ExifTool.exe",
            filetypes=[("ExifTool","ExifTool.exe"),("Executable","*.exe"),("All","*.*")])
        if path:
            exiftool_var.set(path)
            cfg["exiftool"]=path
            save_config(cfg)
            set_status("ExifTool path saved.")

    mkbtn(exif_row,"Browse",browse_exiftool,w=8).pack(side="right")
    file_var=tk.StringVar(value="No file loaded")
    tk.Label(frm,textvariable=file_var,font=("Segoe UI",9),fg="#888",bg=DARK_BG,anchor="w").pack(fill="x")
    frm_out,txt_out=make_textbox(frm,height=15,readonly=True)

    def load_and_run():
        path=filedialog.askopenfilename(title="Select file",
            filetypes=[("All files","*.*"),
                       ("Images","*.jpg *.jpeg *.png *.gif *.tiff *.bmp *.webp"),
                       ("Documents","*.pdf *.docx *.xlsx"),
                       ("Media","*.mp4 *.mp3 *.wav")])
        if not path: return
        exe=exiftool_var.get().strip()
        if not exe or exe=="not found":
            txt_set(txt_out,"ExifTool not found.\nClick Browse above to locate ExifTool.exe.")
            play_speech("error_wav")
            set_status("Exif: ExifTool not configured.")
            return
        file_var.set(os.path.basename(path))
        set_status(f"Exif: reading {os.path.basename(path)}...")
        root.update_idletasks()
        def _run():
            out,err=_run_exiftool(exe,path)
            if err:
                root.after(0,lambda:txt_set(txt_out,err))
                root.after(0,lambda:play_speech("error_wav"))
                root.after(0,lambda:set_status("Exif: error."))
            else:
                root.after(0,lambda:txt_set(txt_out,out))
                lines=out.count('\n')+1
                root.after(0,lambda:play_speech("results_wav"))
                root.after(0,lambda:set_status(f"Exif: {lines} fields extracted."))
        threading.Thread(target=_run,daemon=True).start()

    def save_out():
        content=txt_out.get("1.0",tk.END).strip()
        if not content:
            set_status("Nothing to save.")
            return
        path=filedialog.asksaveasfilename(defaultextension=".txt",
                                          filetypes=[("Text file","*.txt")])
        if path:
            with open(path,"w",encoding="utf-8",errors="replace") as f:
                f.write(content)
            set_status(f"Saved: {os.path.basename(path)}")

    btn_row=tk.Frame(frm,bg=DARK_BG,pady=6)
    btn_row.pack(fill="x")
    mkbtn(btn_row,"  Load File  ",load_and_run,bg=ACCENT,fg="white",bold=True,w=14).pack(side="left")
    mkbtn(btn_row,"Save TXT",save_out,w=10).pack(side="left",padx=8)
    tk.Label(btn_row,text="Supports: images, PDF, Office docs, audio, video",
             font=("Segoe UI",8),fg="#555",bg=DARK_BG).pack(side="left",padx=8)
    frm_out.pack(fill="both",expand=True,pady=(2,0))

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    global cfg, root, status_var, notebook

    loaded=load_config()
    cfg=loaded if loaded else {
        "logo_path":"","splash_video":"","splash_audio":"","exiftool":"",
        "bgm_wav":    os.path.join(APP_DIR,"BGM.wav"),
        "welcome_wav":os.path.join(APP_DIR,"welcome.wav"),
        "results_wav":os.path.join(APP_DIR,"results.wav"),
        "nomatch_wav":os.path.join(APP_DIR,"nomatch.wav"),
        "error_wav":  os.path.join(APP_DIR,"error.wav"),
        "first_run":True,
    }
    if not cfg.get("exiftool"):
        cfg["exiftool"]=find_exiftool() or ""

    first_run=cfg.get("first_run",True)

    audio_init()

    # ── Root window ──
    root=tk.Tk()
    root.title("ForbiddenToolkit -- Forbidden Cheese Development")
    root.geometry("920x680")
    root.minsize(700,520)
    root.configure(bg=DARK_BG)

    # ── Toolbar ──
    frm_top=tk.Frame(root,bg=DARK_BG,pady=6,padx=10)
    frm_top.pack(fill="x")
    tk.Label(frm_top,text="ForbiddenToolkit",
             font=("Segoe UI",13,"bold"),fg=ACCENT,bg=DARK_BG).pack(side="left")
    tk.Label(frm_top,text="  |  Forbidden Cheese Development",
             font=("Segoe UI",9),fg="#555",bg=DARK_BG).pack(side="left")

    def oops():
        """Reinitialise audio engine without restarting the app."""
        bgm_stop()
        audio_init()
        bgm_start()
        set_status("Oops! Audio reset. Ready.")

    mkbtn(frm_top,"⟳ Oops",oops,bg="#2a1a2e",fg="#ff88aa",w=8).pack(side="left",padx=(16,0))

    # Logo -- click fires splash (BGM pause/resume handled inside show_splash)
    logo_path=cfg.get("logo_path","")
    if logo_path and os.path.isfile(logo_path):
        logo_img=load_logo(logo_path,LOGO_HEIGHT)
        if logo_img:
            lbl_logo=tk.Label(frm_top,image=logo_img,bg=DARK_BG,cursor="hand2")
            lbl_logo.image=logo_img
            lbl_logo.pack(side="right",padx=(6,2))
            lbl_logo.bind("<Button-1>",lambda _:show_splash())

    # ── Tab strip ──
    style=ttk.Style()
    style.theme_use("default")
    style.configure("TNotebook",background=DARK_BG,borderwidth=0,tabmargins=[0,0,0,0])
    style.configure("TNotebook.Tab",background=PANEL_BG,foreground=BTN_FG,
                    font=("Segoe UI",10),padding=[16,6],borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected",ACCENT)],
              foreground=[("selected","white")])
    style.configure("TFrame",background=DARK_BG)

    notebook=ttk.Notebook(root)
    notebook.pack(fill="both",expand=True,padx=8,pady=(0,4))

    for tab_name,builder in [
        ("  Encode / Decode  ",build_encode_tab),
        ("  Hash ID  ",        build_hash_tab),
        ("  Strings  ",        build_strings_tab),
        ("  Exif  ",           build_exif_tab),
    ]:
        frame=ttk.Frame(notebook)
        notebook.add(frame,text=tab_name)
        builder(frame)

    # ── Status bar with mute button ──
    status_var = tk.StringVar(value="Ready.")
    status_bar = tk.Frame(root, bg=STS_BG)
    status_bar.pack(fill="x", side="bottom")

    tk.Label(status_bar, textvariable=status_var, anchor="w",
             font=("Consolas", 9), fg=STS_FG, bg=STS_BG,
             padx=10, pady=4).pack(side="left", fill="x", expand=True)

    muted = [False]
    mute_btn_var = tk.StringVar(value="🔊 Mute")

    def toggle_mute():
        muted[0] = not muted[0]
        if muted[0]:
            if _bgm_ch: _bgm_ch.set_volume(0)
            if _speech_ch: _speech_ch.set_volume(0)
            mute_btn_var.set("🔇 Unmute")
        else:
            if _bgm_ch: _bgm_ch.set_volume(BGM_VOLUME)
            if _speech_ch: _speech_ch.set_volume(SPEECH_VOLUME)
            mute_btn_var.set("🔊 Mute")

    tk.Button(status_bar, textvariable=mute_btn_var, command=toggle_mute,
              font=("Segoe UI", 9, "bold"), fg="white", bg=ACCENT,
              relief="flat", cursor="hand2", padx=10, pady=3,
              activebackground="#c73652", activeforeground="white",
              bd=0).pack(side="right", padx=6, pady=2)

    # ── Startup audio ──
    # Step 1: init mixer
    # Step 2: preload all sounds in background (big BGM file needs time to load)
    # Step 3: start BGM once loaded -- keeps hardware warm
    # Step 4: welcome fires 1500ms later -- hardware fully warm by then
    root.update()
    if first_run:
        cfg["first_run"] = False
        save_config(cfg)
        show_splash()

    def _startup_audio():
        preload_sounds()          # blocks until all sounds loaded
        root.after(0, bgm_start)  # BGM starts on main thread
        root.after(1500, lambda: play_speech("welcome_wav"))  # welcome after 1.5s

    threading.Thread(target=_startup_audio, daemon=True).start()

    root.mainloop()
    bgm_stop()


if __name__=="__main__":
    main()
