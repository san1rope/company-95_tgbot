import asyncio
import logging
from multiprocessing import Process

import stripe
from aiogram.types import BotCommand

from config import Config
from tg_bot.handlers import routers
from tg_bot.handlers.company.payments_processing import PaymentsProcessing
from tg_bot.misc.utils import Utils as Ut
from tg_bot.db_models.db_gino import connect_to_db

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
                    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')


async def main():
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    stripe.api_key = Config.STRIPE_SECRET_KEY

    await connect_to_db(remove_data=Config.DATABASE_CLEANUP)
    await Ut.load_localizations_files()

    if routers:
        Config.DISPATCHER.include_routers(*routers)

    bot_commands = [
        BotCommand(command="start", description="Start menu"),
    ]
    await Config.BOT.set_my_commands(commands=bot_commands)

    process_stripe = Process(target=Ut.wrapper, args=(PaymentsProcessing.stripe_handling,))
    process_cryptomus = Process(target=Ut.wrapper, args=(PaymentsProcessing.cryptomus_handling,))

    process_stripe.start()
    process_cryptomus.start()

    await Config.BOT.delete_webhook(drop_pending_updates=True)
    await Config.DISPATCHER.start_polling(Config.BOT, allowed_updates=Config.DISPATCHER.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
