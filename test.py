import asyncio
import logging

from config import Config
from tg_bot.db_models.db_gino import connect_to_db
from tg_bot.db_models.schemas import Driver
from tg_bot.db_models.db_gino import db


async def main():
    await connect_to_db(remove_data=False)

    count = await Driver.query
    print(f"count = {count}")


if __name__ == '__main__':
    asyncio.run(main())
