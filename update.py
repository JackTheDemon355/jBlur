import sys
import os
import glob
import logging
import tempfile
import traceback
import datetime
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- PATH & RESOURCE CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(SCRIPT_DIR, "assets", "icon.ico")

# --- SETUP LOGGING ---
LOG_FILE = os.path.join(tempfile.gettempdir(), "jblur_app.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.info("Starting jBlur Engine v4.0 Pro...")

# --- DETAILED ERROR DICTIONARY FOR SUPPORT ---
ERROR_DATABASE = {
    # --- GENERAL & SYSTEM ---
    "ERR-GEN-000": ("General System Crash", "Uncaught background program crash.", "1. Restart application.\n2. Open Task Manager and check system RAM/CPU.\n3. Send %TEMP%\\blur_app.log to Tier 2 Support."),
    "ERR-GEN-001": ("System Permissions", "Permission denied when executing app resources.", "1. Right-click app > Run as Administrator.\n2. Verify write permissions to AppData folder.\n3. Temporarily disable antivirus auto-sandbox."),
    "ERR-GEN-002": ("Process Thread Lock", "Background worker thread unresponsive or hung.", "1. Wait 30 seconds for process completion.\n2. Open Task Manager and end jBlur process.\n3. Restart app and lower batch processing count."),
    "ERR-GEN-003": ("Unsupported OS Architecture", "Application executed on incompatible OS architecture.", "1. Verify host OS is 64-bit Windows 10 or 11.\n2. 32-bit (x86) architectures are unsupported.\n3. Re-install appropriate x64 runtime package."),

    # --- IMAGE & CANVAS ENGINE ---
    "ERR-IMG-001": ("File Read Access", "Image cannot be read or opened from disk.", "1. Ensure file is stored locally (C: drive), not on cloud drives.\n2. Uncheck Read-Only in file properties.\n3. Re-save file in MS Paint as standard .png or .jpg."),
    "ERR-IMG-002": ("Memory Limit Exceeded", "Image resolution is too large for canvas memory.", "1. Check image dimensions (must be under 8K / 7680x4320).\n2. Resize image using Paint or an external converter.\n3. Set Windows Display Scaling to 100% or 125%."),
    "ERR-IMG-003": ("Corrupt File Header", "Unsupported or corrupted image file structure.", "1. Verify file extension matches actual format.\n2. Re-download or re-export original source file.\n3. Convert image to baseline JPEG format."),
    "ERR-IMG-004": ("Unsupported Color Space", "Image uses non-RGB color profile (e.g., CMYK, RAW).", "1. Open image in an editor (e.g., Photoshop or Paint).\n2. Convert image color mode to standard sRGB / BGR.\n3. Export as 24-bit PNG or JPEG."),
    "ERR-IMG-005": ("Zero Dimension Image", "Image payload has invalid width or height (0x0px).", "1. Check file size in Windows File Explorer (must be >0 KB).\n2. Source file may be corrupted during download.\n3. Re-capture or re-download source image."),
    "ERR-IMG-006": ("Clipboard Import Failed", "Failed to paste image data from system clipboard.", "1. Ensure clipboard contains valid image pixels (e.g. Snipping Tool).\n2. Text or raw file paths cannot be pasted.\n3. Copy image directly from viewer and retry."),

    # --- OPENCV & AI MASKING ---
    "ERR-CV2-001": ("OpenCV Missing", "Core OpenCV library failed to initialize.", "1. Check installed apps for conflicting Python installs.\n2. Run setup installer as Administrator to repair binaries."),
    "ERR-CV2-005": ("Face AI Data Missing", "Face detection Haar Cascade XML model missing.", "1. Verify haarcascade_frontalface_default.xml exists in app folder.\n2. Re-run setup installer as Administrator."),
    "ERR-CV2-010": ("Module Binding Failure", "OpenCV dynamic link library (DLL) binding error.", "1. Confirm host OS is Windows 10/11 64-bit.\n2. Install Visual C++ Redistributable 2015-2022 (x64).\n3. Restart host computer."),
    "ERR-CV2-012": ("Memory Overflow", "AI face detection scan ran out of system buffer.", "1. Close memory-heavy background applications.\n2. Reset zoom to 1.0x before running detection.\n3. Crop target image area before scanning."),
    "ERR-CV2-015": ("Matrix Allocation Error", "OpenCV failed to allocate image buffer for mask.", "1. Free system RAM by closing background web browsers.\n2. Reduce blur kernel size slider value.\n3. Lower workspace zoom level."),
    "ERR-CV2-020": ("Hardware Acceleration Error", "OpenCL / GPU acceleration pipeline crash.", "1. Open GPU driver settings and update graphics drivers.\n2. Disable OpenCL hardware acceleration in app configuration.\n3. Restart application."),

    # --- BATCH PROCESSING ---
    "ERR-BAT-001": ("Empty Input Directory", "No valid images found in target batch folder.", "1. Ensure target directory contains supported formats (.jpg, .png, .webp).\n2. Confirm folder is uncompressed (not inside a .zip file).\n3. Verify folder read permissions."),
    "ERR-BAT-002": ("Batch Partial Failure", "One or more files failed during batch processing.", "1. Check %TEMP%\\jblur_app.log for failed file paths.\n2. Remove corrupted images from input directory.\n3. Re-run batch job for skipped files."),
    "ERR-BAT-003": ("Output Directory Locked", "Target batch output directory is read-only or invalid.", "1. Choose an accessible output location (e.g., Desktop or Documents).\n2. Ensure output directory is not located on a network share.\n3. Run jBlur as Administrator."),

    # --- WATERMARK & TEXT ---
    "ERR-WMK-001": ("Font Rendering Failure", "Selected font file is corrupt or unreadable.", "1. Select standard system font (Segoe UI or Arial).\n2. Reinstall default Windows font package.\n3. Restart jBlur application."),
    "ERR-WMK-002": ("Text Overflow", "Watermark text string exceeds canvas width.", "1. Reduce watermark font scale slider value.\n2. Shorten watermark text string.\n3. Increase image canvas dimensions."),

    # --- EXIF & METADATA ---
    "ERR-EXF-001": ("EXIF Strip Failure", "Unable to remove metadata from image header.", "1. Save file in PNG format to automatically strip EXIF.\n2. Ensure image is not set to Read-Only.\n3. Uncheck 'Strip EXIF' option if metadata retention is acceptable."),
    "ERR-EXF-002": ("Corrupt Orientation Tag", "EXIF auto-rotation tag could not be evaluated.", "1. Manual rotate image using sidebar controls.\n2. Strip EXIF data before editing.\n3. Re-export file to reset rotation flags."),

    # --- GUI & DISPLAY ---
    "ERR-GUI-001": ("Display Bounds Warning", "Window resolution smaller than required grid.", "1. Increase display resolution to at least 1280x720.\n2. Set Windows scaling to 100%.\n3. Maximize application window upon launch."),
    "ERR-GUI-005": ("GUI Engine Crash", "Tkinter widget rendering failure.", "1. Update host system graphics drivers.\n2. Reset Windows display scaling to recommended 100%.\n3. Launch app in compatibility mode."),
    "ERR-GUI-010": ("Icon Load Failure", "Application failed to attach window icon asset.", "1. Verify assets/icon.ico exists in application root.\n2. Check icon file integrity.\n3. Application will default to generic OS window icon."),
    "ERR-GUI-015": ("Theme Palette Error", "System high-contrast mode interfered with GUI colors.", "1. Turn off Windows High Contrast Mode in Settings.\n2. Restart jBlur to re-initialize default dark theme.\n3. Check graphics driver settings."),

    # --- INPUT / OUTPUT & NETWORKING ---
    "ERR-IO-001": ("Save Failure", "Failed to save output image to target path.", "1. Ensure target drive has >500MB free disk space.\n2. Check Windows Controlled Folder Access settings.\n3. Choose alternative destination folder (e.g., Desktop)."),
    "ERR-IO-002": ("File Lock Conflict", "Output file is locked by another program.", "1. Close image viewers, Photoshop, or browser apps.\n2. Save file under a new unique filename."),
    "ERR-IO-003": ("Path Length Exceeded", "Target file path exceeds Windows MAX_PATH limit (260 chars).", "1. Rename file to a shorter name.\n2. Move destination folder closer to drive root (e.g., C:\\Exports).\n3. Enable Long Paths in Windows Group Policy."),
    "ERR-NET-001": ("Offline Mode Active", "No active internet connection detected.", "1. Verify Wi-Fi or Ethernet connection.\n2. Test connection in standard web browser.\n3. Ignore banner if offline processing is intended."),
    "ERR-NET-002": ("Cloud Sync Failure", "Failed to reach download or update server.", "1. Check firewall outbound HTTP/HTTPS settings.\n2. Disable local VPN or proxy servers.\n3. Test download link directly in a web browser."),

    # --- CONFIGURATION ---
    "ERR-CFG-001": ("Configuration Corrupt", "User settings file is unreadable.", "1. Press Win+R, type %APPDATA%, and open app folder.\n2. Delete settings.json file.\n3. Restart app to generate default configuration."),
    "ERR-CFG-002": ("Schema Mismatch", "Settings file version incompatible with app version.", "1. Delete old configuration file in %APPDATA%\\jBlur.\n2. Restart jBlur to initialize default parameters.")
}

class AdvancedErrorDialog(tk.Toplevel):
    def __init__(self, parent, code, details=""):
        super().__init__(parent)
        self.title(f"jBlur Diagnostic Report [{code}]")
        self.geometry("620x450")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)
        
        # Apply Icon to Error Window
        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception as err:
                logging.warning(f"Could not load icon for dialog: {err}")

        title, cause, fix = ERROR_DATABASE.get(code, ("Unknown System Issue", details or "Unspecified error", "Contact administrator."))
        logging.error(f"Error Window Displayed: {code} - {details}")

        hdr = tk.Frame(self, bg="#d32f2f", height=50)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"⚠️ jBlur System Alert: {code}", fg="white", bg="#d32f2f", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=15, pady=10)

        body = tk.Frame(self, bg="#1e1e1e", padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text=f"Issue: {title}", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        tk.Label(body, text="Technical Cause:", fg="#888888", bg="#1e1e1e", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 2))
        cause_lbl = tk.Label(body, text=cause, fg="#e0e0e0", bg="#2a2a2a", font=("Segoe UI", 9), anchor="w", justify=tk.LEFT, padx=10, pady=8, wraplength=550)
        cause_lbl.pack(fill=tk.X)

        tk.Label(body, text="Resolution Steps:", fg="#888888", bg="#1e1e1e", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 2))
        
        fix_txt = tk.Text(body, bg="#2a2a2a", fg="#4caf50", font=("Consolas", 9), relief=tk.FLAT, height=7, padx=10, pady=8)
        fix_txt.insert(tk.END, fix)
        fix_txt.config(state=tk.DISABLED)
        fix_txt.pack(fill=tk.X)

        btn_bar = tk.Frame(self, bg="#1e1e1e", pady=10)
        btn_bar.pack(fill=tk.X)
        tk.Button(btn_bar, text="📋 Copy Log Path", command=lambda: self.clipboard_clear() or self.clipboard_append(LOG_FILE), bg="#333", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_bar, text="Close & Continue", command=self.destroy, bg="#1976d2", fg="white", font=("Segoe UI", 9, "bold"), width=15).pack(side=tk.RIGHT, padx=20)

def global_crash_handler(exc_type, exc_value, exc_tb):
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.critical(f"Unhandled Exception: {err_str}")

    code = "ERR-GEN-000"
    if "pil" in err_str.lower() or "image" in err_str.lower(): code = "ERR-IMG-002"
    elif "permission" in err_str.lower(): code = "ERR-GEN-001"

    root = tk.Tk()
    root.withdraw()
    dlg = AdvancedErrorDialog(root, code, str(exc_value))
    dlg.mainloop()
    sys.exit(1)

sys.excepthook = global_crash_handler

# Core Libraries
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk, ImageEnhance, ImageOps, ImageFilter
except Exception as e:
    logging.critical(f"Failed loading core packages: {e}")
    raise ImportError(f"Core module load failure: {e}")


class jBlurApp:
    def __init__(self, root):
        self.root = root
        self.root.title("jBlur - Advanced Image Redaction & Utility Suite v4.0")
        self.root.geometry("1350x850")
        self.root.minsize(1080, 720)

        # Set Window Icon from assets/icon.ico
        self._set_app_icon()

        # Core State
        self.cv_img = None
        self.original_raw = None
        self.history = []
        self.redo_stack = []
        self.rects = []
        self.selected_rect_idx = None
        
        # Viewport Mechanics
        self.scale_factor = 1.0
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Overlays & Tools
        self.show_grid = False
        self.show_thirds = False
        self.show_center_cross = False
        self.active_tool = "SELECT"  # SELECT, PAN, OVAL
        self.shape_mode = "RECT"    # RECT, OVAL

        # Effect Parameters
        self.effect_mode = tk.StringVar(value="Gaussian")
        self.blur_slider = tk.IntVar(value=45)
        self.invert_var = tk.BooleanVar(value=False)
        self.color_hex = "#000000"
        
        # Watermark / Text Parameters
        self.watermark_text = tk.StringVar(value="CONFIDENTIAL / REDACTED")
        self.watermark_size = tk.IntVar(value=2)
        self.burn_timestamp = tk.BooleanVar(value=False)
        self.strip_exif_var = tk.BooleanVar(value=True)

        self._build_interface()
        self._bind_hotkeys()

    def _set_app_icon(self):
        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
                logging.info(f"Loaded icon from {ICON_PATH}")
            except Exception as e:
                logging.warning(f"Failed to apply iconbitmap from {ICON_PATH}: {e}")
        else:
            logging.info(f"Icon file not found at {ICON_PATH}. Running with default window icon.")

    def _build_interface(self):
        self.main_box = tk.Frame(self.root, bg="#181818")
        self.main_box.pack(fill=tk.BOTH, expand=True)

        # Main Ribbon Toolbar
        self.ribbon = tk.Frame(self.main_box, bg="#252526", height=42)
        self.ribbon.pack(fill=tk.X)

        # File Actions Group
        tk.Button(self.ribbon, text="📁 Open", command=self.load_image, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Button(self.ribbon, text="📂 Batch", command=self.batch_process_dialog, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2, pady=6)
        tk.Button(self.ribbon, text="💾 Save Output", command=self.save_image, bg="#1976D2", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=6, pady=6)
        
        tk.Label(self.ribbon, text="|", fg="#555", bg="#252526").pack(side=tk.LEFT, padx=4)

        # Tool Mode Controls
        tk.Button(self.ribbon, text="📦 Rectangle", command=lambda: self.set_tool("SELECT", "RECT"), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="⭕ Oval / Circle", command=lambda: self.set_tool("SELECT", "OVAL"), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="🖐️ Pan Tool", command=lambda: self.set_tool("PAN"), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        tk.Label(self.ribbon, text="|", fg="#555", bg="#252526").pack(side=tk.LEFT, padx=4)

        # Grid Overlays
        tk.Button(self.ribbon, text="🌐 Grid", command=self.toggle_grid, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="📐 Thirds", command=self.toggle_thirds, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="🎯 Center", command=self.toggle_center_cross, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        tk.Label(self.ribbon, text="|", fg="#555", bg="#252526").pack(side=tk.LEFT, padx=4)

        # Zoom Quick Controls
        tk.Button(self.ribbon, text="🔍 In", command=lambda: self.zoom(0.2), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="🔍 Out", command=lambda: self.zoom(-0.2), bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.ribbon, text="🔍 100%", command=self.reset_zoom, bg="#333", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        tk.Button(self.ribbon, text="❓ Help / Logs", command=self.open_support_center, bg="#4A148C", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(side=tk.RIGHT, padx=10)

        # Work Area Frame
        self.body_frame = tk.Frame(self.main_box, bg="#181818")
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # Multi-Tab Sidebar Panel
        sidebar = tk.Frame(self.body_frame, bg="#212121", width=340)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        nb = ttk.Notebook(sidebar)
        nb.pack(fill=tk.BOTH, expand=True)

        # --- TAB 1: BLUR & REDACTION EFFECTS ---
        t1 = tk.Frame(nb, bg="#212121")
        nb.add(t1, text="Redaction")

        self._lbl(t1, "EFFECT TYPE")
        effects = [
            ("Gaussian Blur", "Gaussian"),
            ("Pixelate / Mosaic", "Pixelate"),
            ("Blackout Box", "Blackout"),
            ("Soft Radial Blur", "Radial"),
            ("Color Solid Mask", "SolidColor"),
            ("Noise Obfuscation", "Noise"),
            ("Invert Colors Mask", "InvertMask")
        ]
        for txt, val in effects:
            tk.Radiobutton(t1, text=txt, value=val, variable=self.effect_mode, bg="#212121", fg="white", selectcolor="#181818").pack(anchor=tk.W, padx=15)

        tk.Checkbutton(t1, text="Invert Selection (Blur Exterior)", variable=self.invert_var, bg="#212121", fg="#FFB74D", selectcolor="#181818").pack(anchor=tk.W, padx=15, pady=6)

        self._lbl(t1, "EFFECT STRENGTH")
        tk.Scale(t1, from_=5, to=200, variable=self.blur_slider, orient=tk.HORIZONTAL, bg="#212121", fg="white", highlightthickness=0).pack(fill=tk.X, padx=15)

        self._lbl(t1, "SOLID MASK COLOR")
        tk.Button(t1, text="🎨 Pick Color", command=self.pick_color, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)

        tk.Button(t1, text="✨ Apply Blur to Regions", command=self.apply_blur, bg="#388E3C", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, padx=15, pady=12)
        tk.Button(t1, text="🧹 Clear All Selection Boxes", command=self.clear_rects, bg="#D32F2F", fg="white", font=("Segoe UI", 9)).pack(fill=tk.X, padx=15)

        # --- TAB 2: IMAGE ENHANCEMENT & TONE ---
        t2 = tk.Frame(nb, bg="#212121")
        nb.add(t2, text="Adjustments")

        self._lbl(t2, "IMAGE TRANSFORMATIONS")
        tk.Button(t2, text="🔄 Rotate 90° Clockwise", command=lambda: self.rotate_image(cv2.ROTATE_90_CLOCKWISE), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="🔄 Rotate 90° Counter-CW", command=lambda: self.rotate_image(cv2.ROTATE_90_COUNTERCLOCKWISE), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="↔️ Flip Horizontal", command=lambda: self.flip_image(1), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="↕️ Flip Vertical", command=lambda: self.flip_image(0), bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)

        self._lbl(t2, "COLOR & LIGHT CORRECTIONS")
        tk.Button(t2, text="🌑 Grayscale", command=self.convert_grayscale, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="📜 Sepia Tone", command=self.apply_sepia, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="⚡ Auto-Contrast Boost", command=self.auto_contrast, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="✏️ Pencil Sketch Filter", command=self.sketch_filter, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)
        tk.Button(t2, text="🔳 Edge Detection Map", command=self.edge_filter, bg="#333", fg="white").pack(fill=tk.X, padx=15, pady=2)

        # --- TAB 3: WATERMARK & METADATA ---
        t3 = tk.Frame(nb, bg="#212121")
        nb.add(t3, text="Watermark")

        self._lbl(t3, "STAMP TEXT")
        tk.Entry(t3, textvariable=self.watermark_text, bg="#111", fg="white", insertbackground="white").pack(fill=tk.X, padx=15, pady=2)

        self._lbl(t3, "FONT SIZE")
        tk.Scale(t3, from_=1, to=10, variable=self.watermark_size, orient=tk.HORIZONTAL, bg="#212121", fg="white", highlightthickness=0).pack(fill=tk.X, padx=15)

        tk.Checkbutton(t3, text="Include Timestamp", variable=self.burn_timestamp, bg="#212121", fg="white", selectcolor="#181818").pack(anchor=tk.W, padx=15, pady=4)
        tk.Checkbutton(t3, text="Strip EXIF Metadata on Save", variable=self.strip_exif_var, bg="#212121", fg="#4CAF50", selectcolor="#181818").pack(anchor=tk.W, padx=15, pady=4)

        tk.Button(t3, text="🏷️ Burn Stamp to Image", command=self.burn_watermark, bg="#E65100", fg="white", font=("Segoe UI", 9, "bold")).pack(fill=tk.X, padx=15, pady=10)

        # Footer Undo / Redo / Reset
        foot = tk.Frame(sidebar, bg="#181818", pady=10)
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(foot, text="↩️ Undo", command=self.undo, bg="#333", fg="white", width=9).pack(side=tk.LEFT, padx=5)
        tk.Button(foot, text="↪️ Redo", command=self.redo, bg="#333", fg="white", width=9).pack(side=tk.LEFT, padx=5)
        tk.Button(foot, text="🔄 Reset All", command=self.reset_original, bg="#D32F2F", fg="white", width=9).pack(side=tk.RIGHT, padx=5)

        # Interactive Canvas
        self.canvas = tk.Canvas(self.body_frame, bg="#111111", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mouse Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_mousedown)
        self.canvas.bind("<B1-Motion>", self.on_mousemove)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouseup)
        self.canvas.bind("<Button-3>", self.on_rightclick)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, fg="#666", bg="#212121", font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, padx=15, pady=(10, 2))

    def _bind_hotkeys(self):
        # Keyboard Shortcuts (Safe bindings preventing TclError crashes)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Delete>", lambda e: self.delete_selected_rect())
        
        # Fixed '+' key binding using standard Tcl '<plus>' syntax
        try:
            self.root.bind("<plus>", lambda e: self.zoom(0.2))
            self.root.bind("<equal>", lambda e: self.zoom(0.2))
            self.root.bind("<minus>", lambda e: self.zoom(-0.2))
        except Exception as err:
            logging.warning(f"Skipped optional key binding: {err}")

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff")])
        if not path: return
        try:
            img = cv2.imread(path)
            if img is None: raise ValueError("Image read returned empty buffer.")
            self.cv_img = img
            self.original_raw = img.copy()
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

        # Draw Active Selection Shapes
        for i, r in enumerate(self.rects):
            color = "#00E676" if i == self.selected_rect_idx else "#FF5722"
            if r.get("shape") == "OVAL":
                self.canvas.create_oval(r["coords"][0], r["coords"][1], r["coords"][2], r["coords"][3], outline=color, width=2)
            else:
                self.canvas.create_rectangle(r["coords"][0], r["coords"][1], r["coords"][2], r["coords"][3], outline=color, width=2)

        # Render Canvas Overlays
        if self.show_grid:
            for x in range(0, cw, 40): self.canvas.create_line(x, 0, x, ch, fill="#222222")
            for y in range(0, ch, 40): self.canvas.create_line(0, y, cw, y, fill="#222222")
        if self.show_thirds:
            self.canvas.create_line(cw/3, 0, cw/3, ch, fill="#00E676", dash=(2, 4))
            self.canvas.create_line(2*cw/3, 0, 2*cw/3, ch, fill="#00E676", dash=(2, 4))
            self.canvas.create_line(0, ch/3, cw, ch/3, fill="#00E676", dash=(2, 4))
            self.canvas.create_line(0, 2*ch/3, cw, 2*ch/3, fill="#00E676", dash=(2, 4))
        if self.show_center_cross:
            self.canvas.create_line(cw/2, 0, cw/2, ch, fill="#FF4081", width=1)
            self.canvas.create_line(0, ch/2, cw, ch/2, fill="#FF4081", width=1)

    def set_tool(self, tool, shape="RECT"):
        self.active_tool = tool
        self.shape_mode = shape

    def toggle_grid(self): self.show_grid = not self.show_grid; self.update_canvas()
    def toggle_thirds(self): self.show_thirds = not self.show_thirds; self.update_canvas()
    def toggle_center_cross(self): self.show_center_cross = not self.show_center_cross; self.update_canvas()
    
    def zoom(self, delta):
        self.zoom_level = max(0.4, min(6.0, self.zoom_level + delta))
        self.update_canvas()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.pan_x, self.pan_y = 0, 0
        self.update_canvas()

    def on_mousewheel(self, e):
        if e.delta > 0: self.zoom(0.1)
        else: self.zoom(-0.1)

    def on_mousedown(self, e):
        self.sx, self.sy = e.x, e.y
        if self.active_tool == "SELECT":
            if self.shape_mode == "OVAL":
                self.curr_box = self.canvas.create_oval(e.x, e.y, e.x, e.y, outline="#00E676", width=2, dash=(4,4))
            else:
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
                self.rects.append({"coords": (x1, y1, x2, y2), "shape": self.shape_mode})
            self.canvas.delete(self.curr_box)
            self.update_canvas()

    def on_rightclick(self, e):
        for i, r in enumerate(list(self.rects)):
            c = r["coords"]
            if c[0] <= e.x <= c[2] and c[1] <= e.y <= c[3]:
                self.rects.pop(i)
                self.update_canvas()
                break

    def delete_selected_rect(self):
        if self.selected_rect_idx is not None and self.selected_rect_idx < len(self.rects):
            self.rects.pop(self.selected_rect_idx)
            self.selected_rect_idx = None
            self.update_canvas()

    def clear_rects(self):
        self.rects.clear()
        self.update_canvas()

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

        for item in self.rects:
            cx1, cy1, cx2, cy2 = item["coords"]
            ix1 = max(0, min(w, int((cx1 - ox) / (self.scale_factor * self.zoom_level))))
            iy1 = max(0, min(h, int((cy1 - oy) / (self.scale_factor * self.zoom_level))))
            ix2 = max(0, min(w, int((cx2 - ox) / (self.scale_factor * self.zoom_level))))
            iy2 = max(0, min(h, int((cy2 - oy) / (self.scale_factor * self.zoom_level))))
            
            if item.get("shape") == "OVAL":
                center = ((ix1 + ix2) // 2, (iy1 + iy2) // 2)
                axes = (abs(ix2 - ix1) // 2, abs(iy2 - iy1) // 2)
                if axes[0] > 0 and axes[1] > 0:
                    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
            else:
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
        elif mode == "InvertMask":
            proc = cv2.bitwise_not(self.cv_img)
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

    def apply_sepia(self):
        if self.cv_img is None: return
        self.push_undo()
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        self.cv_img = cv2.transform(self.cv_img, kernel)
        self.cv_img = np.clip(self.cv_img, 0, 255).astype(np.uint8)
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

    def sketch_filter(self):
        if self.cv_img is None: return
        self.push_undo()
        gray, sketch = cv2.pencilSketch(self.cv_img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
        self.cv_img = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        self.update_canvas()

    def edge_filter(self):
        if self.cv_img is None: return
        self.push_undo()
        gray = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        self.cv_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        self.update_canvas()

    def burn_watermark(self):
        if self.cv_img is None: return
        self.push_undo()
        txt = self.watermark_text.get()
        if self.burn_timestamp.get():
            txt += f" | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        sz = self.watermark_size.get()
        cv2.putText(self.cv_img, txt, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, sz * 0.8, (0, 0, 255), sz * 2, cv2.LINE_AA)
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

    def reset_original(self):
        if self.original_raw is not None:
            self.push_undo()
            self.cv_img = self.original_raw.copy()
            self.rects.clear()
            self.update_canvas()

    def batch_process_dialog(self):
        folder = filedialog.askdirectory(title="Select Input Image Directory")
        if not folder: return
        out_folder = filedialog.askdirectory(title="Select Destination Directory")
        if not out_folder: return

        count = 0
        for p in glob.glob(os.path.join(folder, "*.*")):
            if p.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                img = cv2.imread(p)
                if img is not None:
                    img = cv2.GaussianBlur(img, (51, 51), 0)
                    cv2.imwrite(os.path.join(out_folder, os.path.basename(p)), img)
                    count += 1
        messagebox.showinfo("Batch Processing", f"Batch complete! Processed {count} images into:\n{out_folder}")

    def save_image(self):
        if self.cv_img is None: return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("WebP Image", "*.webp")])
        if not path: return
        try:
            if self.strip_exif_var.get():
                _, buf = cv2.imencode(os.path.splitext(path)[1] or ".png", self.cv_img)
                with open(path, "wb") as f:
                    f.write(buf)
            else:
                cv2.imwrite(path, self.cv_img)
            messagebox.showinfo("jBlur Export", "File saved successfully!")
        except Exception as e:
            AdvancedErrorDialog(self.root, "ERR-IO-001", str(e))

    def open_support_center(self):
        w = tk.Toplevel(self.root)
        w.title("jBlur Diagnostic & Log System")
        w.geometry("700x500")
        w.configure(bg="#1e1e1e")

        if os.path.exists(ICON_PATH):
            try:
                w.iconbitmap(ICON_PATH)
            except Exception:
                pass

        tk.Label(w, text="🔍 jBlur Internal Diagnostics", fg="#4CAF50", bg="#1e1e1e", font=("Segoe UI", 12, "bold")).pack(pady=10)

        tree = ttk.Treeview(w, columns=("Code", "Category", "Title"), show="headings", height=12)
        tree.heading("Code", text="Error Code")
        tree.heading("Category", text="Module")
        tree.heading("Title", text="Description")
        tree.column("Code", width=110)
        tree.column("Category", width=120)
        tree.column("Title", width=420)

        for code, (title, cause, fix) in ERROR_DATABASE.items():
            tree.insert("", tk.END, values=(code, code.split('-')[1], title))
        tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = jBlurApp(root)
    root.mainloop()
