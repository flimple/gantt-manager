import customtkinter as ctk
from PIL import Image
from libs import font_manager as fontM
from libs import ui_util as uiTool

def get_recent_projects_gui() -> ctk.CTk:
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
    prjs_rect = uiTool.create_viewport(recent_prjs_frame)
    
    app.attributes("-topmost", True)

    return app, prjs_rect

def get_dash_board_gui() -> ctk.CTk:
    app = ctk.CTk(fg_color=("#F3F5F9", "#12161C"))
    app.title("Ganttify - Classifier les taches et gerer les roles.")
    app.minsize(1080, 720)
    app.state("zoomed")

    #region Header ui MAIN

    header = ctk.CTkFrame(app, fg_color=("#FFFFFF", "#181D25"), bg_color="transparent", height=50)
    header.pack(fill="x", expand=False)
    header.pack_propagate(False)

    title = ctk.CTkFrame(header, fg_color="transparent", bg_color="transparent", width=300)
    title.pack(fill="y", expand=False, side=ctk.LEFT, padx=(3, 0))
    title.pack_propagate(False)
    title_logo = ctk.CTkLabel(title, text="", fg_color="transparent", bg_color="transparent", image=ctk.CTkImage(light_image=Image.open("assets/logo_form.png"), size=(40,40)))
    title_logo.pack(side=ctk.LEFT, padx=(2, 8))
    title_text = ctk.CTkLabel(title, text="", fg_color="transparent", bg_color="transparent", image=ctk.CTkImage(light_image=Image.open("assets/title_light.png"), dark_image=Image.open("assets/title_dark.png"), size=(120,30)))
    title_text.pack(side=ctk.LEFT, pady=(10,0))

    toggle_mode = ctk.CTkButton(header, text="", height=35, width=35, corner_radius=18)
    toggle_mode.pack()

    #endregion

    main_container = ctk.CTkFrame(app, fg_color="transparent", bg_color="transparent")
    main_container.pack(fill="both", expand=True)

    gantt_visualizer = ctk.CTkFrame(main_container, fg_color=("#FFFFFF", "#1C222B"), bg_color="transparent")
    gantt_visualizer.pack(pady=10, padx=10, fill="both", expand=True)
    return app


class Main_Dashboard:
    def __init__(self):
        self.gui : ctk.CTk = get_dash_board_gui()

    def start_loop(self):
        # Ctk a des processus pour gerer les themes etc avant la loop donc on attend pour appliquer le mode zoomed
        self.gui.after(10, lambda: self.gui.state("zoomed"))
        self.gui.mainloop()


class Recent_Projects_Window:
    recent_projects : ctk.CTkFrame
    gui : ctk.CTk
    projects_data : dict | None

    def __init__(self):
        self.gui, self.recent_projects = get_recent_projects_gui()
        self.projects_data = None

    def refresh_projects(self):
            if not self.projects_data:
                return
            for _, pData in self.projects_data.items():
                pass

    def start_loop(self):
            self.gui.mainloop()

    def assign_projects(self, new_projects : dict, refresh : bool = False):
        self.projects_data = new_projects.copy()
        if refresh: self.refresh_projects()


