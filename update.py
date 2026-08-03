import sys
import os
import glob
import logging
import tempfile
import urllib.request
import threading
import time
import json
import traceback
import datetime
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- SETUP LOGGING ---
LOG_FILE = os.path.join(tempfile.gettempdir(), "blur_app.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.info("Starting Image Anonymizer Pro engine...")

# --- DETAILED ERROR DICTIONARY FOR SUPPORT ---
ERROR_DATABASE = {
    "ERR-GEN-000": ("General System Crash", "Uncaught background program crash.", "1. Restart application.\n2. Open Task Manager and check system RAM/CPU.\n3. Send %TEMP%\\blur_app.log to Tier 2 Support."),
    "ERR-GEN-001": ("System Permissions", "Permission denied when executing app resources.", "1. Right-click app > Run as Administrator.\n2. Verify write permissions to AppData folder.\n3. Temporarily disable antivirus auto-sandbox."),
    "ERR-IMG-001": ("File Read Access", "Image cannot be read or opened from disk.", "1. Ensure file is stored locally (C: drive), not on cloud drives.\n2. Uncheck Read-Only in file properties.\n3. Re-save file in MS Paint as standard .png or .jpg."),
    "ERR-IMG-002": ("Memory Limit Exceeded", "Image resolution is too large for canvas memory.", "1. Check image dimensions (must be under 8K / 7680x4320).\n2. Resize image using Paint or an external converter.\n3. Set Windows Display Scaling to 100% or 125%."),
    "ERR-IMG-003": ("Corrupt File Header", "Unsupported or corrupted image file structure.", "1. Verify file extension matches actual format.\n2. Re-download or re-export original source file.\n3. Convert image to baseline JPEG format."),
    "ERR-CV2-001": ("OpenCV Missing", "Core OpenCV library failed to initialize.", "1. Check installed apps for conflicting Python installs.\n2. Run setup installer as Administrator to repair binaries."),
    "ERR-CV2-005": ("Face AI Data Missing", "Face detection Haar Cascade XML model missing.", "1. Verify haarcascade_frontalface_default.xml exists in app folder.\n2. Re-run setup installer as Administrator."),
    "ERR-CV2-010": ("Module Binding Failure", "OpenCV dynamic link library (DLL) binding error.", "1. Confirm host OS is Windows 10/11 64-bit.\n2. Install Visual C++ Redistributable 2015-2022 (x64).\n3. Restart host computer."),
    "ERR-CV2-012": ("Memory Overflow", "AI face detection scan ran out of system buffer.", "1. Close memory-heavy background applications.\n2. Reset zoom to 1.0x before running detection.\n3. Crop target image area before scanning."),
    "ERR-NET-001": ("Offline Mode Active", "No active internet connection detected.", "1. Verify Wi-Fi or Ethernet connection.\n2. Test connection in standard web browser.\n3. Ignore banner if offline processing is intended."),
    "ERR-NET-002": ("Cloud Sync Failure", "Failed to reach download or update server.", "1. Check firewall outbound HTTP/HTTPS settings.\n2. Disable local VPN or proxy servers.\n3. Test download link directly in a web browser."),
    "ERR-GUI-001": ("Display Bounds Warning", "Window resolution smaller than required grid.", "1. Increase display resolution to at least 1280x720.\n2. Set Windows scaling to 100%.\n3. Maximize application window upon launch."),
    "ERR-GUI-005": ("GUI Engine Crash", "Tkinter widget rendering failure.", "1. Update host system graphics drivers.\n2. Reset Windows display scaling to recommended 100%.\n3. Launch app in compatibility mode."),
    "ERR-IO-001": ("Save Failure", "Failed to save output image to target path.", "1. Ensure target drive has >500MB free disk space.\n2. Check Windows Controlled Folder Access settings.\n3. Choose alternative destination folder (e.g., Desktop)."),
    "ERR-IO-002": ("File Lock Conflict", "Output file is locked by another program.", "1. Close image viewers, Photoshop, or browser apps.\n2. Save file under a new unique filename."),
    "ERR-CFG-001": ("Configuration Corrupt", "User settings file is unreadable.", "1. Press Win+R, type %APPDATA%, and open app folder.\n2. Delete settings.json file.\n3. Restart app to generate default configuration.")
}

AD_PRESETS = [
    "🔥 UPGRADE TO ANONYMIZER PRO GOLD - 80% OFF TODAY ONLY! 🔥",
    "⚡ WIN A FREE RTX 4090! CLICK HERE TO CLAIM YOUR PRIZE! ⚡",
    "🛡️ YOUR PC MAY BE UNPROTECTED! DOWNLOAD ANONYM-SHIELD NOW! 🛡️",
    "💰 LOCAL SINGLES WANT TO BLUR IMAGES NEAR YOU! 💰",
    "🚀 SPEED UP YOUR COMPUTER BY 300% WITH FREE RAM CLEANER! 🚀",
    "🎁 CONGRATULATIONS USER! YOU ARE THE 1,000,000TH VISITOR! 🎁"
]

# --- ADVANCED ERROR WINDOW ---
class AdvancedErrorDialog(tk.Toplevel):
    def __init__(self, parent, code, details=""):
        super().__init__(parent)
        self.title(f"Diagnostic Error Report [{code}]")
        self.geometry("620x450")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)

        title, cause, fix = ERROR_DATABASE.get(code, ("Unknown System Issue", details or "Unspecified error", "Contact administrator."))
        logging.error(f"Error Window Displayed: {code} - {details}")

        hdr = tk.Frame(self, bg="#d32f2f", height=50)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"⚠️ CRITICAL SYSTEM ALERT: {code}", fg="white", bg="#d32f2f", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=15, pady=10)

        body = tk.Frame(self, bg="#1e1e1e", padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text=f"Issue: {title}", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        tk.Label(body, text="Technical Cause:", fg="#888888", bg="#1e1e1e", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 2))
        cause_lbl = tk.Label(body, text=cause, fg="#e0e0e0", bg="#2a2a2a", font=("Segoe UI", 9), anchor="w", justify=tk.LEFT, padx=10, pady=8, wraplength=550)
        cause_lbl.pack(fill=tk.X)

        tk.Label(body, text="Support Resolution Steps:", fg="#888888", bg="#1e1e1e", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 2))
        
        fix_txt = tk.Text(body, bg="#2a2a2a", fg="#4caf50", font=("Consolas", 9), relief=tk.FLAT, height=7, padx=10, pady=8)
        fix_txt.insert(tk.END, fix)
        fix_txt.config(state=tk.DISABLED)
        fix_txt.pack(fill=tk.X)

        btn_bar = tk.Frame(self, bg="#1e1e1e", pady=10)
        btn_bar.pack(fill=tk.X)
        tk.Button(btn_bar, text="📋 Copy Log Path", command=lambda: self.clipboard_clear() or self.clipboard_append(LOG_FILE), bg="#333", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_bar, text="Close & Continue", command=self.destroy, bg="#1976d2", fg="white", font=("Segoe UI", 9, "bold"), width=15).pack(side=tk.RIGHT, padx=20)

# Global Crash Handler
def global_crash_handler(exc_type, exc_value, exc_tb):
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.critical(f"Unhandled Exception: {err_str}")

    code = "ERR-GEN-000"
    if "cv2" in err_str.lower(): code = "ERR-CV2-010"
    elif "pil" in err_str.lower() or "image" in err_str.lower(): code = "ERR-IMG-002"
    elif "permission" in err_str.lower(): code = "ERR-GEN-001"

    root = tk.Tk()
    root.withdraw()
    dlg = AdvancedErrorDialog(root, code, str(exc_value))
    dlg.mainloop()
    sys.exit(1)

sys.excepthook = global_crash_handler

# Core Libraries Import
try:
    import cv2
    import cv2.data
    import numpy as np
    from PIL import Image, ImageTk, ImageEnhance, ImageOps
except Exception as e:
    logging.critical(f"Failed loading core packages: {e}")
    raise ImportError(f"Core module load failure: {e}")


class MegaAnonymizerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Anonymizer Pro v3.0 — Enterprise Suite")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 750)

        # State Core
        self.cv_img = None
        self.history = []
        self.redo_stack = []
        self.rects = []
        self.scale_factor = 1.0
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # UI Preferences
        self.dark_mode = True
        self.show_grid = False
        self.show_thirds = False
        self.active_tool = "SELECT"
        self.watermark_text = tk.StringVar(value="REDACTED")
        self.burn_timestamp = tk.BooleanVar(value=False)
        self.is_online = True

        # AI Detector Settings
        self.ai_scale = tk.DoubleVar(value=1.1)
        self.ai_neighbors = tk.IntVar(value=5)

        self._init_cascade()
        self._build_interface()
        self._bind_hotkeys()
        self.start_network_monitor()
        self.start_ad_rotator()

    def _init_cascade(self):
        try:
            path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(path)
        except Exception:
            self.face_cascade = None

    def _build_interface(self):
        self.main_box = tk.Frame(self.root, bg="#181818")
        self.main_box.pack(fill=tk.BOTH, expand=True)

        # Top Banner
        self.top_ad_frame = tk.Frame(self.main_box, bg="#FFD700", height=45)
        self.top_ad_frame.pack(fill=tk.X, side=tk.TOP)
        self.top_ad_label = tk.Label(
            self.top_ad_frame,
            text="🔥 ADVERTISEMENT: UPGRADE TO ANONYMIZER PRO GOLD FOR NO ADS! 80% OFF TODAY ONLY! 🔥",
            bg="#FFD700", fg="#000000", font=("Segoe UI", 10, "bold")
        )
        self.top_ad_label.pack(side=tk.LEFT, padx=15, pady=8)
        tk.Button(
            self.top_ad_frame, text="[CLICK HERE]", bg="#FF0000", fg="white",
            font=("Segoe UI", 9, "bold"), relief=tk.RAISED,
            command=lambda: messagebox.showinfo("Sponsor", "Thank you for supporting our sponsors!")
        ).pack(side=tk.RIGHT, padx=15, pady=5)

        # Ribbon
        self.ribbon = tk.Frame(self.main_box, bg="#252526", height=40)
        self.ribbon.pack(fill=tk.X)

        tk.Button(self.ribbon, text="📁 Open File", command=self.load_image, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.ribbon, text="📂 Batch Folder", command=self.batch_process_dialog, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Button(self.ribbon, text="💾 Save Output", command=self.save_image, bg="#1976D2", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(self.ribbon, text="|", fg="#555", bg="#252526").pack(side=tk.LEFT, padx=5)
        tk.Button(self.ribbon, text="🖐️ Pan Tool", command=lambda: self.set_tool("PAN"), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="📦 Select Region", command=lambda: self.set_tool("SELECT"), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        tk.Button(self.ribbon, text="🌐 Grid Overlay", command=self.toggle_grid, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="📐 Rule of Thirds", command=self.toggle_thirds, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        tk.Button(self.ribbon, text="❓ Support Center", command=self.open_support_center, bg="#4A148C", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(side=tk.RIGHT, padx=10)

        # Body Frame
        self.body_frame = tk.Frame(self.main_box, bg="#181818")
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(self.body_frame, bg="#212121", width=300)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        nb = ttk.Notebook(sidebar)
        nb.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Effects
        t1 = tk.Frame(nb, bg="#212121")
        nb.add(t1, text="Effects")

        self._lbl(t1, "EFFECT TYPE")
        self.effect_mode = tk.StringVar(value="Gaussian")
        effects = [
            ("Gaussian Blur", "Gaussian"),
            ("Pixelate / Mosaic", "Pixelate"),
            ("Blackout Mask", "Blackout"),
            ("Soft Radial Blur", "Radial"),
            ("Color Solid Block", "SolidColor"),
            ("Noise Obfuscation", "Noise")
        ]
        for txt, val in effects:
            tk.Radiobutton(t1, text=txt, value=val, variable=self.effect_mode, bg="#212121", fg="white", selectcolor="#181818").pack(anchor=tk.W, padx=15)

        self.invert_var = tk.BooleanVar(value=False)
        tk.Checkbutton(t1, text="Invert Mask (Blur Background)", variable=self.invert_var, bg="#212121", fg="#FFB74D", selectcolor="#181818").pack(anchor=tk.W, padx=15, pady=5)

        self._lbl(t1, "EFFECT INTENSITY")
        self.blur_slider = tk.Scale(t1, from_=5, to=150, orient=tk.HORIZONTAL, bg="#212121", fg="white", highlightthickness=0)
        self.blur_slider.set(45)
        self.blur_slider.pack(fill=tk.X, padx=15)

        self._lbl(t1, "COLOR BLOCK PICKER")
        self.color_hex = "#000000"
        tk.Button(t1, text="🎨 Choose Mask Color", command=self.pick_color, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)

        tk.Button(t1, text="✨ Apply Effect", command=self.apply_blur, bg="#388E3C", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, padx=15, pady=15)

        # Tab 2: AI Scanner
        t2 = tk.Frame(nb, bg="#212121")
        nb.add(t2, text="AI Scanner")

        self._lbl(t2, "FACE DETECTION FINE-TUNING")
        tk.Label(t2, text="Scale Factor:", fg="#aaa", bg="#212121").pack(anchor=tk.W, padx=15)
        tk.Scale(t2, from_=1.05, to=1.4, resolution=0.05, variable=self.ai_scale, orient=tk.HORIZONTAL, bg="#212121", fg="white").pack(fill=tk.X, padx=15)
        
        tk.Label(t2, text="Min Neighbors:", fg="#aaa", bg="#212121").pack(anchor=tk.W, padx=15)
        tk.Scale(t2, from_=1, to=10, variable=self.ai_neighbors, orient=tk.HORIZONTAL, bg="#212121", fg="white").pack(fill=tk.X, padx=15)

        tk.Button(t2, text="🤖 Detect Frontal Faces", command=self.auto_detect_faces, bg="#7B1FA2", fg="white", font=("Segoe UI", 9, "bold")).pack(fill=tk.X, padx=15, pady=10)

        # Tab 3: Adjustments
        t3 = tk.Frame(nb, bg="#212121")
        nb.add(t3, text="Adjustments")

        self._lbl(t3, "IMAGE CORRECTIONS")
        tk.Button(t3, text="🔄 Rotate 90° Clockwise", command=lambda: self.rotate_image(270), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t3, text="↔️ Flip Horizontal", command=lambda: self.flip_image(1), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t3, text="↕️ Flip Vertical", command=lambda: self.flip_image(0), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t3, text="🌑 Grayscale Conversion", command=self.convert_grayscale, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t3, text="☀️ Auto-Contrast Boost", command=self.auto_contrast, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)

        # Tab 4: Watermark
        t4 = tk.Frame(nb, bg="#212121")
        nb.add(t4, text="Stamps")

        self._lbl(t4, "WATERMARK BURN")
        tk.Entry(t4, textvariable=self.watermark_text, bg="#111", fg="white", insertbackground="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Checkbutton(t4, text="Burn Timestamp", variable=self.burn_timestamp, bg="#212121", fg="white", selectcolor="#181818").pack(anchor=tk.W, padx=15, pady=5)
        tk.Button(t4, text="🏷️ Burn Stamp to Image", command=self.burn_watermark, bg="#E65100", fg="white", font=("Segoe UI", 9, "bold")).pack(fill=tk.X, padx=15, pady=5)

        # Sidebar Footer Controls
        foot = tk.Frame(sidebar, bg="#181818", pady=10)
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(foot, text="↩️ Undo", command=self.undo, bg="#333", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        tk.Button(foot, text="↪️ Redo", command=self.redo, bg="#333", fg="white", width=12).pack(side=tk.RIGHT, padx=10)

        # Right Panel Banner
        self.right_ad_panel = tk.Frame(self.body_frame, bg="#00E676", width=180)
        self.right_ad_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_ad_panel.pack_propagate(False)
        
        tk.Label(self.right_ad_panel, text="📢 ADVERTISEMENT", bg="#00E676", fg="black", font=("Segoe UI", 9, "bold")).pack(pady=10)
        self.tower_ad_box = tk.Label(
            self.right_ad_panel, 
            text="🚀 BOOST YOUR\nPRIVACY TODAY!\n\nGet Unlimited\nCloud Storage\nfor $0.99/mo!",
            bg="#ffffff", fg="#000000", font=("Segoe UI", 10, "bold"), relief=tk.RAISED, padx=10, pady=20, wraplength=150
        )
        self.tower_ad_box.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(self.right_ad_panel, text="CLAIM OFFER 🎁", bg="#1976D2", fg="white", font=("Segoe UI", 10, "bold"), command=lambda: messagebox.showinfo("Offer", "Offer code copied!")).pack(pady=10)

        # Main Canvas
        self.canvas = tk.Canvas(self.body_frame, bg="#111111", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mousedown)
        self.canvas.bind("<B1-Motion>", self.on_mousemove)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouseup)
        self.canvas.bind("<Button-3>", self.on_rightclick)

        # Bottom Frame
        self.bottom_ad_frame = tk.Frame(self.main_box, bg="#2196F3", height=30)
        self.bottom_ad_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.bottom_ad_label = tk.Label(
            self.bottom_ad_frame, 
            text="🌟 SPECIAL SPONSORED MARQUEE: TRY ANONYM-SHIELD VPN FREE FOR 30 DAYS 🌟", 
            bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold")
        )
        self.bottom_ad_label.pack(pady=4)

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, fg="#666", bg="#212121", font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, padx=15, pady=(12, 2))

    def _bind_hotkeys(self):
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Plus>", lambda e: self.zoom(0.2))
        self.root.bind("<Minus>", lambda e: self.zoom(-0.2))

    def start_ad_rotator(self):
        def rotate():
            while True:
                time.sleep(4)
                new_ad = random.choice(AD_PRESETS)
                bg_color = random.choice(["#FFD700", "#FF1744", "#00E676", "#FF9100", "#00E5FF"])
                fg_color = "#000000" if bg_color in ["#FFD700", "#00E676", "#00E5FF"] else "#FFFFFF"
                
                def update_ui():
                    try:
                        self.top_ad_label.config(text=f"🔥 ADVERTISEMENT: {new_ad} 🔥", bg=bg_color, fg=fg_color)
                        self.top_ad_frame.config(bg=bg_color)
                    except Exception:
                        pass
                
                self.root.after(0, update_ui)
        threading.Thread(target=rotate, daemon=True).start()

    def start_network_monitor(self):
        def loop():
            while True:
                try:
                    urllib.request.urlopen("https://www.google.com", timeout=3)
                    online = True
                except Exception:
                    online = False
                self.root.after(0, self._set_online_status, online)
                time.sleep(5)
        threading.Thread(target=loop, daemon=True).start()

    def _set_online_status(self, online):
        if online != self.is_online:
            self.is_online = online

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp")])
        if not path: return
        try:
            img = cv2.imread(path)
            if img is None: raise ValueError("Image read returned empty buffer.")
            self.cv_img = img
            self.history.clear()
            self.redo_stack.clear()
            self.rects.clear()
            self.zoom_level = 1.0
            self.pan_x, self.pan_y = 0, 0
            self.update_canvas()
        except Exception as e:
            AdvancedErrorDialog(self.root, "ERR-IMG-001", str(e))

    def update_canvas(self):
        if self.cv_img is None: return
        self.canvas.delete("all")

        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        h, w = self.cv_img.shape[:2]

        self.scale_factor = min(cw / w, ch / h)
        nw, nh = int(w * self.scale_factor * self.zoom_level), int(h * self.scale_factor * self.zoom_level)

        rgb = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((nw, nh), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(pil)

        ox = (cw - nw) // 2 + self.pan_x
        oy = (ch - nh) // 2 + self.pan_y

        self.canvas.create_image(ox, oy, anchor=tk.NW, image=self.tk_img)

        for r in self.rects:
            self.canvas.create_rectangle(r[0], r[1], r[2], r[3], outline="#FF5722", width=2)

        if self.show_grid:
            for x in range(0, cw, 40): self.canvas.create_line(x, 0, x, ch, fill="#222")
            for y in range(0, ch, 40): self.canvas.create_line(0, y, cw, y, fill="#222")
        if self.show_thirds:
            self.canvas.create_line(cw/3, 0, cw/3, ch, fill="#00E676", dash=(2, 4))
            self.canvas.create_line(2*cw/3, 0, 2*cw/3, ch, fill="#00E676", dash=(2, 4))
            self.canvas.create_line(0, ch/3, cw, ch/3, fill="#00E676", dash=(2, 4))
            self.canvas.create_line(0, 2*ch/3, cw, 2*ch/3, fill="#00E676", dash=(2, 4))

    def set_tool(self, tool): self.active_tool = tool
    def toggle_grid(self): self.show_grid = not self.show_grid; self.update_canvas()
    def toggle_thirds(self): self.show_thirds = not self.show_thirds; self.update_canvas()
    def zoom(self, delta): self.zoom_level = max(0.4, min(4.0, self.zoom_level + delta)); self.update_canvas()

    def on_mousedown(self, e):
        self.sx, self.sy = e.x, e.y
        if self.active_tool == "SELECT":
            self.curr_box = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#00E676", width=2, dash=(4,4))

    def on_mousemove(self, e):
        if self.active_tool == "SELECT" and hasattr(self, 'curr_box'):
            self.canvas.coords(self.curr_box, self.sx, self.sy, e.x, e.y)
        elif self.active_tool == "PAN":
            self.pan_x += (e.x - self.sx)
            self.pan_y += (e.y - self.sy)
            self.sx, self.sy = e.x, e.y
            self.update_canvas()

    def on_mouseup(self, e):
        if self.active_tool == "SELECT" and hasattr(self, 'curr_box'):
            x1, y1 = min(self.sx, e.x), min(self.sy, e.y)
            x2, y2 = max(self.sx, e.x), max(self.sy, e.y)
            if (x2 - x1) > 5 and (y2 - y1) > 5:
                self.rects.append((x1, y1, x2, y2))
            self.canvas.delete(self.curr_box)
            self.update_canvas()

    def on_rightclick(self, e):
        for r in list(self.rects):
            if r[0] <= e.x <= r[2] and r[1] <= e.y <= r[3]:
                self.rects.remove(r)
                self.update_canvas()
                break

    def auto_detect_faces(self):
        if self.cv_img is None: return
        if not self.face_cascade:
            AdvancedErrorDialog(self.root, "ERR-CV2-005")
            return
        try:
            gray = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, self.ai_scale.get(), self.ai_neighbors.get())
            cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
            h, w = self.cv_img.shape[:2]
            ox, oy = (cw - int(w*self.scale_factor*self.zoom_level))//2 + self.pan_x, (ch - int(h*self.scale_factor*self.zoom_level))//2 + self.pan_y

            for (x, y, fw, fh) in faces:
                x1 = int(x * self.scale_factor * self.zoom_level) + ox
                y1 = int(y * self.scale_factor * self.zoom_level) + oy
                x2 = int((x + fw) * self.scale_factor * self.zoom_level) + ox
                y2 = int((y + fh) * self.scale_factor * self.zoom_level) + oy
                self.rects.append((x1, y1, x2, y2))
            self.update_canvas()
        except Exception as e:
            AdvancedErrorDialog(self.root, "ERR-CV2-012", str(e))

    def apply_blur(self):
        if self.cv_img is None or not self.rects: return
        self.push_undo()

        mode = self.effect_mode.get()
        k = self.blur_slider.get()
        if k % 2 == 0: k += 1

        h, w = self.cv_img.shape[:2]
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        ox, oy = (cw - int(w*self.scale_factor*self.zoom_level))//2 + self.pan_x, (ch - int(h*self.scale_factor*self.zoom_level))//2 + self.pan_y

        mask = np.zeros((h, w), dtype=np.uint8)

        for (cx1, cy1, cx2, cy2) in self.rects:
            ix1 = max(0, min(w, int((cx1 - ox) / (self.scale_factor * self.zoom_level))))
            iy1 = max(0, min(h, int((cy1 - oy) / (self.scale_factor * self.zoom_level))))
            ix2 = max(0, min(w, int((cx2 - ox) / (self.scale_factor * self.zoom_level))))
            iy2 = max(0, min(h, int((cy2 - oy) / (self.scale_factor * self.zoom_level))))
            mask[iy1:iy2, ix1:ix2] = 255

        if self.invert_var.get(): mask = cv2.bitwise_not(mask)

        if mode == "Gaussian":
            proc = cv2.GaussianBlur(self.cv_img, (k, k), 0)
        elif mode == "Pixelate":
            s = max(1, k // 4)
            small = cv2.resize(self.cv_img, (max(1, w//s), max(1, h//s)), interpolation=cv2.INTER_LINEAR)
            proc = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        elif mode == "Blackout":
            proc = np.zeros_like(self.cv_img)
        elif mode == "Noise":
            noise = np.random.randint(0, 255, self.cv_img.shape, dtype='uint8')
            proc = cv2.addWeighted(self.cv_img, 0.5, noise, 0.5, 0)
        elif mode == "SolidColor":
            b, g, r = [int(self.color_hex.lstrip('#')[i:i+2], 16) for i in (4, 2, 0)]
            proc = np.full_like(self.cv_img, (b, g, r))
        else:
            proc = cv2.medianBlur(self.cv_img, k)

        inv = cv2.bitwise_not(mask)
        fg = cv2.bitwise_and(proc, proc, mask=mask)
        bg = cv2.bitwise_and(self.cv_img, self.cv_img, mask=inv)
        self.cv_img = cv2.add(fg, bg)

        self.rects.clear()
        self.update_canvas()

    def rotate_image(self, code):
        if self.cv_img is None: return
        self.push_undo()
        self.cv_img = cv2.rotate(self.cv_img, code)
        self.update_canvas()

    def flip_image(self, code):
        if self.cv_img is None: return
        self.push_undo()
        self.cv_img = cv2.flip(self.cv_img, code)
        self.update_canvas()

    def convert_grayscale(self):
        if self.cv_img is None: return
        self.push_undo()
        gray = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2GRAY)
        self.cv_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        self.update_canvas()

    def auto_contrast(self):
        if self.cv_img is None: return
        self.push_undo()
        lab = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        self.cv_img = cv2.cvtColor(cv2.merge((cl,a,b)), cv2.COLOR_LAB2BGR)
        self.update_canvas()

    def burn_watermark(self):
        if self.cv_img is None: return
        self.push_undo()
        txt = self.watermark_text.get()
        if self.burn_timestamp.get(): txt += f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        cv2.putText(self.cv_img, txt, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3, cv2.LINE_AA)
        self.update_canvas()

    def pick_color(self):
        from tkinter import colorchooser
        c = colorchooser.askcolor()[1]
        if c: self.color_hex = c

    def push_undo(self):
        self.history.append(self.cv_img.copy())
        self.redo_stack.clear()

    def undo(self):
        if self.history:
            self.redo_stack.append(self.cv_img.copy())
            self.cv_img = self.history.pop()
            self.update_canvas()

    def redo(self):
        if self.redo_stack:
            self.history.append(self.cv_img.copy())
            self.cv_img = self.redo_stack.pop()
            self.update_canvas()

    def batch_process_dialog(self):
        folder = filedialog.askdirectory(title="Select Input Image Directory")
        if not folder: return
        out_folder = filedialog.askdirectory(title="Select Destination Directory")
        if not out_folder: return

        count = 0
        for p in glob.glob(os.path.join(folder, "*.*")):
            if p.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img = cv2.imread(p)
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 5) if self.face_cascade else []
                    for (x, y, w, h) in faces:
                        sub = img[y:y+h, x:x+w]
                        img[y:y+h, x:x+w] = cv2.GaussianBlur(sub, (51, 51), 0)
                    cv2.imwrite(os.path.join(out_folder, os.path.basename(p)), img)
                    count += 1
        messagebox.showinfo("Batch Complete", f"Successfully processed {count} image(s) to folder:\n{out_folder}")

    def save_image(self):
        if self.cv_img is None: return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")])
        if not path: return
        try:
            cv2.imwrite(path, self.cv_img)
            messagebox.showinfo("Saved", "Output image successfully saved!")
        except Exception as e:
            AdvancedErrorDialog(self.root, "ERR-IO-001", str(e))

    def open_support_center(self):
        w = tk.Toplevel(self.root)
        w.title("In-App Technical Support & Error Code Documentation")
        w.geometry("700x500")
        w.configure(bg="#1e1e1e")

        tk.Label(w, text="🔍 Technical Support & Error Knowledgebase", fg="#4CAF50", bg="#1e1e1e", font=("Segoe UI", 12, "bold")).pack(pady=10)

        tree = ttk.Treeview(w, columns=("Code", "Category", "Title"), show="headings", height=12)
        tree.heading("Code", text="Error Code")
        tree.heading("Category", text="Module")
        tree.heading("Title", text="Issue Description")
        tree.column("Code", width=110)
        tree.column("Category", width=120)
        tree.column("Title", width=420)

        for code, (title, cause, fix) in ERROR_DATABASE.items():
            tree.insert("", tk.END, values=(code, code.split('-')[1], title))
        tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = MegaAnonymizerPro(root)
    root.mainloop()
