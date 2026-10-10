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
    container = ctk.CTkFrame(parent_frame, fg_color="transparent")
    container.pack(fill="both", expand=True)

    canvas = ctk.CTkCanvas(container, highlightthickness=0, bd=0, bg=resolve_bg(parent_frame))
    scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _pointer_inside():
        try:
            w = container.winfo_containing(*container.winfo_pointerxy())
        except Exception:
            return False
        return w is not None and str(w).startswith(str(container))

    def _scroll(units):
        if canvas.yview() != (0.0, 1.0) and _pointer_inside():
            canvas.yview_scroll(units, "units")

    def _on_wheel(e):
        if canvas.yview() != (0.0, 1.0) and _pointer_inside():
            canvas.yview_scroll(int(-e.delta / 120) * 2, "units")

    canvas.bind_all("<MouseWheel>", _on_wheel, add="+")

    return scrollable_frame