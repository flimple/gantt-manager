import os
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

# Fenêtre d'accueil
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
WELCOME_BG = "#f9f8f3"   # Même couleur que le fond des images du logo, pour qu'elles se fondent
CARD_BG = "white"
CARD_BORDER = "#dcdad2"
BRAND_COLOR = "#1d3a5f"  # Bleu foncé du titre "GANTTIFY"
LIST_BG = CARD_BG
LIST_HOVER_BG = "#eef2f7"

# Gantt : 1 jour = PX_PER_DAY pixels (une seule constante à changer pour tout redimensionner)
PX_PER_DAY = 30
ROW_HEIGHT = 30          # Hauteur d'une ligne de tâches dans un groupe
ROW_PADDING = 4          # Espace vertical entre la barre de tâche et le bord de sa ligne
SIDEBAR_WIDTH = 160      # Colonne de gauche avec les noms des groupes
HEADER_ROW_HEIGHT = 22   # En-tête des dates : une ligne pour les mois, une pour les jours
HEADER_HEIGHT = 2 * HEADER_ROW_HEIGHT
EXTRA_DAYS = 10          # Jours affichés en plus après la dernière tâche
MIN_TIMELINE_DAYS = 365  # Le planning montre au moins 1 an, pour que la scrollbar horizontale serve
GROW_DAYS = 90           # Jours ajoutés quand on arrive au bout à droite
LINE_LENGTH = 100000     # Longueur des lignes de grille/séparateurs (plus grand que tout planning)
GANTT_BG = "white"
GROUP_BG = "gray95"
HEADER_BG = "white"
GROUP_SEPARATOR = "gray75"
GRID_COLOR = "gray88"
WEEKEND_BG = "gray96"
SELECTED_BORDER = "black"     # Bordure de la tâche sélectionnée
DRAG_PLACEHOLDER = "gray80"   # Couleur de la tâche d'origine pendant un drag
RESIZE_EDGE = 6               # Zone (px) sur les bords d'une tâche sélectionnée pour changer sa durée
GROUP_RESIZE_EDGE = 4         # Zone (px) autour de la ligne sous un groupe pour changer sa hauteur


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
    # 3 canvas qui scrollent ensemble :
    #   header  (en haut)  : mois + numéros des jours, suit le scroll horizontal
    #   sidebar (à gauche) : noms des groupes, suit le scroll vertical
    #   body    (centre)   : grille des jours + tâches (des widgets posés sur le canvas)
    # Chaque méthode ne touche que les éléments concernés : jamais de redessin complet des tâches.

    def __init__(self, body:tk.Canvas, sidebar:tk.Canvas, header:tk.Canvas, start_date:date=None):
        self.body, self.sidebar, self.header = body, sidebar, header
        self.start_date = start_date or date.today()  # Date affichée pour le jour 0 (juste de l'affichage)
        self.groups = {}       # group_id -> {"name", "tag", "rows": [[task_id, ...], ...], "y", "height"}
        self.group_order = []  # Ordre d'affichage des groupes, de haut en bas
        self.tasks = {}        # task_id -> {"item", "widget", "label", "group_id", "name", "color", "start", "length", "row"}
        self.total_days = 0
        self.timeline_days = MIN_TIMELINE_DAYS  # Jours affichés, même sans tâches (grandit en scrollant)
        self.min_width = 0     # Taille visible du body : la grille la remplit toujours
        self.min_height = 0
        self.selected = None
        self._drag = None      # Infos du drag en cours (None quand on ne drag pas)
        self._drawn_width = None
        self._next_tag = 0

        # Callbacks pour brancher la logique plus tard (chacun reçoit des ids, pas des widgets)
        self.on_select = None             # on_select(task_id ou None)
        self.on_task_moved = None         # on_task_moved(task_id, group_id, start) après un drag
        self.on_task_resized = None       # on_task_resized(task_id, start, length) après avoir tiré un bord
        self.on_task_right_click = None   # on_task_right_click(task_id)
        self.on_group_resized = None      # on_group_resized(group_id, height) après avoir tiré la ligne d'un groupe

        # Tirer la ligne sous un nom de groupe (dans la sidebar) = changer la hauteur du groupe
        self._group_drag = None
        sidebar.bind("<Motion>", self._on_sidebar_hover)
        sidebar.bind("<ButtonPress-1>", self._on_sidebar_press)
        sidebar.bind("<B1-Motion>", self._on_sidebar_drag)
        sidebar.bind("<ButtonRelease-1>", self._on_sidebar_release)

        body.bind("<Button-1>", lambda e: self.select_task(None))  # Clic dans le vide = désélectionner
        self._on_width_change()

    # ---------- Groupes ----------

    def add_group(self, group_id, name:str):
        # Tag interne (g0, g1...) : les ids peuvent contenir des espaces, pas les tags du canvas
        tag = f"g{self._next_tag}"
        self._next_tag += 1
        y = self._content_height()
        # custom_height : hauteur choisie en tirant la ligne sous le groupe (0 = automatique)
        self.groups[group_id] = {"name": name, "tag": tag, "rows": [], "y": y, "height": ROW_HEIGHT,
                                 "custom_height": 0}
        self.group_order.append(group_id)

        # Ligne de séparation sous le groupe (très longue : pas besoin de la rallonger plus tard)
        self.body.create_line(0, y + ROW_HEIGHT, LINE_LENGTH, y + ROW_HEIGHT, fill=GROUP_SEPARATOR,
                              tags=(tag, tag + "_sep", "separator"))
        self.sidebar.create_line(0, y + ROW_HEIGHT, SIDEBAR_WIDTH, y + ROW_HEIGHT, fill=GROUP_SEPARATOR,
                                 tags=(tag, tag + "_sep"))
        self.sidebar.create_text(10, y + ROW_HEIGHT // 2, text=name, anchor="w", font=("Segoe UI", 9), tags=(tag,))
        self._update_scrollregion()

    def remove_group(self, group_id):
        group = self.groups[group_id]
        for task_id in [t for t, task in self.tasks.items() if task["group_id"] == group_id]:
            if self.selected == task_id:
                self.select_task(None)
            self.tasks.pop(task_id)["widget"].destroy()
        self.body.delete(group["tag"])
        self.sidebar.delete(group["tag"])
        self._shift_groups_after(group_id, -group["height"])
        self.group_order.remove(group_id)
        del self.groups[group_id]
        self._update_scrollregion()

    # ---------- Tâches ----------

    def add_task(self, group_id, task_id, name:str, start:int, length:int, color:str="steelblue"):
        # start et length sont en jours (colonnes) ; le jour 0 correspond à start_date
        self.tasks[task_id] = {"item": None, "widget": None, "label": None, "group_id": group_id, "name": name,
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
            # Tout est dans le même canvas : on change juste le tag du groupe, pas besoin de recréer le widget
            self.body.dtag(task["item"], self.groups[old_group]["tag"])
            self.body.addtag_withtag(self.groups[group_id]["tag"], task["item"])
            task["group_id"] = group_id
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
        task = self.tasks.pop(task_id)
        self.body.delete(task["item"])
        task["widget"].destroy()
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

    def _canvas_xy(self, event):
        # Position de la souris dans le canvas (en tenant compte du scroll)
        return (self.body.canvasx(event.x_root - self.body.winfo_rootx()),
                self.body.canvasy(event.y_root - self.body.winfo_rooty()))

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
            # Le "fantôme" suit la souris ; la tâche d'origine reste grisée à sa place
            ghost = tk.Frame(self.body, bg=task["color"], highlightthickness=2,
                             highlightbackground=SELECTED_BORDER, highlightcolor=SELECTED_BORDER)
            tk.Label(ghost, text=task["name"], bg=task["color"], fg="white", anchor="w", padx=4).pack(fill="both", expand=True)
            drag["ghost"] = ghost
            drag["ghost_item"] = self.body.create_window(0, 0, window=ghost, anchor="nw",
                                                         width=task["length"] * PX_PER_DAY,
                                                         height=ROW_HEIGHT - 2 * ROW_PADDING)
            task["widget"].configure(bg=DRAG_PLACEHOLDER)
            task["label"].configure(bg=DRAG_PLACEHOLDER, fg="gray40")

        x, y = self._canvas_xy(event)
        # Horizontal : on aimante sur les jours. Vertical : suit la souris librement
        drag["start"] = max(0, round((x - drag["offset_x"]) / PX_PER_DAY))
        drag["group_id"] = self._group_at(y) or task["group_id"]
        self.body.coords(drag["ghost_item"], drag["start"] * PX_PER_DAY, y - drag["offset_y"])
        drag["ghost"].lift()

    def _on_resize_motion(self, event, drag):
        # Le bord tiré suit la souris, aimanté sur les jours ; l'autre bord ne bouge pas
        task = self.tasks[drag["task_id"]]
        day = round(self._canvas_xy(event)[0] / PX_PER_DAY)
        end = task["start"] + task["length"]
        if drag["mode"] == "right":
            drag["start"], drag["length"] = task["start"], max(1, day - task["start"])
        else:
            drag["start"] = max(0, min(end - 1, day))
            drag["length"] = end - drag["start"]
        _, y = self.body.coords(task["item"])
        self.body.coords(task["item"], drag["start"] * PX_PER_DAY, y)
        self.body.itemconfigure(task["item"], width=drag["length"] * PX_PER_DAY)
        self._extend_days(drag["start"] + drag["length"])

    def _on_release(self, event):
        drag, self._drag = self._drag, None
        if drag is None:
            return
        task_id = drag["task_id"]
        task = self.tasks[task_id]
        if drag["mode"] != "move":
            if (drag["start"], drag["length"]) != (task["start"], task["length"]):
                # move_task recalcule la ligne (auto-stack) si la tâche chevauche maintenant une autre
                self.move_task(task_id, drag["start"], drag["length"])
                if self.on_task_resized:
                    self.on_task_resized(task_id, drag["start"], drag["length"])
            return
        if drag["ghost"] is None:
            return  # Simple clic : la sélection est déjà faite dans _on_press
        self.body.delete(drag["ghost_item"])
        drag["ghost"].destroy()
        task["widget"].configure(bg=task["color"])
        task["label"].configure(bg=task["color"], fg="white")
        self.move_task(task_id, drag["start"], group_id=drag["group_id"])
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

    # ---------- Hauteur des groupes (sidebar) ----------

    def _group_border_at(self, event):
        # Groupe dont la ligne du bas est sous la souris (None si aucun)
        y = self.sidebar.canvasy(event.y)
        for group_id in self.group_order:
            group = self.groups[group_id]
            if abs(y - (group["y"] + group["height"])) <= GROUP_RESIZE_EDGE:
                return group_id
        return None

    def _on_sidebar_hover(self, event):
        if self._group_drag is None:
            self.sidebar.configure(cursor="sb_v_double_arrow" if self._group_border_at(event) else "")

    def _on_sidebar_press(self, event):
        self._group_drag = self._group_border_at(event)

    def _on_sidebar_drag(self, event):
        group_id = self._group_drag
        if group_id is None:
            return
        group = self.groups[group_id]
        height = max(self._min_group_height(group_id), round(self.sidebar.canvasy(event.y) - group["y"]))
        group["custom_height"] = height
        self._apply_group_height(group_id, height)

    def _on_sidebar_release(self, event):
        group_id, self._group_drag = self._group_drag, None
        if group_id is not None and self.on_group_resized:
            self.on_group_resized(group_id, self.groups[group_id]["height"])

    def _group_at(self, y:float):
        # Quel groupe est à cette hauteur du canvas (None si aucun)
        for group_id in self.group_order:
            group = self.groups[group_id]
            if group["y"] <= y < group["y"] + group["height"]:
                return group_id
        return None

    # ---------- Interne : tâches et lignes ----------

    def _make_task_widget(self, task_id):
        task = self.tasks[task_id]
        # Frame + Label et pas Button, sinon le Button gêne le drag
        widget = tk.Frame(self.body, bg=task["color"], cursor="hand2",
                          highlightthickness=2, highlightbackground=task["color"], highlightcolor=task["color"])
        label = tk.Label(widget, text=task["name"], bg=task["color"], fg="white", anchor="w", padx=4)
        label.pack(fill="both", expand=True)
        for w in (widget, label):  # Le clic peut tomber sur le Frame ou sur le Label
            w.bind("<ButtonPress-1>", lambda e: self._on_press(e, task_id))
            w.bind("<B1-Motion>", self._on_motion)
            w.bind("<Motion>", lambda e: self._on_hover(e, task_id))
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Button-3>", lambda e: self._on_right_click(e, task_id))
        # Tag du groupe sur la tâche : quand un groupe au-dessus grandit, ses tâches bougent avec lui
        task["item"] = self.body.create_window(0, 0, window=widget, anchor="nw",
                                               tags=("task", self.groups[task["group_id"]]["tag"]))
        task["widget"], task["label"] = widget, label

    def _overlaps(self, task_id, other_id) -> bool:
        a, b = self.tasks[task_id], self.tasks[other_id]
        return a["start"] < b["start"] + b["length"] and b["start"] < a["start"] + a["length"]

    def _put_in_free_row(self, task_id):
        # Auto-stack : première ligne du groupe où la tâche ne chevauche personne, sinon nouvelle ligne
        task = self.tasks[task_id]
        group = self.groups[task["group_id"]]
        rows = group["rows"]
        for index, row in enumerate(rows):
            if not any(self._overlaps(task_id, other) for other in row):
                break
        else:
            rows.append([])
            index = len(rows) - 1
            self._resize_group(task["group_id"])
        rows[index].append(task_id)
        task["row"] = index
        self.body.coords(task["item"], task["start"] * PX_PER_DAY, group["y"] + index * ROW_HEIGHT + ROW_PADDING)
        self.body.itemconfigure(task["item"], width=task["length"] * PX_PER_DAY, height=ROW_HEIGHT - 2 * ROW_PADDING)

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

    def _min_group_height(self, group_id) -> int:
        # Hauteur nécessaire pour afficher toutes les lignes de tâches du groupe
        return max(1, len(self.groups[group_id]["rows"])) * ROW_HEIGHT

    def _resize_group(self, group_id):
        # Hauteur choisie à la souris, mais jamais moins que ce que les tâches demandent
        group = self.groups[group_id]
        self._apply_group_height(group_id, max(self._min_group_height(group_id), group["custom_height"]))

    def _apply_group_height(self, group_id, height:int):
        group = self.groups[group_id]
        delta = height - group["height"]
        if delta == 0:
            return
        group["height"] = height
        bottom = group["y"] + height
        self.body.coords(group["tag"] + "_sep", 0, bottom, LINE_LENGTH, bottom)
        self.sidebar.coords(group["tag"] + "_sep", 0, bottom, SIDEBAR_WIDTH, bottom)
        # Les groupes en dessous glissent (avec leurs tâches), sans être recréés
        self._shift_groups_after(group_id, delta)
        self._update_scrollregion()

    def _shift_groups_after(self, group_id, delta:int):
        for other_id in self.group_order[self.group_order.index(group_id) + 1:]:
            other = self.groups[other_id]
            other["y"] += delta
            self.body.move(other["tag"], 0, delta)
            self.sidebar.move(other["tag"], 0, delta)

    def _content_height(self) -> int:
        if not self.group_order:
            return 0
        last = self.groups[self.group_order[-1]]
        return last["y"] + last["height"]

    # ---------- Interne : largeur, grille et en-tête des dates ----------

    def set_min_size(self, width:int, height:int):
        # Appelé quand la fenêtre change de taille : la grille remplit toute la zone visible
        self.min_width, self.min_height = width, height
        self._on_width_change()
        self._update_scrollregion()

    def _extend_days(self, last_day:int):
        if last_day > self.total_days:
            self.total_days = last_day
            self._on_width_change()

    def _width(self) -> int:
        # Au moins timeline_days jours (pour pouvoir scroller), et quelques jours après la dernière tâche
        days = max(self.timeline_days, self.total_days + EXTRA_DAYS)
        return max(self.min_width, days * PX_PER_DAY)

    def extend_timeline_if_at_end(self):
        # Appelé quand on scrolle tout à droite : on rajoute des jours, le scroll peut continuer
        if self.body.xview()[1] >= 0.999:
            self.timeline_days = max(self.timeline_days, self.total_days + EXTRA_DAYS) + GROW_DAYS
            self._on_width_change()

    def _on_width_change(self):
        width = self._width()
        if width == self._drawn_width:
            return
        self._drawn_width = width
        self._draw_grid()
        self._draw_header()
        self._update_scrollregion()

    def _update_scrollregion(self):
        # Jamais plus petit que la zone visible : sinon tkinter laisse scroller au-dessus du 1er groupe
        width, height = self._width(), max(self.min_height, self._content_height())
        self.body.configure(scrollregion=(0, 0, width, height))
        self.sidebar.configure(scrollregion=(0, 0, SIDEBAR_WIDTH, height))
        self.header.configure(scrollregion=(0, 0, width, HEADER_HEIGHT))

    def _days_drawn(self) -> int:
        return self._width() // PX_PER_DAY + 1

    def _draw_grid(self):
        # Colonnes des jours (week-ends en gris clair) derrière les tâches.
        # Lignes très hautes : pas besoin de les redessiner quand on ajoute des groupes.
        self.body.delete("grid")
        for day in range(self._days_drawn()):
            x = day * PX_PER_DAY
            if (self.start_date + timedelta(days=day)).weekday() >= 5:
                self.body.create_rectangle(x, 0, x + PX_PER_DAY, LINE_LENGTH, fill=WEEKEND_BG, outline="", tags=("grid",))
            self.body.create_line(x, 0, x, LINE_LENGTH, fill=GRID_COLOR, tags=("grid",))
        self.body.tag_lower("grid")  # Sous les séparateurs de groupes (les tâches sont toujours au-dessus)

    def _draw_header(self):
        header, row = self.header, HEADER_ROW_HEIGHT
        header.delete("all")
        width = self._width()
        for day in range(self._days_drawn()):
            current = self.start_date + timedelta(days=day)
            x = day * PX_PER_DAY
            if current.weekday() >= 5:
                header.create_rectangle(x, row, x + PX_PER_DAY, 2 * row, fill=WEEKEND_BG, outline="")
            header.create_line(x, row, x, 2 * row, fill=GRID_COLOR)
            header.create_text(x + PX_PER_DAY / 2, row * 1.5, text=str(current.day), font=("Segoe UI", 8))
            # Nom du mois au 1er de chaque mois (et au début, s'il reste assez de place avant le mois suivant)
            days_left_in_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1) - current
            if current.day == 1 or (day == 0 and days_left_in_month.days >= 4):
                header.create_line(x, 0, x, row, fill=GROUP_SEPARATOR)
                header.create_text(x + 6, row / 2, text=current.strftime("%B %Y"), anchor="w",
                                   font=("Segoe UI", 9, "bold"))
        header.create_line(0, row, width, row, fill=GRID_COLOR)
        header.create_line(0, 2 * row - 1, width, 2 * row - 1, fill=GROUP_SEPARATOR)


def get_main_page(start_date:date=None) -> tuple:
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

    # Coin en haut à gauche, au-dessus des noms de groupes
    corner = tk.Frame(container, bg=GROUP_BG, width=SIDEBAR_WIDTH, height=HEADER_HEIGHT,
                      highlightthickness=1, highlightbackground=GROUP_SEPARATOR)
    corner.grid_propagate(False)
    tk.Label(corner, text="Groups", bg=GROUP_BG, font=("Segoe UI", 9, "bold")).place(x=10, rely=0.5, anchor="w")

    header = tk.Canvas(container, bg=HEADER_BG, height=HEADER_HEIGHT, highlightthickness=0)
    # Pas de bordure (highlightthickness=0) : la sidebar doit faire exactement la hauteur du body
    # pour que le scroll vertical reste aligné ; la ligne de séparation est dessinée dedans
    sidebar = tk.Canvas(container, bg=GROUP_BG, width=SIDEBAR_WIDTH, highlightthickness=0)
    sidebar.create_line(SIDEBAR_WIDTH - 1, 0, SIDEBAR_WIDTH - 1, LINE_LENGTH, fill=GROUP_SEPARATOR)
    body = tk.Canvas(container, bg=GANTT_BG, highlightthickness=0)
    v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=body.yview)
    h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=body.xview)

    # Quand le body scrolle, le header suit en horizontal et la sidebar en vertical
    def on_body_y(first, last):
        v_scrollbar.set(first, last)
        sidebar.yview_moveto(first)
    def on_body_x(first, last):
        h_scrollbar.set(first, last)
        header.xview_moveto(first)
        # Arrivé tout à droite : on rallonge le planning (après ce callback, pas pendant)
        if float(last) >= 0.999 and float(first) > 0 and "gantt" in views:
            body.after_idle(views["gantt"].extend_timeline_if_at_end)
    views = {}  # Rempli plus bas, une fois le GanttView créé
    body.configure(yscrollcommand=on_body_y, xscrollcommand=on_body_x)

    corner.grid(row=0, column=0, sticky="nsew")
    header.grid(row=0, column=1, sticky="ew")
    sidebar.grid(row=1, column=0, sticky="ns")
    body.grid(row=1, column=1, sticky="nsew")
    v_scrollbar.grid(row=1, column=2, sticky="ns")
    h_scrollbar.grid(row=2, column=1, sticky="ew")
    container.rowconfigure(1, weight=1)
    container.columnconfigure(1, weight=1)

    # Molette = vertical, Shift + molette = horizontal, seulement quand la souris est sur le Gantt
    # (on regarde le widget sous la souris : les tâches sont des enfants du body)
    gantt_paths = tuple(str(c) for c in (body, sidebar, header))
    def over_gantt(event):
        widget = root.winfo_containing(event.x_root, event.y_root)
        return widget is not None and str(widget).startswith(gantt_paths)
    def on_wheel(event):
        if over_gantt(event):
            body.yview_scroll(-event.delta // 120, "units")
    def on_shift_wheel(event):
        if over_gantt(event):
            body.xview_scroll(-event.delta // 120, "units")
    root.bind_all("<MouseWheel>", on_wheel)
    root.bind_all("<Shift-MouseWheel>", on_shift_wheel)

    gantt = GanttView(body, sidebar, header, start_date)
    views["gantt"] = gantt
    # La grille fait au moins la taille de la fenêtre
    body.bind("<Configure>", lambda e: gantt.set_min_size(e.width, e.height))

    return root, gantt


def load_image(name:str, shrink:int):
    # Image du dossier assets/, réduite (subsample = diviser la taille par un entier).
    # None si le fichier manque : la fenêtre s'affiche quand même, sans l'image.
    try:
        return tk.PhotoImage(file=os.path.join(ASSETS_DIR, name)).subsample(shrink)
    except tk.TclError:
        return None


def make_card(parent) -> tk.Frame:
    # Carte blanche avec bordure ; card.content = la zone où mettre le contenu
    card = tk.Frame(parent, bg=CARD_BG, highlightthickness=1, highlightbackground=CARD_BORDER)
    content = tk.Frame(card, bg=CARD_BG)
    content.pack(fill="both", expand=True, padx=12, pady=12)
    card.content = content
    return card


def get_recent_projects(root:tk.Tk, projects:list=None, on_create=None, on_open_existing=None) -> tk.Toplevel:
    # Fenêtre d'accueil : logo + titre en haut, carte "Open" à gauche, carte "Recent" à droite.
    # Toplevel et pas Tk : une seule fenêtre racine par programme
    window = tk.Toplevel(root, bg=WELCOME_BG)
    window.title("Ganttify")
    width, height = 820, 600
    # Centrée sur l'écran
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.resizable(False, False)

    # ---------- En-tête : logo + titre ----------
    brand = tk.Frame(window, bg=WELCOME_BG)
    brand.pack(fill="x", padx=40, pady=(30, 20))
    logo = load_image("logo.png", 5)
    title = load_image("title.png", 2)
    if logo:
        tk.Label(brand, image=logo, bg=WELCOME_BG).pack(side=tk.LEFT)
    if title:
        tk.Label(brand, image=title, bg=WELCOME_BG).pack(side=tk.LEFT, padx=(12, 0))
    if not logo and not title:
        tk.Label(brand, text="GANTTIFY", bg=WELCOME_BG, fg=BRAND_COLOR, font=("Segoe UI", 36, "bold")).pack(side=tk.LEFT)
    window.images = (logo, title)  # Garder une référence, sinon Python efface les images

    # ---------- Les deux cartes ----------
    cards = tk.Frame(window, bg=WELCOME_BG)
    cards.pack(fill="both", expand=True, padx=40, pady=(0, 40))

    open_card = make_card(cards)
    open_card.configure(width=240)
    open_card.pack(side=tk.LEFT, fill="y")
    open_card.pack_propagate(False)  # Garde la largeur fixe malgré la taille des boutons
    # on_create / on_open_existing : à brancher plus tard, quand on aura le système IO
    ttk.Button(open_card.content, text="Create New Project", command=on_create).pack(fill="x", padx=8, pady=(10, 8), ipady=4)
    ttk.Button(open_card.content, text="Open Existing Project", command=on_open_existing).pack(fill="x", padx=8, ipady=4)

    recent_card = make_card(cards)
    recent_card.pack(side=tk.LEFT, fill="both", expand=True, padx=(30, 0))
    fill_recent_projects(recent_card.content, projects or [])

    window.attributes("-topmost", True)
    return window
