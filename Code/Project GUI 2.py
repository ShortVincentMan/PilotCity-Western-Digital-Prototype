import os
import time
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import ctypes
import sys

def get_file_info(file_path):
    """Return the size and modification time of a file."""
    try:
        file_size = os.path.getsize(file_path)
        mod_time = os.path.getmtime(file_path)
        return file_size, mod_time
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return 0, time.time()

def get_folder_details(folder_path, include_subfolders=True):
    """Return the total size, file count, and oldest file time in a folder."""
    total_size = 0
    file_count = 0
    oldest_time = time.time()
    content_types = {'images': 0, 'videos': 0, 'documents': 0, 'games': 0, 'others': 0}
    
    if include_subfolders:
        for root, _, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_size, mod_time = get_file_info(file_path)
                
                total_size += file_size
                file_count += 1
                if mod_time < oldest_time:
                    oldest_time = mod_time
                
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    content_types['images'] += 1
                elif ext in ['.mp4', '.mkv', '.mov', '.avi']:
                    content_types['videos'] += 1
                elif ext in ['.pdf', '.docx', '.txt']:
                    content_types['documents'] += 1
                elif ext in ['.exe', '.iso']:
                    content_types['games'] += 1
                else:
                    content_types['others'] += 1
    else:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_size, mod_time = get_file_info(file_path)
                total_size += file_size
                file_count += 1
                if mod_time < oldest_time:
                    oldest_time = mod_time

                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    content_types['images'] += 1
                elif ext in ['.mp4', '.mkv', '.mov', '.avi']:
                    content_types['videos'] += 1
                elif ext in ['.pdf', '.docx', '.txt']:
                    content_types['documents'] += 1
                elif ext in ['.exe', '.iso']:
                    content_types['games'] += 1
                else:
                    content_types['others'] += 1
    
    return total_size, file_count, oldest_time, content_types

def list_folders(directory, include_subfolders=True):
    """List all folders with their total size, file count, and oldest file time."""
    folder_details = []
    
    if include_subfolders:
        for root, dirs, files in os.walk(directory):
            for dirname in dirs:
                folder_path = os.path.join(root, dirname)
                total_size, file_count, oldest_time, content_types = get_folder_details(folder_path, include_subfolders)
                folder_details.append((dirname, folder_path, total_size, file_count, oldest_time, content_types))
            for filename in files:
                file_path = os.path.join(root, filename)
                file_size, mod_time = get_file_info(file_path)
                folder_details.append((filename, file_path, file_size, 1, mod_time, {'others': 1}))
    else:
        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)
            if os.path.isdir(path):
                total_size, file_count, oldest_time, content_types = get_folder_details(path, include_subfolders)
                folder_details.append((entry, path, total_size, file_count, oldest_time, content_types))
            elif os.path.isfile(path):
                file_size, mod_time = get_file_info(path)
                folder_details.append((entry, path, file_size, 1, mod_time, {'others': 1}))
    
    return folder_details

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        entry_dir_path.delete(0, tk.END)
        entry_dir_path.insert(0, directory)

def delete_selected_folders():
    for item in tree.get_children():
        if tree.item(item, 'tags')[0] == 'checked':
            folder_path = tree.item(item, 'values')[1]
            try:
                if ctypes.windll.shell32.IsUserAnAdmin():
                    shutil.rmtree(folder_path) if os.path.isdir(folder_path) else os.remove(folder_path)
                    tree.delete(item)
                else:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting {folder_path}: {e}")

def delete_highlighted_folder():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "No folder selected")
        return
    
    folder_path = tree.item(selected_item, 'values')[1]
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            shutil.rmtree(folder_path) if os.path.isdir(folder_path) else os.remove(folder_path)
            tree.delete(selected_item)
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting {folder_path}: {e}")

def toggle_check(event):
    item = tree.identify_row(event.y)
    if 'checked' in tree.item(item, 'tags'):
        tree.item(item, tags=('unchecked',))
    else:
        tree.item(item, tags=('checked',))

def display_folder_details():
    dir_path = entry_dir_path.get()
    if not os.path.isdir(dir_path):
        messagebox.showerror("Error", "Invalid directory path")
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
        messagebox.showerror("Error", "Invalid choice")
        return
    
    folder_details = list_folders(dir_path, include_subfolders)
    if sort_key == 4:
        sorted_folders = sorted(folder_details, key=lambda x: x[sort_key])
    else:
        sorted_folders = sorted(folder_details, key=lambda x: x[sort_key], reverse=True)
    
    for item in tree.get_children():
        tree.delete(item)

    for folder_name, folder_path, total_size, file_count, oldest_time, content_types in sorted_folders:
        content = max(content_types, key=content_types.get)
        icon = icon_dict.get(content, default_icon)
        size_display = f"{total_size / (1024 * 1024):.2f} MB"
        tree.insert('', 'end', text=folder_path, values=(folder_name, folder_path, size_display, file_count, time.ctime(oldest_time)), image=icon, tags=('unchecked',))
    
    update_disk_usage_bar(sorted_folders)

def update_disk_usage_bar(folder_details):
    total_size = sum(folder[2] for folder in folder_details)
    total, used, free = shutil.disk_usage('/')
    used_percentage = (total_size / total) * 100
    bar_var.set(used_percentage)
    bar_label.config(text=f"Used by selected folders: {total_size / (1024 * 1024 * 1024):.2f} GB / Total: {total / (1024 * 1024 * 1024):.2f} GB")

def on_subfolder_check():
    display_folder_details()

def on_size_unit_change(*args):
    display_folder_details()

def update_progress_bar(selected_folders):
    total_size = sum(folder[2] for folder in selected_folders)
    total, used, free = shutil.disk_usage('/')
    used_percentage = (total_size / total) * 100
    bar_var.set(used_percentage)
    bar_label.config(text=f"Selected folders use: {total_size / (1024 * 1024 * 1024):.2f} GB / Total: {total / (1024 * 1024 * 1024):.2f} GB")

def toggle_color_theme():
    global current_theme
    current_theme = "light" if current_theme == "dark" else "dark"
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
        bar_label.config(bg="white", fg="black")

def show_context_menu(event):
    selected_item = tree.identify_row(event.y)
    if selected_item:
        tree.selection_set(selected_item)
        context_menu.post(event.x_root, event.y_root)

app = tk.Tk()
app.title("Folder Cleaner")

# Load icons (update these paths to actual icon paths)
try:
    image_icon = ImageTk.PhotoImage(Image.open("images.png"))
    video_icon = ImageTk.PhotoImage(Image.open("videos.png"))
    document_icon = ImageTk.PhotoImage(Image.open("documents.png"))
    game_icon = ImageTk.PhotoImage(Image.open("games.png"))
    other_icon = ImageTk.PhotoImage(Image.open("other.png"))
    default_icon = ImageTk.PhotoImage(Image.open("default.png"))
except Exception as e:
    print(f"Error loading icons: {e}")

icon_dict = {
    'images': image_icon,
    'videos': video_icon,
    'documents': document_icon,
    'games': game_icon,
    'others': other_icon,
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

combo_sort_choice = ttk.Combobox(frame, values=["Size", "File quantity", "Oldest file date"])
combo_sort_choice.grid(row=1, column=1, padx=5, pady=5)
combo_sort_choice.current(0)
combo_sort_choice.bind('<<ComboboxSelected>>', on_size_unit_change)

subfolder_var = tk.BooleanVar()
subfolder_check = tk.Checkbutton(frame, text="Include Subfolders", variable=subfolder_var, command=on_subfolder_check)
subfolder_check.grid(row=2, columnspan=3, pady=5)

size_unit_var = tk.StringVar(value="MB")
size_unit_menu = ttk.Combobox(frame, textvariable=size_unit_var, values=["KB", "MB", "GB"])
size_unit_menu.grid(row=1, column=2, padx=5, pady=5)
size_unit_menu.bind('<<ComboboxSelected>>', on_size_unit_change)

button_display = tk.Button(frame, text="Display Folder Details", command=display_folder_details)
button_display.grid(row=3, columnspan=3, pady=10)

button_delete = tk.Button(frame, text="Delete Selected Folders", command=delete_selected_folders)
button_delete.grid(row=4, columnspan=3, pady=10)

theme_button = tk.Button(frame, text="Toggle Theme", command=toggle_color_theme)
theme_button.grid(row=5, columnspan=3, pady=10)

result_frame = tk.Frame(app)
result_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(result_frame, columns=('folder_name', 'folder_path', 'size', 'file_count', 'oldest_time'), show='headings')
tree.heading('folder_name', text='Folder/File Name')
tree.heading('folder_path', text='Path')
tree.heading('size', text='Size')
tree.heading('file_count', text='File Count')
tree.heading('oldest_time', text='Oldest File Date')
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
tree.bind('<Button-1>', toggle_check)

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

# Create right-click context menu
context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(label="Delete", command=delete_highlighted_folder)
tree.bind("<Button-3>", show_context_menu)

current_theme = "light"
set_color_theme(current_theme)

app.mainloop()
