import msghandler
import config

import threading
import asyncio
import time

from javascript import require, On

mineflayer = require("mineflayer")

bots = dict()
selected_bot = None


class MineflayerBot:
    def __init__(self, username, params):
        self.bot = None
        self.username = username
        self.params = params

    def setup(self):
        self.bot = mineflayer.createBot({
            "host": self.params["host"],
            "port": self.params["port"],
            "username": self.username
        })

        @On(self.bot, "message")
        def message_handler(_self, message, *args):
            msg = message.getText()
            print(msg)

        @On(self.bot, "windowOpen")
        def window_handler(_self, message, *args):
            self.click_slot(config.portal_numbers[config.portal])

        @On(self.bot, "kicked")
        def kicked_handler(_self, reason, err, *args):
            unsetup_bot(self.username, "ERROR_BOT_KICKED")

        @On(self.bot, "error")
        def error_handler(_self, err, *args):
            print("-------------ERROR--------------\nS"
                  + str(err)
                  + "\n-------------------------------")
            unsetup_bot(self.username, "ERROR_BOT_OCCURRED")

    def unsetup(self):
        try:
            self.bot.end()
        except:
            pass
        self.bot = None

    def is_started(self):
        return self.bot is not None

    def right_click(self):
        self.bot.activateItem(False)

    def click_slot(self, slot):
        self.bot.clickWindow(slot, 0, 0)

    def tab_players(self):
        return self.bot.players

    def chat_message(self, message):
        self.bot.chat(message)


def execute_command(cmd):
    global selected_bot
    name = cmd.split(" ")[0]
    args = cmd.split(" ")[1:]
    if name == ".select":
        if len(args) == 0 or len(args[0]) < 3:
            return "Ошибка: Неправильный синтаксис."
        elif get_bot(args[0]) is None:
            return "Ошибка: Бот не найден."
        selected_bot = args[0]
        return f"Выбран бот: {selected_bot}."

    elif name == ".setupbot":
        if len(args) < 1:
            return "Ошибка: Неправильный синтаксис."
        elif get_bot(args[0]) is not None:
            return "Ошибка: Бот уже запущен."

        setup_bot(args[0], args[1:])

    elif name == ".unsetupbot":
        if len(args) < 1:
            return "Ошибка: Неправильный синтаксис."
        elif get_bot(args[0]) is None:
            return "Ошибка: Бот не найден."

        unsetup_bot(args[0], "DISABLED_BY_USER")

    elif name == ".list":
        resp = f"------------------------\nСписок активных ботов({len(bots)}):"
        if len(bots) == 0:
            resp += "- Пусто."
        else:
            for username in bots.keys():
                resp += f"\n- {username}"
        resp += "\n------------------------"
        return resp

    elif name == ".online":
        if selected_bot is None:
            return "Выберите бота."
        result = ""
        players = get_bot(selected_bot).tab_players();
        index = 0
        for nickname in players:
            index += 1
            result += str(nickname).ljust(16) + "   "
            if index % 3 == 0:
                result += "\n"
        return result

    elif name == ".chatAll":
        for username in bots.keys():
            time.sleep(0.1)
            bot = get_bot(username)
            bot.chat_message(" ".join(args))

    elif name.startswith("."):
        return "Неизвестная команда."
    else:
        if selected_bot is None:
            return "Ошибка: Выберите бота."
        elif len(cmd) > 125:
            return "Ошибка: Слишком большое сообщение, оно должно быть не больше 125 символов."
        try:
            get_bot(selected_bot).chat_message(cmd)
        except:
            pass
    return None


def setup_bot(username, args):
    global bots
    params = parse_params(args)
    if params is None:
        return
    print("---------------------------------")
    print(f"Запуск бота {username}...")
    print("Параметры:")
    for key in params.keys():
        print(f"- {key}: {str(params[key])}")
    print("---------------------------------")
    bot = MineflayerBot(username, params)
    bot.setup()
    bots[username] = bot


def parse_params(args):
    params = {
        "host": config.host,
        "port": config.port,
        "adblock": False
    }
    nextValueParam = None
    for arg in args:
        if arg.startswith("--"):
            paramName = arg[2:]
            if paramName not in params.keys():
                print(f"[!] Ошибка: Неизвестный параметр: {arg}.")
                return None
            elif isinstance(params[paramName], bool):
                params[paramName] = True
                print(f"{arg} воспринят как boolean")
            else:
                nextValueParam = paramName
                print(f"{arg} воспринят как string, ждём след. аргумент.")
        else:
            if nextValueParam is None:
                print(f"[!] Ошибка: Укажите через --, какой параметр имеется ввиду у: {arg}.")
                return None
            params[nextValueParam] = arg
            nextValueParam = None
    return params


def unsetup_bot(username, reason):
    global bots
    bot = get_bot(username)
    bot.unsetup()
    del bots[username]
    print(f"[!] Бот {username} был завершён! Причина: {reason}")


def get_bot(username):
    global bots
    if not username in bots:
        return None
    return bots[username]


def console_handler():
    while True:
        cmd = input("> ")
        result = execute_command(cmd)
        if result is not None:
            print(result)


def main():
    t = threading.Thread(target=console_handler)
    t.start()


if __name__ == "__main__":
    main()
