import requests
import json
from datetime import *
from classes import *

def collectData(group_id: int, date: datetime) -> dict:
    response = requests.get(
        url=f"https://ruz.spbstu.ru/api/v1/ruz/scheduler/{group_id}?date={date.year}-{date.month}-{date.day}"
    )
    data = response.json()

    return data

def getGroups(data: dict) -> dict:
    groups = dict()
    for group in data:
        groups[group["name"]] = Group(group["id"], group["name"])

    return groups

def getLessons(group_id: int, date: datetime) -> list[Lesson]:
    data = collectData(group_id, date)
    days = data["days"]
    for day in days:
        if date.date() == datetime(*[int(i) for i in day["date"].split("-")]).date():
            current_day = day
            break
    else:
        return []
    lessons = list()
    for lesson in current_day["lessons"]:
        teachers = list()
        for teacher in lesson.get("teachers") if lesson.get("teachers") else []:
            teachers.append(Teacher(teacher["id"], teacher["full_name"], teacher["first_name"], teacher["middle_name"], teacher["last_name"]))
        classrooms = list()
        for classroom in lesson.get("auditories") if lesson.get("auditories") else []:
            classrooms.append(Classroom(classroom["name"], classroom["building"]["name"]))
        hour, min = [int(i) for i in lesson["time_start"].split(":")]
        time_start = date.replace(hour=hour, minute=min)
        hour, min = [int(i) for i in lesson["time_end"].split(":")]
        time_end = date.replace(hour=hour, minute=min)
        lesson_type = LessonType(lesson["typeObj"]["id"], lesson["typeObj"]["name"])
        groups = []
        for group in lesson["groups"]:
            groups.append(Group(group["id"], group["name"]))
        lessons.append(Lesson(time_start, time_end, lesson["subject"], lesson_type, groups, teachers, classrooms, lesson["additional_info"]))
    return lessons

def main():
    groups = getGroups(json.load(open("TaskBot/groups.json")))
    lessons = getLessons(groups["3530902/20001"].id, datetime(2022,9,19))
    for lesson in lessons:
        teachers = "\n".join(teacher.full_name for teacher in lesson.teachers)
        time_start = lesson.time_start.strftime("%H:%M")
        time_end = lesson.time_end.strftime("%H:%M")
        print(f"{time_start}-{time_end} {lesson.subject}\n{lesson.type.name}\n{teachers}\n")
    

if __name__ == "__main__":
    main()