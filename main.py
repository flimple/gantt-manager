import libs.ui as ui
import libs.ui2 as gui
import libs.util as tools

DEMO = True  # TEMPORAIRE : lance demo.setup() pour tester l'UI

def main():
    root, gantt = ui.get_main_page()

    if DEMO:
        import demo
        demo.setup(root, gantt)
        # "Create New Project" ferme juste la fenêtre pour arriver sur le Gantt vide
        recent = ui.get_recent_projects(root, on_create=lambda: recent.destroy())
    else:
        ui.get_recent_projects(root)

    root.mainloop()

if __name__ == "__main__":
    main()