import tkinter as tk
from tkinter import ttk

LIST_BG = "lightgray"
LIST_HOVER_BG = "gray75"

# Gantt : 1 jour = PX_PER_DAY pixels (une seule constante à changer pour tout redimensionner)
PX_PER_DAY = 30
ROW_HEIGHT = 30          # Hauteur d'une ligne de tâches dans un groupe
ROW_PADDING = 4          # Espace vertical entre la barre de tâche et le bord de sa ligne
GROUP_LABEL_WIDTH = 140  # Colonne de gauche avec le nom du groupe
GANTT_BG = "white"
GROUP_BG = "gray95"
SELECTED_BORDER = "black"     # Bordure de la tâche sélectionnée
DRAG_PLACEHOLDER = "gray80"   # Couleur de la tâche d'origine pendant un drag
RESIZE_EDGE = 6               # Zone (px) sur les bords d'une tâche sélectionnée pour changer sa durée


def fill_recent_projects(frame:tk.Frame, projects:list):
    # Chaque projet : {"name": ..., "folder": ..., "date": ...} (textes déjà prêts à afficher)
    header = tk.Frame(frame, bg=LIST_BG)
    header.pack(fill="x", padx=8, pady=(8, 2))
    tk.Label(header, text="Name", bg=LIST_BG, fg="gray25").pack(side=tk.LEFT)
    tk.Label(header, text="Date modified", bg=LIST_BG, fg="gray25").pack(side=tk.RIGHT)
    tk.Frame(frame, bg="gray60", height=1).pack(fill="x", padx=8)

    if not projects:
        tk.Label(frame, text="No recent projects", bg=LIST_BG, fg="gray40").pack(pady=20)
        return

    for project in projects:
        row = tk.Frame(frame, bg=LIST_BG, cursor="hand2")
        row.pack(fill="x", padx=8)
        # La date d'abord, à droite, pour que le nom prenne le reste de la largeur
        date = tk.Label(row, text=project["date"], bg=LIST_BG, fg="gray25")
        date.pack(side=tk.RIGHT, anchor="n", pady=6)
        name = tk.Label(row, text=project["name"], bg=LIST_BG, font=("Segoe UI", 10), anchor="w")
        name.pack(fill="x", pady=(6, 0))
        folder = tk.Label(row, text=project["folder"], bg=LIST_BG, fg="gray35", font=("Segoe UI", 8), anchor="w")
        folder.pack(fill="x", pady=(0, 6))
        tk.Frame(frame, bg="gray60", height=1).pack(fill="x", padx=8)

        widgets = (row, date, name, folder)
        # Survol : on colore toute la ligne, peu importe le widget sous la souris
        def set_bg(color, widgets=widgets):
            for w in widgets:
                w.configure(bg=color)
        for w in widgets:
            w.bind("<Enter>", lambda e, s=set_bg: s(LIST_HOVER_BG))
            w.bind("<Leave>", lambda e, s=set_bg: s(LIST_BG))


class GanttView:
    # Viewport -> groupe (catégorie) -> tâches.
    # Chaque méthode ne touche que le widget concerné : jamais de redessin complet.

    def __init__(self, viewport:tk.Frame):
        self.viewport = viewport
        self.groups = {}  # group_id -> {"frame", "lane", "rows": [[task_id, ...], ...]}
        self.tasks = {}   # task_id -> {"widget", "label", "group_id", "name", "color", "start", "length", "row"}
        self.total_days = 0
        self.min_width = 0  # Largeur visible du canvas : le Gantt ne sera jamais plus étroit
        self.selected = None
        self._drag = None  # Infos du drag en cours (None quand on ne drag pas)

        # Callbacks pour brancher la logique plus tard (chacun reçoit des ids, pas des widgets)
        self.on_select = None             # on_select(task_id ou None)
        self.on_task_moved = None         # on_task_moved(task_id, group_id, start) après un drag
        self.on_task_resized = None       # on_task_resized(task_id, start, length) après avoir tiré un bord
        self.on_task_right_click = None   # on_task_right_click(task_id)

        # Cadre invisible qui fixe la largeur du viewport : tous les groupes s'étirent dessus,
        # donc élargir le planning = changer la largeur de ce seul widget
        self.width_spacer = tk.Frame(viewport, height=0, width=GROUP_LABEL_WIDTH)
        self.width_spacer.pack(side=tk.BOTTOM, anchor="w")

    # ---------- Groupes ----------

    def add_group(self, group_id, name:str):
        frame = tk.Frame(self.viewport, bg=GROUP_BG, highlightthickness=1, highlightbackground="gray75")
        frame.pack(fill="x", pady=(0, 2))  # pack l'ajoute en bas, sans bouger les autres groupes

        label = tk.Label(frame, text=name, bg=GROUP_BG, anchor="nw", padx=8, pady=6)
        label.place(x=0, y=0, width=GROUP_LABEL_WIDTH, relheight=1)

        # Zone où les tâches sont placées avec place(x=...)
        lane = tk.Frame(frame, bg=GANTT_BG)
        lane.place(x=GROUP_LABEL_WIDTH, y=0, relwidth=1, width=-GROUP_LABEL_WIDTH, relheight=1)
        lane.bind("<Button-1>", lambda e: self.select_task(None))  # Clic dans le vide = désélectionner

        self.groups[group_id] = {"frame": frame, "lane": lane, "rows": []}
        self._resize_group(group_id)

    def remove_group(self, group_id):
        for task_id in [t for t, task in self.tasks.items() if task["group_id"] == group_id]:
            if self.selected == task_id:
                self.select_task(None)
            del self.tasks[task_id]
        self.groups.pop(group_id)["frame"].destroy()

    # ---------- Tâches ----------

    def add_task(self, group_id, task_id, name:str, start:int, length:int, color:str="steelblue"):
        # start et length sont en jours (colonnes), pas en vraies dates
        self.tasks[task_id] = {"widget": None, "label": None, "group_id": group_id, "name": name,
                               "color": color, "start": start, "length": length, "row": None}
        self._make_task_widget(task_id)
        self._put_in_free_row(task_id)
        self._extend_days(start + length)

    def move_task(self, task_id, start:int, length:int=None, group_id=None):
        task = self.tasks[task_id]
        old_group = task["group_id"]
        self._take_out_of_row(task_id)
        task["start"] = start
        if length is not None:
            task["length"] = length
        if group_id is not None and group_id != old_group:
            # tkinter ne peut pas changer le parent d'un widget : on recrée juste celui-ci
            task["widget"].destroy()
            task["group_id"] = group_id
            self._make_task_widget(task_id)
        self._put_in_free_row(task_id)
        self._extend_days(task["start"] + task["length"])
        self._shrink_group(old_group)

    def set_task_color(self, task_id, color:str):
        task = self.tasks[task_id]
        task["color"] = color
        task["label"].configure(bg=color)
        task["widget"].configure(bg=color)
        self._set_highlight(task_id, task_id == self.selected)

    def remove_task(self, task_id):
        if self.selected == task_id:
            self.select_task(None)
        group_id = self.tasks[task_id]["group_id"]
        self._take_out_of_row(task_id)
        self.tasks.pop(task_id)["widget"].destroy()
        self._shrink_group(group_id)

    # ---------- Sélection ----------

    def select_task(self, task_id):
        # task_id = None pour désélectionner
        if self.selected in self.tasks:
            self._set_highlight(self.selected, False)
        self.selected = task_id
        if task_id is not None:
            self._set_highlight(task_id, True)
        if self.on_select:
            self.on_select(task_id)

    def _set_highlight(self, task_id, selected:bool):
        # La bordure existe toujours (2px) : non sélectionnée elle a la couleur de la tâche,
        # donc la tâche ne change pas de taille quand on la sélectionne
        task = self.tasks[task_id]
        border = SELECTED_BORDER if selected else task["color"]
        task["widget"].configure(highlightbackground=border, highlightcolor=border)

    # ---------- Drag & drop ----------

    def _on_press(self, event, task_id):
        # Le bord est testé AVANT de sélectionner : on ne redimensionne qu'une tâche déjà sélectionnée
        edge = self._edge_at(task_id, event.x_root)
        self.select_task(task_id)
        task = self.tasks[task_id]
        if edge:
            self._drag = {"task_id": task_id, "mode": edge, "start": task["start"], "length": task["length"]}
            return
        widget = task["widget"]
        self._drag = {"task_id": task_id, "mode": "move", "x0": event.x_root, "y0": event.y_root,
                      "offset_x": event.x_root - widget.winfo_rootx(),
                      "offset_y": event.y_root - widget.winfo_rooty(), "ghost": None}

    def _on_motion(self, event):
        drag = self._drag
        if drag is None:
            return
        if drag["mode"] != "move":
            return self._on_resize_motion(event, drag)
        task = self.tasks[drag["task_id"]]
        if drag["ghost"] is None:
            # Petit seuil pour qu'un simple clic ne soit pas pris pour un drag
            if abs(event.x_root - drag["x0"]) < 4 and abs(event.y_root - drag["y0"]) < 4:
                return
            # Le "fantôme" vit dans le viewport (parent commun de tous les groupes),
            # donc il peut passer d'un groupe à l'autre
            ghost = tk.Frame(self.viewport, bg=task["color"], highlightthickness=2,
                             highlightbackground=SELECTED_BORDER, highlightcolor=SELECTED_BORDER)
            tk.Label(ghost, text=task["name"], bg=task["color"], fg="white", anchor="w", padx=4).pack(fill="both", expand=True)
            drag["ghost"] = ghost
            # La tâche d'origine reste à sa place mais grisée, pour voir d'où elle part
            task["widget"].configure(bg=DRAG_PLACEHOLDER)
            task["label"].configure(bg=DRAG_PLACEHOLDER, fg="gray40")

        x = event.x_root - self.viewport.winfo_rootx() - drag["offset_x"]
        y = event.y_root - self.viewport.winfo_rooty() - drag["offset_y"]
        # Horizontal : on aimante sur les jours. Vertical : suit la souris librement
        drag["start"] = max(0, round((x - GROUP_LABEL_WIDTH) / PX_PER_DAY))
        drag["group_id"] = self._group_at(event.y_root) or task["group_id"]
        drag["ghost"].place(x=GROUP_LABEL_WIDTH + drag["start"] * PX_PER_DAY, y=y,
                            width=task["length"] * PX_PER_DAY, height=ROW_HEIGHT - 2 * ROW_PADDING)
        drag["ghost"].lift()

    def _on_resize_motion(self, event, drag):
        # Le bord tiré suit la souris, aimanté sur les jours ; l'autre bord ne bouge pas
        task = self.tasks[drag["task_id"]]
        lane = self.groups[task["group_id"]]["lane"]
        day = round((event.x_root - lane.winfo_rootx()) / PX_PER_DAY)
        end = task["start"] + task["length"]
        if drag["mode"] == "right":
            drag["start"], drag["length"] = task["start"], max(1, day - task["start"])
        else:
            drag["start"] = max(0, min(end - 1, day))
            drag["length"] = end - drag["start"]
        task["widget"].place_configure(x=drag["start"] * PX_PER_DAY, width=drag["length"] * PX_PER_DAY)
        self._extend_days(drag["start"] + drag["length"])

    def _on_release(self, event):
        drag, self._drag = self._drag, None
        if drag is None:
            return
        if drag["mode"] != "move":
            task_id = drag["task_id"]
            task = self.tasks[task_id]
            if (drag["start"], drag["length"]) != (task["start"], task["length"]):
                # move_task recalcule la ligne (auto-stack) si la tâche chevauche maintenant une autre
                self.move_task(task_id, drag["start"], drag["length"])
                if self.on_task_resized:
                    self.on_task_resized(task_id, drag["start"], drag["length"])
            return
        if drag["ghost"] is None:
            return  # Simple clic : la sélection est déjà faite dans _on_press
        drag["ghost"].destroy()
        task_id = drag["task_id"]
        task = self.tasks[task_id]
        task["widget"].configure(bg=task["color"])
        task["label"].configure(bg=task["color"], fg="white")
        self.move_task(task_id, drag["start"], group_id=drag["group_id"])
        self._set_highlight(task_id, True)
        if self.on_task_moved:
            self.on_task_moved(task_id, drag["group_id"], drag["start"])

    def _on_right_click(self, event, task_id):
        if self.on_task_right_click:
            self.on_task_right_click(task_id)

    def _edge_at(self, task_id, x_root:int):
        # "left" / "right" si la souris est sur un bord de la tâche sélectionnée, sinon None
        if task_id != self.selected:
            return None
        widget = self.tasks[task_id]["widget"]
        x = x_root - widget.winfo_rootx()
        if x <= RESIZE_EDGE:
            return "left"
        if x >= widget.winfo_width() - RESIZE_EDGE:
            return "right"
        return None

    def _on_hover(self, event, task_id):
        # Curseur ↔ sur les bords de la tâche sélectionnée, pour montrer qu'on peut la redimensionner
        if self._drag is not None:
            return
        cursor = "sb_h_double_arrow" if self._edge_at(task_id, event.x_root) else "hand2"
        task = self.tasks[task_id]
        task["widget"].configure(cursor=cursor)
        task["label"].configure(cursor=cursor)

    def _group_at(self, y_root:int):
        # Quel groupe est sous la souris (None si aucun)
        y = y_root - self.viewport.winfo_rooty()
        for group_id, group in self.groups.items():
            frame = group["frame"]
            if frame.winfo_y() <= y < frame.winfo_y() + frame.winfo_height():
                return group_id
        return None

    # ---------- Interne ----------

    def _make_task_widget(self, task_id):
        task = self.tasks[task_id]
        # Frame + Label et pas Button, sinon le Button gêne le drag
        widget = tk.Frame(self.groups[task["group_id"]]["lane"], bg=task["color"], cursor="hand2",
                          highlightthickness=2, highlightbackground=task["color"], highlightcolor=task["color"])
        label = tk.Label(widget, text=task["name"], bg=task["color"], fg="white", anchor="w", padx=4)
        label.pack(fill="both", expand=True)
        for w in (widget, label):  # Le clic peut tomber sur le Frame ou sur le Label
            w.bind("<ButtonPress-1>", lambda e: self._on_press(e, task_id))
            w.bind("<B1-Motion>", self._on_motion)
            w.bind("<Motion>", lambda e: self._on_hover(e, task_id))
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Button-3>", lambda e: self._on_right_click(e, task_id))
        task["widget"], task["label"] = widget, label
        if task_id == self.selected:
            self._set_highlight(task_id, True)

    def _overlaps(self, task_id, other_id) -> bool:
        a, b = self.tasks[task_id], self.tasks[other_id]
        return a["start"] < b["start"] + b["length"] and b["start"] < a["start"] + a["length"]

    def _put_in_free_row(self, task_id):
        # Auto-stack : première ligne du groupe où la tâche ne chevauche personne, sinon nouvelle ligne
        task = self.tasks[task_id]
        rows = self.groups[task["group_id"]]["rows"]
        for index, row in enumerate(rows):
            if not any(self._overlaps(task_id, other) for other in row):
                break
        else:
            rows.append([])
            index = len(rows) - 1
            self._resize_group(task["group_id"])
        rows[index].append(task_id)
        task["row"] = index
        task["widget"].place(x=task["start"] * PX_PER_DAY, y=index * ROW_HEIGHT + ROW_PADDING,
                             width=task["length"] * PX_PER_DAY, height=ROW_HEIGHT - 2 * ROW_PADDING)

    def _take_out_of_row(self, task_id):
        task = self.tasks[task_id]
        self.groups[task["group_id"]]["rows"][task["row"]].remove(task_id)

    def _shrink_group(self, group_id):
        # On enlève seulement les lignes vides du bas, pour ne pas déplacer les autres tâches
        rows = self.groups[group_id]["rows"]
        if rows and not rows[-1]:
            while rows and not rows[-1]:
                rows.pop()
            self._resize_group(group_id)

    def _resize_group(self, group_id):
        rows = max(1, len(self.groups[group_id]["rows"]))
        self.groups[group_id]["frame"].configure(height=rows * ROW_HEIGHT)

    def set_min_width(self, width:int):
        # Appelé quand la fenêtre change de taille : les lignes remplissent toute la largeur visible
        self.min_width = width
        self._update_width()

    def _extend_days(self, last_day:int):
        if last_day > self.total_days:
            self.total_days = last_day
            self._update_width()

    def _update_width(self):
        content_width = GROUP_LABEL_WIDTH + self.total_days * PX_PER_DAY
        self.width_spacer.configure(width=max(self.min_width, content_width))


def get_main_page() -> tuple:
    root = tk.Tk()
    root.title("Gantt Manager")

    # Thème Windows natif pour les widgets ttk (boutons, scrollbars), "clam" ailleurs
    style = ttk.Style(root)
    style.theme_use("vista" if "vista" in style.theme_names() else "clam")
    root.geometry("1080x720")
    root.state("zoomed")
    #root.attributes("-fullscreen", True)

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg="lightgray", highlightthickness=0)
    v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # grid pour que les deux scrollbars se rejoignent proprement dans le coin
    canvas.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)

    viewport = tk.Frame(canvas, bg="lightgray")
    canvas.create_window((0, 0), window=viewport, anchor="nw")
    # Dès que le contenu change de taille, on met à jour la zone scrollable
    viewport.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Molette = vertical, Shift + molette = horizontal (seulement quand la souris est sur le Gantt)
    def on_wheel(event):
        canvas.yview_scroll(-event.delta // 120, "units")
    def on_shift_wheel(event):
        canvas.xview_scroll(-event.delta // 120, "units")
    def bind_wheel(event):
        canvas.bind_all("<MouseWheel>", on_wheel)
        canvas.bind_all("<Shift-MouseWheel>", on_shift_wheel)
    def unbind_wheel(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Shift-MouseWheel>")
    canvas.bind("<Enter>", bind_wheel)
    canvas.bind("<Leave>", unbind_wheel)

    gantt = GanttView(viewport)
    # Le Gantt fait au moins la largeur de la fenêtre (sinon les lignes s'arrêtent à la dernière tâche)
    canvas.bind("<Configure>", lambda e: gantt.set_min_width(e.width))

    return root, gantt


def get_recent_projects(root:tk.Tk, projects:list=None, on_create=None, on_open_existing=None) -> tk.Toplevel:
    # Toplevel et pas Tk : une seule fenêtre racine par programme
    window = tk.Toplevel(root)
    window.title("Recent Projects")
    window.geometry("650x450")
    window.resizable(False, False)

    parent_frame = tk.Frame(window)
    parent_frame.pack(fill="both", expand=True, pady=15)

    manip_frame = tk.Frame(parent_frame, bg="lightgray", width=180)
    manip_frame.pack(fill="y", side=tk.LEFT, padx=10)
    manip_frame.pack_propagate(False)  # Garde la largeur fixe malgré la taille des boutons

    # on_create / on_open_existing : à brancher plus tard, quand on aura le système IO
    create_new_button = ttk.Button(manip_frame, text="Create New Project", command=on_create)
    create_new_button.pack(pady=(40, 10))
    open_existing = ttk.Button(manip_frame, text="Open Existing Project", command=on_open_existing)
    open_existing.pack(pady=(10, 40))

    recent_prjs_frame = tk.Frame(parent_frame, bg="lightgray")
    recent_prjs_frame.pack(fill="both", expand=True, side=tk.LEFT, padx=10)
    fill_recent_projects(recent_prjs_frame, projects or [])
    window.attributes("-topmost", True)

    return window
