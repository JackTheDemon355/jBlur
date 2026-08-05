import os
import sys
import time
import random
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk
import requests

# Optional metadata preservation library
try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False


APP_VERSION = "1.0.0"
GITHUB_REPO = "JackTheDemon355/jBlur"


# ============================================================================
# AUTO-UPDATE PROGRESS DIALOG & EMERGENCY BYPASS
# ============================================================================
class UpdateDialog(ctk.CTkToplevel):
    """
    Modal Update Window featuring a randomized loading bar (11-90s)
    and an Emergency Skip Hotkey (CTRL + ALT + SPACE + Z).
    """
    def __init__(self, parent, download_url, version_str):
        super().__init__(parent)
        self.parent = parent
        self.download_url = download_url
        self.version_str = version_str
        
        self.title("jBlur - System Auto-Updater")
        self.geometry("480x260")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()  # Make window modal

        # Randomized update duration between 11 and 90 seconds
        self.total_duration = random.randint(11, 90)
        self.elapsed = 0
        self.is_skipped = False
        self.is_completed = False

        self._build_ui()
        self._bind_emergency_hotkey()

        # Start update worker thread
        self.update_thread = threading.Thread(target=self._run_update_process, daemon=True)
        self.update_thread.start()

    def _build_ui(self):
        self.lbl_title = ctk.CTkLabel(
            self, 
            text=f"Updating jBlur to v{self.version_str}...", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_title.pack(pady=(20, 5))

        self.lbl_status = ctk.CTkLabel(
            self, 
            text="Preparing update packages...", 
            font=ctk.CTkFont(size=12), 
            text_color="gray"
        )
        self.lbl_status.pack(pady=(0, 15))

        self.progress_bar = ctk.CTkProgressBar(self, width=400, height=18)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(pady=10)

        self.lbl_timer = ctk.CTkLabel(
            self, 
            text=f"Estimated time remaining: {self.total_duration}s", 
            font=ctk.CTkFont(size=11)
        )
        self.lbl_timer.pack(pady=5)

        self.lbl_hint = ctk.CTkLabel(
            self, 
            text="Emergency Bypass: [Ctrl + Alt + Space + Z]", 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#e74c3c"
        )
        self.lbl_hint.pack(pady=(15, 0))

    def _bind_emergency_hotkey(self):
        """Binds Ctrl+Alt+Space+Z emergency bypass combination."""
        self.bind_all("<Control-Alt-space-z>", self._trigger_emergency_bypass)
        self.bind_all("<Control-Alt-space-Z>", self._trigger_emergency_bypass)

    def _trigger_emergency_bypass(self, event=None):
        """Instantly overrides timer and jumps to completion."""
        if not self.is_completed and not self.is_skipped:
            self.is_skipped = True
            self.lbl_status.configure(text="[EMERGENCY BYPASS TRIGGERED] Finalizing setup...", text_color="#f39c12")
            self.progress_bar.set(1.0)
            self.lbl_timer.configure(text="Time remaining: 0s (Skipped)")

    def _run_update_process(self):
        """Simulates download/installation progress while checking for emergency skip."""
        interval = 0.2
        steps = int(self.total_duration / interval)

        # Step 1: Simulate network download progress bar
        for i in range(1, steps + 1):
            if self.is_skipped:
                break
            time.sleep(interval)
            self.elapsed += interval
            progress = min(1.0, self.elapsed / self.total_duration)
            remaining = max(0, int(self.total_duration - self.elapsed))

            # Update UI from worker thread safely
            self.after(0, self._update_ui_state, progress, remaining)

        # Step 2: Download installer binary to local TEMP folder
        self.after(0, lambda: self.lbl_status.configure(text="Downloading setup binary...", text_color="#27ae60"))
        installer_path = Path(os.environ.get("TEMP", "C:\\Temp")) / f"jBlur_Setup_v{self.version_str}.exe"
        
        try:
            if self.download_url and self.download_url.startswith("http"):
                res = requests.get(self.download_url, timeout=30)
                if res.status_code == 200:
                    with open(installer_path, "wb") as f:
                        f.write(res.content)
        except Exception:
            pass

        # Step 3: Trigger silent installer overwrite and exit main app
        self.is_completed = True
        self.after(0, self._launch_installer_and_exit, str(installer_path))

    def _update_ui_state(self, progress, remaining):
        if not self.is_skipped:
            self.progress_bar.set(progress)
            self.lbl_timer.configure(text=f"Estimated time remaining: {remaining}s")
            if progress > 0.6:
                self.lbl_status.configure(text="Applying binary patches...")
            elif progress > 0.3:
                self.lbl_status.configure(text="Extracting payload...")

    def _launch_installer_and_exit(self, installer_path):
        if os.path.exists(installer_path):
            # Launch setup executable silently in separate process
            subprocess.Popen([installer_path, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])
        else:
            messagebox.showinfo("Auto-Update Complete", f"jBlur v{self.version_str} update sequence finished.")

        self.destroy()
        self.parent.destroy()
        sys.exit(0)


# ============================================================================
# MAIN APPLICATION GUI
# ============================================================================
class ImageBlurTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title(f"jBlur v{APP_VERSION} - Image Blur & Anonymization Tool")
        self.geometry("1100x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- Internal State ---
        self.current_image_path = None
        self.cv_image_original = None      # Clean BGR OpenCV Image
        self.cv_image_processed = None     # Current processed state
        self.tk_image = None
        
        # Scaling & Crop Box Data
        self.scale_factor = 1.0
        self.img_offset_x = 0
        self.img_offset_y = 0
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.manual_blur_boxes = []         # List of (x1, y1, x2, y2) in original pixels

        # --- OpenCV Haar Cascade Initialization ---
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.exists(cascade_path):
            cascade_path = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Build UI Layout
        self._build_ui()

        # Check for Updates silently in background thread
        threading.Thread(target=self._check_for_updates, daemon=True).start()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===================================================================
        # LEFT CONTROL PANEL
        # ===================================================================
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # App Title
        title_label = ctk.CTkLabel(self.sidebar, text="jBlur Tool", font=ctk.CTkFont(size=22, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # File Operations
        self.btn_load = ctk.CTkButton(self.sidebar, text="Open Image", command=self.load_image)
        self.btn_load.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Blur Type Switch
        self.blur_type_var = ctk.StringVar(value="Gaussian")
        blur_label = ctk.CTkLabel(self.sidebar, text="Blur Style:", font=ctk.CTkFont(size=13, weight="bold"))
        blur_label.grid(row=2, column=0, padx=20, pady=(15, 0), sticky="w")
        
        self.blur_type_selector = ctk.CTkOptionMenu(
            self.sidebar, 
            values=["Gaussian", "Pixelate", "Box Blur"],
            variable=self.blur_type_var
        )
        self.blur_type_selector.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        # Blur Intensity Slider
        intensity_label = ctk.CTkLabel(self.sidebar, text="Blur Intensity:", font=ctk.CTkFont(size=13, weight="bold"))
        intensity_label.grid(row=4, column=0, padx=20, pady=(15, 0), sticky="w")
        
        self.intensity_slider = ctk.CTkSlider(self.sidebar, from_=3, to=99, number_of_steps=48, command=self._on_slider_change)
        self.intensity_slider.set(31)
        self.intensity_slider.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # Automatic Detection
        self.btn_auto_faces = ctk.CTkButton(
            self.sidebar, 
            text="Auto-Detect Faces", 
            fg_color="#1f538d", 
            hover_color="#14375e",
            command=self.detect_and_blur_faces
        )
        self.btn_auto_faces.grid(row=6, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Reset & Save Controls
        self.btn_reset = ctk.CTkButton(self.sidebar, text="Reset Image", fg_color="#a83232", hover_color="#7a2323", command=self.reset_image)
        self.btn_reset.grid(row=7, column=0, padx=20, pady=10, sticky="ew")

        self.btn_save = ctk.CTkButton(self.sidebar, text="Save Image", fg_color="#27ae60", hover_color="#1e8449", command=self.save_image)
        self.btn_save.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="ew")

        # Status Bar
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Status: Ready", font=ctk.CTkFont(size=11), text_color="gray")
        self.lbl_status.grid(row=11, column=0, padx=20, pady=10, sticky="w")

        # ===================================================================
        # RIGHT CANVAS WORKSPACE
        # ===================================================================
        self.canvas_frame = ctk.CTkFrame(self, corner_radius=10)
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Mouse Binds for Manual Blur Selection Box
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)
        self.bind("<Configure>", self._on_window_resize)

    # =======================================================================
    # AUTO-UPDATE CHECKER LOGIC
    # =======================================================================
    def _check_for_updates(self):
        """Polls GitHub API for latest release tags in background."""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                latest_version = data.get("tag_name", "").lstrip("v")
                
                # Compare semantic versions
                if latest_version and latest_version != APP_VERSION:
                    assets = data.get("assets", [])
                    download_url = assets[0]["browser_download_url"] if assets else ""
                    self.after(0, self._prompt_update, latest_version, download_url)
        except Exception:
            pass  # Silent failure if offline or GitHub API rate-limited

    def _prompt_update(self, new_version, download_url):
        ans = messagebox.askyesno(
            "Update Available", 
            f"A new version of jBlur (v{new_version}) is available!\n\nWould you like to install it now?"
        )
        if ans:
            UpdateDialog(self, download_url, new_version)

    # =======================================================================
    # IMAGE PROCESSING LOGIC
    # =======================================================================
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if not file_path:
            return

        self.current_image_path = file_path
        self.cv_image_original = cv2.imread(file_path)
        if self.cv_image_original is None:
            messagebox.showerror("Error", "Failed to load selected image file.")
            return

        self.cv_image_processed = self.cv_image_original.copy()
        self.manual_blur_boxes.clear()
        self.update_canvas()
        self.set_status(f"Loaded: {Path(file_path).name}")

    def apply_blur_region(self, img, x1, y1, x2, y2, intensity, blur_type):
        h, w = img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return img

        roi = img[y1:y2, x1:x2]
        ksize = int(intensity)
        if ksize % 2 == 0:
            ksize += 1

        if blur_type == "Gaussian":
            blurred_roi = cv2.GaussianBlur(roi, (ksize, ksize), 0)
        elif blur_type == "Box Blur":
            blurred_roi = cv2.blur(roi, (ksize, ksize))
        elif blur_type == "Pixelate":
            pixel_size = max(4, ksize // 3)
            rh, rw = roi.shape[:2]
            temp = cv2.resize(roi, (max(1, rw // pixel_size), max(1, rh // pixel_size)), interpolation=cv2.INTER_LINEAR)
            blurred_roi = cv2.resize(temp, (rw, rh), interpolation=cv2.INTER_NEAREST)
        else:
            blurred_roi = roi

        img[y1:y2, x1:x2] = blurred_roi
        return img

    def detect_and_blur_faces(self):
        if self.cv_image_original is None:
            messagebox.showwarning("Warning", "Please open an image first.")
            return

        self.set_status("Detecting faces...")
        gray = cv2.cvtColor(self.cv_image_processed, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) == 0:
            self.set_status("No faces detected.")
            messagebox.showinfo("Result", "No faces were automatically detected.")
            return

        intensity = int(self.intensity_slider.get())
        blur_style = self.blur_type_var.get()

        for (x, y, w, h) in faces:
            self.manual_blur_boxes.append((x, y, x + w, y + h))
            self.cv_image_processed = self.apply_blur_region(
                self.cv_image_processed, x, y, x + w, y + h, intensity, blur_style
            )

        self.update_canvas()
        self.set_status(f"Blurred {len(faces)} face(s).")

    def reapply_all_blurs(self):
        if self.cv_image_original is None:
            return

        self.cv_image_processed = self.cv_image_original.copy()
        intensity = int(self.intensity_slider.get())
        blur_style = self.blur_type_var.get()

        for (x1, y1, x2, y2) in self.manual_blur_boxes:
            self.cv_image_processed = self.apply_blur_region(
                self.cv_image_processed, x1, y1, x2, y2, intensity, blur_style
            )

        self.update_canvas()

    def reset_image(self):
        if self.cv_image_original is not None:
            self.cv_image_processed = self.cv_image_original.copy()
            self.manual_blur_boxes.clear()
            self.update_canvas()
            self.set_status("Image reset to original.")

    # =======================================================================
    # UI CANVAS & SELECTION HANDLERS
    # =======================================================================
    def update_canvas(self):
        if self.cv_image_processed is None:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 10 or canvas_height < 10:
            return

        rgb_img = cv2.cvtColor(self.cv_image_processed, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        img_w, img_h = pil_img.size
        self.scale_factor = min(canvas_width / img_w, canvas_height / img_h)

        new_w = int(img_w * self.scale_factor)
        new_h = int(img_h * self.scale_factor)

        resized_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")
        self.img_offset_x = (canvas_width - new_w) // 2
        self.img_offset_y = (canvas_height - new_h) // 2

        self.canvas.create_image(self.img_offset_x, self.img_offset_y, anchor=tk.NW, image=self.tk_image)

    def _on_drag_start(self, event):
        if self.cv_image_processed is None:
            return
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="cyan", width=2
        )

    def _on_drag_motion(self, event):
        if self.rect_id and self.start_x is not None:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def _on_drag_release(self, event):
        if not self.rect_id or self.start_x is None:
            return

        end_x, end_y = event.x, event.y
        self.canvas.delete(self.rect_id)
        self.rect_id = None

        x1_canvas = min(self.start_x, end_x) - self.img_offset_x
        y1_canvas = min(self.start_y, end_y) - self.img_offset_y
        x2_canvas = max(self.start_x, end_x) - self.img_offset_x
        y2_canvas = max(self.start_y, end_y) - self.img_offset_y

        x1 = int(x1_canvas / self.scale_factor)
        y1 = int(y1_canvas / self.scale_factor)
        x2 = int(x2_canvas / self.scale_factor)
        y2 = int(y2_canvas / self.scale_factor)

        if (x2 - x1) > 5 and (y2 - y1) > 5:
            intensity = int(self.intensity_slider.get())
            blur_style = self.blur_type_var.get()
            self.manual_blur_boxes.append((x1, y1, x2, y2))
            
            self.cv_image_processed = self.apply_blur_region(
                self.cv_image_processed, x1, y1, x2, y2, intensity, blur_style
            )
            self.update_canvas()
            self.set_status("Applied manual blur area.")

    def _on_slider_change(self, value):
        if self.manual_blur_boxes:
            self.reapply_all_blurs()

    def _on_window_resize(self, event):
        self.update_canvas()

    # =======================================================================
    # SAVE & METADATA HANDLING
    # =======================================================================
    def save_image(self):
        if self.cv_image_processed is None:
            messagebox.showwarning("Warning", "No image available to save.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")]
        )
        if not save_path:
            return

        rgb_img = cv2.cvtColor(self.cv_image_processed, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        exif_bytes = None
        if PIEXIF_AVAILABLE and self.current_image_path:
            try:
                exif_bytes = piexif.dump(piexif.load(self.current_image_path))
            except Exception:
                exif_bytes = None

        try:
            if exif_bytes and save_path.lower().endswith(('.jpg', '.jpeg')):
                pil_img.save(save_path, exif=exif_bytes)
            else:
                pil_img.save(save_path)
            
            self.set_status(f"Saved: {Path(save_path).name}")
            messagebox.showinfo("Success", "Image saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")

    def set_status(self, message):
        self.lbl_status.configure(text=f"Status: {message}")


if __name__ == "__main__":
    app = ImageBlurTool()
    app.mainloop()
