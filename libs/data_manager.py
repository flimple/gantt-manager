import os
import re
import time
import json
import shutil
from datetime import date

# Chemins absolus (à partir du dossier du projet) : l'app marche peu importe d'où on la lance
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
# workspaces.json = juste la liste des projets récents : {id : {"name", "path", "created", "last_opened"}}
# Chaque projet est UN fichier .gantt : {"format", "name", "created", "settings", "tasks"}
WORKSPACES_FILE = os.path.join(DATA_FOLDER, "workspaces.json")
GANTT_FORMAT = 1
DEFAULT_SETTINGS = {"default_view" : "Weeks"}
DEFAULT_TASK_COLOR = "#3A86D9"
_HEX_COLOR = re.compile(r"\A#[0-9a-fA-F]{6}\Z")   # \A et \Z, pas ^ et $ : $ laisse passer un saut de ligne final
# Bornes d'année plausibles : au-delà, la timeline dépasse le million de pixels
MIN_YEAR, MAX_YEAR = 1970, 2200
INVALID_NAME_CHARS = '<>:"/\\|?*'  # Interdits dans les noms de fichiers Windows

#region IO Code

def check_data_folder() -> bool:
    if not os.path.exists(DATA_FOLDER):
        try:
            os.mkdir(DATA_FOLDER)
        except Exception:
            return False
    return True

def check_workspaces_file() -> bool:
    # Crée le fichier s'il manque, et le répare s'il est vide ou cassé (sinon get_workspaces plante)
    try:
        if os.path.exists(WORKSPACES_FILE):
            with open(WORKSPACES_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                try:
                    json.loads(content)
                    migrate_old_folders()
                    return True
                except json.JSONDecodeError:
                    # Fichier cassé : on le garde de côté au lieu de perdre les données
                    os.replace(WORKSPACES_FILE, WORKSPACES_FILE + f".broken-{int(time.time())}")
        _write_json(WORKSPACES_FILE, {})
        return True
    except Exception:
        return False

def _read_json(path : str, default):
    # Renvoie default si le fichier manque, est vide ou cassé
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default

def _write_json(path : str, data) -> bool:
    # On écrit dans un fichier temporaire puis on remplace : si l'app plante pendant
    # l'écriture, l'ancien fichier reste intact au lieu d'être à moitié écrit
    try:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
        return True
    except OSError:
        return False

def _same_path(a : str, b : str) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))

#endregion


#region Projets récents (workspaces.json)

def get_workspaces() -> dict:
    # Les clés JSON sont toujours des str : on les remet en int pour le reste de l'app
    data = _read_json(WORKSPACES_FILE, {})
    return {int(prj_id) : quick_data for prj_id, quick_data in data.items()}

def save_workspaces(workspaces : dict) -> bool:
    return _write_json(WORKSPACES_FILE, {str(prj_id) : quick_data for prj_id, quick_data in workspaces.items()})

def get_workspace(prj_id : int) -> dict | None:
    return get_workspaces().get(int(prj_id))

def new_workspace_id() -> int:
    return max(get_workspaces().keys(), default=0) + 1

def update_workspace(prj_id : int, **changes) -> bool:
    workspaces = get_workspaces()
    if int(prj_id) not in workspaces:
        return False
    workspaces[int(prj_id)].update(changes)
    return save_workspaces(workspaces)

def remove_workspace(prj_id : int) -> bool:
    # Enlève le projet de la liste des récents (le fichier .gantt n'est PAS supprimé)
    workspaces = get_workspaces()
    workspaces.pop(int(prj_id), None)
    return save_workspaces(workspaces)

#endregion


#region Fichiers .gantt

def is_valid_project_name(name : str) -> bool:
    return not any(c in INVALID_NAME_CHARS for c in name)

def default_project_path(prj_name : str) -> str:
    return os.path.join(DATA_FOLDER, f"{prj_name}.gantt")

def project_path(prj_id : int) -> str | None:
    quick_data = get_workspace(prj_id)
    return quick_data.get("path") if quick_data else None

def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M")

def create_project(prj_name : str) -> int | None:
    # Nouveau projet = un fichier data/<nom>.gantt + une entrée dans la liste des récents
    path = default_project_path(prj_name)
    if os.path.exists(path):
        return None
    project = {"format" : GANTT_FORMAT, "name" : prj_name, "created" : _now(),
               "settings" : dict(DEFAULT_SETTINGS), "tasks" : {}}
    if not _write_json(path, project):
        return None
    prj_id = new_workspace_id()
    workspaces = get_workspaces()
    workspaces[prj_id] = {"name" : prj_name, "path" : path, "created" : project["created"], "last_opened" : _now()}
    save_workspaces(workspaces)
    return prj_id

def _clean_date(value, fallback : str) -> str:
    # Une date utilisable au format AAAA-MM-JJ, sinon fallback. Une année aberrante
    # ("0205" au lieu de "2025") faisait dessiner une timeline de 600 000 jours.
    try:
        parsed = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return fallback
    return parsed.isoformat() if is_plausible_year(parsed) else fallback

def is_plausible_year(value : date) -> bool:
    return MIN_YEAR <= value.year <= MAX_YEAR

def _clean_color(value) -> str:
    # L'UI attend un hex #RRGGBB pour choisir la couleur du texte par-dessus.
    # int(x, 16) acceptait "0x12345", "# 12345", "+12345" ou "12_345" : Tk les
    # refuse ensuite (TclError), donc on vérifie chaque chiffre.
    text = str(value)
    return text if _HEX_COLOR.match(text) else DEFAULT_TASK_COLOR

def clean_tasks(tasks) -> dict:
    # L'UI lit task["name"], ["start"], ["end"] et ["done"] directement : une tâche
    # incomplète (fichier .gantt modifié à la main ou tronqué) faisait planter l'affichage.
    # On répare chaque champ manquant au lieu de refuser tout le projet.
    if not isinstance(tasks, dict):
        return {}
    today = time.strftime("%Y-%m-%d")
    cleaned = {}
    for task_id, task in tasks.items():
        if not isinstance(task, dict):
            continue  # Rien de récupérable dans une entrée qui n'est pas un objet
        name = task.get("name")
        start = _clean_date(task.get("start"), today)
        end = _clean_date(task.get("end"), start)
        cleaned[str(task_id)] = {"name" : name if isinstance(name, str) and name.strip() else f"Task {task_id}",
                                 "start" : start,
                                 # Les dates AAAA-MM-JJ se comparent comme des textes
                                 "end" : max(end, start),
                                 "color" : _clean_color(task.get("color")),
                                 "done" : bool(task.get("done"))}
    return cleaned

def new_task_id(tasks : dict) -> str:
    # Les ids viennent du fichier : on ignore ceux qui ne sont pas des nombres au lieu de planter
    numbers = [int(task_id) for task_id in tasks if str(task_id).isdecimal()]
    return str(max(numbers, default=0) + 1)

def read_project_file(path : str) -> dict | None:
    # Contenu d'un fichier .gantt, None s'il n'est pas valide
    data = _read_json(path, None)
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return None  # Sans nom utilisable, ce n'est pas un projet Ganttify
    data.setdefault("format", GANTT_FORMAT)
    data.setdefault("created", _now())
    settings = data.get("settings")
    data["settings"] = settings if isinstance(settings, dict) else dict(DEFAULT_SETTINGS)
    # Réparé ici une fois pour toutes : tout le reste de l'app suppose des tâches complètes
    data["tasks"] = clean_tasks(data.get("tasks"))
    return data

def load_project(prj_id : int) -> dict | None:
    path = project_path(prj_id)
    return read_project_file(path) if path else None

def save_project(prj_id : int, project : dict) -> bool:
    path = project_path(prj_id)
    return bool(path) and _write_json(path, project)

def register_project_file(path : str) -> int | None:
    # "Open Project" : ajoute un .gantt (n'importe où sur le PC) à la liste des récents ; renvoie son id
    project = read_project_file(path)
    if project is None:
        return None
    workspaces = get_workspaces()
    for prj_id, quick_data in workspaces.items():
        if quick_data.get("path") and _same_path(quick_data["path"], path):
            update_workspace(prj_id, name=project["name"], last_opened=_now())
            return prj_id
    prj_id = new_workspace_id()
    workspaces[prj_id] = {"name" : project["name"], "path" : os.path.abspath(path),
                          "created" : project["created"], "last_opened" : _now()}
    save_workspaces(workspaces)
    return prj_id

def is_name_taken(prj_name : str) -> bool:
    names = [w["name"].lower() for w in get_workspaces().values()]
    return prj_name.lower() in names or os.path.exists(default_project_path(prj_name))

def compute_stats(tasks : dict) -> dict:
    # tasks : {task_id : {"name", "start", "end" (AAAA-MM-JJ), "color", "done"}}
    today = time.strftime("%Y-%m-%d")
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t.get("done"))
    # Les dates AAAA-MM-JJ se comparent correctement comme des textes
    late = sum(1 for t in tasks.values() if not t.get("done") and t.get("end", today) < today)
    return {"total_tasks" : total, "total_completed" : done, "late_tasks" : late,
            "stats_str" : f"{total} tasks • {done} done • {late} late"}

#endregion


#region Conversion de l'ancien format (un dossier data/<id>/ par projet)

def migrate_old_folders():
    # Ancien format : data/<id>/tasks.json + settings.json + stats.json + <nom>.gantt
    # Nouveau : un seul fichier data/<nom>.gantt. L'ancien dossier n'est supprimé
    # qu'APRÈS avoir vérifié que le nouveau fichier contient bien les mêmes données.
    workspaces = get_workspaces()
    changed = False
    for prj_id, quick_data in workspaces.items():
        old_dir = os.path.join(DATA_FOLDER, str(prj_id))
        if quick_data.get("path") or not os.path.isdir(old_dir):
            continue
        name = str(quick_data.get("name", f"Project {prj_id}"))
        settings = _read_json(os.path.join(old_dir, "settings.json"), dict(DEFAULT_SETTINGS))
        # Mêmes nettoyages que read_project_file, sinon la vérification plus bas
        # échouerait toujours et la conversion ne se ferait jamais
        project = {"format" : GANTT_FORMAT, "name" : name, "created" : quick_data.get("created", _now()),
                   "settings" : settings if isinstance(settings, dict) else dict(DEFAULT_SETTINGS),
                   "tasks" : clean_tasks(_read_json(os.path.join(old_dir, "tasks.json"), {}))}
        path = default_project_path(name)
        if os.path.exists(path):
            path = default_project_path(f"{name} ({prj_id})")
        if not _write_json(path, project) or read_project_file(path) != project:
            continue  # En cas de problème on ne touche à rien : l'ancien dossier reste
        quick_data["path"] = path
        changed = True
        shutil.rmtree(old_dir, ignore_errors=True)
    if changed:
        save_workspaces(workspaces)

#endregion
