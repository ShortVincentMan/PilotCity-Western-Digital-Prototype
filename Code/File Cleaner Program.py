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
        frame.config(bg="black")
        result_frame.config(bg="black")
        bar_frame.config(bg="black")
        label_dir_path.config(bg="black", fg="white")
        label_sort_choice.config(bg="black", fg="white")
        subfolder_check.config(bg="black", fg="white", selectcolor="black")
        button_browse.config(bg="grey", fg="white")
        button_display.config(bg="grey", fg="white")
        button_delete.config(bg="grey", fg="white")
        theme_button.config(bg="grey", fg="white")
        bar_label.config(bg="black", fg="white")
    else:
        app.config(bg="white")
        frame.config(bg="white")
        result_frame.config(bg="white")
        bar_frame.config(bg="white")
        label_dir_path.config(bg="white", fg="black")
        label_sort_choice.config(bg="white", fg="black")
        subfolder_check.config(bg="white", fg="black", selectcolor="white")
        button_browse.config(bg="lightgrey", fg="black")
        button_display.config(bg="lightgrey", fg="black")
        button_delete.config(bg="lightgrey", fg="black")
        theme_button.config(bg="lightgrey", fg="black")
        bar_label.config(bg="white", fg="black")


def show_context_menu(event):
    selected_item = tree.identify_row(event.y)
    if selected_item:
        tree.selection_set(selected_item)
        context_menu.post(event.x_root, event.y_root)


app = tk.Tk()
app.title("Folder Cleaner")

try:
    image_icon = ImageTk.PhotoImage(Image.open("images.png"))
    video_icon = ImageTk.PhotoImage(Image.open("videos.png"))
    document_icon = ImageTk.PhotoImage(Image.open("documents.png"))
    game_icon = ImageTk.PhotoImage(Image.open("games.png"))
    other_icon = ImageTk.PhotoImage(Image.open("others.png"))
    default_icon = ImageTk.PhotoImage(Image.open("default.png"))
except Exception as e:
    print(f"Error loading icons: {e}")

icon_dict = {
    "images": image_icon,
    "videos": video_icon,
    "documents": document_icon,
    "games": game_icon,
    "others": other_icon,
}

frame = tk.Frame(app)
frame.pack(padx=10, pady=10)

label_dir_path = tk.Label(frame, text="Directory Path:")
label_dir_path.grid(row=0, column=0, padx=5, pady=5)

entry_dir_path = tk.Entry(frame, width=50)
entry_dir_path.grid(row=0, column=1, padx=5, pady=5)

button_browse = tk.Button(frame, text="Browse", command=browse_directory)
button_browse.grid(row=0, column=2, padx=5, pady=5)

label_sort_choice = tk.Label(frame, text="Sort by:")
label_sort_choice.grid(row=1, column=0, padx=5, pady=5)

combo_sort_choice = ttk.Combobox(
    frame, values=["Size", "File quantity", "Oldest file date"]
)
combo_sort_choice.grid(row=1, column=1, padx=5, pady=5)
combo_sort_choice.current(0)
combo_sort_choice.bind("<<ComboboxSelected>>", on_display_setting_change)

subfolder_var = tk.BooleanVar()
subfolder_check = tk.Checkbutton(
    frame, text="Analyze Subfolders", variable=subfolder_var, command=on_subfolder_check
)
subfolder_check.grid(row=2, columnspan=3, pady=5)

button_display = tk.Button(
    frame, text="Display Folder Details", command=display_folder_details
)
button_display.grid(row=3, columnspan=3, pady=10)

button_delete = tk.Button(
    frame, text="Delete Selected Folders", command=delete_selected_folders
)
button_delete.grid(row=4, columnspan=3, pady=10)

use_recycle_bin_var = tk.BooleanVar()
use_recycle_bin_check = tk.Checkbutton(
    frame,
    text="Send to Recycle Bin instead of permanently deleting files",
    variable=use_recycle_bin_var,
)
use_recycle_bin_check.grid(row=5, pady=5)

theme_button = tk.Button(frame, text="Toggle Theme", command=toggle_color_theme)
theme_button.grid(row=5, column=2, pady=10)

result_frame = tk.Frame(app)
result_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(
    result_frame,
    columns=("folder_name", "folder_path", "size", "file_count", "oldest_time"),
    show="headings",
)
tree.heading("folder_name", text="Folder/File Name")
tree.heading("folder_path", text="Path")
tree.heading("size", text="Size")
tree.heading("file_count", text="File Count")
tree.heading("oldest_time", text="Oldest Modification Time")
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
tree.bind("<Button-1>", toggle_check)

scrollbar = tk.Scrollbar(result_frame, command=tree.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.config(yscrollcommand=scrollbar.set)

bar_frame = tk.Frame(app)
bar_frame.pack(padx=10, pady=10, fill=tk.X, expand=True)

bar_var = tk.DoubleVar()
bar = ttk.Progressbar(bar_frame, variable=bar_var, maximum=100)
bar.pack(fill=tk.X, expand=True)

bar_label = tk.Label(bar_frame, text="")
bar_label.pack()

context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(label="Delete", command=delete_highlighted_folder)
tree.bind("<Button-3>", show_context_menu)

current_theme = "light"
set_color_theme(current_theme)

app.mainloop()
