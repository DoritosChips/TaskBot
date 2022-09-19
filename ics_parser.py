from icalendar import Calendar

def getEvents(file) -> dict:
    events = []
    g = open(file,'rb')
    gcal = Calendar.from_ical(g.read())
    for component in gcal.walk():
        if component.name == "VEVENT":
            events.append({"title": str(component.get('summary')), "start": component.get('dtstart').dt, "end": component.get('dtend').dt})
    g.close()
    return events