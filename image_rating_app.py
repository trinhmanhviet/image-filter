import os
import shutil
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import threading

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
        self.thumb_images = {}
        self.rated_thumbs = []
        self.rating_buttons = []
        self.image_cache = {}

        self.tk_img = None
        self.current_img_path = None

        self.page_size = 200
        self.current_page = 0

        self.status_var = tk.StringVar()

        self.supported_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp")

        self.setup_ui()
        self.bind_keys()

    def set_widgets_state(self, state):
        for child in self.root.winfo_children():
            try:
                child.configure(state=state)
            except:
                pass

    def setup_ui(self):
        self.main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_frame, width=250)
        self.main_frame.add(self.left_frame, minsize=250, stretch='never')

        self.center_frame = tk.Frame(self.main_frame)
        self.main_frame.add(self.center_frame, stretch='always')

        self.right_frame = tk.Frame(self.main_frame, width=250)
        self.main_frame.add(self.right_frame, minsize=250, stretch='never')

        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Folder", command=self.import_folder)

        self.thumb_slider = tk.Scale(self.left_frame, from_=40, to=160, label="Thumbnail Size", orient=tk.HORIZONTAL, command=self.update_thumbnail_size)
        self.thumb_slider.set(self.thumb_size)
        self.thumb_slider.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.thumb_canvas = tk.Canvas(self.left_frame)
        self.thumb_scrollbar = tk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.thumb_canvas.yview)
        self.thumb_frame = tk.Frame(self.thumb_canvas)

        self.thumb_inner_id = self.thumb_canvas.create_window((0, 0), window=self.thumb_frame, anchor="nw")
        self.thumb_canvas.configure(yscrollcommand=self.thumb_scrollbar.set)

        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        self.thumb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.thumb_frame.bind("<Configure>", self.on_thumb_configure)
        self.thumb_canvas.bind_all("<MouseWheel>", self.mousewheel_scroll)

        self.canvas = tk.Canvas(self.center_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.display_image())

        self.counter_label = tk.Label(self.center_frame, text="0 / 0", fg="white", bg="black", anchor="se")
        self.counter_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        filter_frame = tk.Frame(self.right_frame)
        filter_frame.pack(fill=tk.X, pady=2)
        tk.Label(filter_frame, text="Filter by rating:").pack(side=tk.LEFT, padx=10)
        self.filter_var = tk.StringVar(value="All")
        options = ["All", 1, 2, 3, 4, 5]
        self.filter_menu = tk.OptionMenu(filter_frame, self.filter_var, *options, command=self.apply_filter)
        self.filter_menu.config(width=8)
        self.filter_menu.pack(side=tk.LEFT, padx=5)
        
        self.filter_count_var = tk.StringVar(value="0 images")
        self.filter_count_label = tk.Label(self.right_frame, textvariable=self.filter_count_var, anchor="w")
        self.filter_count_label.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.rated_canvas = tk.Canvas(self.right_frame)
        self.rated_scroll = tk.Scrollbar(self.right_frame, orient=tk.VERTICAL, command=self.rated_canvas.yview)
        self.rated_frame = tk.Frame(self.rated_canvas)

        self.rated_canvas.create_window((0, 0), window=self.rated_frame, anchor="nw")
        self.rated_canvas.configure(yscrollcommand=self.rated_scroll.set)

        self.rated_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.rated_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.rated_frame.bind("<Configure>", lambda e: self.rated_canvas.configure(scrollregion=self.rated_canvas.bbox("all")))

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(fill=tk.X)

        for i in range(1, 6):
            btn = tk.Button(self.bottom_frame, text="☆", width=4, command=lambda i=i: self.rate_image(i))
            btn.pack(side=tk.LEFT, padx=2)
            self.rating_buttons.append(btn)

        tk.Button(self.bottom_frame, text="Skip", command=self.skip_image).pack(side=tk.LEFT, padx=10)
        tk.Button(self.bottom_frame, text="Copy Filtered Images", command=self.copy_filtered_images).pack(side=tk.RIGHT, padx=10)

    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)

        # Filter supported image files or directories
        dropped_files = []
        for path in paths:
            if os.path.isdir(path):
                for f in os.listdir(path):
                    full_path = os.path.join(path, f)
                    if f.lower().endswith(self.supported_extensions):
                        dropped_files.append(full_path)
            elif path.lower().endswith(self.supported_extensions):
                dropped_files.append(path)

        if not dropped_files:
            return

        answer = self.ask_add_or_replace()

        if answer == "add":
            self.image_list.extend(dropped_files)
            self.image_list = sorted(set(self.image_list))  # Remove duplicates
            self.display_image()
            self.update_thumbnails()

        elif answer == "new":
            self.image_list = dropped_files
            self.image_index = 0
            self.image_ratings.clear()
            self.current_page = 0
            self.display_image()
            self.update_thumbnails()

        # if "cancel", do nothing
    
    def ask_add_or_replace(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add or Replace Thumbnails?")
        popup.geometry("350x100")
        popup.transient(self.root)
        popup.grab_set()

        result = tk.StringVar(value="cancel")

        tk.Label(popup, text="Do you want to add new images or replace the current list?").pack(pady=10)

        btn_frame = tk.Frame(popup)
        btn_frame.pack()

        tk.Button(btn_frame, text="Add", width=10, command=lambda: [result.set("add"), popup.destroy()]).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="New Set", width=10, command=lambda: [result.set("new"), popup.destroy()]).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=lambda: popup.destroy()).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(popup)
        return result.get()

    def on_thumb_configure(self, event):
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))

    def bind_keys(self):
        self.root.bind("<Down>", lambda e: self.move_selection(1))
        self.root.bind("<Right>", lambda e: self.move_selection(1))
        self.root.bind("<Up>", lambda e: self.move_selection(-1))
        self.root.bind("<Left>", lambda e: self.move_selection(-1))
        for i in range(1, 6):
            self.root.bind(str(i), lambda e, i=i: self.rate_image(i))
        self.root.bind("<space>", lambda e: self.skip_image())

    def mousewheel_scroll(self, event):
        self.thumb_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def import_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        progress_popup = tk.Toplevel(self.root)
        progress_popup.title("Loading Images")
        progress_popup.geometry("400x100")
        progress_popup.transient(self.root)
        progress_popup.grab_set()

        label = tk.Label(progress_popup, text="Loading images...")
        label.pack(pady=5)

        progress = ttk.Progressbar(progress_popup, orient="horizontal", length=300, mode="determinate")
        progress.pack(pady=5)

        self.root.update()

        def load_images():
            self.set_widgets_state("disabled")
            file_list = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(self.supported_extensions)]
            file_list.sort()

            self.image_list = file_list
            total = len(file_list)
            progress.config(maximum=total)

            for idx, path in enumerate(file_list):
                self.get_cached_image(path, self.thumb_size)
                progress['value'] = idx + 1
                label.config(text=f"Loading {idx + 1}/{total} images...")
                self.root.update_idletasks()

            self.image_index = 0
            self.current_page = 0
            self.display_image()
            self.update_thumbnails()
            progress_popup.destroy()
            self.set_widgets_state("normal")

        threading.Thread(target=load_images, daemon=True).start()

    def update_thumbnails(self):
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()

        start = self.current_page * self.page_size
        end = min(len(self.image_list), start + self.page_size)
        for i in range(start, end):
            path = self.image_list[i]
            img = self.get_cached_image(path, self.thumb_size)
            if not img:
                continue
            panel = tk.Label(self.thumb_frame, image=img, text=os.path.basename(path), compound="left", anchor="w", bd=0, relief="flat")
            panel.pack(fill=tk.X, pady=1)
            panel.bind("<Button-1>", lambda e, idx=i: self.select_image(idx))
            if i == self.image_index:
                panel.config(bg="#a6d4fa")
            else:
                panel.config(bg="SystemButtonFace")

        self.root.after(50, self.ensure_visible)

    def ensure_visible(self):
        children = self.thumb_frame.winfo_children()
        local_index = self.image_index - self.current_page * self.page_size
        if 0 <= local_index < len(children):
            panel = children[local_index]
            canvas_height = self.thumb_canvas.winfo_height()
            panel_top = panel.winfo_y()
            panel_bottom = panel_top + panel.winfo_height()
            view_top = self.thumb_canvas.canvasy(0)
            view_bottom = view_top + canvas_height

            if panel_top < view_top:
                self.thumb_canvas.yview_moveto(panel_top / max(1, self.thumb_frame.winfo_height()))
            elif panel_bottom > view_bottom:
                offset = panel_bottom - canvas_height
                self.thumb_canvas.yview_moveto(offset / max(1, self.thumb_frame.winfo_height()))

    def select_image(self, idx):
        self.image_index = idx
        self.current_page = self.image_index // self.page_size
        self.display_image()
        self.update_thumbnails()

    def move_selection(self, direction):
        new_index = self.image_index + direction
        if 0 <= new_index < len(self.image_list):
            self.image_index = new_index
            new_page = self.image_index // self.page_size
            if new_page != self.current_page:
                self.current_page = new_page
            self.display_image()
            self.update_thumbnails()

    def update_thumbnail_size(self, val):
        self.thumb_size = int(val)
        self.update_thumbnails()
        self.update_rated_list()

    def get_cached_image(self, path, size):
        key = (path, size)
        if key not in self.image_cache:
            try:
                img = Image.open(path)
                img.thumbnail((size, size))
                self.image_cache[key] = ImageTk.PhotoImage(img)
            except:
                return None
        return self.image_cache[key]

    def display_image(self):
        if not self.image_list or self.image_index >= len(self.image_list):
            return
        img_path = self.image_list[self.image_index]
        self.current_img_path = img_path
        if (img_path, 'full') not in self.image_cache:
            try:
                image = Image.open(img_path)
                w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
                image.thumbnail((w, h))
                self.image_cache[(img_path, 'full')] = ImageTk.PhotoImage(image)
            except:
                return
        self.tk_img = self.image_cache[(img_path, 'full')]
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.create_image(w // 2, h // 2, image=self.tk_img)
        self.update_rating_buttons(img_path)
        self.counter_label.config(text=f"{self.image_index + 1} / {len(self.image_list)}")

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
        self.move_selection(1)

    def skip_image(self):
        self.move_selection(1)

    def apply_filter(self, event):
        selection = self.filter_var.get()
        self.filtered_star = None if selection == "All" else int(selection)
        self.update_rated_list()

    def update_rated_list(self):
        for widget in self.rated_frame.winfo_children():
            widget.destroy()
        self.rated_thumbs.clear()

        for path, star in self.image_ratings.items():
            if self.filtered_star is None or star == self.filtered_star:
                tk_img = self.get_cached_image(path, self.thumb_size)
                if not tk_img:
                    continue
                self.rated_thumbs.append(tk_img)
                panel = tk.Label(self.rated_frame, image=tk_img, text=os.path.basename(path), compound="left", anchor="w")
                panel.pack(fill=tk.X, pady=1)
                
        self.filter_count_var.set(f"{len(self.rated_thumbs)} image(s)")

    def copy_filtered_images(self):
        target_dir = filedialog.askdirectory()
        if not target_dir:
            return
        for img_path, rating in self.image_ratings.items():
            if self.filtered_star is None or rating == self.filtered_star:
                shutil.copy(img_path, os.path.join(target_dir, os.path.basename(img_path)))

if __name__ == '__main__':
    root = TkinterDnD.Tk()
    app = ImageClassifierApp(root)
    root.mainloop()