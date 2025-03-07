import logging
from typing import Union

from aiogram import Router, F, enums, types
from aiogram.filters import CommandStart

from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.filters.driver import IsDriver
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.chat.type == enums.ChatType.PRIVATE, CommandStart(), IsDriver())
async def show_menu(message: Union[types.Message, types.CallbackQuery]):
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message

    driver = await DbCompany(tg_user_id=uid).select()
