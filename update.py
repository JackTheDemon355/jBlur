import os
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk

# Optional metadata preservation library
try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False


class ImageBlurTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("jBlur - Image Blur & Anonymization Tool")
        self.geometry("1100x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- Internal State ---
        self.current_image_path = None
        self.cv_image_original = None      # Clean BGR OpenCV Image
        self.cv_image_processed = None     # Current processed state
        self.display_image = None          # Scaled PIL Image for canvas
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
        """Applies chosen blur effect directly onto OpenCV image matrix."""
        h, w = img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return img

        roi = img[y1:y2, x1:x2]

        # Ensure intensity is odd integer for OpenCV filters
        ksize = int(intensity)
        if ksize % 2 == 0:
            ksize += 1

        if blur_type == "Gaussian":
            blurred_roi = cv2.GaussianBlur(roi, (ksize, ksize), 0)
        elif blur_type == "Box Blur":
            blurred_roi = cv2.blur(roi, (ksize, ksize))
        elif blur_type == "Pixelate":
            # Scale down and upscale back to get pixelation effect
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
        
        # Multiscale Haar Cascade Detection
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

        # Convert BGR OpenCV image to RGB PIL image
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

        # Calculate bounding coordinates relative to original unscaled image
        x1_canvas = min(self.start_x, end_x) - self.img_offset_x
        y1_canvas = min(self.start_y, end_y) - self.img_offset_y
        x2_canvas = max(self.start_x, end_x) - self.img_offset_x
        y2_canvas = max(self.start_y, end_y) - self.img_offset_y

        # Convert canvas scale back to native image resolution
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

        # Convert back to RGB for PIL export
        rgb_img = cv2.cvtColor(self.cv_image_processed, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        # Preserve EXIF metadata if original was JPEG/TIFF and piexif is installed
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
