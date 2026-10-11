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
        return json.load(f)
    return None

def save_workspaces(workspaces : dict) -> bool:
    try:
        with open(WORKSPACES_FILE, "w") as f:
            json.dump(workspaces, f)
        return True
    except Exception:
        return False

def get_workspace(prj_id : int) -> dict:
    pass


def save_new_workspace_data(prj_id : int):
    WORKSPACE_DIR = DATA_FOLDER + f"{prj_id}/"
    if not os.path.exists(WORKSPACE_DIR):
        os.mkdir(WORKSPACE_DIR)
    pths = [WORKSPACE_DIR + "tasks.json",  WORKSPACE_DIR + "settings.json", WORKSPACE_DIR + "stats.json"]
    for pth in pths:
        with open(pth, "w") as f:
            json.dump({}, f)
    

def save_new_workspace(prj_id : int, quick_data : dict) -> bool:
    try:
        data = {}
        with open(WORKSPACES_FILE, "r") as f:
            data = json.load(f)
        data[prj_id] = quick_data
        with open(WORKSPACES_FILE, "w"):
            json.dump(data, f)
            return True
    except Exception:
        return False

#endregion