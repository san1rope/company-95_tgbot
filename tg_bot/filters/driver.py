from aiogram import types
from aiogram.filters import Filter

from tg_bot.db_models.quick_commands import DbDriver


class DriverFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return bool(await DbDriver(tg_user_id=message.from_user.id).select())
