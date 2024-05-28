#File Project Prototype 2
import os
import time

def get_file_info(file_path):
    """Return the size and modification time of a file."""
    file_size = os.path.getsize(file_path)
    mod_time = os.path.getmtime(file_path)
    return file_size, mod_time

def get_folder_details(folder_path):
    """Return the total size, file count, and oldest file time in a folder."""
    total_size = 0
    file_count = 0
    oldest_time = time.time()
    
    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_size, mod_time = get_file_info(file_path)
            
            total_size += file_size
            file_count += 1
            if mod_time < oldest_time:
                oldest_time = mod_time
    
    return total_size, file_count, oldest_time

def list_folders(directory):
    """List all folders with their total size, file count, and oldest file time."""
    folder_details = []
    
    for root, dirs, _ in os.walk(directory):
        for dirname in dirs:
            folder_path = os.path.join(root, dirname)
            total_size, file_count, oldest_time = get_folder_details(folder_path)
            folder_details.append((folder_path, total_size, file_count, oldest_time))
    
    return folder_details

def main():
    dir_path = input("Enter the directory path: ")
    if not os.path.isdir(dir_path):
        print("Invalid directory path")
        return
    
    choice = input("Organize folders by (1) Size, (2) File quantity, or (3) Oldest file date? Enter 1, 2, or 3: ")
    
    folder_details = list_folders(dir_path)
    
    if choice == '1':
        sorted_folders = sorted(folder_details, key=lambda x: x[1], reverse=True)
        sort_by = "size"
    elif choice == '2':
        sorted_folders = sorted(folder_details, key=lambda x: x[2], reverse=True)
        sort_by = "file quantity"
    elif choice == '3':
        sorted_folders = sorted(folder_details, key=lambda x: x[3])
        sort_by = "oldest file date"
    else:
        print("Invalid choice")
        return
    
    print(f"Folders sorted by {sort_by}:")
    for folder_path, total_size, file_count, oldest_time in sorted_folders:
        print(f"Folder: {folder_path}")
        print(f"  Total size: {total_size / (1024 * 1024):.2f} MB")
        print(f"  File count: {file_count}")
        print(f"  Oldest file date: {time.ctime(oldest_time)}")
        print()

if __name__ == "__main__":
    main()
