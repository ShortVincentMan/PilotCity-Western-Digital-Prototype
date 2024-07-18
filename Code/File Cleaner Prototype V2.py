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

def list_folders(directory, recursive=True):
    listing = []
    size = 0
    direct_child_count = 0
    oldest_mod_time = os.stat(directory).st_mtime
    categories = {
        "images": 0,
        "videos": 0,
        "documents": 0,
        "games": 0,
        "others": 0,
    }

    for entry in os.scandir(directory):
        direct_child_count += 1
        try:
            file_stat = entry.stat()
            if file_stat.st_mtime < oldest_mod_time:
                oldest_mod_time = file_stat.st_mtime
            if entry.is_dir():
                if not recursive:
                    children = os.scandir(entry.path)
                    child_count = 0
                    direct_child_size = 0
                    oldest_mtime = file_stat.st_mtime
                    c_categories = {
                        "images": 0,
                        "videos": 0,
                        "documents": 0,
                        "games": 0,
                        "others": 0,
                    }
                    for c in children:
                        child_count += 1
                        if not c.is_file():
                            continue
                        c_stat = c.stat()
                        direct_child_size += c_stat.st_size
                        if c_stat.st_mtime < oldest_mtime:
                            oldest_mtime = c_stat.st_mtime
                        c_categories[get_file_category(c.name)] += 1
                    listing.append(
                        (
                            entry.name,
                            entry.path,
                            direct_child_size,
                            child_count,
                            oldest_mtime,
                            c_categories,
                        )
                    )
                    size += direct_child_size
                else:
                    extras, dir_size, dir_cc, dir_mtime, dir_categories = list_folders(
                        entry.path, recursive=True
                    )
                    size += dir_size
                    listing.extend(extras)
                    listing.append(
                        (
                            entry.name,
                            entry.path,
                            dir_size,
                            dir_cc,
                            dir_mtime,
                            dir_categories,
                        )
                    )
            elif entry.is_file():
                file_size = file_stat.st_size
                mod_time = file_stat.st_mtime
                listing.append(
                    (
                        entry.name,
                        entry.path,
                        file_size,
                        1,
                        mod_time,
                        {get_file_category(entry.name): 1},
                    )
                )
                size += file_size
                categories[get_file_category(entry.name)] += 1
        except Exception as e:
            print(f"Error while processing {entry.path}: {e}")
            listing.append(
                (
                    entry.name,
                    entry.path,
                    0,
                    0,
                    0,
                    {get_file_category(entry.name): 1},
                )
            )
            continue
    return listing, size, direct_child_count, oldest_mod_time, categories

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        entry_dir_path.delete(0, tk.END)
        entry_dir_path.insert(0, directory)

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
        if tree.item(item, "tags")[0] == "checked":
            folder_path = tree.item(item, "values")[1]
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
    if subfolder_var.get():
        display_folder_details()

def delete_highlighted_folder():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "No folder selected")
        return
    folder_path = tree.item(selected_item, "values")[1]
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
    if subfolder_var.get():
        display_folder_details()

def toggle_check(event):
    item = tree.identify_row(event.y)
    if "checked" in tree.item(item, "tags"):
        tree.item(item, tags=("unchecked",))
    else:
        tree.item(item, tags=("checked",))
    if subfolder_var.get():
        display_folder_details()

def display_folder_details():
    dir_path = entry_dir_path.get()
    if not os.path.isdir(dir_path):
        messagebox.showerror("Error", "Invalid directory path selected")
        return
    choice = combo_sort_choice.get()
    include_subfolders = subfolder_var.get()
    if choice == "Size":
        sort_key = 2
    elif choice == "File quantity":
        sort_key = 3
    elif choice == "Oldest file date":
        sort_key = 4
    else:
        sort_key = 2
    folder_details, total_size, _, _, _ = list_folders(dir_path, include_subfolders)
    sorted_folders = sorted(
        folder_details, key=lambda x: x[sort_key], reverse=(sort_key != 4)
    )
    tree.delete(*tree.get_children())
    for name, path, size, count, mod_time, content_types in sorted_folders:
        size_str = convert_size(size)
        oldest_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(mod_time))
        icon = icon_dict.get(get_icon_type(content_types), default_icon)
        tree.insert(
            "",
            "end",
            values=(name, path, size_str, count, oldest_time_str),
            image=icon,
            tags=("unchecked",),
        )
    total_space = shutil.disk_usage(dir_path).total
    update_storage_bar(total_size, total_space)

def on_display_setting_change(event):
    display_folder_details()

def on_subfolder_check():
    display_folder_details()

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

def get_icon_type(content_types):
    max_type = max(content_types, key=content_types.get)
    return max_type if content_types[max_type] > 0 else "others"

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
        result_frame.config(bg="black")
        bar_frame.config(bg="black")
        label_dir_path.config(bg="black", fg="white")
        label_sort_choice.config(bg="black", fg="white")
        subfolder_check.config(bg="black", fg="white", selectcolor="black")
        button_browse.config(bg="grey", fg="white")
        button_display.config(bg="grey", fg="white")
        button_delete.config(bg="grey", fg="white") # type: ignore
        theme_button.config(bg="grey", fg="white")
        bar_label.config(bg="black", fg="white")
    else:
        app.config(bg="white")
        result_frame.config(bg="white")
        bar_frame.config(bg="white")
        label_dir_path.config(bg="white", fg="black")
        label_sort_choice.config(bg="white", fg="black")
        subfolder_check.config(bg="white", fg="black", selectcolor="white")
        button_browse.config(bg="grey", fg="black")
        button_display.config(bg="grey", fg="black")
        # Comment out the line since "button_delete" is not defined
        # button_delete.config(bg="grey", fg="black")
        theme_button.config(bg="grey", fg="black")
        bar_label.config(bg="white", fg="black")
        
# Add the following code to set the color theme to match the color of the Windows API
def set_windows_color_theme():
    app.config(bg="SystemButtonFace")
    result_frame.config(bg="SystemButtonFace")
    bar_frame.config(bg="SystemButtonFace")
    label_dir_path.config(bg="SystemButtonFace", fg="SystemButtonText")
    label_sort_choice.config(bg="SystemButtonFace", fg="SystemButtonText")
    subfolder_check.config(bg="SystemButtonFace", fg="SystemButtonText", selectcolor="SystemButtonFace")
    button_browse.config(bg="ButtonFace", fg="ButtonText")
    button_display.config(bg="ButtonFace", fg="ButtonText")
    # Comment out the line since "button_delete" is not defined
    # button_delete.config(bg="ButtonFace", fg="ButtonText")
    theme_button.config(bg="ButtonFace", fg="ButtonText")
    bar_label.config(bg="SystemButtonFace", fg="SystemButtonText")

def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

def on_double_click(event):
    item = tree.identify_row(event.y)
    if not item:
        return
    folder_path = tree.item(item, "values")[1]
    if not os.path.isdir(folder_path):
        return
    children, _, _, _, _ = list_folders(folder_path, recursive=False)
    tree.delete(*tree.get_children(item))
    for name, path, size, count, mod_time, content_types in children:
        size_str = convert_size(size)
        oldest_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(mod_time))
        icon = icon_dict.get(get_icon_type(content_types), default_icon)
        tree.insert(
            item,
            "end",
            values=(name, path, size_str, count, oldest_time_str),
            image=icon,
            tags=("unchecked",),
        )

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

label_sort_choice = tk.Label(frame, text="Sort by:")
label_sort_choice.grid(row=1, column=0, padx=5, pady=5)

combo_sort_choice = ttk.Combobox(frame, values=["Size", "File quantity", "Oldest file date"])
combo_sort_choice.grid(row=1, column=1, padx=5, pady=5)
combo_sort_choice.current(0)
combo_sort_choice.bind("<<ComboboxSelected>>", on_display_setting_change)

subfolder_var = tk.BooleanVar()
subfolder_check = tk.Checkbutton(frame, text="Include Subfolders", variable=subfolder_var, command=on_subfolder_check)
subfolder_check.grid(row=1, column=2, padx=5, pady=5)

button_display = tk.Button(frame, text="Display", command=display_folder_details)
button_display.grid(row=2, column=1, padx=5, pady=5)

use_recycle_bin_var = tk.BooleanVar()
recycle_bin_check = tk.Checkbutton(frame, text="Use Recycle Bin", variable=use_recycle_bin_var)
recycle_bin_check.grid(row=2, column=2, padx=5, pady=5)

theme_button = tk.Button(frame, text="Toggle Theme", command=toggle_color_theme)
theme_button.grid(row=2, column=0, padx=5, pady=5)

result_frame = tk.Frame(app)
result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(result_frame, columns=("Name", "Path", "Size", "Files", "Oldest"), show="headings")
tree.heading("Name", text="Name")
tree.heading("Path", text="Path")
tree.heading("Size", text="Size")
tree.heading("Files", text="Files")
tree.heading("Oldest", text="Oldest File Date")
tree.pack(fill=tk.BOTH, expand=True)

tree.bind("<Double-1>", on_double_click)
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
