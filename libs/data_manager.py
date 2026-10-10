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
            with open(WORKSPACES_FILE, "w"):
                pass
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

#endregion