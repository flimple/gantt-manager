# gantt-manager

Ganttify : gestionnaire de projets avec timeline Gantt, calendrier et to-do list
(CustomTkinter + tkinter.Canvas).

## Installation

Python 3.11 ou plus, puis :

```
pip install -r requirements.txt
```

Sous Linux, tkinter n'est pas toujours livre avec Python : `sudo apt install python3-tk`.

## Lancer

```
python main.py
```

## Donnees

Un projet = un fichier `data/<nom>.gantt` (du JSON). `data/workspaces.json` ne
contient que la liste des projets recents. Le dossier `data/` n'est pas versionne.
