import asyncio
import logging

import aiogram.types

import Scrape

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import exceptions, executor

API_TOKEN = open('apitoken.txt', 'r').read().strip() 

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('hss-bot')

toggled_users = set()
toggled_debug_users = set()

current_html = ""
current_results = []

bot = Bot(token=API_TOKEN)


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
        current_results, current_html = Scrape.get_ids()
        cur_tog_users = toggled_users
        for user in cur_tog_users:
            for result in current_results:
                if result[0]:
                    await send_message(user, result[1] + '-' + result[2] + " ist frei! Schnell anmelden.")
                elif user in toggled_debug_users:
                    await send_message(user, result[1] + '-' + result[2] + " ist leider voll.")

        for i in range(7):
            for user in toggled_users:
                if user in toggled_debug_users:
                    await send_message(user, f"Next check in {30 - i} seconds.")
            await asyncio.sleep(1)


async def bruv_kek(message: types.Message):
    i = 0
    while True:
        await message.answer(str(i))
        i += 1
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
    msg_str = "Currently enabled" if uid in toggled_users else "Currently disabled"
    await message.answer(msg_str)


async def toggle_test(message: types.Message):
    uid = message.from_user.id
    if uid not in toggled_users:
        await message.answer("Checking periodically now enabled.")
        toggled_users.add(uid)
    else:
        await message.answer("Checking periodically now disabled.")
        toggled_users.remove(uid)


async def default(message: types.Message):
    await message.answer("I don't understand you :(. Please use a valid command.")


async def start_handler(event: types.Message):
    await event.answer(
        f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",
        parse_mode=types.ParseMode.HTML,
    )

    await event.answer("Available commands are: help, check, toggle, check_toggled, debug, start, help, toggle_debug")


async def check(message: types.Message):
    scrape_res, _ = Scrape.get_ids()
    for res in scrape_res:
        if not res[0]:
            await message.answer(res[1] + '-' + res[2] + " ist leider voll.")
        else:
            await message.answer(res[1] + '-' + res[2] + " ist frei! Schnell anmelden.")


async def debug(message: types.Message):
    _, html_text = Scrape.get_ids()
    #file = aiogram.types.input_file.InputFile(html_text)
    await message.answer(f"Length of result is :{str(len(html_text))}")

async def main():
    try:
        # Initialize bot and dispatcher
        disp = Dispatcher(bot=bot)
        disp.register_message_handler(start_handler, commands={"start", "help"})
        disp.register_message_handler(toggle_test, commands={"toggle"})
        disp.register_message_handler(check_if_toggled, commands={"check_toggled"})
        disp.register_message_handler(check, commands={"check"})
        disp.register_message_handler(debug, commands={"debug"})
        disp.register_message_handler(toggle_debug, commands={"toggle_debug"})
        disp.register_message_handler(default)

        asyncio.create_task(check_background())

        await disp.start_polling()
    finally:
        await bot.close()


asyncio.run(main())
