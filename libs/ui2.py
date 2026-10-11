import customtkinter as ctk
from PIL import Image
from libs import font_manager as fontM
from libs import ui_util as uiTool
from libs import data_manager as dataT
from datetime import datetime, timedelta
import random

def get_recent_projects_gui(default_view_mode : str = "Weeks") -> tuple[ctk.CTk, ctk.CTkFrame]:
    app_data : dict = {}

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
    app_data["create_new"] = create_new_button
    open_existing = ctk.CTkButton(manip_frame, text="Open Existing Project", border_width=0, fg_color=("#E3EBF5", "#2A3445"), text_color=("#2E5A8B", "#BFD6F5"), hover_color=("#D3E0F0", "#344058"))
    open_existing.pack(pady=(10, 230), expand=True)
    app_data["open_existing"] = open_existing

    recent_prjs_frame = ctk.CTkFrame(parent_frame, bg_color="transparent", fg_color=("#FFFFFF", "#1C222B"), border_width=0)
    recent_prjs_frame.pack(fill="both", expand=True, side=ctk.LEFT, padx=10)
    prjs_rect = uiTool.create_viewport(recent_prjs_frame)
    
    app.attributes("-topmost", True)

    return app, app_data, prjs_rect


#region DashBoard GUI
def get_dash_board_gui() -> tuple[ctk.CTk, dict]:
    app_data : dict = {}

    app = ctk.CTk(fg_color=("#F3F5F9", "#12161C"))
    app.title("Ganttify - Classifier les taches et gerer les roles.")
    app.minsize(1080, 720)
    app.state("zoomed")

    #region Header ui MAIN

    header = ctk.CTkFrame(app, fg_color=("#FFFFFF", "#181D25"), corner_radius=0, bg_color="transparent", height=50, border_color=("#D8DFE9", "#323B4A"), border_width=1)
    header.pack(fill="x", expand=False)
    header.pack_propagate(False)
    ctk.CTkFrame(app, height=1, corner_radius=0, fg_color=("#D8DFE9", "#323B4A")).pack(fill="x")   # under the header

    title = ctk.CTkFrame(header, fg_color="transparent", bg_color="transparent", width=300)
    title.pack(fill="y", expand=False, side=ctk.LEFT, padx=(3, 0), pady=3)
    title.pack_propagate(False)
    title_logo = ctk.CTkLabel(title, text="", fg_color="transparent", bg_color="transparent", image=ctk.CTkImage(light_image=Image.open("assets/logo_form.png"), size=(40,40)))
    title_logo.pack(side=ctk.LEFT, padx=(2, 8))
    title_text = ctk.CTkLabel(title, text="", fg_color="transparent", bg_color="transparent", image=ctk.CTkImage(light_image=Image.open("assets/title_light.png"), dark_image=Image.open("assets/title_dark.png"), size=(120,30)))
    title_text.pack(side=ctk.LEFT, pady=(5,0))

    
    def change_theme():
        ctk.set_appearance_mode("Dark" if ctk.get_appearance_mode() == "Light" else "Light")
        
    toggle_mode = ctk.CTkButton(header, text="", height=35, width=35, corner_radius=10, bg_color="transparent", fg_color=("#FFFFFF", "#1C222B"), hover_color=("#EAF1FA", "#2A3342"), border_color=("#D8DFE9", "#323B4A"), border_width=1, image=ctk.CTkImage(light_image=Image.open("assets/ui/dark_mode.png"), dark_image=Image.open("assets/ui/light_mode.png"), size=(15, 15)), command=change_theme)
    toggle_mode.pack(side=ctk.RIGHT, padx=(0, 15))

    def create_task():
        pass
    create_task_button = ctk.CTkButton(header, text="+ New Task", corner_radius=10, height=35, width=130, bg_color="transparent", fg_color=("#2E5A8B", "#5B9BE6"), hover_color=("#234770", "#78AEEE"), border_width=1, border_color=("#D6E6F8", "#2F4666"), text_color=("#FFFFFF", "#0B1220"), font=("Arial", 13), command=create_task)
    create_task_button.pack(side=ctk.RIGHT, padx=(0, 10))

    gantt_view_period = ctk.CTkSegmentedButton(header, height=35, corner_radius=10, bg_color="transparent", border_width=1, values=["Days", "Weeks", "Months"], fg_color=("#F3F5F9", "#12161C"), selected_color=("#D6E6F8", "#2F4666"), selected_hover_color=("#C2D3E9", "#3E4C68"), unselected_color=("#F3F5F9", "#12161C"), unselected_hover_color=("#EAF1FA", "#2A3342"), text_color=("#1B2430", "#E6EAF0"), text_color_disabled=("#9AA3B0", "#5A6577"))
    gantt_view_period.pack(side=ctk.RIGHT, padx=(0, 10))
    gantt_view_period.set("Weeks")
    app_data["timeline_view_mode"] = gantt_view_period

    def search_tasks(var_name, index, mode):
        current_text = search_txt_var.get()
        
    search_txt_var = ctk.StringVar()
    search_txt_var.trace_add("write", search_tasks)
    search_tasks_entry = ctk.CTkEntry(header, textvariable=search_txt_var, height=35, corner_radius=10, width=200, placeholder_text="Search tasks", bg_color="transparent", fg_color=("#FFFFFF", "#11151B"), text_color=("#1B2430", "#E6EAF0"), placeholder_text_color=("#7A869A", "#6F7B8E"), border_color=("#D8DFE9", "#323B4A"))
    search_tasks_entry.pack(side=ctk.RIGHT, padx=(0, 10))


    #endregion

    main_container = ctk.CTkFrame(app, fg_color=("#F3F5F9", "#12161C"), bg_color="transparent")
    main_container.pack(fill="both", expand=True)

    
    workspace_details = ctk.CTkFrame(main_container, fg_color=("#FFFFFF", "#1C222B"), corner_radius=0, bg_color="transparent", width=250, border_width=1, border_color=("#D8DFE9", "#323B4A"))
    workspace_details.pack(fill="y", expand=False, side=ctk.LEFT)
    workspace_details.pack_propagate(False)

    workspace_indic = ctk.CTkLabel(workspace_details, fg_color="transparent", bg_color="transparent", border_width=0, text="WORKSPACE", text_color=("#7A869A", "#6F7B8E"), font=("Segoe UI", 14))
    workspace_indic.pack(pady=(10, 25), padx=10, expand=False, anchor="nw")
    works_infos = ctk.CTkButton(workspace_details, fg_color="transparent", bg_color="transparent", text="   Workspace Details", text_color=("#2E5A8B", "#B9D3F2"), hover_color=("#EAF1FA", "#2A3342"), anchor="w", corner_radius=6, height=34, font=("Segoe UI", 14))
    works_infos.pack(fill="x", padx=10, pady=2)
    works_settings = ctk.CTkButton(workspace_details, fg_color="transparent", bg_color="transparent", text="   Workspace Settings", text_color=("#2E5A8B", "#B9D3F2"), hover_color=("#EAF1FA", "#2A3342"), anchor="w", corner_radius=6, height=34, font=("Segoe UI", 14))
    works_settings.pack(fill="x", padx=10, pady=2)

    panels_indic = ctk.CTkLabel(workspace_details, fg_color="transparent", bg_color="transparent", border_width=0, text="VIEWS", text_color=("#7A869A", "#6F7B8E"), font=("Segoe UI", 14))
    panels_indic.pack(pady=(10, 25), padx=10, expand=False, anchor="nw")
    
    timeline_btn = ctk.CTkButton(workspace_details, text="  Timeline", anchor="w", height=34, corner_radius=6, border_width=0, fg_color="transparent", hover_color=("#EAF1FA", "#2A3342"), text_color=("#2E5A8B", "#B9D3F2"), font=("Segoe UI", 14))
    timeline_btn.pack(pady=2, padx=10, fill="x")
    app_data["timeline_toggle"] = timeline_btn
    todoL_btn = ctk.CTkButton(workspace_details, text="  To-do lists", anchor="w", height=34, corner_radius=6, border_width=0, fg_color="transparent", hover_color=("#EAF1FA", "#2A3342"), text_color=("#2E5A8B", "#B9D3F2"), font=("Segoe UI", 14))
    todoL_btn.pack(pady=2, padx=10, fill="x")
    app_data["todoList_toggle"] = todoL_btn
    calendar_btn = ctk.CTkButton(workspace_details, text="  Calendar", anchor="w", height=34, corner_radius=6, border_width=0, fg_color="transparent", hover_color=("#EAF1FA", "#2A3342"), text_color=("#2E5A8B", "#B9D3F2"), font=("Segoe UI", 14))
    calendar_btn.pack(pady=2, padx=10, fill="x")
    app_data["calendar_toggle"] = calendar_btn
    
    app_data["timeline"] = list(uiTool.get_timeline_table(main_container, view_mode="Days"))
    app_data["timeline"][0].pack_forget()
    app_data["calendar"] = list(uiTool.get_calendar_grid(main_container, "Weeks"))
    app_data["calendar"][0].pack_forget()
    app_data["todoList"] = list(uiTool.get_todo_list(main_container, ["Buy markers", ("Write report", True)]))
    app_data["todoList"][0].pack_forget()
    
    task_details = ctk.CTkFrame(main_container, fg_color=("#FFFFFF", "#1C222B"), corner_radius=0, bg_color="transparent", width=330, border_width=1, border_color=("#D8DFE9", "#323B4A"))
    task_details.pack(fill="y", expand=False, side=ctk.RIGHT)
    task_details.pack_propagate(False)

    task_details_indic = ctk.CTkLabel(task_details, fg_color="transparent", bg_color="transparent", border_width=0, text="TASK DETAILS", text_color=("#7A869A", "#6F7B8E"), font=("Segoe UI", 14))
    task_details_indic.pack(pady=(10, 25), expand=False, anchor="nw", padx=10)
    no_task_selected = ctk.CTkLabel(task_details, fg_color="transparent", bg_color="transparent", border_width=0, text="No task was selected.", text_color=("#7A869A", "#6F7B8E"), font=("Segoe UI", 14))
    no_task_selected.pack(expand=False, anchor="w", padx=10, fill="x")
    app_data["no_task_selected"] = no_task_selected
        
    
    #region Footer ui MAIN
        
    footer = ctk.CTkFrame(app, fg_color=("#FFFFFF", "#181D25"), border_color=("#D8DFE9", "#323B4A"), border_width=1, corner_radius=0, bg_color="transparent", height=25)
    footer.pack(fill="x", expand=False)
    footer.pack_propagate(False)
    
    # si on veux utiliser le cloud apres
    save_mode = ctk.CTkLabel(footer, text="Saved locally", bg_color="transparent", fg_color="transparent", text_color=("#5B6778", "#9AA6B8"))
    save_mode.pack(side=ctk.LEFT, padx=10, pady=2)
    file_name_indic = ctk.CTkLabel(footer, text="filename.gantt", bg_color="transparent", fg_color="transparent", text_color=("#5B6778", "#9AA6B8"))
    file_name_indic.pack(side=ctk.LEFT, padx=10, pady=2)
    app_data["file_name"] = file_name_indic
    statistics_indic = ctk.CTkLabel(footer, text="7 tasks • 2 done • 0 late", bg_color="transparent", fg_color="transparent", text_color=("#5B6778", "#9AA6B8"))
    statistics_indic.pack(side=ctk.LEFT, padx=10, pady=2)
    app_data["workspace_stats"] = statistics_indic

    cur_view_mode = ctk.CTkLabel(footer, text="Week view", bg_color="transparent", fg_color="transparent", text_color=("#5B6778", "#9AA6B8"))
    cur_view_mode.pack(side=ctk.RIGHT, padx=(0, 10), pady=2)

    
    #endregion
            
    return app, app_data
#endregion




class Main_Dashboard:
    gui : ctk.CTk
    _data : dict

    def __init__(self):
        self.gui, self._data = get_dash_board_gui()
        self._data["timeline_view_mode"].configure(command=lambda val: self.switch_view_mode(val))
        self._data["timeline"][0].pack(**self._data["timeline"][1])
        self._data["timeline_toggle"].configure(command=lambda: self.switch_main_panel(0))
        self._data["todoList_toggle"].configure(command=lambda: self.switch_main_panel(1))
        self._data["calendar_toggle"].configure(command=lambda: self.switch_main_panel(2))

    def start_loop(self):
        # Ctk a des processus pour gerer les themes etc avant la loop donc on attend pour appliquer le mode zoomed
        self.gui.after(10, lambda: self.gui.state("zoomed"))
        self.gui.mainloop()

    def switch_view_mode(self, view_mode : str = "Weeks"):
        print(view_mode)

    def switch_main_panel(self, main_panel_id : int):
        match main_panel_id:
            case 0:
                self._data["calendar"][0].pack_forget()
                self._data["todoList"][0].pack_forget()
                self._data["timeline"][0].pack(**(self._data["timeline"][1]))
                self._data["todoList_toggle"].configure(fg_color="transparent")
                self._data["calendar_toggle"].configure(fg_color="transparent")
                self._data["timeline_toggle"].configure(fg_color=("#D6E6F8", "#2F4666"))
            case 1:
                self._data["calendar"][0].pack_forget()
                self._data["todoList"][0].pack(**(self._data["todoList"][1]))
                self._data["timeline"][0].pack_forget()
                self._data["timeline_toggle"].configure(fg_color="transparent")
                self._data["calendar_toggle"].configure(fg_color="transparent")
                self._data["todoList_toggle"].configure(fg_color=("#D6E6F8", "#2F4666"))
            case 2:
                self._data["calendar"][0].pack(**(self._data["calendar"][1]))
                self._data["todoList"][0].pack_forget()
                self._data["timeline"][0].pack_forget()
                self._data["todoList_toggle"].configure(fg_color="transparent")
                self._data["timeline_toggle"].configure(fg_color="transparent")
                self._data["calendar_toggle"].configure(fg_color=("#D6E6F8", "#2F4666"))
            case _:
                print("error in main panel id parsed")


class Recent_Projects_Window:
    recent_projects : ctk.CTkFrame
    gui : ctk.CTk
    _data : dict
    projects_data : dict

    def __init__(self, workspaces : dict | None = None):
        self.gui, self._data, self.recent_projects = get_recent_projects_gui()
        self.projects_data = {} if not workspaces else workspaces
        self.projects_buttons : list[ctk.CTkFrame] = []
        self._data["create_new"].configure(command=self.create_new_project)
        self._data["open_existing"].configure(command=self.find_existing)

    def refresh_projects(self):
        if not self.projects_data:
            return
        for prj_dt in self.projects_buttons:
            prj_dt.destroy()
        self.projects_buttons = []
        for id, pData in self.projects_data.items():
            prj_button = ctk.CTkButton(self.recent_projects, text=pData["name"], command=lambda: self.open_project(id))
            self.projects_buttons.append(prj_button)

    def create_new_project(self):
        container = self.gui
        create_new_popup = ctk.CTkToplevel(container, fg_color=("#F3F5F9", "#12161C"))
        create_new_popup.title("Create A New Project")
        create_new_popup.geometry("400x300")
        create_new_popup.resizable(False, False)

        def confirm_creation(prj_name : str):
            id = random.randrange(0, 10000)
            while id in list(self.projects_data.keys()):
                id = random.randrange(0, 10000)
            create_ts = datetime.now()
            dataT.save_new_workspace(id, {"name" : prj_name, "created" : create_ts})
            new_gui = Main_Dashboard()

        els_cont = ctk.CTkFrame(create_new_popup, fg_color=("#FFFFFF", "#1C222B"))
        els_cont.pack(fill="both", expand=True, padx=10, pady=10)

        def check_existence(var_name, index, mode):
            current_text = search_txt_var.get()
            if len(current_text) == 0:
                submit_request.configure(state="disabled")
                existence_verifier.configure(text="The name cannot be empty.", text_color=("#D6455D", "#F0788A"))
            elif len(current_text) <= 3:
                submit_request.configure(state="disabled")
                existence_verifier.configure(text="The name should be longer than 3 chars.", text_color=("#D6455D", "#F0788A"))
            elif  current_text not in [f["name"] for _, f in self.projects_data.items()]:
                existence_verifier.configure(text="The name is available.", text_color=("#2F9E69", "#4FC38A"))
                submit_request.configure(state="normal")
            else:
                existence_verifier.configure(text="The name is NOT available.", text_color=("#D6455D", "#F0788A"))
                submit_request.configure(state="disabled")
            
        search_txt_var = ctk.StringVar()
        search_txt_var.trace_add("write", check_existence)
        prompt = ctk.CTkLabel(els_cont, text="Enter the name of your new project :", fg_color="transparent", text_color=("#1B2430", "#E6EAF0"), font=("Segoe UI", 14))
        prompt.pack(pady=8)
        search_tasks_entry = ctk.CTkEntry(els_cont, textvariable=search_txt_var, height=35, corner_radius=10, width=200, placeholder_text="Search tasks", bg_color="transparent", fg_color=("#FFFFFF", "#11151B"), text_color=("#1B2430", "#E6EAF0"), placeholder_text_color=("#7A869A", "#6F7B8E"), border_color=("#D8DFE9", "#323B4A"))
        search_tasks_entry.pack(pady=(0, 8))
        existence_verifier = ctk.CTkLabel(els_cont, text="The name cannot be empty.", text_color=("#D6455D", "#F0788A"), fg_color="transparent", bg_color="transparent")
        existence_verifier.pack(pady=(0, 8))
        submit_request = ctk.CTkButton(els_cont, text="Create Project", command=lambda: confirm_creation(search_txt_var.get()), fg_color=("#2E5A8B", "#5B9BE6"), hover_color=("#234770", "#78AEEE"), text_color=("#FFFFFF", "#0B1220"), font=("Segoe UI", 14), corner_radius=10, height=35)
        submit_request.pack(pady=(0, 8))
        submit_request.configure(state="disabled")

        # This creates a bug when we close the create new window, cz the self.gui becomes non topmost and doesnt revert back
        self.gui.attributes("-topmost", False)
        create_new_popup.attributes("-topmost", True)

    def find_existing(self):
        pass

    def start_loop(self):
        self.gui.mainloop()

    def assign_projects(self, new_projects : dict, refresh : bool = False):
        self.projects_data = new_projects.copy()
        if refresh: self.refresh_projects()


