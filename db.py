import pymysql
from config import *
from main import Task, Reminder
from ics_parser import Event
from datetime import datetime

def connectToDB():
    connection = pymysql.connect(
        host = host,
        user = user,
        password = password,
        database = db_name,
        cursorclass = pymysql.cursors.DictCursor
    )
    return connection


def getTasks(connection: pymysql.connections.Connection,user_id: int) -> list[Task]:
    cursor = connection.cursor()
    select_tasks = f"SELECT * FROM `tasks` WHERE user_id = {user_id}"
    cursor.execute(select_tasks)
    tasks = list()
    for task in cursor.fetchall():
        tasks.append(Task(task["user_id"], task["task_id"], task["task_title"],desc=task["task_desc"]))
    return tasks

def getEvents(connection: pymysql.connections.Connection, user_id:int) -> list[Event]:
    cursor = connection.cursor()
    select_events = f"SELECT * FROM `events` WHERE user_id = {user_id}"
    cursor.execute(select_events)
    events = list()
    for event in cursor.fetchall():
        events.append(Event(event["user_id"], event["event_id"], event["title"], event["start_time"], event["end_time"]))
    return events

def getReminders(connection: pymysql.connections.Connection, task_id=None) -> list[Reminder]:
    cursor = connection.cursor()
    if task_id:
        select_reminders = f"SELECT * FROM `events` WHERE user_id = {task_id}"
    else:
        select_reminders = "SELECT * FROM `events`"
    cursor.execute(select_reminders)
    reminders = list()
    for reminder in cursor.fetchall():
        reminders.append(Reminder(reminder["user_id"], reminder["task_id"], reminder["title"], reminder["remind_time"]))
    return reminders

def createTask(connection: pymysql.connections.Connection, user_id: int, task_id: int, title: str, desc="") -> None:
    cursor = connection.cursor()
    create_task = f"INSERT INTO `tasks` (user_id, task_id, task_title, task_desc) VALUES ({user_id}, {task_id}, '{title}', '{desc}')"
    cursor.execute(create_task)
    connection.commit()

def createEvent(connection: pymysql.connections.Connection, user_id: int, event_id: int, title: str, start: datetime, end: datetime):
    cursor = connection.cursor()
    create_event = f"INSERT INTO `events` (user_id, event_id, title, start_time, end_time) VALUES ({user_id}, {event_id}, '{title}', '{start}', '{end}')"
    cursor.execute(create_event)
    connection.commit()

def createReminder(connection: pymysql.connections.Connection, user_id: int, title: str, remind_time: datetime, task_id=-1, event_id=-1):
    cursor = connection.cursor()
    create_remind = f"INSERT INTO `reminders` (user_id, task_id, event_id, title, remind_time) VALUES ({user_id}, {task_id}, {event_id}, '{title}','{remind_time}')"
    cursor.execute(create_remind)
    connection.commit()

def deleteTask(connection: pymysql.connections.Connection, user_id: int, task_id: int):
    cursor = connection.cursor()
    delete_task = f"DELETE FROM `tasks` WHERE user_id = {user_id} and task_id = {task_id}"
    cursor.execute(delete_task)
    connection.commit()

def main():
    connection = connectToDB()
    deleteTask(connection, 4, 1)

if __name__ == "__main__":
    main()