import asyncio
import json
import logging
import os

from aiogram.types import BotCommand

from config import Config
from tg_bot.handlers import routers
from tg_bot.misc.utils import localization, corrections
from tg_bot.db_models.db_gino import connect_to_db

logger = logging.getLogger(__name__)


async def main():
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    await connect_to_db(remove_data=Config.DATABASE_CLEANUP)

    localization_folder = "tg_bot/misc/localization/"
    for filename in os.listdir(os.path.abspath(localization_folder)):
        lang = filename.replace(".json", "")
        with open(os.path.abspath(localization_folder + filename), "r", encoding="utf-8") as file:
            data = json.load(file)

        localization.update({lang: data})

    corrections_file = "tg_bot/misc/corrections.json"
    with open(os.path.abspath(corrections_file), "r", encoding="utf-8") as file:
        corrections.update(json.load(file))

    if routers:
        Config.DISPATCHER.include_routers(*routers)

    bot_commands = [
        BotCommand(command="start", description="Start menu"),
    ]
    await Config.BOT.set_my_commands(commands=bot_commands)

    await Config.BOT.delete_webhook(drop_pending_updates=True)
    await Config.DISPATCHER.start_polling(Config.BOT, allowed_updates=Config.DISPATCHER.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
