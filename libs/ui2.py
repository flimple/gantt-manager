import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from libs import ui_util as uiTool
from libs import data_manager as dataT
from datetime import date, datetime, timedelta

# Couleurs partagées (clair, sombre)
ACCENT = ("#2E5A8B", "#5B9BE6")
ACCENT_HOVER = ("#234770", "#78AEEE")
ON_ACCENT = ("#FFFFFF", "#0B1220")
PANEL = ("#FFFFFF", "#1C222B")
TEXT = ("#1B2430", "#E6EAF0")
MUTED = ("#7A869A", "#6F7B8E")
BORDER = ("#D8DFE9", "#323B4A")
HOVER = ("#EAF1FA", "#2A3342")
SELECTED = ("#D6E6F8", "#2F4666")
ERROR = ("#D6455D", "#F0788A")
SUCCESS = ("#2F9E69", "#4FC38A")
DEFAULT_TASK_COLOR = dataT.DEFAULT_TASK_COLOR  # Une seule source de vérité
RESIZE_EDGE = 6  # Zone (px) sur les bords d'une tâche sélectionnée pour changer ses dates
DRAG_THRESHOLD = 5  # Pixels minimum avant qu'un clic devienne un déplacement


def _asset(*parts) -> str:
    # Chemin absolu vers assets/ : l'app marche peu importe d'où on la lance
    return os.path.join(dataT.BASE_DIR, "assets", *parts)


def _image(light : str, dark : str | None = None, size : tuple = (40, 40)) -> ctk.CTkImage:
    return ctk.CTkImage(light_image=Image.open(_asset(light)),
                        dark_image=Image.open(_asset(dark)) if dark else None, size=size)


def _popup(root, title : str, size : str) -> ctk.CTkToplevel:
    # Petite fenêtre au-dessus de la fenêtre principale
    popup = ctk.CTkToplevel(root, fg_color=("#F3F5F9", "#12161C"))
    popup.title(title)
    popup.geometry(size)
    popup.resizable(False, False)
    popup.transient(root)
    # CTkToplevel s'affiche parfois derrière : on le remet devant une fois créé
    popup.after(150, lambda: (popup.lift(), popup.focus_force()))
    return popup


def choose_project_file(parent) -> int | None:
    # Choisir un fichier .gantt (n'importe où sur le PC) ; il est ajouté aux projets récents ; renvoie son id
    # Utilisé par l'écran des projets ET par le dashboard ("Open Project...")
    path = filedialog.askopenfilename(parent=parent, title="Open Project", initialdir=dataT.DATA_FOLDER,
                                      filetypes=[("Ganttify project", "*.gantt")])
    if not path:
        return None
    prj_id = dataT.register_project_file(path)
    if prj_id is None:
        messagebox.showerror("Open Project", "This is not a valid Ganttify project file.", parent=parent)
    return prj_id


def get_recent_projects_gui(root : ctk.CTk, default_view_mode : str = "Weeks") -> tuple[ctk.CTk, dict, ctk.CTkFrame]:
    app_data : dict = {}

    app = root
    app.title("Ganttify - Recent Projects")
    app.geometry("650x500")
    app.resizable(False, False)

    title_frame = ctk.CTkFrame(app, height=90, border_width=0, fg_color=("#FFFFFF", "#181D25"), bg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 0))
    title_frame.pack_propagate(False)

    logo = ctk.CTkLabel(title_frame, text="", image=_image("logo_form.png", size=(60,60)))
    logo.pack(pady=3, side=ctk.LEFT, padx=20)

    title_logo = ctk.CTkLabel(title_frame, text="", image=_image("title_light.png", "title_dark.png", size=(240,60)))
    title_logo.pack(padx=10, side=ctk.LEFT)

    parent_frame = ctk.CTkFrame(app, border_width=0, fg_color="transparent", bg_color="transparent")
    parent_frame.pack(fill="both", expand=True, pady=(5, 15))

    manip_frame = ctk.CTkFrame(parent_frame, fg_color=PANEL, bg_color="transparent", width=180, border_width=0)
    manip_frame.pack(fill="y", side=ctk.LEFT, padx=10)
    manip_frame.pack_propagate(False)

    create_new_button = ctk.CTkButton(manip_frame, text="Create New Project", border_width=0, fg_color=ACCENT, text_color=ON_ACCENT, hover_color=ACCENT_HOVER)
    create_new_button.pack(pady=(90, 10), expand=True)
    app_data["create_new"] = create_new_button
    open_existing = ctk.CTkButton(manip_frame, text="Open Existing Project", border_width=0, fg_color=("#E3EBF5", "#2A3445"), text_color=("#2E5A8B", "#BFD6F5"), hover_color=("#D3E0F0", "#344058"))
    open_existing.pack(pady=(10, 230), expand=True)
    app_data["open_existing"] = open_existing

    recent_prjs_frame = ctk.CTkFrame(parent_frame, bg_color="transparent", fg_color=PANEL, border_width=0)
    recent_prjs_frame.pack(fill="both", expand=True, side=ctk.LEFT, padx=10)
    prjs_rect = uiTool.create_viewport(recent_prjs_frame)

    app.attributes("-topmost", True)

    return app, app_data, prjs_rect


#region DashBoard GUI
def get_dash_board_gui(root : ctk.CTk) -> tuple[ctk.CTk, dict]:
    app_data : dict = {}

    app = root
    app.title("Ganttify - Classifier les taches et gerer les roles.")
    app.minsize(1080, 720)
    app.state("zoomed")

    #region Header ui MAIN
    header = ctk.CTkFrame(app, fg_color=("#FFFFFF", "#181D25"), corner_radius=0, bg_color="transparent", height=50, border_color=BORDER, border_width=1)
    header.pack(fill="x", expand=False)
    header.pack_propagate(False)
    ctk.CTkFrame(app, height=1, corner_radius=0, fg_color=BORDER).pack(fill="x")   # under the header

    title = ctk.CTkFrame(header, fg_color="transparent", bg_color="transparent", width=300)
    title.pack(fill="y", expand=False, side=ctk.LEFT, padx=(3, 0), pady=3)
    title.pack_propagate(False)
    title_logo = ctk.CTkLabel(title, text="", fg_color="transparent", bg_color="transparent", image=_image("logo_form.png", size=(40,40)))
    title_logo.pack(side=ctk.LEFT, padx=(2, 8))
    title_text = ctk.CTkLabel(title, text="", fg_color="transparent", bg_color="transparent", image=_image("title_light.png", "title_dark.png", size=(120,30)))
    title_text.pack(side=ctk.LEFT, pady=(5,0))

    def change_theme():
        ctk.set_appearance_mode("Dark" if ctk.get_appearance_mode() == "Light" else "Light")

    toggle_mode = ctk.CTkButton(header, text="", height=35, width=35, corner_radius=10, bg_color="transparent", fg_color=PANEL, hover_color=HOVER, border_color=BORDER, border_width=1, image=_image("ui/dark_mode.png", "ui/light_mode.png", size=(15, 15)), command=change_theme)
    toggle_mode.pack(side=ctk.RIGHT, padx=(0, 15))

    create_task_button = ctk.CTkButton(header, text="+ New Task", corner_radius=10, height=35, width=130, bg_color="transparent", fg_color=ACCENT, hover_color=ACCENT_HOVER, border_width=1, border_color=SELECTED, text_color=ON_ACCENT, font=("Arial", 13))
    create_task_button.pack(side=ctk.RIGHT, padx=(0, 10))
    app_data["create_task"] = create_task_button

    gantt_view_period = ctk.CTkSegmentedButton(header, height=35, corner_radius=10, bg_color="transparent", border_width=1, values=["Days", "Weeks", "Months"], fg_color=("#F3F5F9", "#12161C"), selected_color=SELECTED, selected_hover_color=("#C2D3E9", "#3E4C68"), unselected_color=("#F3F5F9", "#12161C"), unselected_hover_color=HOVER, text_color=TEXT, text_color_disabled=("#9AA3B0", "#5A6577"))
    gantt_view_period.pack(side=ctk.RIGHT, padx=(0, 10))
    gantt_view_period.set("Weeks")
    app_data["timeline_view_mode"] = gantt_view_period

    search_txt_var = ctk.StringVar()
    app_data["search_var"] = search_txt_var
    search_tasks_entry = ctk.CTkEntry(header, textvariable=search_txt_var, height=35, corner_radius=10, width=200, placeholder_text="Search tasks", bg_color="transparent", fg_color=("#FFFFFF", "#11151B"), text_color=TEXT, placeholder_text_color=MUTED, border_color=BORDER)
    search_tasks_entry.pack(side=ctk.RIGHT, padx=(0, 10))

    #endregion

    main_container = ctk.CTkFrame(app, fg_color=("#F3F5F9", "#12161C"), bg_color="transparent")
    main_container.pack(fill="both", expand=True)

    workspace_details = ctk.CTkFrame(main_container, fg_color=PANEL, corner_radius=0, bg_color="transparent", width=250, border_width=1, border_color=BORDER)
    workspace_details.pack(fill="y", expand=False, side=ctk.LEFT)
    workspace_details.pack_propagate(False)

    side_button = dict(fg_color="transparent", bg_color="transparent", text_color=("#2E5A8B", "#B9D3F2"), hover_color=HOVER, anchor="w", corner_radius=6, height=34, font=("Segoe UI", 14))
    workspace_indic = ctk.CTkLabel(workspace_details, fg_color="transparent", bg_color="transparent", text="WORKSPACE", text_color=MUTED, font=("Segoe UI", 14))
    workspace_indic.pack(pady=(10, 25), padx=10, expand=False, anchor="nw")
    works_infos = ctk.CTkButton(workspace_details, text="   Workspace Details", **side_button)
    works_infos.pack(fill="x", padx=10, pady=2)
    app_data["workspace_details"] = works_infos
    works_settings = ctk.CTkButton(workspace_details, text="   Workspace Settings", **side_button)
    works_settings.pack(fill="x", padx=10, pady=2)
    app_data["workspace_settings"] = works_settings

    panels_indic = ctk.CTkLabel(workspace_details, fg_color="transparent", bg_color="transparent", text="VIEWS", text_color=MUTED, font=("Segoe UI", 14))
    panels_indic.pack(pady=(10, 25), padx=10, expand=False, anchor="nw")

    timeline_btn = ctk.CTkButton(workspace_details, text="  Timeline", border_width=0, **side_button)
    timeline_btn.pack(pady=2, padx=10, fill="x")
    app_data["timeline_toggle"] = timeline_btn
    todoL_btn = ctk.CTkButton(workspace_details, text="  To-do lists", border_width=0, **side_button)
    todoL_btn.pack(pady=2, padx=10, fill="x")
    app_data["todoList_toggle"] = todoL_btn
    calendar_btn = ctk.CTkButton(workspace_details, text="  Calendar", border_width=0, **side_button)
    calendar_btn.pack(pady=2, padx=10, fill="x")
    app_data["calendar_toggle"] = calendar_btn

    project_indic = ctk.CTkLabel(workspace_details, fg_color="transparent", bg_color="transparent", text="PROJECT", text_color=MUTED, font=("Segoe UI", 14))
    project_indic.pack(pady=(10, 25), padx=10, expand=False, anchor="nw")
    recent_btn = ctk.CTkButton(workspace_details, text="  Recent Projects", border_width=0, **side_button)
    recent_btn.pack(pady=2, padx=10, fill="x")
    app_data["recent_projects"] = recent_btn
    open_btn = ctk.CTkButton(workspace_details, text="  Open Project...", border_width=0, **side_button)
    open_btn.pack(pady=2, padx=10, fill="x")
    app_data["open_project"] = open_btn

    app_data["timeline"] = list(uiTool.get_timeline_table(main_container, view_mode="Weeks"))
    app_data["timeline"][0].pack_forget()
    app_data["calendar"] = list(uiTool.get_calendar_grid(main_container, "Weeks"))
    app_data["calendar"][0].pack_forget()
    app_data["todoList"] = list(uiTool.get_todo_list(main_container))
    app_data["todoList"][0].pack_forget()

    task_details = ctk.CTkFrame(main_container, fg_color=PANEL, corner_radius=0, bg_color="transparent", width=330, border_width=1, border_color=BORDER)
    task_details.pack(fill="y", expand=False, side=ctk.RIGHT)
    task_details.pack_propagate(False)
    app_data["task_details"] = task_details

    task_details_indic = ctk.CTkLabel(task_details, fg_color="transparent", bg_color="transparent", text="TASK DETAILS", text_color=MUTED, font=("Segoe UI", 14))
    task_details_indic.pack(pady=(10, 25), expand=False, anchor="nw", padx=10)
    no_task_selected = ctk.CTkLabel(task_details, fg_color="transparent", bg_color="transparent", text="No task was selected.", text_color=MUTED, font=("Segoe UI", 14))
    no_task_selected.pack(expand=False, anchor="w", padx=10, fill="x")
    app_data["no_task_selected"] = no_task_selected

    #region Footer ui MAIN

    footer = ctk.CTkFrame(app, fg_color=("#FFFFFF", "#181D25"), border_color=BORDER, border_width=1, corner_radius=0, bg_color="transparent", height=25)
    footer.pack(fill="x", expand=False)
    footer.pack_propagate(False)

    footer_text = dict(bg_color="transparent", fg_color="transparent", text_color=("#5B6778", "#9AA6B8"))
    # si on veux utiliser le cloud apres
    save_mode = ctk.CTkLabel(footer, text="Saved locally", **footer_text)
    save_mode.pack(side=ctk.LEFT, padx=10, pady=2)
    file_name_indic = ctk.CTkLabel(footer, text="filename.gantt", **footer_text)
    file_name_indic.pack(side=ctk.LEFT, padx=10, pady=2)
    app_data["file_name"] = file_name_indic
    statistics_indic = ctk.CTkLabel(footer, text="0 tasks • 0 done • 0 late", **footer_text)
    statistics_indic.pack(side=ctk.LEFT, padx=10, pady=2)
    app_data["workspace_stats"] = statistics_indic

    cur_view_mode = ctk.CTkLabel(footer, text="Week view", **footer_text)
    cur_view_mode.pack(side=ctk.RIGHT, padx=(0, 10), pady=2)
    app_data["view_mode_label"] = cur_view_mode

    #endregion

    return app, app_data
#endregion


class Main_Dashboard:
    gui : ctk.CTk
    _data : dict

    def __init__(self, root : ctk.CTk, workspace_id : int, on_close_project=None, on_open_project=None):
        self.workspace_id = workspace_id
        self.on_close_project = on_close_project  # Retour à l'écran des projets récents
        self.on_open_project = on_open_project    # on_open_project(prj_id) : ouvrir un autre projet
        # Tout le projet vient de son fichier .gantt : {"name", "created", "settings", "tasks"}
        self.project = dataT.load_project(workspace_id) or {"name" : f"Project {workspace_id}", "settings" : {}, "tasks" : {}}
        self.path = dataT.project_path(workspace_id) or ""
        self.workspace = self.project  # Nom et date de création
        # tasks : {task_id (str) : {"name", "start", "end" (AAAA-MM-JJ), "color", "done"}}
        # Mêmes dicts que dans self.project : les modifier puis save_project() suffit
        self.tasks, self.settings = self.project["tasks"], self.project["settings"]
        self.selected = None
        self.bars = {}          # task_id -> (widget, canvas_item) sur la timeline
        self._range = None      # (début, fin) affichés par la timeline
        self._drag = None       # Geste en cours sur une barre : déplacement ou étirement (None sinon)
        self._theme = ctk.get_appearance_mode()

        self.gui, self._data = get_dash_board_gui(root)
        self.timeline, _, self.timeline_canvas, self.timeline_names = self._data["timeline"]
        self.calendar = self._data["calendar"][0]
        self.todo = self._data["todoList"][0]

        self._data["timeline_view_mode"].configure(command=self.switch_view_mode)
        self._data["file_name"].configure(text=os.path.basename(self.path) or f"{self.workspace['name']}.gantt")
        self._data["timeline_toggle"].configure(command=lambda: self.switch_main_panel(0))
        self._data["todoList_toggle"].configure(command=lambda: self.switch_main_panel(1))
        self._data["calendar_toggle"].configure(command=lambda: self.switch_main_panel(2))
        self._data["create_task"].configure(command=self.open_new_task_popup)
        self._data["workspace_details"].configure(command=self.open_details_popup)
        self._data["workspace_settings"].configure(command=self.open_settings_popup)
        self._data["recent_projects"].configure(command=self.close_project)
        self._data["open_project"].configure(command=self.open_other_project)
        self.gui.bind("<Control-o>", lambda e: self.open_other_project())  # Ctrl+O, comme partout
        self._data["search_var"].trace_add("write", lambda *_: self.render())

        view = self.settings.get("default_view", "Weeks")
        self._data["timeline_view_mode"].set(view)
        self.switch_view_mode(view, render=False)
        self.switch_main_panel(0)  # La timeline est affichée par défaut (avant : le centre était vide)
        self.render()
        self._watch_theme()

    def start_loop(self):
        # Ctk a des processus pour gerer les themes etc avant la loop donc on attend pour appliquer le mode zoomed
        self.gui.after(10, lambda: self.gui.state("zoomed"))
        self.gui.mainloop()

    # ---------- Vues ----------

    def switch_view_mode(self, view_mode : str = "Weeks", render : bool = True):
        self.timeline.set_view(view_mode=view_mode)
        self.calendar.set_view(view_mode=view_mode)
        self._data["view_mode_label"].configure(text=f"{view_mode[:-1]} view")
        if render:
            self._place_bars()

    def switch_main_panel(self, main_panel_id : int):
        panels = [(self._data["timeline"], self._data["timeline_toggle"]),
                  (self._data["todoList"], self._data["todoList_toggle"]),
                  (self._data["calendar"], self._data["calendar_toggle"])]
        if not 0 <= main_panel_id < len(panels):
            print("error in main panel id parsed")
            return
        # Chaque panneau est une liste (frame, pack_data, ...) : timeline, to-do et calendrier n'ont pas la même taille
        for index, (panel, button) in enumerate(panels):
            frame, pack_data = panel[0], panel[1]
            if index == main_panel_id:
                # before= : le panneau reste entre la barre de gauche et les détails à droite
                frame.pack(**pack_data, before=self._data["task_details"])
                button.configure(fg_color=SELECTED)
            else:
                frame.pack_forget()
                button.configure(fg_color="transparent")

    # ---------- Affichage des tâches ----------

    def _visible_tasks(self) -> list:
        # Tâches qui correspondent à la recherche, triées par date de début
        query = self._data["search_var"].get().strip().lower()
        items = sorted(self.tasks.items(), key=lambda kv: (kv[1]["start"], kv[1]["name"].lower()))
        return [(task_id, task) for task_id, task in items if query in task["name"].lower()]

    def render(self):
        visible = self._visible_tasks()
        self._render_timeline(visible)
        self._render_todo(visible)
        self._render_calendar(visible)
        self._update_stats()
        self._show_details()

    def _render_timeline(self, visible):
        colors = uiTool._tl_colors()
        for child in self.timeline_names.winfo_children():
            child.destroy()
        for widget, item in self.bars.values():
            self.timeline_canvas.delete(item)
            widget.destroy()
        self.bars = {}

        # Plage de dates : englobe toutes les tâches (on ne la change que si besoin, pour garder le scroll)
        if self.tasks:
            first = min(date.fromisoformat(t["start"]) for t in self.tasks.values())
            last = max(date.fromisoformat(t["end"]) for t in self.tasks.values())
            start = first - timedelta(days=first.weekday() + 7)
            wanted = (start, max(last + timedelta(days=30), start + timedelta(days=89)))
            if wanted != self._range:
                self._range = wanted
                self.timeline.set_view(start_date=wanted[0], end_date=wanted[1])
        elif self._range is not None:
            # Plus aucune tâche : on revient à la fenêtre par défaut au lieu de garder l'ancienne
            self._range = None
            default_start, default_end = self.timeline.default_range()
            self.timeline.set_view(start_date=default_start, end_date=default_end)

        row_height = self.timeline.row_height
        for task_id, task in visible:
            # Une ligne par tâche dans la colonne des noms (tk et pas CTk : hauteur exacte en pixels)
            row = tk.Frame(self.timeline_names, height=row_height, bg=colors["panel"])
            row.pack(fill="x")
            row.pack_propagate(False)
            name = tk.Label(row, text=("✓ " if task["done"] else "") + task["name"], anchor="w", padx=14,
                            bg=colors["panel"], fg=colors["dim"] if task["done"] else colors["text"], font=("Segoe UI", 10))
            name.pack(fill="both", expand=True)
            name.bind("<Button-1>", lambda e, tid=task_id: self.select_task(tid))

            color = task.get("color", DEFAULT_TASK_COLOR)
            bar = tk.Label(self.timeline_canvas, text=task["name"], anchor="w", padx=6, bg=color,
                           fg=uiTool._text_on(color), font=("Segoe UI", 9), cursor="hand2")
            # Clic = sélectionner ; sur une tâche déjà sélectionnée, tirer un bord = changer ses dates
            bar.bind("<ButtonPress-1>", lambda e, tid=task_id: self._on_bar_press(e, tid))
            bar.bind("<B1-Motion>", self._on_bar_drag)
            bar.bind("<ButtonRelease-1>", self._on_bar_release)
            bar.bind("<Motion>", lambda e, tid=task_id: self._on_bar_hover(e, tid))
            item = self.timeline_canvas.create_window(0, 0, window=bar, anchor="nw")
            self.bars[task_id] = (bar, item)
        self._place_bars()

    def _place_bars(self):
        # Position des barres selon le mode de vue (la largeur d'un jour change entre Days/Weeks/Months)
        row_height, day_width = self.timeline.row_height, self.timeline.day_width()
        for index, (task_id, _) in enumerate(self._visible_tasks()):
            if task_id not in self.bars:
                continue
            task = self.tasks[task_id]
            widget, item = self.bars[task_id]
            start, end = date.fromisoformat(task["start"]), date.fromisoformat(task["end"])
            selected = task_id == self.selected
            widget.configure(relief="solid" if selected else "flat", bd=2 if selected else 0)
            self.timeline_canvas.coords(item, self.timeline.date_to_x(start), self.timeline.row_to_y(index) + 6)
            self.timeline_canvas.itemconfigure(item, width=max(((end - start).days + 1) * day_width, 6),
                                               height=row_height - 12)

    def _render_todo(self, visible):
        self.todo.clear()
        for task_id, task in visible:
            self.todo.add_task(task["name"], task["done"],
                               on_toggle=lambda text, done, tid=task_id: self.set_done(tid, done))

    def _render_calendar(self, visible):
        # La tâche apparaît sur chaque jour qu'elle couvre (limité à 62 jours pour rester lisible)
        events = []
        for _, task in visible:
            start, end = date.fromisoformat(task["start"]), date.fromisoformat(task["end"])
            for offset in range(min((end - start).days, 61) + 1):
                events.append((start + timedelta(days=offset), task["name"], task.get("color", DEFAULT_TASK_COLOR)))
        self.calendar.set_view(events=events)

    def _update_stats(self):
        stats = dataT.compute_stats(self.tasks)
        self._data["workspace_stats"].configure(text=stats["stats_str"])

    def _watch_theme(self):
        # Les widgets tk de la timeline ne suivent pas le thème CTk : on redessine quand il change
        if not self.timeline.winfo_exists():
            return
        if ctk.get_appearance_mode() != self._theme:
            self._theme = ctk.get_appearance_mode()
            self.render()
        self.gui.after(300, self._watch_theme)

    # ---------- Sélection et détails ----------

    # ---------- Déplacer une tâche sur sa ligne, ou l'étirer par ses bords ----------

    def _bar_edge(self, task_id, x_root : int):
        # "left" / "right" si la souris est sur un bord de la tâche sélectionnée, sinon None
        if task_id != self.selected or task_id not in self.bars:
            return None
        bar = self.bars[task_id][0]
        width = bar.winfo_width()
        x = x_root - bar.winfo_rootx()
        # Sur une barre étroite (vue Months) deux zones de 6 px se recouvrent et
        # avalaient toute la barre : plus de milieu pour la saisir, et le bord droit
        # tirait la date de début. On les limite au tiers de la largeur.
        edge = min(RESIZE_EDGE, max(width // 3, 1))
        if x >= width - edge:
            return "right"
        if x <= edge:
            return "left"
        return None

    def _on_bar_hover(self, event, task_id):
        # Curseur ↔ sur les bords de la tâche sélectionnée (l'étirer), croix de
        # déplacement partout ailleurs sur la barre (la faire glisser sur sa ligne)
        if self._drag is None and task_id in self.bars:
            edge = self._bar_edge(task_id, event.x_root)
            self.bars[task_id][0].configure(cursor="sb_h_double_arrow" if edge else "fleur")

    def _on_bar_press(self, event, task_id):
        # Le bord est testé AVANT de sélectionner : on n'étire qu'une tâche déjà
        # sélectionnée. Ailleurs sur la barre, le geste déplace la tâche entière.
        edge = self._bar_edge(task_id, event.x_root)
        if task_id != self.selected:
            self.select_task(task_id)
        task = self.tasks[task_id]
        self._drag = {"task_id" : task_id, "mode" : edge or "move",
                      "start" : date.fromisoformat(task["start"]), "end" : date.fromisoformat(task["end"]),
                      "grab" : self._date_at(event.x_root), "x_press" : event.x_root,
                      "new_start" : None, "new_end" : None, "moved" : False}

    def _date_at(self, x_root : int) -> date:
        # Jour le plus proche de la souris sur la timeline (aimanté sur les jours)
        canvas, day_width = self.timeline_canvas, self.timeline.day_width()
        x = canvas.canvasx(x_root - canvas.winfo_rootx())
        return self.timeline.start_date() + timedelta(days=round(x / day_width))

    def _on_bar_drag(self, event):
        drag = self._drag
        if drag is None:
            return
        if not drag["moved"]:
            # Un simple clic ne doit pas décaler les dates. En vue Months un jour ne
            # fait que 5 px : on exige aussi une demi-journée, sinon un tremblement
            # de souris suffisait à déplacer la tâche d'un jour et à l'enregistrer.
            if abs(event.x_root - drag["x_press"]) < max(DRAG_THRESHOLD, self.timeline.day_width() / 2):
                return
            drag["moved"] = True
        start, end, boundary = drag["start"], drag["end"], self._date_at(event.x_root)
        if drag["mode"] == "move":
            # La tâche glisse d'un bloc : même durée, seules les dates changent.
            # L'écart est compté depuis le jour saisi, donc la barre suit la souris sans sauter.
            delta = boundary - drag["grab"]
            new_start, new_end = start + delta, end + delta
        elif drag["mode"] == "right":
            # Le bord droit est APRÈS le dernier jour : la date de fin est la veille du bord
            new_start, new_end = start, max(start, boundary - timedelta(days=1))
        else:
            new_start, new_end = min(end, boundary), end
        drag["new_start"], drag["new_end"] = new_start, new_end
        # Aperçu en direct : seule cette barre bouge, et uniquement en X. Le Y relu ici est
        # celui que _place_bars a posé depuis l'index de ligne et il est réécrit tel quel :
        # la barre ne peut pas changer de ligne.
        _, item = self.bars[drag["task_id"]]
        _, y = self.timeline_canvas.coords(item)
        self.timeline_canvas.coords(item, self.timeline.date_to_x(new_start), y)
        self.timeline_canvas.itemconfigure(item, width=((new_end - new_start).days + 1) * self.timeline.day_width())

    def _on_bar_release(self, event):
        drag, self._drag = self._drag, None
        if drag is None or not drag["moved"]:
            return  # Le clic a seulement sélectionné la tâche
        task = self.tasks.get(drag["task_id"])
        if task is None or drag["new_start"] is None:
            return
        new_start, new_end = drag["new_start"].isoformat(), drag["new_end"].isoformat()
        if (new_start, new_end) == (task["start"], task["end"]):
            return
        task["start"], task["end"] = new_start, new_end
        self._save()
        # after_idle : on reconstruit la timeline après le relâchement, pas pendant
        self.gui.after_idle(self.render)

    def select_task(self, task_id):
        self.selected = task_id
        self._place_bars()
        self._show_details()

    def _show_details(self):
        panel = self._data["task_details"]
        if getattr(self, "_details_box", None) is not None:
            self._details_box.destroy()
            self._details_box = None
        task = self.tasks.get(self.selected)
        if task is None:
            self.selected = None
            self._data["no_task_selected"].pack(expand=False, anchor="w", padx=10, fill="x")
            return
        self._data["no_task_selected"].pack_forget()

        box = ctk.CTkFrame(panel, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10)
        self._details_box = box
        start, end = date.fromisoformat(task["start"]), date.fromisoformat(task["end"])
        if task["done"]:
            status, status_color = "Done", SUCCESS
        elif end < date.today():
            status, status_color = "Late", ERROR
        else:
            status, status_color = "In progress", ACCENT

        title = ctk.CTkFrame(box, fg_color="transparent")
        title.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(title, width=14, height=14, corner_radius=4, fg_color=task.get("color", DEFAULT_TASK_COLOR)).pack(side=ctk.LEFT, padx=(0, 8))
        ctk.CTkLabel(title, text=task["name"], text_color=TEXT, font=("Segoe UI", 16, "bold"), anchor="w",
                     wraplength=260, justify="left").pack(side=ctk.LEFT, fill="x")
        for label, value in (("Start", f"{start:%d %b %Y}"), ("End", f"{end:%d %b %Y}"),
                             ("Duration", f"{(end - start).days + 1} day(s)")):
            line = ctk.CTkFrame(box, fg_color="transparent")
            line.pack(fill="x", pady=2)
            ctk.CTkLabel(line, text=label, text_color=MUTED, width=80, anchor="w").pack(side=ctk.LEFT)
            ctk.CTkLabel(line, text=value, text_color=TEXT, anchor="w").pack(side=ctk.LEFT)
        line = ctk.CTkFrame(box, fg_color="transparent")
        line.pack(fill="x", pady=2)
        ctk.CTkLabel(line, text="Status", text_color=MUTED, width=80, anchor="w").pack(side=ctk.LEFT)
        ctk.CTkLabel(line, text=status, text_color=status_color, anchor="w").pack(side=ctk.LEFT)

        ctk.CTkButton(box, text="Mark as not done" if task["done"] else "Mark as done", fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color=ON_ACCENT, corner_radius=8,
                      command=lambda: self.set_done(self.selected, not task["done"])).pack(fill="x", pady=(18, 6))
        ctk.CTkButton(box, text="Delete task", fg_color="transparent", border_width=1, border_color=ERROR,
                      text_color=ERROR, hover_color=HOVER, corner_radius=8,
                      command=self.delete_selected).pack(fill="x")

    # ---------- Modifications (sauvegardées tout de suite) ----------

    def _save(self):
        # Tout le projet est réécrit dans son fichier .gantt (tâches + réglages)
        dataT.save_project(self.workspace_id, self.project)

    def set_done(self, task_id, done : bool):
        if task_id not in self.tasks:
            return
        self.tasks[task_id]["done"] = done
        self._save()
        # after_idle : on ne reconstruit pas la liste pendant le clic sur sa propre case à cocher
        self.gui.after_idle(self.render)

    def delete_selected(self):
        task = self.tasks.get(self.selected)
        if task is None:
            return
        if not messagebox.askyesno("Delete task", f"Delete \"{task['name']}\"?", parent=self.gui):
            return
        del self.tasks[self.selected]
        self.selected = None
        self._save()
        self.gui.after_idle(self.render)

    def open_new_task_popup(self):
        popup = _popup(self.gui, "New Task", "380x330")
        body = ctk.CTkFrame(popup, fg_color=PANEL)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        state = {"color" : DEFAULT_TASK_COLOR}

        def field(text, default=""):
            ctk.CTkLabel(body, text=text, text_color=TEXT, anchor="w").pack(fill="x", padx=16, pady=(8, 0))
            entry = ctk.CTkEntry(body, height=32, corner_radius=8, fg_color=("#FFFFFF", "#11151B"), text_color=TEXT, border_color=BORDER)
            entry.insert(0, default)
            entry.pack(fill="x", padx=16)
            return entry

        today = date.today()
        name_entry = field("Task name")
        start_entry = field("Start date (YYYY-MM-DD)", today.isoformat())
        end_entry = field("End date (YYYY-MM-DD)", (today + timedelta(days=3)).isoformat())

        color_row = ctk.CTkFrame(body, fg_color="transparent")
        color_row.pack(fill="x", padx=16, pady=(10, 0))
        swatch = ctk.CTkFrame(color_row, width=28, height=28, corner_radius=6, fg_color=state["color"])
        swatch.pack(side=ctk.LEFT)

        def pick_color():
            _, hex_color = colorchooser.askcolor(color=state["color"], title="Task color", parent=popup)
            if hex_color:
                state["color"] = hex_color
                swatch.configure(fg_color=hex_color)
        ctk.CTkButton(color_row, text="Pick color...", width=110, fg_color="transparent", border_width=1,
                      border_color=BORDER, text_color=TEXT, hover_color=HOVER, command=pick_color).pack(side=ctk.LEFT, padx=8)

        error = ctk.CTkLabel(body, text="", text_color=ERROR)
        error.pack(pady=(6, 0))

        def create():
            name = name_entry.get().strip()
            try:
                start, end = date.fromisoformat(start_entry.get().strip()), date.fromisoformat(end_entry.get().strip())
            except ValueError:
                return error.configure(text="Dates must look like 2026-10-11.")
            if not name:
                return error.configure(text="The task needs a name.")
            if end < start:
                return error.configure(text="The end date is before the start date.")
            if not (dataT.is_plausible_year(start) and dataT.is_plausible_year(end)):
                # Une faute de frappe sur l'année rendait la timeline inutilisable
                return error.configure(text=f"Years must be between {dataT.MIN_YEAR} and {dataT.MAX_YEAR}.")
            task_id = dataT.new_task_id(self.tasks)
            self.tasks[task_id] = {"name" : name, "start" : start.isoformat(), "end" : end.isoformat(),
                                   "color" : state["color"], "done" : False}
            self.selected = task_id
            self._save()
            popup.destroy()
            self.render()

        ctk.CTkButton(color_row, text="Create Task", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      text_color=ON_ACCENT, corner_radius=8, command=create).pack(side=ctk.RIGHT)
        popup.bind("<Return>", lambda e: create())
        popup.after(200, name_entry.focus_set)

    def open_details_popup(self):
        popup = _popup(self.gui, "Workspace Details", "420x300")
        body = ctk.CTkFrame(popup, fg_color=PANEL)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        stats = dataT.compute_stats(self.tasks)
        rows = (("Name", self.workspace["name"]), ("File", self.path),
                ("Created", self.workspace.get("created", "-")), ("Tasks", stats["total_tasks"]),
                ("Done", stats["total_completed"]), ("Late", stats["late_tasks"]))
        for label, value in rows:
            line = ctk.CTkFrame(body, fg_color="transparent")
            line.pack(fill="x", padx=16, pady=(8, 0))
            ctk.CTkLabel(line, text=label, text_color=MUTED, width=90, anchor="w").pack(side=ctk.LEFT)
            # wraplength : le chemin du fichier peut être long
            ctk.CTkLabel(line, text=str(value), text_color=TEXT, anchor="w", justify="left",
                         wraplength=280).pack(side=ctk.LEFT)

    def open_settings_popup(self):
        popup = _popup(self.gui, "Workspace Settings", "360x200")
        body = ctk.CTkFrame(popup, fg_color=PANEL)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(body, text="Default view when opening this project", text_color=TEXT).pack(padx=16, pady=(16, 8))
        default_view = ctk.CTkSegmentedButton(body, values=["Days", "Weeks", "Months"])
        default_view.set(self.settings.get("default_view", "Weeks"))
        default_view.pack(pady=(0, 16))

        def save():
            self.settings["default_view"] = default_view.get()
            dataT.save_project(self.workspace_id, self.project)
            popup.destroy()
        ctk.CTkButton(body, text="Save", fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=ON_ACCENT,
                      corner_radius=8, command=save).pack()

    def close_project(self):
        self.gui.unbind("<Control-o>")  # Le raccourci n'existe que sur le dashboard
        if self.on_close_project:
            self.on_close_project()

    def open_other_project(self):
        prj_id = choose_project_file(self.gui)
        if prj_id is not None and self.on_open_project:
            self.gui.unbind("<Control-o>")
            self.on_open_project(prj_id)


class Recent_Projects_Window:
    recent_projects : ctk.CTkFrame
    gui : ctk.CTk
    _data : dict
    projects_data : dict

    def __init__(self, root : ctk.CTk, workspaces : dict | None = None, close_window_callback = None, open_dashboard_callback = None):
        self.gui, self._data, self.recent_projects = get_recent_projects_gui(root)
        self.close_window = close_window_callback
        self.open_dashboard = open_dashboard_callback
        self.projects_data = {} if not workspaces else workspaces
        self.projects_buttons : list = []
        self._data["create_new"].configure(command=self.create_new_project)
        self._data["open_existing"].configure(command=self.find_existing)
        self.refresh_projects()

    def refresh_projects(self):
        for prj_dt in self.projects_buttons:
            prj_dt.destroy()
        self.projects_buttons = []
        if not self.projects_data:
            empty = ctk.CTkLabel(self.recent_projects, text="No projects yet.\nCreate one to get started.", text_color=MUTED)
            empty.pack(pady=40)
            self.projects_buttons.append(empty)
            return
        
        ordered = sorted(self.projects_data.items(), key=lambda kv: kv[1].get("last_opened", ""), reverse=True)
        for prj_id, pData in ordered:
            when = pData.get("last_opened", pData.get("created", ""))
            folder = os.path.basename(os.path.dirname(pData.get("path", ""))) or "?"
            prj_button = ctk.CTkButton(self.recent_projects, text=f"{pData['name']}\n{folder}  •  {when}", anchor="w", height=44, fg_color="transparent", hover_color=HOVER, text_color=TEXT, corner_radius=8, command=lambda prj_id=prj_id: self.open_project(prj_id))
            prj_button.pack(fill="x", padx=6, pady=3)
            self.projects_buttons.append(prj_button)

    def open_project(self, prj_id : int):
        if self.open_dashboard:
            self.open_dashboard(prj_id)

    def create_new_project(self):
        create_new_popup = _popup(self.gui, "Create A New Project", "400x300")

        def close_popup():
            create_new_popup.destroy()
            if self.gui.winfo_exists():
                self.gui.attributes("-topmost", True)
        create_new_popup.protocol("WM_DELETE_WINDOW", close_popup)

        def confirm_creation(prj_name : str):
            prj_name = prj_name.strip()
            if submit_request.cget("state") == "disabled":
                return
            prj_id = dataT.create_project(prj_name)
            if prj_id is None:
                existence_verifier.configure(text="Could not create the project file.", text_color=ERROR)
                return
            close_popup()
            self.open_project(prj_id)

        els_cont = ctk.CTkFrame(create_new_popup, fg_color=PANEL)
        els_cont.pack(fill="both", expand=True, padx=10, pady=10)

        def check_existence(var_name, index, mode):
            current_text = name_txt_var.get().strip()
            if len(current_text) == 0:
                submit_request.configure(state="disabled")
                existence_verifier.configure(text="The name cannot be empty.", text_color=ERROR)
            elif len(current_text) <= 3:
                submit_request.configure(state="disabled")
                existence_verifier.configure(text="The name should be longer than 3 chars.", text_color=ERROR)
            elif not dataT.is_valid_project_name(current_text):
                submit_request.configure(state="disabled")
                existence_verifier.configure(text=f"The name cannot contain {dataT.INVALID_NAME_CHARS}", text_color=ERROR)
            elif not dataT.is_name_taken(current_text):
                existence_verifier.configure(text="The name is available.", text_color=SUCCESS)
                submit_request.configure(state="normal")
            else:
                existence_verifier.configure(text="The name is NOT available.", text_color=ERROR)
                submit_request.configure(state="disabled")

        name_txt_var = ctk.StringVar()
        name_txt_var.trace_add("write", check_existence)
        prompt = ctk.CTkLabel(els_cont, text="Enter the name of your new project :", fg_color="transparent", text_color=TEXT, font=("Segoe UI", 14))
        prompt.pack(pady=8)
        name_entry = ctk.CTkEntry(els_cont, textvariable=name_txt_var, height=35, corner_radius=10, width=200, placeholder_text="Project name", bg_color="transparent", fg_color=("#FFFFFF", "#11151B"), text_color=TEXT, placeholder_text_color=MUTED, border_color=BORDER)
        name_entry.pack(pady=(0, 8))
        existence_verifier = ctk.CTkLabel(els_cont, text="The name cannot be empty.", text_color=ERROR, fg_color="transparent", bg_color="transparent")
        existence_verifier.pack(pady=(0, 8))
        submit_request = ctk.CTkButton(els_cont, text="Create Project", command=lambda: confirm_creation(name_txt_var.get()), fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=ON_ACCENT, font=("Segoe UI", 14), corner_radius=10, height=35)
        submit_request.pack(pady=(0, 8))
        submit_request.configure(state="disabled")
        create_new_popup.bind("<Return>", lambda e: confirm_creation(name_txt_var.get()))

        self.gui.attributes("-topmost", False)
        create_new_popup.attributes("-topmost", True)
        create_new_popup.after(200, name_entry.focus_set)

    def find_existing(self):
        self.gui.attributes("-topmost", False)  # Sinon la fenêtre cache le sélecteur de fichier
        prj_id = choose_project_file(self.gui)
        self.gui.attributes("-topmost", True)
        if prj_id is not None:
            self.open_project(prj_id)

    def start_loop(self):
        self.gui.mainloop()

    def assign_projects(self, new_projects : dict, refresh : bool = False):
        self.projects_data = new_projects.copy()
        if refresh: self.refresh_projects()


class App_Manager:
    def __init__(self):
        self.root = ctk.CTk()
        self.screen = None

    def _clear(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.attributes("-topmost", False)
        self.root.state("normal")
        self.root.minsize(1, 1)
        self.root.resizable(True, True)

    def open_recent_project(self):
        self.root.after(0, self._show_recent_projects)

    def _show_recent_projects(self):
        self._clear()
        self.screen = Recent_Projects_Window(self.root, dataT.get_workspaces(), open_dashboard_callback=self.open_dashboard)

    def open_dashboard(self, prj_id : int):
        self.root.after(0, lambda: self._show_dashboard(prj_id))

    def _show_dashboard(self, prj_id : int):
        if dataT.load_project(prj_id) is None:
            path = dataT.project_path(prj_id) or "?"
            messagebox.showerror("Open Project", f"The project file can't be opened:\n{path}\n\n"
                                 "It was moved, deleted or damaged. It has been removed from the recent list.", parent=self.root)
            dataT.remove_workspace(prj_id)
            if isinstance(self.screen, Recent_Projects_Window):
                self._show_recent_projects()
            return
        dataT.update_workspace(prj_id, last_opened=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self._clear()
        self.screen = Main_Dashboard(self.root, prj_id, on_close_project=self.open_recent_project,
                                     on_open_project=self.open_dashboard)
        self.root.after(10, lambda: self.root.state("zoomed"))

    def start_loop(self):
        self.root.mainloop()
