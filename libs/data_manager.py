import os
import time
import json

DATA_FOLDER="data/"
WORKSPACES_FILE="data/workspaces.json"

#region IO Code

def check_data_folder() -> bool:
    if not os.path.exists(DATA_FOLDER):
        try:
            os.mkdir(DATA_FOLDER)
        except Exception:
            return False
    return True

def check_workspaces_file() -> bool:
    if not os.path.exists(WORKSPACES_FILE):
        try:
            with open(WORKSPACES_FILE, "w") as f:
                json.dump({}, f)
        except Exception:
            return False
    return True

#endregion


#region Data stream

def get_workspaces() -> dict | None:
    with open(WORKSPACES_FILE, "r") as f:
        return {int(v) : k for v, k in json.load(f).items()}
    return None

def save_workspaces(workspaces : dict) -> bool:
    try:
        with open(WORKSPACES_FILE, "w") as f:
            json.dump(workspaces, f)
        return True
    except Exception:
        return False

def get_workspace(prj_id : int) -> dict | None:
    dat = get_workspaces()
    print(dat)
    if prj_id not in list(dat.keys()):
        return None
    return dat[prj_id]

def load_workspace_data(prj_id : int) -> tuple[dict, dict, dict] | None:
    WORKSPACE_DIR = DATA_FOLDER + f"{prj_id}/"
    if not os.path.exists(WORKSPACE_DIR):
        return None
    qk_data = get_workspace(prj_id)
    tasks_dat, settings_dat, stats_dat = WORKSPACE_DIR + "tasks.json", WORKSPACE_DIR + "settings.json", WORKSPACE_DIR + "stats.json"
    tasks_data, settings_data, stats_data = {}, {}, {}
    with open(tasks_dat, "r") as f:
        tasks_data = json.load(f)
    with open(settings_dat, "r") as f:
        settings_data = json.load(f)
    with open(stats_dat, "r") as f:
        stats_data = json.load(f)

    return tasks_data, settings_data, stats_data


def save_new_workspace_data(prj_id : int):
    WORKSPACE_DIR = DATA_FOLDER + f"{prj_id}/"
    if not os.path.exists(WORKSPACE_DIR):
        os.mkdir(WORKSPACE_DIR)
    prj_name = get_workspace(prj_id)["name"]
    tasks_dat, settings_dat, stats_dat, workspace_file = WORKSPACE_DIR + "tasks.json", WORKSPACE_DIR + "settings.json", WORKSPACE_DIR + "stats.json", WORKSPACE_DIR + f"{prj_name}.gantt"
    #with open(workspace_file, "w") as f:
        #json.dump({"tasks_file" : tasks_dat, "settings_file" : settings_dat, "stats_file" : stats_dat, "preferences" : {}}, f)
    with open(tasks_dat, "w") as f:
        json.dump({}, f)
    with open(settings_dat, "w") as f:
        json.dump({}, f)
    with open(stats_dat, "w") as f:
        json.dump({"stats_str" : "0", "file_name" : f"{prj_name}.gantt", "total_tasks" : 0, "total_completed" : 0, "late_tasks" : 0}, f)
    

def save_new_workspace(prj_id : int, quick_data : dict) -> bool:
    try:
        data = {}
        with open(WORKSPACES_FILE, "r") as f:
            data = json.load(f)
        data[prj_id] = quick_data
        with open(WORKSPACES_FILE, "w") as f:
            json.dump(data, f)
        return True
    except Exception:
        return False

#endregion