from icalendar import Calendar
from classes import *

def getEvents(file)->list[Event]:
    events = []
    g = open(file,'rb')
    gcal = Calendar.from_ical(g.read())
    for component in gcal.walk():
        if component.name == "VEVENT":
            events.append(Event(str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt))
    g.close()
    return events