from datetime import datetime

class User:
    def __init__(self):
        self.current_task_id = -1
        self.current_event_id = -1
        self.current_page = 0

class Task:
    def __init__(self, user_id: int, task_id: int, title: str, desc="", delTime:datetime=None):
        self.user_id = user_id
        self.task_id = task_id
        self.title = title
        self.desc = desc
        self.delTime = delTime

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

class Teacher:
    def __init__(self, id: int, full_name: str, first_name: str, middle_name:str, last_name:str) -> None:
        self.id = id
        self.full_name = full_name
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name

class LessonType:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

class Group:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

class Classroom:
    def __init__(self, name: str, building: str) -> None:
        self.name = name
        self.building = building

class Lesson:
    def __init__(self, time_start: datetime, time_end: datetime, subject: str, type: LessonType, groups: list[Group], teachers: list[Teacher], classrooms: list[Classroom], additional_info: str) -> None:
        self.time_start = time_start
        self.time_end = time_end
        self.subject = subject
        self.type = type
        self.groups = groups
        self.teachers = teachers
        self.classrooms = classrooms
        self.additional_info = additional_info