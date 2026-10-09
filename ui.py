import tkinter as tk

def get_main_page() -> tk.Tk:
    root = tk.Tk()
    root.title = "Gantt Manager"
    root.geometry("1080x720")
    root.state("zoomed")
    #root.attributes("-fullscreen", True)

    button = tk.Button(root, text="Click Me")
    button.pack(pady=20)

    return root

def get_recent_projects() -> tk.Tk:
    root = tk.Tk()
    root.title = "Recent Projects"
    root.geometry("300x600")
    root.resizable(False, False)

    parent_frame = tk.Frame(root)
    parent_frame.pack(pady=15)

    manip_frame = tk.Frame(parent_frame)
    manip_frame.pack(side=tk.LEFT, padx=10)

    create_new_button = tk.Button(manip_frame, text="Create New Project")
    create_new_button.pack(pady=(40, 10))
    open_existing = tk.Button(manip_frame, text="Open Existing Project")
    open_existing.pack(pady=(10, 40))

    recent_prjs_frame = tk.Frame(parent_frame)
    recent_prjs_frame.pack(side=tk.LEFT, padx=10)
    root.attributes("-topmost", True)

    return root