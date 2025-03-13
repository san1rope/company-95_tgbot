import logging

from aiogram import Router, F, types

from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "saved_drivers")
async def show_saved_drivers(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)
