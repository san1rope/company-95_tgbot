import asyncio

from tg_bot.db_models.db_gino import connect_to_db
from tg_bot.db_models.quick_commands import DbDriver


async def main():
    await connect_to_db(remove_data=False)

    result = await DbDriver(car_types=["4", "2", "8"], citizenships=["ba", "hr"]).select(by_filters=True)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
