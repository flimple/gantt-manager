import tkinter as tk

def get_main_page() -> tk.Tk:
    root = tk.Tk()
    root.title = "Gantt Manager"
    root.geometry("1080x720")
    root.state("zoomed")
    #root.attributes("-fullscreen", True)

    canvas = tk.Canvas(root, bg="lightgray")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    viewport = tk.Frame(canvas)

    canvas.create_window((0, 0), window=viewport, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


    return root

def get_recent_projects() -> tk.Tk:
    root = tk.Tk()
    root.title = "Recent Projects"
    root.geometry("500x450")
    root.resizable(False, False)

    parent_frame = tk.Frame(root)
    parent_frame.pack(fill="both", expand=True, pady=15)

    manip_frame = tk.Frame(parent_frame, bg="lightgray")
    manip_frame.pack(fill="both", expand=True, side=tk.LEFT, padx=10)

    create_new_button = tk.Button(manip_frame, text="Create New Project")
    create_new_button.pack(pady=(40, 10))
    open_existing = tk.Button(manip_frame, text="Open Existing Project")
    open_existing.pack(pady=(10, 40))

    recent_prjs_frame = tk.Frame(parent_frame, bg="lightgray")
    recent_prjs_frame.pack(fill="both", expand=True, side=tk.LEFT, padx=10)
    root.attributes("-topmost", True)

    return root