import os
import shutil
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk

class ImageClassifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Rating App")
        self.root.geometry("1200x700")

        self.image_list = []
        self.image_index = 0
        self.image_ratings = {}
        self.filtered_star = None
        self.thumb_size = 80
        self.thumb_images = []
        self.rated_thumbs = []
        self.rating_buttons = []
        self.thumb_panels = []
        self.image_cache = {}

        self.active_canvas = None

        self.setup_ui()
        self.bind_keys()

    def setup_ui(self):
        self._thumb_update_job = None
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_frame, width=250)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.center_frame = tk.Frame(self.main_frame)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.main_frame, width=250)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Folder", command=self.import_folder)

        self.thumb_canvas = tk.Canvas(self.left_frame)
        self.thumb_scroll = tk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.thumb_canvas.yview)
        self.thumb_frame = tk.Frame(self.thumb_canvas)

        self.thumb_canvas.create_window((0, 0), window=self.thumb_frame, anchor="nw")
        self.thumb_canvas.configure(yscrollcommand=self.thumb_scroll.set)

        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thumb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.thumb_frame.bind("<Configure>", lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all")))
        self.thumb_canvas.bind("<Enter>", lambda e: self.set_active_canvas(self.thumb_canvas))
        self.thumb_canvas.bind("<Leave>", lambda e: self.set_active_canvas(None))

        self.thumb_slider = tk.Scale(self.left_frame, from_=40, to=160, label="Thumbnail Size", orient=tk.HORIZONTAL, command=self.schedule_thumbnail_update)
        self.thumb_slider.set(self.thumb_size)
        self.thumb_slider.pack(fill=tk.X)

        self.canvas = tk.Canvas(self.center_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.filter_label = tk.Label(self.right_frame, text="Filter by rating:")
        self.filter_label.pack(anchor="ne", padx=10, pady=5)

        self.filter_combobox = ttk.Combobox(self.right_frame, values=["All", 1, 2, 3, 4, 5], width=10)
        self.filter_combobox.set("All")
        self.filter_combobox.pack(anchor="ne", padx=10)
        self.filter_combobox.bind("<<ComboboxSelected>>", self.apply_filter)

        self.rated_canvas = tk.Canvas(self.right_frame)
        self.rated_scroll = tk.Scrollbar(self.right_frame, orient=tk.VERTICAL, command=self.rated_canvas.yview)
        self.rated_frame = tk.Frame(self.rated_canvas)

        self.rated_canvas.create_window((0, 0), window=self.rated_frame, anchor="nw")
        self.rated_canvas.configure(yscrollcommand=self.rated_scroll.set)

        self.rated_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.rated_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.rated_frame.bind("<Configure>", lambda e: self.rated_canvas.configure(scrollregion=self.rated_canvas.bbox("all")))
        self.rated_canvas.bind("<Enter>", lambda e: self.set_active_canvas(self.rated_canvas))
        self.rated_canvas.bind("<Leave>", lambda e: self.set_active_canvas(None))

        self.root.bind_all("<MouseWheel>", self.mousewheel_scroll)

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(fill=tk.X)

        for i in range(1, 6):
            btn = tk.Button(self.bottom_frame, text="☆", width=4, command=lambda i=i: self.rate_image(i))
            btn.pack(side=tk.LEFT, padx=2)
            self.rating_buttons.append(btn)

        tk.Button(self.bottom_frame, text="Skip", command=self.skip_image).pack(side=tk.LEFT, padx=10)
        tk.Button(self.bottom_frame, text="Copy Filtered Images", command=self.copy_filtered_images).pack(side=tk.RIGHT, padx=10)

    def set_active_canvas(self, canvas):
        self.active_canvas = canvas

    def mousewheel_scroll(self, event):
        if self.active_canvas:
            self.active_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def schedule_thumbnail_update(self, val):
        if self._thumb_update_job:
            self.root.after_cancel(self._thumb_update_job)
        self._thumb_update_job = self.root.after(150, lambda: self.update_thumbnail_size(val))

    def bind_keys(self):
        for i in range(1, 6):
            self.root.bind(str(i), lambda e, i=i: self.rate_image(i))
        self.root.bind("<space>", lambda e: self.skip_image())

    def import_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.image_list = [os.path.join(folder, f) for f in os.listdir(folder)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        self.image_list.sort()
        self.image_index = 0
        self.image_cache.clear()
        self.display_thumbnails()
        self.display_image()

    def get_cached_image(self, path, size):
        key = (path, size)
        if key not in self.image_cache:
            img = Image.open(path)
            img.thumbnail((size, size))
            self.image_cache[key] = ImageTk.PhotoImage(img)
        return self.image_cache[key]

    def display_thumbnails(self):
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumb_images.clear()
        self.thumb_panels.clear()

        for i, path in enumerate(self.image_list):
            tk_img = self.get_cached_image(path, self.thumb_size)
            self.thumb_images.append(tk_img)
            panel = tk.Label(self.thumb_frame, image=tk_img, text=os.path.basename(path), compound="left", anchor="w", bd=0, relief="flat")
            panel.pack(fill=tk.X, pady=1)
            panel.bind("<Button-1>", lambda e, idx=i: self.select_image(idx))
            self.thumb_panels.append(panel)

        self.highlight_selected_thumbnail()

    def highlight_selected_thumbnail(self):
        for idx, panel in enumerate(self.thumb_panels):
            if idx == self.image_index:
                panel.config(bg="#a6d4fa")
            else:
                panel.config(bg="SystemButtonFace")

    def update_thumbnail_size(self, val):
        self.thumb_size = int(val)
        self.display_thumbnails()
        self.update_rated_list()  # this now runs after throttling

    def select_image(self, idx):
        self.image_index = idx
        self.display_image()
        self.highlight_selected_thumbnail()

    def display_image(self):
        if not self.image_list or self.image_index >= len(self.image_list):
            return
        img_path = self.image_list[self.image_index]
        if (img_path, 'full') not in self.image_cache:
            image = Image.open(img_path)
            w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
            image.thumbnail((w, h))
            self.image_cache[(img_path, 'full')] = ImageTk.PhotoImage(image)
        self.tk_img = self.image_cache[(img_path, 'full')]
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.create_image(w // 2, h // 2, image=self.tk_img)
        self.update_rating_buttons(img_path)

    def update_rating_buttons(self, img_path):
        rating = self.image_ratings.get(img_path, 0)
        for i, btn in enumerate(self.rating_buttons):
            btn.config(text="★" if i + 1 == rating else "☆")

    def rate_image(self, stars):
        if not self.image_list:
            return
        img_path = self.image_list[self.image_index]
        self.image_ratings[img_path] = stars
        self.update_rating_buttons(img_path)
        self.update_rated_list()
        self.next_image()

    def skip_image(self):
        self.next_image()

    def next_image(self):
        self.image_index += 1
        if self.image_index < len(self.image_list):
            self.display_image()
            self.highlight_selected_thumbnail()

    def apply_filter(self, event):
        selection = self.filter_combobox.get()
        self.filtered_star = None if selection == "All" else int(selection)
        self.update_rated_list()

    def update_rated_list(self):
        for widget in self.rated_frame.winfo_children():
            widget.destroy()
        self.rated_thumbs.clear()

        for path, star in self.image_ratings.items():
            if self.filtered_star is None or star == self.filtered_star:
                tk_img = self.get_cached_image(path, self.thumb_size)
                self.rated_thumbs.append(tk_img)
                panel = tk.Label(self.rated_frame, image=tk_img, text=os.path.basename(path), compound="left", anchor="w")
                panel.pack(fill=tk.X, pady=1)

    def copy_filtered_images(self):
        target_dir = filedialog.askdirectory()
        if not target_dir:
            return
        for img_path, rating in self.image_ratings.items():
            if self.filtered_star is None or rating == self.filtered_star:
                shutil.copy(img_path, os.path.join(target_dir, os.path.basename(img_path)))

if __name__ == '__main__':
    root = tk.Tk()
    app = ImageClassifierApp(root)
    root.mainloop()
