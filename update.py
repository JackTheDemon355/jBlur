import io
import os
import sys
import urllib.request
import webbrowser
import json
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
CURRENT_VERSION = "1.4.3"
UPDATE_URL = "https://raw.githubusercontent.com/JackTheDemon355/jBlur/refs/heads/main/update.py"

# Rotating Ad Banners list (Includes your custom uploaded images)
AD_BANNERS = [
    {
        "name": "Aternos",
        "image_url": "https://uploads.onecompiler.io/445cmzn8g/1785656258981/aternos.png",
        "link_url": "https://aternos.org"
    },
    {
        "name": "Woolworths",
        "image_url": "https://uploads.onecompiler.io/445cmzn8g/1785656418727/Screenshot%202026-08-02%20153952.png",
        "link_url": "https://www.woolworths.com.au"
    },
    {
        "name": "GitHub",
        "image_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Logo.png",
        "link_url": "https://github.com"
    },
    {
        "name": "Python Foundation",
        "image_url": "https://www.python.org/static/img/python-logo.png",
        "link_url": "https://www.python.org"
    }
]


class JBlurApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("jBlur - Advanced Image & Text Blurrer")
        self.geometry("950x750")

        # Layout Setup: Banner Top, Tabs Center, Ad Bottom
        self.update_banner_frame = tk.Frame(self, bg="#2196F3")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Tabs
        self.tab_image = ttk.Frame(self.notebook)
        self.tab_text = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_image, text="Image Blurrer")
        self.notebook.add(self.tab_text, text="Text Blurrer")

        # Bottom Ad Banner setup
        self.current_ad_index = 0
        self.create_ad_banner()

        # Build Tab UIs
        self.build_image_blurrer_tab()
        self.build_text_blurrer_tab()

        # Check for auto-updates at startup & start ad rotator
        self.after(1000, self.check_for_updates)
        self.after(500, self.rotate_ad_banner)

    # -----------------------------------------------------------------------
    # 1. AUTO-UPDATE SYSTEM & DYNAMIC BANNER
    # -----------------------------------------------------------------------
    def check_for_updates(self):
        """Checks remote update.py script to see if a newer version exists."""
        try:
            req = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')
                
                remote_version = CURRENT_VERSION
                for line in content.splitlines():
                    if line.startswith("REMOTE_VERSION") or line.startswith("VERSION"):
                        remote_version = line.split("=")[1].strip().strip('"').strip("'")
                        break
                
                if remote_version > CURRENT_VERSION:
                    self.show_update_banner(remote_version, content)
        except Exception as e:
            print(f"Update check skipped/failed: {e}")

    def show_update_banner(self, new_version, script_content):
        """Displays top banner when an update is detected on GitHub."""
        self.update_banner_frame.pack(side="top", fill="x", before=self.notebook)

        msg_label = tk.Label(
            self.update_banner_frame,
            text=f"🚀 Update Now! A new version (v{new_version}) is available on GitHub.",
            fg="white", bg="#2196F3", font=("Arial", 11, "bold")
        )
        msg_label.pack(side="left", padx=15, pady=8)

        update_btn = tk.Button(
            self.update_banner_frame,
            text="Update Now",
            bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
            relief="raised", command=lambda: self.apply_update(script_content)
        )
        update_btn.pack(side="right", padx=15, pady=8)

    def apply_update(self, script_content):
        """Overwrites local file with updated script content."""
        if messagebox.askyesno("Confirm Update", "Do you want to update jBlur now?"):
            try:
                with open(sys.argv[0], "w", encoding="utf-8") as f:
                    f.write(script_content)
                messagebox.showinfo("Updated", "App updated successfully! Please restart jBlur.")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Update Error", f"Could not write update: {e}")

    # -----------------------------------------------------------------------
    # 2. ROTATING AD BANNER ENGINE
    # -----------------------------------------------------------------------
    def create_ad_banner(self):
        self.ad_frame = tk.Frame(self, height=80, bg="#111111", cursor="hand2")
        self.ad_frame.pack(side="bottom", fill="x")
        self.ad_frame.pack_propagate(False)

        self.ad_label = tk.Label(self.ad_frame, bg="#111111", text="Loading Ad Banner...", fg="#AAAAAA")
        self.ad_label.pack(expand=True)
        
        # Click event opens sponsor link
        self.ad_frame.bind("<Button-1>", self.on_ad_click)
        self.ad_label.bind("<Button-1>", self.on_ad_click)

    def rotate_ad_banner(self):
        """Fetches the active ad image and updates the bottom banner."""
        ad_data = AD_BANNERS[self.current_ad_index]
        
        try:
            req = urllib.request.Request(ad_data["image_url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw_data = resp.read()
                pil_ad = Image.open(io.BytesIO(raw_data))
                
                # Resize banner to fit the bottom area (max height 70px)
                pil_ad.thumbnail((800, 70), Image.Resampling.LANCZOS)
                
                self.current_ad_tk = ImageTk.PhotoImage(pil_ad)
                self.ad_label.config(image=self.current_ad_tk, text="")
        except Exception as e:
            # Fallback text if image fails to load
            self.ad_label.config(
                image="", 
                text=f"📢 Visit Sponsor: {ad_data['name']} ({ad_data['link_url']})", 
                fg="#00E676", font=("Arial", 11, "bold")
            )

        # Advance to next ad in sequence
        self.current_ad_index = (self.current_ad_index + 1) % len(AD_BANNERS)
        
        # Rotate ad every 8000 ms (8 seconds)
        self.after(8000, self.rotate_ad_banner)

    def on_ad_click(self, event):
        """Opens sponsor URL when the user clicks the ad banner."""
        # Get current ad URL
        ad_index = (self.current_ad_index - 1) % len(AD_BANNERS)
        target_url = AD_BANNERS[ad_index]["link_url"]
        webbrowser.open(target_url)

    # -----------------------------------------------------------------------
    # 3. TAB 1: STANDARD IMAGE BLURRER
    # -----------------------------------------------------------------------
    def build_image_blurrer_tab(self):
        controls = ttk.Frame(self.tab_image)
        controls.pack(fill="x", padx=5, pady=5)

        ttk.Button(controls, text="Open Image", command=self.load_image).pack(side="left", padx=5)
        ttk.Label(controls, text="Blur Radius:").pack(side="left", padx=5)
        self.img_blur_slider = ttk.Scale(controls, from_=1, to=50, value=15)
        self.img_blur_slider.pack(side="left", padx=5)
        ttk.Button(controls, text="Save Image", command=self.save_image).pack(side="left", padx=5)

        self.img_canvas = tk.Canvas(self.tab_image, bg="#cccccc")
        self.img_canvas.pack(fill="both", expand=True)
        self.img_canvas.bind("<B1-Motion>", self.blur_image_region)

        self.loaded_pil_img = None
        self.displayed_tk_img = None

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if path:
            self.loaded_pil_img = Image.open(path).convert("RGB")
            self.redraw_canvas_image()

    def redraw_canvas_image(self):
        if self.loaded_pil_img:
            self.displayed_tk_img = ImageTk.PhotoImage(self.loaded_pil_img)
            self.img_canvas.config(width=self.displayed_tk_img.width(), height=self.displayed_tk_img.height())
            self.img_canvas.create_image(0, 0, anchor="nw", image=self.displayed_tk_img)

    def blur_image_region(self, event):
        if not self.loaded_pil_img:
            return
        
        r = int(self.img_blur_slider.get())
        x, y = event.x, event.y
        box = (max(0, x - r), max(0, y - r), min(self.loaded_pil_img.width, x + r), min(self.loaded_pil_img.height, y + r))
        
        cropped = self.loaded_pil_img.crop(box)
        blurred = cropped.filter(ImageFilter.GaussianBlur(radius=r // 2))
        self.loaded_pil_img.paste(blurred, box)
        self.redraw_canvas_image()

    def save_image(self):
        if self.loaded_pil_img:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path:
                self.loaded_pil_img.save(path)

    # -----------------------------------------------------------------------
    # 4. TAB 2: TEXT-TO-IMAGE BLURRER
    # -----------------------------------------------------------------------
    def build_text_blurrer_tab(self):
        side_panel = ttk.Frame(self.tab_text)
        side_panel.pack(side="left", fill="y", padx=5, pady=5)

        ttk.Label(side_panel, text="Enter Text:").pack(anchor="w", pady=(0, 2))
        self.text_entry = tk.Text(side_panel, width=25, height=8)
        self.text_entry.insert("1.0", "Type custom text here...\nClick Render then click & drag to blur!")
        self.text_entry.pack(pady=5)

        self.bg_color = "#FFFFFF"
        self.text_color = "#000000"
        
        ttk.Button(side_panel, text="Change BG Color", command=self.pick_bg_color).pack(fill="x", pady=2)
        ttk.Button(side_panel, text="Change Text Color", command=self.pick_text_color).pack(fill="x", pady=2)
        
        ttk.Label(side_panel, text="Font Size:").pack(anchor="w", pady=(10, 2))
        self.font_size_scale = ttk.Scale(side_panel, from_=12, to=72, value=28)
        self.font_size_scale.pack(fill="x")

        ttk.Button(side_panel, text="Render Text to Canvas", command=self.render_text_to_image).pack(fill="x", pady=10)
        
        ttk.Label(side_panel, text="Blur Radius:").pack(anchor="w", pady=(10, 2))
        self.txt_blur_slider = ttk.Scale(side_panel, from_=1, to=50, value=15)
        self.txt_blur_slider.pack(fill="x")

        ttk.Button(side_panel, text="Save Result", command=self.save_text_image).pack(fill="x", pady=10)

        # Canvas for rendered text
        self.text_canvas = tk.Canvas(self.tab_text, bg="#eeeeee")
        self.text_canvas.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        self.text_canvas.bind("<B1-Motion>", self.blur_text_image_region)

        self.rendered_text_pil = None
        self.rendered_text_tk = None

    def pick_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")[1]
        if color:
            self.bg_color = color

    def pick_text_color(self):
        color = colorchooser.askcolor(title="Choose Text Color")[1]
        if color:
            self.text_color = color

    def render_text_to_image(self):
        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            return

        font_size = int(self.font_size_scale.get())
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        img_w, img_h = 600, 400
        img = Image.new("RGB", (img_w, img_h), color=self.bg_color)
        draw = ImageDraw.Draw(img)

        draw.multiline_text((20, 20), text, fill=self.text_color, font=font, spacing=6)

        self.rendered_text_pil = img
        self.redraw_text_canvas()

    def redraw_text_canvas(self):
        if self.rendered_text_pil:
            self.rendered_text_tk = ImageTk.PhotoImage(self.rendered_text_pil)
            self.text_canvas.config(width=self.rendered_text_tk.width(), height=self.rendered_text_tk.height())
            self.text_canvas.create_image(0, 0, anchor="nw", image=self.rendered_text_tk)

    def blur_text_image_region(self, event):
        if not self.rendered_text_pil:
            return

        r = int(self.txt_blur_slider.get())
        x, y = event.x, event.y
        box = (max(0, x - r), max(0, y - r), min(self.rendered_text_pil.width, x + r), min(self.rendered_text_pil.height, y + r))
        
        cropped = self.rendered_text_pil.crop(box)
        blurred = cropped.filter(ImageFilter.GaussianBlur(radius=r // 2))
        self.rendered_text_pil.paste(blurred, box)
        self.redraw_text_canvas()

    def save_text_image(self):
        if self.rendered_text_pil:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path:
                self.rendered_text_pil.save(path)


if __name__ == "__main__":
    app = JBlurApp()
    app.mainloop()
