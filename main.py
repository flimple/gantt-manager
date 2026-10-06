import time
import os
import random

class Workspace:
    def __init__(self, name : str="Project-id"):
        self.proj_name = name
        self.create_date = time.time()
        self.data = {}
        self.last_selected_task = None
        self.task_ids : set = {}
        self.max_tasks = 100

    @property
    def can_add_task(self) -> bool:
        return True if len(self.task_ids) < 100 else False

    @property
    def get_new_task_id(self) -> int | None:
        if not self.can_add_task:
            return None
        # Par example un max des task = 100 -> min_id = 100/10 = 10 et max_id = 100-1 = 99 donc le random
        # range va selectionner entre 10 et 99 et on aura toujours un nombre de digits egal
        max_task_id, min_task_id = self.max_tasks-1, self.max_tasks / 10
        rnd_task_id = min_task_id
        while rnd_task_id in self.task_ids:
            rnd_task_id = random.randrange(min_task_id, max_task_id+1)
        return rnd_task_id



    def add_task(self, start_date=None, end_date=None, color=None, dependency=None):
        task_id = 0


    def add_subtask(self, task_id=None, start_date=None, end_date=None, main_color=None, hue=None, dependency=None) -> bool:
        if not self.last_selected_task:
            return False
        subtask_id = 0

    def add_milestone(self):
        pass

    