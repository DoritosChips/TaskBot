from telegram import *
from telegram.ext import *
from requests import *
import asyncio
from datetime import *
from ics_parser import *
from classes import *
import os
from db import DataBase
from polyschedule import *

TOKEN = os.environ.get('TOKEN')

MAIN_MENU_BUTTONS = [[KeyboardButton("📝Мои задачи"), KeyboardButton("📅Календарь")]]
TIMEZONE_DIFFERENCE = 3600 * 3 - datetime.now().astimezone().utcoffset().seconds

def updateReminders():
    global reminders
    reminders = db.getReminders()

def updateAutoDelTasks():
    global autoDelTasks
    autoDelTasks = db.getAutoDeleteTasks()

async def remind():
    bot = Bot(TOKEN)
    global reminders
    global autoDelTasks
    while True:
        for reminder in reminders:
            if datetime.now().timestamp() >= reminder.remind_time.timestamp() - TIMEZONE_DIFFERENCE:
                bot.sendMessage(chat_id=reminder.user_id, text=f"⏰Напоминание: <b>{reminder.title}</b>.", parse_mode="HTML")
                db.deleteReminder(reminder.user_id, reminder.reminder_id)
                updateReminders()
        for task in autoDelTasks:
            if datetime.now().timestamp() >= task.delTime.timestamp() - TIMEZONE_DIFFERENCE:
                db.deleteTask(task.user_id, task.task_id)
                db.deleteReminders(task.user_id, task_id=task.task_id)
                updateAutoDelTasks()
                updateReminders()


def startCommandHandler(update: Update, context: CallbackContext):
    context.user_data["current_task_id"] = context.user_data["current_event_id"] = -1
    context.user_data["current_page"] = 0
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Приветствую!", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

def createTask(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название задачи.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить создание задачи")]], resize_keyboard=True))
    
    return 3

def setTitle(update: Update, context: CallbackContext):
    if update.message.text.startswith("/"):
            buttons = MAIN_MENU_BUTTONS
            context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Невозможно создать задачу с таким названием..", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            context.user_data["current_task_id"] = -1
            return ConversationHandler.END

    context.user_data["current_task_id"] = db.getNextTaskIndex(update.effective_chat.id)
    db.createTask(update.effective_chat.id, update.message.text)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите описание или /skip, чтобы создать задачу без описания.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить создание задачи")]], resize_keyboard=True))

    return 4

def setDesc(update: Update, context: CallbackContext):
    db.updateTask(update.effective_chat.id, context.user_data["current_task_id"], desc=update.message.text)
    title = db.getTask(update.effective_chat.id, context.user_data["current_task_id"]).title
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача создана: <b>{title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    context.user_data["current_task_id"] = -1

    return ConversationHandler.END

def skipDesc(update: Update, context: CallbackContext):
    title = db.getTask(update.effective_chat.id, context.user_data["current_task_id"]).title
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача создана: <b>{title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    context.user_data["current_task_id"] = -1

    return ConversationHandler.END

def cancelTaskCreation(update: Update, context: CallbackContext):
    if context.user_data["current_task_id"] != -1:
        db.deleteTask(update.effective_chat.id, context.user_data["current_task_id"])
        context.user_data["current_task_id"] = -1
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Создание задачи отменено.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def showTaskList(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("✏️Создать задачу")]]
    page = context.user_data["current_page"]
    tasks = db.getTasks(update.effective_chat.id)
    for task in tasks[page * 10:page * 10 + 10]:
        buttons.append([f"{task.task_id}: {task.title}"])
    page_buttons = []
    if page > 0:
        page_buttons.append("<")
    if (page + 1) * 10 < len(tasks):
        page_buttons.append(">")
    if page_buttons != []:
        buttons.append(page_buttons)
    
    c_page = context.user_data["current_page"] + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"📄Страница {c_page}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

def viewTasks(update: Update, context: CallbackContext):
    context.user_data["current_page"] = 0

    context.bot.send_message(chat_id=update.effective_chat.id, text="📖Ваши задачи. /menu, чтобы вернуться на главную.")
    showTaskList(update, context)
    
    return 0

def viewTask(update: Update, context: CallbackContext):
    try:
        task = db.getTask(update.effective_chat.id, int(update.message.text.split(":")[0]))
        context.user_data["current_task_id"] = task.task_id
        buttons = [[KeyboardButton("🏠На главную")], [KeyboardButton("⏰Напоминания")], [KeyboardButton("❌Удалить задачу")]]
        text = f"<b>{'📝' + task.title}</b>"
        if task.desc != "":
            text += f"\n{task.desc}"
        if task.delTime:
            time_text = task.delTime.strftime("%d.%m.%Y %H:%M")
            text += f"\n\nЗадача будет удалена <b>{time_text}</b>"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
        
        return 1
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Такой задачи не существует.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        
        return ConversationHandler.END


def mainMenu(update: Update, context: CallbackContext):
    context.user_data["current_page"] = 0
    context.user_data["current_task_id"] = -1
    context.user_data["current_reminder_id"] = -1
    context.bot.send_message(chat_id=update.effective_chat.id, text="🏠Главное меню.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def createTaskReminder(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🕰Введите время (ДД.ММ.ГГГГ чч.мм).", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить добавление напоминания")]], resize_keyboard=True))

    return 2

def deleteTask(update: Update, context: CallbackContext):
    task = db.getTask(update.effective_chat.id, context.user_data["current_task_id"])
    db.deleteTask(update.effective_chat.id, task.task_id)
    db.deleteReminders(update.effective_chat.id, task_id=task.task_id)
    updateReminders()
    context.user_data["current_task_id"] = -1
    context.user_data["current_page"] = 0

    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача удалена: <b>{task.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    
    return ConversationHandler.END

def setTaskReminder(update: Update, context: CallbackContext):
    try:
        date, time = update.message.text.split()
        dt = datetime(*list(map(int, date.split(".")))[::-1] + list(map(int, time.split("."))))
        task = db.getTask(update.effective_chat.id, context.user_data["current_task_id"])
        db.createReminder(update.effective_chat.id, task.title, dt, task_id=task.task_id)
        updateReminders()

        time_text = dt.strftime("%d.%m.%Y %H:%M")
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Напоминание добавлено: {time_text}.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Ошибка при добавлении напоминания. Вероятно, время введено в неверном формате.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    context.user_data["current_task_id"] = -1
    context.user_data["current_page"] = 0
    
    return ConversationHandler.END

def cancelReminderCreation(update: Update, context: CallbackContext):
    context.user_data["current_task_id"] = -1
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Добавление напоминания отменено.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def tasksPrevPage(update: Update, context: CallbackContext):
    context.user_data["current_page"] -= 1
    showTaskList(update, context)

    return 0

def tasksNextPage(update: Update, context: CallbackContext):
    context.user_data["current_page"] += 1
    showTaskList(update, context)

    return 0

def viewReminders(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("⏰Добавить напоминание")]]
    reminders = db.getReminders(update.effective_chat.id, context.user_data["current_task_id"])
    for reminder in reminders:
        time_text = reminder.remind_time.strftime("%d.%m.%Y %H:%M")
        buttons.append([KeyboardButton(f"{reminder.reminder_id}: {time_text}") ])
    context.bot.send_message(chat_id=update.effective_chat.id, text="⏰Напоминания. /menu, чтобы вернуться на главную.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

    return 5

def viewReminder(update: Update, context: CallbackContext):
    try:
        context.user_data["current_reminder_id"] = int(update.message.text.split(":")[0])
        reminder = db.getReminder(update.effective_chat.id, context.user_data["current_reminder_id"])
        time_text = reminder.remind_time.strftime("%d.%m.%Y %H:%M")
        buttons=[[KeyboardButton("🏠На главную")], [KeyboardButton("🗑Удалить задачу после напоминания")], [KeyboardButton("❌Удалить напоминание")]]
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏰{time_text}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

        return 6
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Такого напоминания не существует.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

        return ConversationHandler.END

def deleteReminder(update: Update, context: CallbackContext):
    reminder = db.getReminder(update.effective_chat.id, context.user_data["current_reminder_id"])
    context.user_data["current_reminder_id"] = -1
    db.deleteReminder(update.effective_chat.id, reminder.reminder_id)
    updateReminders()
    time_text = reminder.remind_time.strftime("%d.%m.%Y %H:%M")
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Напоминание удалено: <b>{time_text} | {reminder.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")

    return ConversationHandler.END

def autoDeleteTask(update: Update, context: CallbackContext):
    reminder = db.getReminder(update.effective_chat.id, context.user_data["current_reminder_id"])
    task = db.getTask(update.effective_chat.id, context.user_data["current_task_id"])
    time_text = reminder.remind_time.strftime("%d.%m.%Y %H:%M")
    db.updateTask(update.effective_chat.id, task.task_id, delTime=reminder.remind_time)
    updateAutoDelTasks()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача <b>{task.title}</b> будет удалена <b>{time_text}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")

    return ConversationHandler.END


viewTasksConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("📝Мои задачи"), viewTasks)],

    states={
        0: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("✏️Создать задачу"), createTask), MessageHandler(Filters.text, viewTask), MessageHandler(Filters.regex("<"), tasksPrevPage), MessageHandler(Filters.regex(">"), tasksNextPage)],
        1: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("⏰Напоминания"), viewReminders), MessageHandler(Filters.regex("❌Удалить задачу"), deleteTask)],
        2: [MessageHandler(Filters.regex("🚫Отменить добавление напоминания"), cancelReminderCreation), MessageHandler(Filters.text, setTaskReminder)],
        3: [MessageHandler(Filters.regex("🚫Отменить создание задачи"), cancelTaskCreation), MessageHandler(Filters.text, setTitle)],
        4: [CommandHandler("skip", skipDesc), MessageHandler(Filters.regex("🚫Отменить создание задачи"), cancelTaskCreation), MessageHandler(Filters.text, setDesc)],
        5: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("⏰Добавить напоминание"), createTaskReminder), MessageHandler(Filters.text, viewReminder)],
        6: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🗑Удалить задачу после напоминания"), autoDeleteTask), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("❌Удалить напоминание"), deleteReminder)]
    },

    fallbacks=[]
)

def importCalendar(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="📁Отправьте .ics файл календаря.", reply_markup=ReplyKeyboardMarkup([["🚫Отменить импорт календаря"]], resize_keyboard=True))

    return 2

def icsHandler(update: Update, context: CallbackContext):
    try:
        filename = str(update.effective_chat.id)+"_"+str(datetime.now().timestamp())+".ics"
        context.bot.get_file(update.message.document).download(custom_path=filename)
        
        events = getEvents(filename)
        for event in events:
            event["start"] -= timedelta(seconds=TIMEZONE_DIFFERENCE)
            event["end"] -= timedelta(seconds=TIMEZONE_DIFFERENCE)
            start = event["start"].strftime("%d.%m.%Y %H:%M")
            if event["start"].strftime("%d.%m.%Y") == event["end"].strftime("%d.%m.%Y"):
                end = event["end"].strftime("%H:%M")
            else:
                end = event["end"].strftime("%d.%m.%Y %H:%M")
            event_title = event["title"]
            title = f"{start} - {end} | {event_title}"
            db.createEvent(update.effective_chat.id, title, event["start"], event["end"])
            if event["start"].timestamp() > datetime.now().timestamp():
                db.createReminder(update.effective_chat.id, title, event["start"]-timedelta(minutes=15))

        os.remove(filename)
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅Календарь импортирован успешно.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Ошибка при чтении файла календаря.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def showEventsList(update: Update, context: CallbackContext):
    buttons = [["🎓Расписание Политеха"], ["📲Импортировать календарь"]]
    page = context.user_data["current_page"]
    events = db.getEvents(update.effective_chat.id)
    for event in events[page * 10:page * 10 + 10]:
        buttons.append([f"{event.event_id}: {event.title}"])
    page_buttons = []
    if page > 0:
        page_buttons.append("<")
    if (page + 1) * 10 < len(events):
        page_buttons.append(">")
    if page_buttons != []:
        buttons.append(page_buttons)
        
    c_page = context.user_data["current_page"]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"📄Страница {c_page + 1}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

def viewCalendar(update: Update, context: CallbackContext):
    context.user_data["current_page"] = 0

    context.bot.send_message(chat_id=update.effective_chat.id, text="📅Календарь. /menu, чтобы вернуться на главную.")
    showEventsList(update, context)
    
    return 0

def viewEvent(update: Update, context: CallbackContext):
    try:
        event = db.getEvent(update.effective_chat.id, int(update.message.text.split(":")[0]))
        context.user_data["current_event_id"] = event.event_id
        buttons = [[KeyboardButton("🏠На главную")], [KeyboardButton("❌Удалить событие")]]
        text = f"<b>{'• ' + event.title}</b>"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
        return 1
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Такого события не существует. {e}", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        return ConversationHandler.END

def deleteEvent(update: Update, context: CallbackContext):
    event = db.getEvent(update.effective_chat.id, context.user_data["current_event_id"])
    db.deleteEvent(update.effective_chat.id, event.event_id)
    db.deleteReminders(update.effective_chat.id, event_id=event.event_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Событие удалено: <b>{event.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    context.user_data["current_event_id"] = -1
    context.user_data["current_page"] = 0
    
    return ConversationHandler.END

def cancelIcsImport(update: Update, context: CallbackContext):
    context.user_data["current_event_id"] = -1
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Импорт календаря отменён.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def calendarPrevPage(update: Update, context: CallbackContext):
    context.user_data["current_page"] -= 1
    showEventsList(update, context)

    return 0

def calendarNextPage(update: Update, context: CallbackContext):
    context.user_data["current_page"] += 1
    showEventsList(update, context)

    return 0

def handlePolySchedule(update: Update, context: CallbackContext):
    buttons = [["🏠На главную"], ["📅Расписание на сегодня"], ["📆Расписание на другой день"], ["👥Ввести номер группы"]]
    context.bot.send_message(chat_id=update.effective_chat.id, text="🎓Расписание Политеха.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

    return 3

def setPolyGroup(update: Update, context: CallbackContext):
    group = update.message.text
    if group in groups:
        context.user_data["polygroup"] = group
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Ваша группа: <b>{group}</b>.", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Группа не найдена: <b>{group}</b>.", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def getScheduleText(lessons: list[Lesson], dt: datetime) -> str:
    text = ""
    for lesson in lessons:
        time_start = lesson.time_start.strftime("%H:%M")
        time_end = lesson.time_end.strftime("%H:%M")
        text += f"<b>{time_start}-{time_end} {lesson.subject}</b>\n   {lesson.type.name}\n"
        if lesson.additional_info != "":
            text += f"   {lesson.additional_info}\n"
        if lesson.teachers != []:
            teachers = "\n   ".join(teacher.full_name for teacher in lesson.teachers)
            text += f"   {teachers}\n"
        if lesson.classrooms != []:
            classrooms = "\n   ".join(f"{classroom.building}, ауд. {classroom.name}" for classroom in lesson.classrooms)
            text += f"   {classrooms}\n"
        text += "\n"
    if text == "":
        text = "⛔️Нет занятий."
    else:
        date_text = dt.strftime("%d.%m.%Y")
        text = f"<ins><b>🎓Расписание на {date_text}</b></ins>\n\n" + text

    return text

def polyScheduleToday(update: Update, context: CallbackContext):
    if "polygroup" not in context.user_data:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Группа не задана.", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        return ConversationHandler.END
    
    try:
        dt = datetime.today() - timedelta(seconds=TIMEZONE_DIFFERENCE)
        lessons = getLessons(groups[context.user_data["polygroup"]].id, dt)
        text = getScheduleText(lessons, dt)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Ошибка при получении расписания.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def polyScheduleDate(update: Update, context: CallbackContext):
    if "polygroup" not in context.user_data:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Группа не задана.", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        return ConversationHandler.END

    context.bot.send_message(chat_id=update.effective_chat.id, text="📅Введите дату (ДД.ММ.ГГГГ).", reply_markup=ReplyKeyboardRemove())

    return 5

def changePolyGroup(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="👥Введите номер группы.", reply_markup=ReplyKeyboardRemove())

    return 4

def showPolyScheduleByDate(update: Update, context: CallbackContext):
    try:
        dt = datetime(*[int(i) for i in update.message.text.split(".")][::-1])
        lessons = getLessons(groups[context.user_data["polygroup"]].id, dt)
        text = getScheduleText(lessons, dt)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Ошибка при получении расписания.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

viewCalendarConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("📅Календарь"), viewCalendar)],

    states={
        0: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("📲Импортировать календарь"), importCalendar), MessageHandler(Filters.regex("🎓Расписание Политеха"), handlePolySchedule), MessageHandler(Filters.regex("<"), calendarPrevPage), MessageHandler(Filters.regex(">"), calendarNextPage), MessageHandler(Filters.text, viewEvent)],
        1: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("❌Удалить событие"), deleteEvent)],
        2: [MessageHandler(Filters.regex("🚫Отменить импорт календаря"), cancelIcsImport), MessageHandler(Filters.document, icsHandler)],
        3: [MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("👥Ввести номер группы"), changePolyGroup), MessageHandler(Filters.regex("📅Расписание на сегодня"), polyScheduleToday), MessageHandler(Filters.regex("📆Расписание на другой день"), polyScheduleDate)],
        4: [MessageHandler(Filters.text, setPolyGroup)],
        5: [MessageHandler(Filters.text, showPolyScheduleByDate)]
    },

    fallbacks=[]
)

def main():
    global db
    db = DataBase()
    db.connect()

    global reminders
    reminders = db.getReminders()
    global autoDelTasks
    autoDelTasks = db.getAutoDeleteTasks()

    global groups
    groups = getGroups(json.load(open("groups.json")))

    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", startCommandHandler))
    dispatcher.add_handler(viewTasksConvHandler)
    dispatcher.add_handler(viewCalendarConvHandler)
        
    updater.start_polling()
    asyncio.run(remind())

if __name__ == "__main__":
    main()