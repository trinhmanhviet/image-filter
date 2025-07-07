import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import os
import shutil
from pathlib import Path

class ImageRatingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Rating App")
        self.root.geometry("1200x700")
        self.images = []
        self.current_image_index = -1
        self.ratings = {}
        self.thumbnails = []
        self.rated_thumbnails = []
        self.thumbnail_size = tk.DoubleVar(value=100)  # Default thumbnail size
        
        # Main paned window for resizable frames
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Left frame: Thumbnail canvas with scrollbar and slider
        self.left_frame = ttk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.left_frame, weight=1)
        # Slider for thumbnail size
        self.size_slider = ttk.Scale(self.left_frame, from_=50, to=150, orient=tk.HORIZONTAL, variable=self.thumbnail_size, command=self.update_thumbnails)
        self.size_slider.pack(fill="x", padx=5, pady=5)
        self.size_label = ttk.Label(self.left_frame, text="Thumbnail Size")
        self.size_label.pack()
        self.left_canvas_frame = ttk.Frame(self.left_frame)
        self.left_canvas_frame.pack(fill="both", expand=True)
        self.left_image_canvas = tk.Canvas(self.left_canvas_frame, bg="white")
        self.left_scrollbar = ttk.Scrollbar(self.left_canvas_frame, orient="vertical", command=self.left_image_canvas.yview)
        self.left_scrollable_frame = ttk.Frame(self.left_image_canvas)
        self.left_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.left_image_canvas.configure(scrollregion=self.left_image_canvas.bbox("all"))
        )
        self.left_image_canvas.create_window((0, 0), window=self.left_scrollable_frame, anchor="nw")
        self.left_image_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        self.left_image_canvas.pack(side="left", fill="both", expand=True)
        self.left_scrollbar.pack(side="right", fill="y")
        self.left_image_canvas.bind("<MouseWheel>", self.on_left_mouse_wheel)
        self.left_scrollable_frame.bind("<MouseWheel>", self.on_left_mouse_wheel)
        # Bind frame resize to update canvas width
        self.left_frame.bind("<Configure>", self.on_left_frame_resize)
        
        # Center frame: Image display, rating, and skip
        self.center_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.center_frame, weight=3)
        self.image_label = ttk.Label(self.center_frame, anchor="center")
        self.image_label.pack(fill="both", expand=True, pady=10)
        self.rating_frame = ttk.Frame(self.center_frame)
        self.rating_frame.pack(pady=5)
        self.star_buttons = []
        for i in range(5):
            btn = ttk.Button(self.rating_frame, text="☆", command=lambda x=i+1: self.rate_image(x))
            btn.grid(row=0, column=i, padx=2)
            self.star_buttons.append(btn)
        self.skip_button = ttk.Button(self.center_frame, text="Skip", command=self.skip_image)
        self.skip_button.pack(pady=5)
        
        # Right frame: Rated images canvas with scrollbar
        self.right_frame = ttk.Frame(self.paned_window, width=200)
        self.paned_window.add(self.right_frame, weight=1)
        self.filter_label = ttk.Label(self.right_frame, text="Filter by rating:")
        self.filter_label.pack()
        self.filter_var = tk.StringVar(value="All")
        self.filter_menu = ttk.OptionMenu(self.right_frame, self.filter_var, "All", "All", "5 stars", "4 stars", "4+ stars", "3+ stars", "2+ stars", "1+ star", command=self.update_rated_list)
        self.filter_menu.pack()
        self.right_canvas_frame = ttk.Frame(self.right_frame)
        self.right_canvas_frame.pack(fill="both", expand=True)
        self.right_image_canvas = tk.Canvas(self.right_canvas_frame, width=180, bg="white")
        self.right_scrollbar = ttk.Scrollbar(self.right_canvas_frame, orient="vertical", command=self.right_image_canvas.yview)
        self.right_scrollable_frame = ttk.Frame(self.right_image_canvas)
        self.right_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.right_image_canvas.configure(scrollregion=self.right_image_canvas.bbox("all"))
        )
        self.right_image_canvas.create_window((0, 0), window=self.right_scrollable_frame, anchor="nw")
        self.right_image_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        self.right_image_canvas.pack(side="left", fill="both", expand=True)
        self.right_scrollbar.pack(side="right", fill="y")
        self.right_image_canvas.bind("<MouseWheel>", self.on_right_mouse_wheel)
        self.right_scrollable_frame.bind("<MouseWheel>", self.on_right_mouse_wheel)
        
        # Copy button
        self.copy_button = ttk.Button(self.right_frame, text="Copy Filtered Images", command=self.copy_filtered_images)
        self.copy_button.pack(pady=5)
        
        # Menu bar
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Import Folder", command=self.import_folder)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=self.menubar)
        
        # Keyboard bindings
        for i in range(1, 6):
            self.root.bind(str(i), lambda event, r=i: self.rate_image(r))
        self.root.bind("<space>", lambda event: self.skip_image())
        
        # Bind resize event to update center image
        self.center_frame.bind("<Configure>", self.on_center_frame_resize)
    
    def on_left_mouse_wheel(self, event):
        self.left_image_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_right_mouse_wheel(self, event):
        self.right_image_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_center_frame_resize(self, event):
        if 0 <= self.current_image_index < len(self.images):
            self.display_image(self.current_image_index)
    
    def on_left_frame_resize(self, event):
        # Update canvas width based on left frame width, accounting for scrollbar and padding
        new_width = max(200, self.left_frame.winfo_width() - self.left_scrollbar.winfo_width() - 10)
        self.left_image_canvas.configure(width=new_width)
        self.update_thumbnails()  # Refresh thumbnails to adjust wraplength
    
    def update_thumbnails(self, *args):
        if not self.images:
            return
        # Clear current thumbnails
        for widget in self.left_scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnails = []
        # Regenerate thumbnails with new size
        size = int(self.thumbnail_size.get())
        canvas_width = self.left_image_canvas.winfo_width()
        if canvas_width < 200:  # Ensure minimum width during init
            canvas_width = 300
        for idx, image_path in enumerate(self.images):
            try:
                image = Image.open(image_path)
                image.thumbnail((size, size))
                photo = ImageTk.PhotoImage(image)
                self.thumbnails.append(photo)
                # Create frame for thumbnail and label
                frame = ttk.Frame(self.left_scrollable_frame)
                frame.pack(fill="x", pady=2)
                frame.grid_columnconfigure(1, weight=1)  # Make filename column expandable
                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.grid(row=0, column=0, padx=5, sticky="w")
                label.bind("<Button-1>", lambda e, idx=idx: self.on_image_select(idx))
                fname_label = ttk.Label(frame, text=os.path.basename(image_path), wraplength=max(150, canvas_width-size-20), anchor="w")
                fname_label.grid(row=0, column=1, sticky="ew", padx=5)
                fname_label.bind("<Button-1>", lambda e, idx=idx: self.on_image_select(idx))
            except Exception as e:
                print(f"Error loading {image_path}: {e}")
        # Update canvas scroll region
        self.left_scrollable_frame.update_idletasks()
        self.left_image_canvas.configure(scrollregion=self.left_image_canvas.bbox("all"))
    
    def import_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.images = []
            self.thumbnails = []
            self.rated_thumbnails = []
            for widget in self.left_scrollable_frame.winfo_children():
                widget.destroy()
            for widget in self.right_scrollable_frame.winfo_children():
                widget.destroy()
            self.ratings.clear()
            self.update_rated_list()
            for file in os.listdir(folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    image_path = os.path.join(folder, file)
                    try:
                        # Create thumbnail for left frame
                        image = Image.open(image_path)
                        size = int(self.thumbnail_size.get())
                        image.thumbnail((size, size))
                        photo = ImageTk.PhotoImage(image)
                        self.images.append(image_path)
                        self.thumbnails.append(photo)
                        # Create smaller thumbnail for right frame (50x50)
                        image.thumbnail((50, 50))
                        rated_photo = ImageTk.PhotoImage(image)
                        self.rated_thumbnails.append(rated_photo)
                        # Create frame for thumbnail and label
                        frame = ttk.Frame(self.left_scrollable_frame)
                        frame.pack(fill="x", pady=2)
                        frame.grid_columnconfigure(1, weight=1)  # Make filename column expandable
                        label = ttk.Label(frame, image=photo)
                        label.image = photo
                        label.grid(row=0, column=0, padx=5, sticky="w")
                        label.bind("<Button-1>", lambda e, idx=len(self.images)-1: self.on_image_select(idx))
                        canvas_width = self.left_image_canvas.winfo_width() or 300  # Fallback during init
                        fname_label = ttk.Label(frame, text=file, wraplength=max(150, canvas_width-size-20), anchor="w")
                        fname_label.grid(row=0, column=1, sticky="ew", padx=5)
                        fname_label.bind("<Button-1>", lambda e, idx=len(self.images)-1: self.on_image_select(idx))
                    except Exception as e:
                        print(f"Error loading {file}: {e}")
            # Update canvas scroll region
            self.left_scrollable_frame.update_idletasks()
            self.left_image_canvas.configure(scrollregion=self.left_image_canvas.bbox("all"))
            if self.images:
                self.current_image_index = 0
                self.display_image(0)
    
    def on_image_select(self, index):
        self.current_image_index = index
        self.display_image(self.current_image_index)
    
    def display_image(self, index):
        if 0 <= index < len(self.images):
            image_path = self.images[index]
            try:
                image = Image.open(image_path)
                # Get center frame dimensions
                frame_width = self.center_frame.winfo_width()
                frame_height = self.center_frame.winfo_height() - 100  # Account for rating/skip buttons
                if frame_width < 10 or frame_height < 10:  # Avoid invalid dimensions during init
                    frame_width, frame_height = 500, 500
                # Calculate scaling to fit frame while preserving aspect ratio
                img_width, img_height = image.size
                scale = min(frame_width / img_width, frame_height / img_height)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=photo)
                self.image_label.image = photo
                # Update star buttons
                rating = self.ratings.get(image_path, 0)
                for i in range(5):
                    self.star_buttons[i].config(text="★" if i < rating else "☆")
            except Exception as e:
                print(f"Error displaying {image_path}: {e}")
    
    def rate_image(self, rating):
        if 0 <= self.current_image_index < len(self.images):
            image_path = self.images[self.current_image_index]
            self.ratings[image_path] = rating
            self.update_rated_list()
            # Update star buttons
            for i in range(5):
                self.star_buttons[i].config(text="★" if i < rating else "☆")
            # Move to next image
            if self.current_image_index < len(self.images) - 1:
                self.current_image_index += 1
                self.display_image(self.current_image_index)
    
    def skip_image(self):
        if 0 <= self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.display_image(self.current_image_index)
    
    def update_rated_list(self, *args):
        for widget in self.right_scrollable_frame.winfo_children():
            widget.destroy()
        filter_value = self.filter_var.get()
        for idx, image_path in enumerate(self.ratings):
            rating = self.ratings[image_path]
            if self.filter_matches(rating, filter_value):
                try:
                    # Create frame for thumbnail and label
                    frame = ttk.Frame(self.right_scrollable_frame)
                    frame.pack(fill="x", pady=2)
                    label = ttk.Label(frame, image=self.rated_thumbnails[idx])
                    label.image = self.rated_thumbnails[idx]
                    label.grid(row=0, column=0, padx=5, sticky="w")
                    ttk.Label(frame, text=f"{os.path.basename(image_path)} ({rating} stars)", wraplength=120).grid(row=0, column=1, sticky="w")
                except Exception as e:
                    print(f"Error displaying rated image {image_path}: {e}")
        # Update canvas scroll region
        self.right_scrollable_frame.update_idletasks()
        self.right_image_canvas.configure(scrollregion=self.right_image_canvas.bbox("all"))
    
    def filter_matches(self, rating, filter_value):
        if filter_value == "All":
            return True
        if filter_value == "5 stars" and rating == 5:
            return True
        if filter_value == "4 stars" and rating == 4:
            return True
        if filter_value == "4+ stars" and rating >= 4:
            return True
        if filter_value == "3+ stars" and rating >= 3:
            return True
        if filter_value == "2+ stars" and rating >= 2:
            return True
        if filter_value == "1+ star" and rating >= 1:
            return True
        return False
    
    def copy_filtered_images(self):
        dest_folder = filedialog.askdirectory(title="Select Destination Folder")
        if dest_folder:
            filter_value = self.filter_var.get()
            for image_path in self.ratings:
                if self.filter_matches(self.ratings[image_path], filter_value):
                    try:
                        shutil.copy(image_path, os.path.join(dest_folder, os.path.basename(image_path)))
                    except Exception as e:
                        print(f"Error copying {image_path}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRatingApp(root)
    root.mainloop()