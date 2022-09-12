from icalendar import Calendar
import datetime

TIMEZONE_DIFFERENCE = datetime.datetime.now().astimezone().utcoffset().seconds

class Event:
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

def getEvents(file):
    events = []
    g = open(file,'rb')
    gcal = Calendar.from_ical(g.read())
    for component in gcal.walk():
        if component.name == "VEVENT":
            events.append(Event(str(component.get('summary')), component.get('dtstart').dt + datetime.timedelta(seconds=TIMEZONE_DIFFERENCE), component.get('dtend').dt + datetime.timedelta(seconds=TIMEZONE_DIFFERENCE)))
    g.close()
    return events