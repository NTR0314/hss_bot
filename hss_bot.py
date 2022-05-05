#!/bin/python3
import logging
import asyncio

import aiogram.types
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions

import Scrape

API_TOKEN = open('apitoken.txt', 'r').read().strip()

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('hss-bot')

# toggled_users = {}  # keys: course number, vals: set containing all users signed up for the course specified by the key
toggled_users = set()
toggled_debug_users = set()

current_htmls = {}  # The latest fetch of the html of the Hochschulsport site
current_results = {}  # welche Kurse frei sind, key = Sportart, value = dict mit k: Kursname v: "Frei"/"Voll"

bot = Bot(token=API_TOKEN)

# Volleyball
volleyball_url = "https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Volleyball.html"
volleyball_ids = ['6800', '6802', '6803', '6804', '6805', '6806', '6807']

# Sportmix
sportmix_url = "https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Sportmix.html"
sportmix_ids = ['5105', '5110', '5111']

urls_ids = {'Volleyball': (volleyball_url, volleyball_ids), 'Sportmix': (sportmix_url, sportmix_ids)}


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender

    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def check_background():
    while True:
        for sportart in urls_ids.keys():
            current_htmls[sportart] = Scrape.get_html(urls_ids[sportart][0])
            current_results[sportart] = Scrape.check(current_htmls[sportart], urls_ids[sportart][1])

        cur_tog_users = toggled_users
        for user in cur_tog_users:
            for sportart, result in current_results.items():
                for kurs, zugaenglichkeit in result.items():
                    if kurs[0] == 'Frei':
                        await send_message(user, sportart + '-' + kurs + " ist frei! Schnell anmelden. Hier ist der Link: https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Volleyball.html")
                    elif user in toggled_debug_users:
                        await send_message(user, sportart + '-' + kurs + " ist leider voll. https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Volleyball.html")

        frequency = 5  # freq in seconds
        for i in range(frequency):
            for user in toggled_users:
                if user in toggled_debug_users:
                    await send_message(user, f"Next check in {frequency - i} seconds.")
            await asyncio.sleep(1)


async def toggle_debug(message: types.Message):
    uid = message.from_user.id
    if uid not in toggled_debug_users:
        await message.answer("Debug for periodic check now enabled.")
        toggled_debug_users.add(uid)
    else:
        await message.answer("Debug for periodic check now disabled.")
        toggled_debug_users.remove(uid)


async def check_if_toggled(message: types.Message):
    uid = message.from_user.id
    msg_str = "Currently toggled to receive updates" if uid in toggled_users else "Currently not toggled"
    await message.answer(msg_str)


async def toggle_course(message: types.Message):
    uid = message.from_user.id
    if uid not in toggled_users:
        toggled_users.add(uid)
    else:
        toggled_users.remove(uid)

    await message.answer("You will now get messages about Volleyball")

    # TODO: implement that the user can choose which course he wants to get updates about for now the user gets updated for every course
    # uid = message.from_user.id

    # await message.answer("Which course do you want to get updates about?")
    # print(current_results)
    # for sportart, courses in current_results.items():
    #     for course in courses:
    #         await message.answer(f"{sportart} - {course}")


async def default(message: types.Message):
    await message.answer("I don't understand you :(. Please use a valid command.")


async def start_handler(event: types.Message):
    ib = aiogram.types.reply_keyboard.ReplyKeyboardMarkup()
    ib.add(aiogram.types.KeyboardButton('/start'))
    ib.add(aiogram.types.KeyboardButton('/debug'))
    ib.add(aiogram.types.KeyboardButton('/toggle_course'))
    ib.add(aiogram.types.KeyboardButton('/check_if_toggled'))
    ib.add(aiogram.types.KeyboardButton('/toggle_debug'))

    await event.answer(
        f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",
        parse_mode=types.ParseMode.HTML,
        reply_markup=ib
    )

    await event.answer("Available commands are: help, toggle_course, toggle_debug")


async def debug(message: types.Message):
    for html in current_htmls.values():
        await message.answer(
            f"Length of result is :{str(len(html))}.\nIf the length is low it might be that the bot is sending"
            f" to many requests")


async def main():
    try:
        # Initialize bot and dispatcher
        disp = Dispatcher(bot=bot)
        disp.register_message_handler(start_handler, commands={"start", "help"})
        disp.register_message_handler(toggle_course, commands={"toggle_course"})
        disp.register_message_handler(debug, commands={"debug"})
        disp.register_message_handler(toggle_debug, commands={"toggle_debug"})
        disp.register_message_handler(check_if_toggled, commands={"check_if_toggled"})
        disp.register_message_handler(default)
        asyncio.create_task(check_background())

        await disp.start_polling()
    finally:
        await bot.close()


asyncio.run(main())
