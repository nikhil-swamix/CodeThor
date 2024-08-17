import tkinter as tk
from tkinter import filedialog, ttk
import os


def select_folders():
    folder_paths = filedialog.askdirectory(title="Select Folders", initialdir=os.getcwd(), mustexist=True)
    if folder_paths:
        folder_name = os.path.basename(folder_paths)
        var = tk.BooleanVar(value=True)
        checkbox = ttk.Checkbutton(checkbox_frame, text=folder_name, variable=var)
        checkbox.pack(anchor="w")
        checkboxes.append((checkbox, var, folder_paths))


def get_selected_folders():
    selected_folders = [folder_path for _, var, folder_path in checkboxes if var.get()]
    print("Selected Folders:", selected_folders)


root = tk.Tk()
root.title("Folder Selection")
root.geometry("400x300")
root.configure(bg="#F0F0F0")

style = ttk.Style()
style.configure("TCheckbutton", background="#F0F0F0")

checkboxes = []

# Pre-populate the list with some folders
pre_populated_folders = ["/path/to/folder1", "/path/to/folder2", "/path/to/folder3"]
for folder_path in pre_populated_folders:
    folder_name = os.path.basename(folder_path)
    var = tk.BooleanVar(value=True)
    checkbox = ttk.Checkbutton(root, text=folder_name, variable=var)
    checkbox.pack(anchor="w")
    checkboxes.append((checkbox, var, folder_path))

checkbox_frame = ttk.Frame(root)
checkbox_frame.pack(padx=20, pady=10, fill="both", expand=True)

button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

select_button = ttk.Button(button_frame, text="Select Folders", command=select_folders)
select_button.pack(side="left", padx=5)

get_selected_button = ttk.Button(button_frame, text="Get Selected Folders", command=get_selected_folders)
get_selected_button.pack(side="left", padx=5)

root.mainloop()
