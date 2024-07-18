import os
import time
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import ctypes
import sys
from send2trash import send2trash

def get_file_category(name: str) -> str:
    ext = os.path.splitext(name)[-1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".gif"]:
        return "images"
    elif ext in [".mp4", ".mkv", ".mov", ".avi"]:
        return "videos"
    elif ext in [".pdf", ".docx", ".txt"]:
        return "documents"
    elif ext in [".exe", ".iso"]:
        return "games"
    else:
        return "others"

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        entry_dir_path.delete(0, tk.END)
        entry_dir_path.insert(0, directory)
        display_folder_details()

def delete_path(folder_path):
    if use_recycle_bin_var.get():
        send2trash(folder_path.replace("/", "\\"))
        return
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    else:
        os.remove(folder_path)

def delete_selected_folders():
    for item in tree.get_children():
        if "checked" in tree.item(item, "tags"):
            folder_path = tree.item(item, "values")[0]
            try:
                if ctypes.windll.shell32.IsUserAnAdmin() or True:
                    delete_path(folder_path)
                    tree.delete(item)
                else:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, f'"{__file__}"', None, 1
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting {folder_path}: {e}")
    display_folder_details()

def delete_highlighted_folder():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "No folder selected")
        return
    folder_path = tree.item(selected_item, "values")[0]
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            delete_path(folder_path)
            tree.delete(selected_item)
        else:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting {folder_path}: {e}")
    display_folder_details()

def toggle_check(event):
    item = tree.identify_row(event.y)
    if "checked" in tree.item(item, "tags"):
        tree.item(item, tags=("unchecked",))
    else:
        tree.item(item, tags=("checked",))

def display_folder_details():
    dir_path = entry_dir_path.get()
    if not os.path.isdir(dir_path):
        messagebox.showerror("Error", "Invalid directory path selected")
        return
    tree.delete(*tree.get_children())
    insert_directory_tree("", dir_path)

def insert_directory_tree(parent, directory):
    for entry in os.scandir(directory):
        entry_type = "dir" if entry.is_dir() else "file"
        size_str = convert_size(entry.stat().st_size)
        mod_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(entry.stat().st_mtime))
        icon = icon_dict.get(get_file_category(entry.name), default_icon)
        node = tree.insert(parent, "end", text=entry.name, values=(entry.path, size_str, mod_time_str), image=icon, tags=("unchecked", entry_type))
        if entry.is_dir():
            tree.insert(node, "end", text="dummy")  # Add a dummy child to make the folder expandable

def on_expand(event):
    item = tree.focus()
    if not item:
        return
    path = tree.item(item, "values")[0]
    if not os.path.isdir(path):
        return
    # Remove the dummy child
    if tree.get_children(item):
        tree.delete(tree.get_children(item))
    insert_directory_tree(item, path)

def convert_size(size_bytes):
    if size_bytes < 1024:
        size = size_bytes
        size_label = "Bytes"
    elif size_bytes < (1024 * 1024):
        size = size_bytes / 1024
        size_label = "KB"
    elif size_bytes < (1024**3):
        size = size_bytes / (1024 * 1024)
        size_label = "MB"
    elif size_bytes < (1024**4):
        size = size_bytes / (1024**3)
        size_label = "GB"
    else:
        size = size_bytes / (1024**4)
        size_label = "TB"
    return f"{size:.2f} {size_label}"

def update_storage_bar(used_size, total_size):
    used_percent = (used_size / total_size) * 100
    bar_var.set(used_percent)
    bar_label.config(
        text=f"Used space: {convert_size(used_size)} / {convert_size(total_size)}"
    )

def toggle_color_theme():
    global current_theme
    current_theme = "dark" if current_theme == "light" else "light"
    set_color_theme(current_theme)

def set_color_theme(theme):
    if theme == "dark":
        app.config(bg="black")
        frame.config(bg="black")
        result_frame.config(bg="black")
        bar_frame.config(bg="black")
        label_dir_path.config(bg="black", fg="white")
        label_sort_choice.config(bg="black", fg="white")
        subfolder_check.config(bg="black", fg="white", selectcolor="black")
        button_browse.config(bg="grey", fg="white")
        button_display.config(bg="grey", fg="white")
        # Comment out the line since button_delete is not defined
        # button_delete.config(bg="grey", fg="white")
        theme_button.config(bg="grey", fg="white")
        bar_label.config(bg="black", fg="white")
    else:
        app.config(bg="white")
        frame.config(bg="white")
        result_frame.config(bg="white")
        bar_frame.config(bg="white")
        label_dir_path.config(bg="white", fg="black")
        if "label_sort_choice" in locals():
            label_sort_choice.config(bg="white", fg="black")
        use_recycle_bin_var = tk.BooleanVar()
        subfolder_check = tk.Checkbutton(frame, text="Subfolders", variable=use_recycle_bin_var)
        subfolder_check.config(bg="white", fg="black", selectcolor="white")
        button_browse.config(bg="grey", fg="black")
        button_display.config(bg="grey", fg="black")
        # Comment out the line since button_delete is not defined
        # button_delete.config(bg="grey", fg="black")
        theme_button.config(bg="grey", fg="black")
        bar_label.config(bg="white", fg="black")

def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

app = tk.Tk()
app.title("Folder Cleaner")
app.geometry("800x600")

frame = tk.Frame(app)
frame.pack(pady=10)

label_dir_path = tk.Label(frame, text="Directory Path:")
label_dir_path.grid(row=0, column=0, padx=5, pady=5)

entry_dir_path = tk.Entry(frame, width=50)
entry_dir_path.grid(row=0, column=1, padx=5, pady=5)

button_browse = tk.Button(frame, text="Browse", command=browse_directory)
button_browse.grid(row=0, column=2, padx=5, pady=5)

button_display = tk.Button(frame, text="Display", command=display_folder_details)
button_display.grid(row=2, column=1, padx=5, pady=5)

use_recycle_bin_var = tk.BooleanVar()
recycle_bin_check = tk.Checkbutton(frame, text="Use Recycle Bin", variable=use_recycle_bin_var)
recycle_bin_check.grid(row=2, column=2, padx=5, pady=5)

theme_button = tk.Button(frame, text="Toggle Theme", command=toggle_color_theme)
theme_button.grid(row=2, column=0, padx=5, pady=5)

result_frame = tk.Frame(app)
result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(result_frame, columns=("Path", "Size", "Oldest"), show="tree headings")
tree.heading("#0", text="Name")
tree.heading("Path", text="Path")
tree.heading("Size", text="Size")
tree.heading("Oldest", text="Oldest File Date")
tree.pack(fill=tk.BOTH, expand=True)

tree.bind("<Double-1>", on_expand)  # Bind the double-click event
tree.bind("<Button-1>", toggle_check)

bar_frame = tk.Frame(app)
bar_frame.pack(pady=10)

bar_var = tk.DoubleVar()
storage_bar = ttk.Progressbar(bar_frame, variable=bar_var, maximum=100)
storage_bar.pack(fill=tk.BOTH, expand=True)

bar_label = tk.Label(bar_frame, text="")
bar_label.pack()

context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(label="Delete", command=delete_highlighted_folder)
tree.bind("<Button-3>", show_context_menu)

icon_dict = {}
for category in ["images", "videos", "documents", "games", "others"]:
    img = Image.open(f"{category}.png").resize((16, 16))
    icon_dict[category] = ImageTk.PhotoImage(img)
default_icon = icon_dict["others"]

current_theme = "light"
set_color_theme(current_theme)

app.mainloop()
