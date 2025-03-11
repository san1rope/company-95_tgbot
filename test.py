import asyncio

from tg_bot.db_models.db_gino import connect_to_db


async def main():
    await connect_to_db(remove_data=False)


if __name__ == "__main__":
    asyncio.run(main())
