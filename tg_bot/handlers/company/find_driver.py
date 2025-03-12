import logging

from aiogram import Router, F, types

from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "find_driver")
async def show_driver(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()
