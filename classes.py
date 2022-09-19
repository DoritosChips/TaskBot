class User:
    def __init__(self):
        self.tasks = []
        self.current_task = None
        self.events = []
        self.current_event = None
        self.current_page = 0
        self.current_task_id = 0

class Task:
    def __init__(self, user_id: int, task_id: int, title: str, desc = ""):
        self.user_id = user_id
        self.task_id = task_id
        self.title = title
        self.desc = desc

class Reminder:
    def __init__(self, user_id, task_id, title, remind_time):
        self.user_id = user_id
        self.task_id = task_id
        self.text = title
        self.remind_time = remind_time

class Event:
    def __init__(self, user_id, event_id, title, start, end):
        self.user_id = user_id
        self.event_id = event_id
        self.title = title
        self.start = start
        self.end = end