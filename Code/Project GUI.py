import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

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
    
    if include_subfolders:
        for root, _, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_size, mod_time = get_file_info(file_path)
                
                total_size += file_size
                file_count += 1
                if mod_time < oldest_time:
                    oldest_time = mod_time
    else:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_size, mod_time = get_file_info(file_path)
                total_size += file_size
                file_count += 1
                if mod_time < oldest_time:
                    oldest_time = mod_time
    
    return total_size, file_count, oldest_time

def list_folders(directory, include_subfolders=True):
    """List all folders with their total size, file count, and oldest file time."""
    folder_details = []
    
    if include_subfolders:
        for root, dirs, _ in os.walk(directory):
            for dirname in dirs:
                folder_path = os.path.join(root, dirname)
                total_size, file_count, oldest_time = get_folder_details(folder_path, include_subfolders)
                folder_details.append((folder_path, total_size, file_count, oldest_time))
    else:
        for dirname in next(os.walk(directory))[1]:
            folder_path = os.path.join(directory, dirname)
            total_size, file_count, oldest_time = get_folder_details(folder_path, include_subfolders)
            folder_details.append((folder_path, total_size, file_count, oldest_time))
    
    return folder_details

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        entry_dir_path.delete(0, tk.END)
        entry_dir_path.insert(0, directory)

def display_folder_details():
    dir_path = entry_dir_path.get()
    if not os.path.isdir(dir_path):
        messagebox.showerror("Error", "Invalid directory path")
        return
    
    choice = combo_sort_choice.get()
    include_subfolders = subfolder_var.get()
    
    if choice == "Size":
        sort_key = 1
    elif choice == "File quantity":
        sort_key = 2
    elif choice == "Oldest file date":
        sort_key = 3
    else:
        messagebox.showerror("Error", "Invalid choice")
        return
    
    folder_details = list_folders(dir_path, include_subfolders)
    if sort_key == 3:
        sorted_folders = sorted(folder_details, key=lambda x: x[sort_key])
    else:
        sorted_folders = sorted(folder_details, key=lambda x: x[sort_key], reverse=True)
    
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, f"Folders sorted by {choice}:\n\n")
    for folder_path, total_size, file_count, oldest_time in sorted_folders:
        result_text.insert(tk.END, f"Folder: {folder_path}\n")
        result_text.insert(tk.END, f"  Total size: {total_size / (1024 * 1024):.2f} MB\n")
        result_text.insert(tk.END, f"  File count: {file_count}\n")
        result_text.insert(tk.END, f"  Oldest file date: {time.ctime(oldest_time)}\n\n")

app = tk.Tk()
app.title("Folder Analyzer")

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

subfolder_var = tk.BooleanVar()
subfolder_check = tk.Checkbutton(frame, text="Include Subfolders", variable=subfolder_var)
subfolder_check.grid(row=2, columnspan=3, pady=5)

button_display = tk.Button(frame, text="Display Folder Details", command=display_folder_details)
button_display.grid(row=3, columnspan=3, pady=10)

# Frame for result text and scrollbar
result_frame = tk.Frame(app)
result_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

result_text = tk.Text(result_frame, wrap="word", width=80, height=20)
result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(result_frame, command=result_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

result_text.config(yscrollcommand=scrollbar.set)

app.mainloop()
