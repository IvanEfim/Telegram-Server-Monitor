import requests
import datetime
import psutil
import config
import persistence
import time

last_notification = 0
storage = persistence.Persistence()

def processMessage(message):
    if "text" in message:
        processTextMessage(message)

def processTextMessage(message):
    text = message["text"]

    if text.startswith("/"):
        processCommandMessage(message)

def processCommandMessage(message):
    text = message["text"]

    if " " in text:
        command, parameter = text.split(" ", 1)
    else:
        command = text
        parameter = ""

    if "@" in command:
        command, botname = command.split("@", 1)
        if botname.lower() != config.NAME.lower():
            # Ignore messages for other bots
            return

    if command == "/старт":
        commandStart(message, parameter)
    elif command == "/стоп":
        commandStop(message)
    elif command == "/помощь":
        commandHelp(message)
    elif command == "/состояние":
        commandUsage(message)
    elif command == "/пользователь":
        commandUsers(message)
    elif command == "/диск":
        commandDisks(message)
    else:
        sendTextMessage(message["chat"]["id"], "Я не знаю что ты имеешь в виду.")

def sendTextMessage(chat_id, text):
    r = requests.post(config.API_URL + "sendMessage", json={
        "chat_id" : chat_id,
        "text" : text
    })

    result = r.json()
    if not result["ok"]:
        print(result)

def sendAuthMessage(chat_id):
    sendTextMessage(chat_id, "Пожалуйста авторизируйтесь.")

def startupMessage():
    for id in storage.allUsers():
        sendTextMessage(id, "Привет,Начинаю мониторинг.")

def shutdownMessage():
    for id in storage.allUsers():
        sendTextMessage(id, "Я выключил мониторинг.")

def commandStart(message, parameter):
    chat_id = message["chat"]["id"]
    if storage.isRegisteredUser(chat_id):
        sendTextMessage(chat_id, "Авторизация прошла успешно. Я готов.")
    else:
        if parameter.strip() == config.PASSWORD:
            storage.registerUser(chat_id)
            sendTextMessage(chat_id, "Я готов. " +
                "Напишите  /помощь для информации.")
        else:
            sendTextMessage(chat_id, "Не верный пароль. " +
                "Тип /старт <пароль> для авторизации.")

def commandStop(message):
    chat_id = message["chat"]["id"]
    if storage.isRegisteredUser(chat_id):
        storage.unregisterUser(chat_id)
        sendTextMessage(chat_id, "Я выключаюсь пока.")
    else:
        sendAuthMessage(chat_id)

def commandHelp(message):
    chat_id = message["chat"]["id"]
    sendTextMessage(chat_id, config.NAME + """
Мониторинг Вашего сервера и общая информация.

/состояние - ЦП и Память
/пользователь - Активные пользватели
/диск - Использование дисков


/стоп - остановка мониторинга
""")

def commandUsage(message):
    chat_id = message["chat"]["id"]
    if not storage.isRegisteredUser(chat_id):
        sendAuthMessage(chat_id)
        return

    text = """Время работы: {0}
ЦП: {1} %
Память: {2} %
Подкачка: {3} %""".format(
    str(datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())),
    psutil.cpu_percent(),
    psutil.virtual_memory().percent,
    psutil.swap_memory().percent)

    sendTextMessage(chat_id, text)

def commandUsers(message):
    chat_id = message["chat"]["id"]
    if not storage.isRegisteredUser(chat_id):
        sendAuthMessage(chat_id)
        return

    text = ""
    for user in psutil.users():
        text = text + "{0}@{1} {2}\n".format(user.name, user.host, str(datetime.datetime.fromtimestamp(user.started)))

    sendTextMessage(chat_id, text)

def commandDisks(message):
    chat_id = message["chat"]["id"]
    if not storage.isRegisteredUser(chat_id):
        sendAuthMessage(chat_id)
        return

    text = ""
    for dev in psutil.disk_partitions():
        text = text + "{0} ({1}) {2} %\n".format(dev.device, dev.mountpoint, psutil.disk_usage(dev.mountpoint).percent)

    sendTextMessage(chat_id, text)

def alarms():
    global last_notification
    now = time.time()

    if config.ENABLE_NOTIFICATIONS and (now - last_notification > config.NOTIFCATION_INTERVAL):
        text = "ВНИМАНИЕ!\n"
        should_send = False

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        if cpu > config.NOTIFY_CPU_PERCENT:
            text = text + "ЦП: {0} %\n".format(cpu)
            should_send = True
        if ram > config.NOTIFY_RAM_PERCENT:
            text = text + "Память: {0} %\n".format(ram)
            should_send = True

        if should_send:
            last_notification = now
            for id in storage.allUsers():
                sendTextMessage(id, text)
