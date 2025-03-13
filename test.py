import asyncio
from datetime import datetime, timezone, timedelta

from tg_bot.db_models.db_gino import connect_to_db
from tg_bot.db_models.quick_commands import DbDriver


async def main():
    await connect_to_db(remove_data=False)

    result = await DbDriver(
        birth_year=[1993, 1995],
        basis_of_stay=["1", "2", "3", "8"],
        citizenships=["pl", "al", "be"],
        date_stark_work=[datetime.now(), datetime.now() + timedelta(days=10)],
        expected_salary=[60, 120]
    ).select(viewed_drivers_id=[])
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
