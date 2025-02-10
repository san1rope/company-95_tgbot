import logging

from aiogram import Router, F, types

from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.misc.models import DriverForm
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "driver_my_form")
async def show_my_form(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    driver = await DbDriver(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="driver_menu_my_form", lang=driver.lang)
    markup = await Ut.get_markup(mtype="inline", lang=driver.lang, key="driver_menu_my_form")

    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await DriverForm.form_completion(title="\n".join(text), lang=driver.lang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


@router.callback_query(F.data == "driver_my_form_reset_all")
async def form_reset(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)
