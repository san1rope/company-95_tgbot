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

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="company_menu_text", lang=company.lang)
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_menu")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)
