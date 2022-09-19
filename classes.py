from datetime import datetime

class User:
    def __init__(self):
        self.current_task_id = -1
        self.current_event_id = -1
        self.current_page = 0

class Task:
    def __init__(self, user_id: int, task_id: int, title: str, desc = ""):
        self.user_id = user_id
        self.task_id = task_id
        self.title = title
        self.desc = desc

class Reminder:
    def __init__(self, reminder_id: int, user_id: int, task_id: int, title: str, remind_time: datetime):
        self.reminder_id = reminder_id
        self.user_id = user_id
        self.task_id = task_id
        self.title = title
        self.remind_time = remind_time

class Event:
    def __init__(self, user_id: int, event_id: int, title: str, start: datetime, end: datetime):
        self.user_id = user_id
        self.event_id = event_id
        self.title = title
        self.start = start
        self.end = end