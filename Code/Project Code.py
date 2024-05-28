import os
import time

def get_file_info(file_path):
    """Return the size and modification time of a file."""
    file_size = os.path.getsize(file_path)
    mod_time = os.path.getmtime(file_path)
    return file_size, mod_time

def get_folder_size(folder_path):
    """Return the total size of all files in a folder."""
    total_size = 0
    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            total_size += os.path.getsize(file_path)
    return total_size

def find_oldest_file(directory):
    oldest_file = None
    oldest_time = time.time()
    
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            _, mod_time = get_file_info(file_path)
            
            if mod_time < oldest_time:
                oldest_time = mod_time
                oldest_file = file_path
    
    return oldest_file, oldest_time

def find_largest_file(directory):
    largest_file = None
    largest_size = 0
    
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_size, _ = get_file_info(file_path)
            
            if file_size > largest_size:
                largest_size = file_size
                largest_file = file_path
    
    return largest_file, largest_size

def find_largest_folder(directory):
    largest_folder = None
    largest_size = 0
    
    for root, dirs, _ in os.walk(directory):
        for dirname in dirs:
            folder_path = os.path.join(root, dirname)
            folder_size = get_folder_size(folder_path)
            
            if folder_size > largest_size:
                largest_size = folder_size
                largest_folder = folder_path
    
    return largest_folder, largest_size

def main():
    dir_path = input("Enter the directory path: ")
    if not os.path.isdir(dir_path):
        print("Invalid directory path")
        return
    
    choice = input("Do you want to find the (1) Oldest file, (2) Largest file, or (3) Largest folder? Enter 1, 2, or 3: ")
    
    if choice == '1':
        oldest_file, oldest_time = find_oldest_file(dir_path)
        if oldest_file:
            print(f"The oldest file is: {oldest_file}")
            print(f"Last modified time: {time.ctime(oldest_time)}")
        else:
            print("No files found in the directory.")
    
    elif choice == '2':
        largest_file, largest_size = find_largest_file(dir_path)
        if largest_file:
            print(f"The largest file is: {largest_file}")
            print(f"Size: {largest_size / (1024 * 1024):.2f} MB")
        else:
            print("No files found in the directory.")
    
    elif choice == '3':
        largest_folder, largest_size = find_largest_folder(dir_path)
        if largest_folder:
            print(f"The largest folder is: {largest_folder}")
            print(f"Total size: {largest_size / (1024 * 1024):.2f} MB")
        else:
            print("No folders found in the directory.")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()