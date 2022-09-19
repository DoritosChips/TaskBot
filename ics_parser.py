from icalendar import Calendar

class Event:
    def __init__(self, user_id, task_id, title, start, end):
        self.user_id = user_id
        self.task_id = task_id
        self.title = title
        self.start = start
        self.end = end

def getEvents(file)->list[Event]:
    events = []
    g = open(file,'rb')
    gcal = Calendar.from_ical(g.read())
    for component in gcal.walk():
        if component.name == "VEVENT":
            events.append(Event(str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt))
    g.close()
    return events