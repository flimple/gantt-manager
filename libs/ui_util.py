import customtkinter as ctk

def resolve_bg(widget):
    w = widget
    while w is not None:
        try:
            color = w.cget("fg_color")
            if color != "transparent":
                return w._apply_appearance_mode(color)
        except Exception:
            pass
        w = w.master
    return "#000000"  

def create_viewport(parent_frame) -> ctk.CTkFrame:
    container = ctk.CTkFrame(parent_frame, fg_color="transparent", bg_color="transparent")
    container.pack(fill="both", expand=True)
    canvas = ctk.CTkCanvas(container, highlightthickness=0, bd=0, bg=resolve_bg(parent_frame))
    scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=canvas.yview, fg_color="transparent", bg_color="transparent")
    scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent", bg_color="transparent")
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.bind(
        "<Configure>",
        lambda event: canvas.itemconfig(window_id, width=event.width)
    )
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return scrollable_frame