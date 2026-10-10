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

def create_viewport(parent_frame, horizontal: bool = False) -> ctk.CTkFrame:
    container = ctk.CTkFrame(parent_frame, fg_color="transparent")
    container.pack(fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    canvas = ctk.CTkCanvas(container, highlightthickness=0, bd=0, bg=resolve_bg(parent_frame))
    vbar = ctk.CTkScrollbar(container, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent")

    canvas.grid(row=0, column=0, sticky="nsew")
    vbar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vbar.set)

    if horizontal:
        hbar = ctk.CTkScrollbar(container, orientation="horizontal", command=canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=hbar.set)

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _fit(_event=None):
        width = canvas.winfo_width()
        if horizontal:
            # never narrower than the viewport, but grow if content is wider
            width = max(width, scrollable_frame.winfo_reqwidth())
        canvas.itemconfig(window_id, width=width)
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", _fit)
    canvas.bind("<Configure>", _fit)

    def _pointer_inside():
        try:
            w = container.winfo_containing(*container.winfo_pointerxy())
        except Exception:
            return False
        return w is not None and str(w).startswith(str(container))

    def _on_wheel(e):
        if not _pointer_inside():
            return
        step = int(-e.delta / 120) * 2
        shift_held = bool(e.state & 0x1)
        if horizontal and shift_held:
            if canvas.xview() != (0.0, 1.0):
                canvas.xview_scroll(step, "units")
        elif canvas.yview() != (0.0, 1.0):
            canvas.yview_scroll(step, "units")

    canvas.bind_all("<MouseWheel>", _on_wheel, add="+")

    return scrollable_frame