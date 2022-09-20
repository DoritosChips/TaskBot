import pymysql
from config import *
from datetime import datetime
from classes import *

class DataBase:
    def connect():
        self.connection = pymysql.connect(
            host = host,
            user = user,
            password = password,
            database = db_name,
            cursorclass = pymysql.cursors.DictCursor
        )

    def getTasks(user_id: int) -> list[Task]:
        cursor = self.connection.cursor()
        select_tasks = f"SELECT * FROM tasks WHERE user_id = {user_id}"
        cursor.execute(select_tasks)
        tasks = list()
        for task in cursor.fetchall():
            tasks.append(Task(task["user_id"], task["task_id"], task["task_title"],desc=task["task_desc"]))
        return tasks

    def getTask(user_id: int, task_id: int) -> Task:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} and task_id = {task_id}")
        task = cursor.fetchall()[0]
        task = Task(task["user_id"], task["task_id"], task["task_title"],desc=task["task_desc"])
        return task

    def getEvents(user_id:int) -> list[Event]:
        cursor = self.connection.cursor()
        select_events = f"SELECT * FROM events WHERE user_id = {user_id}"
        cursor.execute(select_events)
        events = list()
        for event in cursor.fetchall():
            events.append(Event(event["user_id"], event["event_id"], event["title"], event["start_time"], event["end_time"]))
        return events

    def getEvent(user_id: int, event_id: int) -> Event:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} and event_id = {event_id}")
        event = cursor.fetchall()[0]
        event = Event(event["user_id"], event["event_id"], event["title"], event["start_time"], event["end_time"])
        return event

    def getReminders(user_id: int = None, task_id: int = None) -> list[Reminder]:
        cursor = self.connection.cursor()
        if user_id and task_id:
            select_reminders = f"SELECT * FROM reminders WHERE task_id = {task_id}"
        else:
            select_reminders = "SELECT * FROM reminders"
        cursor.execute(select_reminders)
        reminders = list()
        for reminder in cursor.fetchall():
            reminders.append(Reminder(reminder["reminder_id"], reminder["user_id"], reminder["task_id"], reminder["title"], reminder["remind_time"]))
        return reminders

    def createTask(user_id: int, title: str, desc="") -> None:
        cursor = self.connection.cursor()
        current_task_id = 0
        while True:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM tasks WHERE user_id={user_id} and task_id={current_task_id})")
            if not cursor.fetchall()[0][f"EXISTS(SELECT * FROM tasks WHERE user_id={user_id} and task_id={current_task_id})"]:
                cursor.execute(f"INSERT INTO tasks (user_id, task_id, task_title, task_desc) VALUES ({user_id}, {current_task_id}, '{title}','{desc}')")
                connection.commit()
                break
            current_task_id += 1

    def createEvent(user_id: int, title: str, start: datetime, end: datetime) -> None:
        cursor = self.connection.cursor()
        current_event_id = 0
        while True:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM events WHERE user_id={user_id} and event_id={current_event_id})")
            if not cursor.fetchall()[0][f"EXISTS(SELECT * FROM events WHERE user_id={user_id} and event_id={current_event_id})"]:
                cursor.execute(f"INSERT INTO events (user_id, event_id, title, start_time, end_time) VALUES ({user_id}, {current_event_id}, '{title}', '{start}', '{end}')")
                connection.commit()
                break
            current_event_id += 1

    def createReminder(user_id: int, title: str, remind_time: datetime, task_id=-1, event_id=-1) -> None:
        cursor = self.connection.cursor()
        current_reminder_id = 0
        while True:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM reminders WHERE reminder_id={current_reminder_id})")
            if not cursor.fetchall()[0][f"EXISTS(SELECT * FROM reminders WHERE reminder_id={current_reminder_id})"]:
                cursor.execute(f"INSERT INTO reminders (reminder_id, user_id, task_id, event_id, title, remind_time) VALUES ({current_reminder_id}, {user_id}, {task_id}, {event_id}, '{title}','{remind_time}')")
                connection.commit()
                break
            current_reminder_id += 1

    def deleteTask(user_id: int, task_id: int) -> None:
        cursor = self.connection.cursor()
        delete_task = f"DELETE FROM tasks WHERE user_id = {user_id} and task_id = {task_id}"
        cursor.execute(delete_task)
        connection.commit()
        current_task_id = task_id + 1
        while True:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM tasks WHERE user_id={user_id} and task_id={current_task_id})")
            if cursor.fetchall()[0][f"EXISTS(SELECT * FROM tasks WHERE user_id={user_id} and task_id={current_task_id})"]:
                cursor.execute(f"UPDATE tasks SET task_id={current_task_id-1} WHERE user_id={user_id} and task_id={current_task_id}")
                connection.commit()
                current_task_id += 1
            else:
                break

    def deleteEvent(user_id: int, event_id: int) -> None:
        cursor = self.connection.cursor()
        delete_event = f"DELETE FROM events WHERE user_id = {user_id} and event_id = {event_id}"
        cursor.execute(delete_event)
        connection.commit()
        current_event_id = event_id + 1
        while True:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM events WHERE user_id={user_id} and event_id={current_event_id})")
            if cursor.fetchall()[0][f"EXISTS(SELECT * FROM events WHERE user_id={user_id} and event_id={current_event_id})"]:
                cursor.execute(f"UPDATE events SET event_id={current_event_id-1} WHERE user_id={user_id} and event_id={current_event_id}")
                connection.commit()
                current_event_id += 1
            else:
                break

    def deleteReminders(user_id: int, event_id=-1, task_id=-1) -> None:
        cursor = self.connection.cursor()
        if task_id!=-1:
            delete_reminders = f"DELETE FROM reminders WHERE user_id = {user_id} and task_id = {task_id}"
        else:
            delete_reminders = f"DELETE FROM reminders WHERE user_id = {user_id} and event_id = {event_id}"
        cursor.execute(delete_reminders)
        connection.commit()

    def deleteReminder(reminder_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM reminders WHERE reminder_id = {reminder_id}")
        connection.commit()
        current_reminder_id = reminder_id + 1
        while True:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM reminders WHERE reminder_id={current_reminder_id})")
            if cursor.fetchall()[0][f"EXISTS(SELECT * FROM reminders WHERE reminder_id={current_reminder_id})"]:
                cursor.execute(f"UPDATE reminders SET reminder_id={current_reminder_id-1} WHERE reminder_id={current_reminder_id}")
                connection.commit()
                current_reminder_id += 1
            else:
                break

    def updateTask(connection: pymysql.connections.Connection, user_id: int, task_id: int, title: str = None, desc: str = None) -> None:
        cursor = connection.cursor()
        if title:
            cursor.execute(f"UPDATE tasks SET task_title='{title}' WHERE user_id={user_id} and task_id={task_id}")
        if desc:
            cursor.execute(f"UPDATE tasks SET task_desc='{desc}' WHERE user_id={user_id} and task_id={task_id}")
        connection.commit()

def main():
    db = DataBase()
    db.connect()
    db.deleteTask(connection, 296691655, 0)

if __name__ == "__main__":
    main()