# TEMPORAIRE : barre de saisie pour remplir le Gantt à la main et tester l'UI.
# Clic = sélectionner, glisser = déplacer (jours / groupes), tirer un bord (tâche sélectionnée) = durée,
# clic droit = supprimer.
# Pour l'enlever : supprimer ce fichier et mettre DEMO = False dans main.py.
import tkinter as tk
from tkinter import colorchooser, ttk

BAR_BG = "khaki"
NEW_TASK_START = 0
NEW_TASK_LENGTH = 3


def setup(root, gantt):
    bar = tk.Frame(root, bg=BAR_BG, padx=8, pady=6)
    bar.pack(side=tk.BOTTOM, fill="x")
    state = {"next_task_id": 1, "color": "#4682b4"}

    def label(parent, text):
        tk.Label(parent, text=text, bg=BAR_BG).pack(side=tk.LEFT, padx=(8, 2))

    # ---------- Ligne 1 : groupes ----------
    group_row = tk.Frame(bar, bg=BAR_BG)
    group_row.pack(fill="x", pady=2)
    label(group_row, "Group name")
    group_name = ttk.Entry(group_row, width=18)
    group_name.pack(side=tk.LEFT)

    # ---------- Ligne 2 : tâches ----------
    task_row = tk.Frame(bar, bg=BAR_BG)
    task_row.pack(fill="x", pady=2)
    label(task_row, "Group")
    task_group = ttk.Combobox(task_row, width=16, state="readonly")
    task_group.pack(side=tk.LEFT)
    label(task_row, "Task name")
    task_name = ttk.Entry(task_row, width=16)
    task_name.pack(side=tk.LEFT)
    label(task_row, "Color")
    # Petit carré qui montre la couleur choisie (cliquable aussi)
    color_swatch = tk.Label(task_row, bg=state["color"], width=3, relief="solid", bd=1, cursor="hand2")
    color_swatch.pack(side=tk.LEFT, ipady=1)

    # ---------- Actions de la barre ----------

    def pick_color():
        # Ouvre le sélecteur de couleur de Windows : n'importe quelle couleur
        _, hex_color = colorchooser.askcolor(color=state["color"], title="Task color", parent=root)
        if hex_color:
            state["color"] = hex_color
            color_swatch.configure(bg=hex_color)

    def add_group():
        name = group_name.get().strip()
        if not name or name in gantt.groups:
            return
        gantt.add_group(name, name)  # Pour la démo, le nom sert aussi d'id
        task_group.configure(values=list(gantt.groups))
        task_group.set(name)
        group_name.delete(0, tk.END)

    def add_task():
        if not task_group.get():
            return
        task_id = state["next_task_id"]
        state["next_task_id"] += 1
        name = task_name.get().strip() or f"Task {task_id}"
        # Nouvelle tâche au jour 0, 3 jours : on la place et on l'étire ensuite à la souris
        gantt.add_task(task_group.get(), task_id, name, NEW_TASK_START, NEW_TASK_LENGTH, state["color"])
        task_name.delete(0, tk.END)

    def update_selected():
        # Applique le groupe et la couleur du formulaire à la tâche sélectionnée
        task_id = gantt.selected
        if task_id is None:
            return
        task = gantt.tasks[task_id]
        gantt.move_task(task_id, task["start"], group_id=task_group.get() or None)
        gantt.set_task_color(task_id, state["color"])

    # ---------- Réactions aux événements du Gantt ----------

    def on_select(task_id):
        if task_id is None:
            return
        task = gantt.tasks[task_id]
        # Le formulaire se remplit avec la tâche, pour pouvoir la modifier
        task_group.set(task["group_id"])
        state["color"] = task["color"]
        color_swatch.configure(bg=task["color"])

    def on_task_moved(task_id, group_id, start):
        task_group.set(group_id)

    gantt.on_select = on_select
    gantt.on_task_moved = on_task_moved
    gantt.on_task_right_click = gantt.remove_task

    ttk.Button(group_row, text="Add group", command=add_group).pack(side=tk.LEFT, padx=6)
    ttk.Button(task_row, text="Pick color...", command=pick_color).pack(side=tk.LEFT, padx=(4, 3))
    ttk.Button(task_row, text="Add task", command=add_task).pack(side=tk.LEFT, padx=(10, 3))
    ttk.Button(task_row, text="Update selected", command=update_selected).pack(side=tk.LEFT, padx=3)

    color_swatch.bind("<Button-1>", lambda e: pick_color())
    # Entrée = valider le champ en cours
    group_name.bind("<Return>", lambda e: add_group())
    task_name.bind("<Return>", lambda e: add_task())
