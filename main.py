from telegram import *
from telegram.ext import *
from requests import *
import asyncio
from datetime import *
from ics_parser import *
from classes import *
import os
import db

TOKEN = os.environ.get('TOKEN')

MAIN_MENU_BUTTONS = [[KeyboardButton("📝Мои задачи"), KeyboardButton("📅Календарь")]]
TIMEZONE_DIFFERENCE = 3600 * 3 - datetime.now().astimezone().utcoffset().seconds

def updateReminders():
    global reminders
    reminders = db.getReminders(connection)

async def remind():
    bot = Bot(TOKEN)
    global reminders
    while True:
        for reminder in reminders:
            if datetime.now().timestamp() >= reminder.remind_time.timestamp() - TIMEZONE_DIFFERENCE:
                bot.sendMessage(chat_id=reminder.user_id, text=f"⏰Напоминание: <b>{reminder.title}</b>.", parse_mode="HTML")
                db.deleteReminder(connection, reminder.reminder_id)
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

    context.user_data["current_task_id"] += 1
    db.createTask(connection, update.effective_chat.id, update.message.text)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите описание или /skip, чтобы создать задачу без описания.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить создание задачи")]], resize_keyboard=True))

    return 4

def setDesc(update: Update, context: CallbackContext):
    db.updateTask(connection, update.effective_chat.id, context.user_data["current_task_id"], desc=update.message.text)
    title = db.getTask(connection, update.effective_chat.id, context.user_data["current_task_id"]).title
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача создана: <b>{title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    context.user_data["current_task_id"] = -1

    return ConversationHandler.END

def skipDesc(update: Update, context: CallbackContext):
    title = db.getTask(connection, update.effective_chat.id, context.user_data["current_task_id"]).title
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача создана: <b>{title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    context.user_data["current_task_id"] = -1

    return ConversationHandler.END

def cancelTaskCreation(update: Update, context: CallbackContext):
    db.deleteTask(connection, update.effective_chat.id, context.user_data["current_task_id"])
    context.user_data["current_task_id"] = -1
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Создание задачи отменено.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def showTaskList(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("✏️Создать задачу")]]
    page = context.user_data["current_page"]
    tasks = db.getTasks(connection, update.effective_chat.id)
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
    context.bot.send_message(chat_id=update.effective_chat.id, text="📖Ваши задачи. /menu, чтобы вернуться на главную.")
    showTaskList(update, context)
    
    return 0

def viewTask(update: Update, context: CallbackContext):
    try:
        task = db.getTask(connection, update.effective_chat.id, int(update.message.text.split(":")[0]))
        context.user_data["current_task_id"] = task.task_id
        buttons = [[KeyboardButton("🏠На главную")], [KeyboardButton("⏰Добавить напоминание")], [KeyboardButton("❌Удалить задачу")]]
        text = f"<b>{'• ' + task.title}</b>"
        if task.desc != "":
            text += f"\n{task.desc}"
        reminders = db.getReminders(connection, update.effective_chat.id, task.task_id)
        if reminders != []:
            text += "\n\n-----"
            for reminder in reminders:
                time_text = reminder.remind_time.strftime("%d.%m.%Y %H:%M")
                text += f"\n⏰Напоминание: {time_text}"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
        return 1
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Такой задачи не существует.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        return ConversationHandler.END


def mainMenu(update: Update, context: CallbackContext):
    context.user_data["current_page"] = 0
    context.bot.send_message(chat_id=update.effective_chat.id, text="🏠Главное меню.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def createTaskReminder(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🕰Введите время (год.месяц.день.час.минута).", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить добавление напоминания")]], resize_keyboard=True))

    return 2

def deleteTask(update: Update, context: CallbackContext):
    task = db.getTask(connection, update.effective_chat.id, context.user_data["current_task_id"])
    db.deleteTask(connection, update.effective_chat.id, task.task_id)
    db.deleteReminders(connection, update.effective_chat.id, task_id=task.task_id)
    updateReminders()
    context.user_data["current_task_id"] = -1
    context.user_data["current_page"] = 0

    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача удалена: <b>{task.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    
    return ConversationHandler.END

def setTaskReminder(update: Update, context: CallbackContext):
    try:
        time = datetime(*[int(i) for i in update.message.text.split(".")])
        task = db.getTask(connection, update.effective_chat.id, context.user_data["current_task_id"])
        db.createReminder(connection, update.effective_chat.id, task.title, time, task_id=task.task_id)
        updateReminders()

        time_text = time.strftime("%d.%m.%Y %H:%M")
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

viewTasksConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("📝Мои задачи"), viewTasks)],

    states={
        0: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("✏️Создать задачу"), createTask), MessageHandler(Filters.text, viewTask), MessageHandler(Filters.regex("<"), tasksPrevPage), MessageHandler(Filters.regex(">"), tasksNextPage)],
        1: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("⏰Добавить напоминание"), createTaskReminder), MessageHandler(Filters.regex("❌Удалить задачу"), deleteTask)],
        2: [MessageHandler(Filters.regex("🚫Отменить добавление напоминания"), cancelReminderCreation), MessageHandler(Filters.text, setTaskReminder)],
        3: [MessageHandler(Filters.regex("🚫Отменить создание задачи"), cancelTaskCreation), MessageHandler(Filters.text, setTitle)],
        4: [CommandHandler("skip", skipDesc), MessageHandler(Filters.regex("🚫Отменить создание задачи"), cancelTaskCreation), MessageHandler(Filters.text, setDesc)]
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
            db.createEvent(connection, update.effective_chat.id, title, event["start"], event["end"])
            if event["start"].timestamp() > datetime.now().timestamp():
                db.createReminder(connection, update.effective_chat.id, title, event["start"]-timedelta(minutes=15))

        os.remove(filename)
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅Календарь импортирован успешно.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Ошибка при чтении файла календаря.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def showEventsList(update: Update, context: CallbackContext):
    buttons = [["📲Импортировать календарь"]]
    page = context.user_data["current_page"]
    events = db.getEvents(connection, update.effective_chat.id)
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
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"📄Страница {c_page}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

def viewCalendar(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="📅Календарь. /menu, чтобы вернуться на главную.")
    showEventsList(update, context)
    
    return 0

def viewEvent(update: Update, context: CallbackContext):
    try:
        event = db.getEvent(connection, update.effective_chat.id, int(update.message.text.split(":")[0]))
        context.user_data["current_event_id"] = event.event_id
        buttons = [[KeyboardButton("🏠На главную")], [KeyboardButton("❌Удалить событие")]]
        text = f"<b>{'• ' + event.title}</b>"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
        return 1
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Такого события не существует. {e}", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        return ConversationHandler.END

def deleteEvent(update: Update, context: CallbackContext):
    event = db.getEvent(connection, update.effective_chat.id, context.user_data["current_event_id"])
    db.deleteEvent(connection, update.effective_chat.id, event.event_id)
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

viewCalendarConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("📅Календарь"), viewCalendar)],

    states={
        0: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("📲Импортировать календарь"), importCalendar), MessageHandler(Filters.regex("<"), calendarPrevPage), MessageHandler(Filters.regex(">"), calendarNextPage), MessageHandler(Filters.text, viewEvent)],
        1: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("❌Удалить событие"), deleteEvent)],
        2: [MessageHandler(Filters.regex("🚫Отменить импорт календаря"), cancelIcsImport), MessageHandler(Filters.document, icsHandler)]
    },

    fallbacks=[]
)

def main():
    global connection
    connection = db.connectToDB()

    global reminders
    reminders = db.getReminders(connection)

    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", startCommandHandler))
    dispatcher.add_handler(viewTasksConvHandler)
    dispatcher.add_handler(viewCalendarConvHandler)
        
    updater.start_polling()
    asyncio.run(remind())

if __name__ == "__main__":
    main()