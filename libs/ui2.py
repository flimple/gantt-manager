import customtkinter as ctk

def get_recent_projects() -> ctk.CTk:
    # Toplevel et pas Tk : une seule fenêtre racine par programme
    app = ctk.CTk()
    app.title("Recent Projects")
    app.geometry("650x450")
    app.resizable(False, False)

    parent_frame = ctk.CTkFrame(app)
    parent_frame.pack(fill="both", expand=True, pady=15)

    manip_frame = ctk.CTkFrame(parent_frame, bg_color="lightgray", width=180)
    manip_frame.pack(fill="y", side=ctk.LEFT, padx=10)
    manip_frame.pack_propagate(False)  # Garde la largeur fixe malgré la taille des boutons

    # on_create / on_open_existing : à brancher plus tard, quand on aura le système IO
    create_new_button = ctk.CTkButton(manip_frame, text="Create New Project")
    create_new_button.pack(pady=(40, 10))
    open_existing = ctk.CTkButton(manip_frame, text="Open Existing Project")
    open_existing.pack(pady=(10, 40))

    recent_prjs_frame = ctk.CTkFrame(parent_frame, bg_color="lightgray")
    recent_prjs_frame.pack(fill="both", expand=True, side=ctk.LEFT, padx=10)
    app.attributes("-topmost", True)

    return app