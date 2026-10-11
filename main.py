import libs.ui as ui
import libs.ui2 as gui
import libs.util as tools
import libs.data_manager as dataT

DEMO = True

def main():
    root, gantt = ui.get_main_page()

    if DEMO:
        import demo
        demo.setup(root, gantt)
        recent = ui.get_recent_projects(root, on_create=lambda: recent.destroy())
    else:
        ui.get_recent_projects(root)

    root.mainloop()

def check_env() -> bool:
    res = dataT.check_data_folder() and dataT.check_workspaces_file()
    if not res:
        print("Error in IO init")
    return res

def main2():
    if not check_env():
        return
    root = gui.Recent_Projects_Window(dataT.get_workspaces())
    root.start_loop()

if __name__ == "__main__":
    main2()