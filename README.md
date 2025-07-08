# 🖼️ Image Rating App

A desktop application written in Python + Tkinter to browse, rate, and filter images using a 1–5 star system. Useful for quickly classifying large sets of images and exporting filtered subsets.

---

## 🔧 Technologies Used

- **Python 3.10+**
- **Tkinter** – GUI framework
- **PIL (Pillow)** – image processing
- **threading** – for non-blocking UI during image loading
- **shutil** – for copying filtered images

---

## ⚙️ Features

### ✅ User Interface (UI)

- **Left Panel:** Thumbnail list of images
- **Center Panel:** Enlarged view of selected image
- **Right Panel:** Rated images grouped by selected star filter
- **Bottom Panel:** Star rating buttons (☆), Skip button, and Copy button
- **Top Menu:** Import Folder

### ✅ Supported Image Extensions

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

### ✅ Rating and Browsing

- Navigate images using arrow keys (←, →, ↑, ↓)
- Rate images with number keys (1–5) or by clicking star buttons
- Press `Space` to skip an image
- Rated images shown on the right panel

### ✅ Thumbnail Features

- Adjustable thumbnail size via slider
- 100 thumbnails per page (configurable via `self.page_size`)
- Pagination: Prev / Next buttons
- Automatically switches pages after finishing a set of 100 images
- Selected image is always kept in visible scroll area

### ✅ Filtering and Exporting

- Filter by rating (All, 1–5 stars)
- "Copy Filtered Images" button copies selected-rated images to a target folder

---

## 🔑 Keyboard Shortcuts

| Key            | Action                       |
|----------------|------------------------------|
| 1 → 5          | Rate the current image       |
| Space          | Skip current image           |
| ← ↑ ↓ →        | Navigate between images      |

---

## 📁 File Structure

The application runs from a single file:

```
image_rating_app.py
```

---

## ✅ Solved Issues

- Fixed a bug where >400 thumbnails failed to render (pagination added)
- Scrollbar now keeps selection in view and doesn’t jump on click
- Clicking a thumbnail updates the main view correctly
- Removed duplicate bottom progress bar
- Fixed missing `refresh_displayed_image()` error

---

## 🚀 Suggestions for Expansion

- Add image search by filename
- Save/load rating state to/from a file
- Improve UI aesthetics using `ttk` or `customtkinter`
- Add slideshow or AI auto-rating feature

---

## 🧪 How to Run

```bash
python image_rating_app.py
```

Make sure to have `Pillow` installed:

```bash
pip install pillow
```

---

## 📦 Author Notes

Created with care for fast and efficient local image rating. Useful in data labeling, photo curation, and classification projects.

Feel free to fork and enhance! ✨