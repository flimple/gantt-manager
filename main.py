import libs.ui as ui
import libs.ui2 as gui
import libs.util as tools
import libs.data_manager as dataT

DEMO = True

def check_env() -> bool:
    res = dataT.check_data_folder() and dataT.check_workspaces_file()
    if not res:
        print("Error in IO init")
    return res

def main2():
    if not check_env():
        return
    app = gui.App_Manager()
    app.open_recent_project()
    app.start_loop()

if __name__ == "__main__":
    main2()