import os
import time
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import ctypes
from ctypes import wintypes
import sys
import win32api
import win32gui
import win32con
import win32process
import win32clipboard
from send2trash import send2trash


# Define constants
SHGFI_ICON = 0x000000100
SHGFI_SMALLICON = 0x000000001
SHGFI_LARGEICON = 0x000000000

class SHFILEINFO(ctypes.Structure):
    _fields_ = [("hIcon", wintypes.HICON),
                ("iIcon", wintypes.INT),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", wintypes.WCHAR * 260),
                ("szTypeName", wintypes.WCHAR * 80)]

# Define the SHGetFileInfo function
def get_file_icon(file_path, large_icon=True):
    try:
        # Prepare buffers
        shinfo = wintypes.SHFILEINFO()
        
        # Get icon
        ctypes.windll.shell32.SHGetFileInfoW(
            file_path, 0, ctypes.byref(shinfo), ctypes.sizeof(shinfo), SHGFI_ICON | (SHGFI_LARGEICON if large_icon else SHGFI_SMALLICON)
        )
        hIcon = shinfo.hIcon

        if hIcon == 0:
            print(f"No icon found for file: {file_path}")
            return None

        # Extract icon to PIL Image
        hdc = win32gui.GetDC(0)
        hdc_mem = win32gui.CreateCompatibleDC(hdc)
        hbm = win32gui.CreateCompatibleBitmap(hdc, 32, 32)
        old_hbm = win32gui.SelectObject(hdc_mem, hbm)
        
        win32gui.DrawIconEx(hdc, 0, 0, hIcon, 32, 32, 0, 0, win32con.DI_NORMAL)
        bmpinfo = win32gui.GetObject(hbm)
        
        # Convert to PIL Image
        bmp = Image.frombytes('RGB', (bmpinfo.bmWidth, bmpinfo.bmHeight), win32gui.GetBitmapBits(hbm, True))
        win32gui.ReleaseDC(0, hdc)
        win32gui.DeleteObject(hbm)
        win32gui.DeleteDC(hdc_mem)
        
        return ImageTk.PhotoImage(bmp)
    except Exception as e:
        print(f"Error extracting icon for {file_path}: {e}")
        return None

icon_cache = {}

def get_icon_for_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in icon_cache:
        return icon_cache[ext]
    
    icon = get_file_icon(file_path)
    if icon:
        icon_cache[ext] = icon
    return icon



def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        entry_dir_path.delete(0, tk.END)
        entry_dir_path.insert(0, directory)
        display_folder_details()

def open_temp_folder():
    temp_dir = os.getenv("TEMP")
    if temp_dir:
        subprocess.Popen(f'explorer "{temp_dir}"')

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
                if ctypes.windll.shell32.IsUserAnAdmin():
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

    # Update storage bar
    folder_size = get_directory_size(dir_path)
    total_drive_space = get_total_drive_space()
    update_storage_bar(folder_size, total_drive_space)

def insert_directory_tree(parent, directory):
    for entry in os.scandir(directory):
        entry_type = "dir" if entry.is_dir() else "file"
        size_str = convert_size(entry.stat().st_size)
        mod_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(entry.stat().st_mtime))
        
        # Get icon for the file
        icon = get_file_icon(entry.path) if not entry.is_dir() else None
        
        # Insert the item into the tree
        try:
            node = tree.insert(parent, "end", text=entry.name, values=(entry.path, size_str, mod_time_str), tags=(entry_type,), image=icon)
        except tk.TclError as e:
            print(f"Error inserting {entry.name}: {e}")
            node = tree.insert(parent, "end", text=entry.name, values=(entry.path, size_str, mod_time_str), tags=(entry_type,))
        
        # Add a dummy child to make the folder expandable
        if entry.is_dir():
            tree.insert(node, "end", text="dummy", tags=("dummy",))  # Add a dummy child to make the folder expandable


def on_expand(event):
    item = tree.focus()
    if not item:
        return

    path = tree.item(item, "values")[0]
    
    if not os.path.isdir(path):
        return
    
    # Remove all dummy children of the expanded item
    for child in tree.get_children(item):
        if "dummy" in tree.item(child, "tags"):
            tree.delete(child)
    
    # Reinsert the contents of the directory
    insert_directory_tree(item, path)


def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_total_drive_space():
    total, used, free = shutil.disk_usage(os.path.splitdrive(entry_dir_path.get())[0])
    return total

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

def convert_size_to_bytes(size_str):
    size, unit = size_str.split()
    size = float(size)
    unit = unit.lower()
    if unit == "bytes":
        return size
    elif unit == "kb":
        return size * 1024
    elif unit == "mb":
        return size * 1024 ** 2
    elif unit == "gb":
        return size * 1024 ** 3
    elif unit == "tb":
        return size * 1024 ** 4
    return size

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
        button_browse.config(bg="grey", fg="black")
        button_display.config(bg="grey", fg="black")
        theme_button.config(bg="grey", fg="black")
        bar_label.config(bg="white", fg="black")

def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

def sort_tree_column(col, reverse):
    # Get the items in the tree
    items = [(tree.set(k, col), k) for k in tree.get_children('')]
    
    # Sort items
    items.sort(reverse=reverse)
    
    # Rearrange items
    for index, (val, k) in enumerate(items):
        tree.move(k, '', index)
    
    # Update column heading to reflect the sorting order
    tree.heading(col, command=lambda: sort_tree_column(col, not reverse))

def run_health_checks():
    # Define the PowerShell script name and path
    script_name = "write_commands.ps1"
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    
    # Verify the file exists
    if not os.path.isfile(script_path):
        messagebox.showerror("Error", f"PowerShell script not found: {script_path}")
        return

    # Prepare the PowerShell command
    command = f"powershell.exe -ExecutionPolicy Bypass -NoExit -File \"{script_path}\""
    
    # Check if running as admin and execute the script
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "powershell.exe", command, None, 1
        )
    else:
        subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

def open_file():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "No file selected")
        return
    file_path = tree.item(selected_item, "values")[0]
    try:
        subprocess.Popen(f'explorer "{file_path}"')
    except Exception as e:
        messagebox.showerror("Error", f"Error opening {file_path}: {e}")

def rename_file():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "No file selected")
        return
    file_path = tree.item(selected_item, "values")[0]
    new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=os.path.basename(file_path))
    if new_name:
        try:
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            os.rename(file_path, new_path)
            tree.item(selected_item, text=new_name, values=(new_path, *tree.item(selected_item, "values")[1:]))
        except Exception as e:
            messagebox.showerror("Error", f"Error renaming {file_path}: {e}")

def show_properties():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "No file selected")
        return
    file_path = tree.item(selected_item, "values")[0]
    try:
        subprocess.Popen(f'explorer /select,"{file_path}"')
    except Exception as e:
        messagebox.showerror("Error", f"Error showing properties for {file_path}: {e}")


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


# Create the Tkinter UI
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
button_display.grid(row=1, column=1, padx=5, pady=5)

button_open_temp = tk.Button(frame, text="Open Temp Folder", command=open_temp_folder)
button_open_temp.grid(row=1, column=2, padx=5, pady=5)

use_recycle_bin_var = tk.BooleanVar()
recycle_bin_check = tk.Checkbutton(frame, text="Use Recycle Bin", variable=use_recycle_bin_var)
recycle_bin_check.grid(row=2, column=2, padx=5, pady=5)

theme_button = tk.Button(frame, text="Toggle Theme", command=toggle_color_theme)
theme_button.grid(row=2, column=0, padx=5, pady=5)

button_run_health_checks = tk.Button(frame, text="Run Health Checks", command=run_health_checks)
button_run_health_checks.grid(row=3, column=0, padx=5, pady=5)

result_frame = tk.Frame(app)
result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

# Treeview with scrollbars
tree = ttk.Treeview(result_frame, columns=("Name", "Path", "Size", "Oldest"), show="tree headings")
tree.heading("#0", text="Name")
tree.heading("Path", text="Path")
tree.heading("Size", text="Size")
tree.heading("Oldest", text="Oldest")

# Configure the column headings to use the sort function
tree.heading("Name", command=lambda: sort_tree_column("Name", False))
tree.heading ("Path", command=lambda: sort_tree_column("Path", False))
tree.heading("Size", command=lambda: sort_tree_column("Size", False))
tree.heading("Oldest", command=lambda: sort_tree_column("Oldest", False))

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Vertical scrollbar
vsb = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
vsb.pack(fill='y', side='right')
tree.configure(yscrollcommand=vsb.set)

# Horizontal scrollbar
hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=tree.xview)
hsb.pack(fill='x', side='bottom')
tree.configure(xscrollcommand=hsb.set)

tree.bind("<Double-1>", on_expand)  # Bind the double-click event
tree.bind("<Button-1>", toggle_check)

bar_frame = tk.Frame(app)
bar_frame.pack(pady=10)

bar_var = tk.DoubleVar()
storage_bar = ttk.Progressbar(bar_frame, variable=bar_var, maximum=100)
storage_bar.pack(fill=tk.BOTH, expand=True)

bar_label = tk.Label(bar_frame, text="")
bar_label.pack()

# Define the context menu with additional options
context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(label="Open", command=open_file)
context_menu.add_command(label="Rename", command=rename_file)
context_menu.add_command(label="Properties", command=show_properties)
context_menu.add_command(label="Delete", command=delete_highlighted_folder)

# Bind the right-click event to show the context menu
tree.bind("<Button-3>", show_context_menu)

current_theme = "light"
set_color_theme(current_theme)

app.mainloop()
