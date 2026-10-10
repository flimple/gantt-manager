import customtkinter as ctk
from PIL import Image
from libs import font_manager as fontM
from libs import ui_util as uiTool

def get_recent_projects() -> ctk.CTk:
    # Toplevel et pas Tk : une seule fenêtre racine par programme
    app = ctk.CTk(fg_color=("#F3F5F9", "#12161C"))
    app.title("Ganttify - Recent Projects")
    app.geometry("650x500")
    app.resizable(False, False)

    title_frame = ctk.CTkFrame(app, height=90, border_width=0, fg_color=("#FFFFFF", "#181D25"), bg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 0))
    title_frame.pack_propagate(False)

    logo = ctk.CTkLabel(title_frame, text="", image=ctk.CTkImage(light_image=Image.open("assets/logo_form.png"), size=(60,60)))
    logo.pack(pady=3, side=ctk.LEFT, padx=20)

    title_logo = ctk.CTkLabel(title_frame, text="", image=ctk.CTkImage(light_image=Image.open("assets/title_light.png"), dark_image=Image.open("assets/title_dark.png"), size=(240,60)))
    title_logo.pack(padx=10, side=ctk.LEFT)
    
    parent_frame = ctk.CTkFrame(app, border_width=0, fg_color="transparent", bg_color="transparent")
    parent_frame.pack(fill="both", expand=True, pady=(5, 15))

    manip_frame = ctk.CTkFrame(parent_frame, fg_color=("#FFFFFF", "#1C222B"), bg_color="transparent", width=180, border_width=0)
    manip_frame.pack(fill="y", side=ctk.LEFT, padx=10)
    manip_frame.pack_propagate(False)

    create_new_button = ctk.CTkButton(manip_frame, text="Create New Project", border_width=0, fg_color=("#2E5A8B", "#5B9BE6"), text_color=("#FFFFFF", "#0B1220"), hover_color=("#234770", "#78AEEE"))
    create_new_button.pack(pady=(90, 10), expand=True)
    open_existing = ctk.CTkButton(manip_frame, text="Open Existing Project", border_width=0, fg_color=("#E3EBF5", "#2A3445"), text_color=("#2E5A8B", "#BFD6F5"), hover_color=("#D3E0F0", "#344058"))
    open_existing.pack(pady=(10, 230), expand=True)

    recent_prjs_frame = ctk.CTkFrame(parent_frame, bg_color="transparent", fg_color=("#FFFFFF", "#1C222B"), border_width=0)
    recent_prjs_frame.pack(fill="both", expand=True, side=ctk.LEFT, padx=10)
    scroll_rect = uiTool.create_viewport(recent_prjs_frame)
    for i in range(30):
        item = ctk.CTkButton(scroll_rect, text=f"Project {i+1}")
        item.pack(fill="x", padx=10, pady=5)

    app.attributes("-topmost", True)

    return app