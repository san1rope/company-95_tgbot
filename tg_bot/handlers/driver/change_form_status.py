import logging

from aiogram import Router, F, types, enums

from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.misc.utils import Utils as Ut, AdditionalButtons

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "driver_change_form_status")
async def change_status(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    forms_count = len(await DbDriver(status=1).select())
    driver = await DbDriver(tg_user_id=uid).select()
    new_status = int(not bool(driver.status))
    await DbDriver(tg_user_id=uid).update(status=new_status)

    text_notify = await Ut.get_message_text(key="driver_menu_change_form_status", lang=driver.lang)
    text_menu = await Ut.get_message_text(key="driver_menu_text", lang=driver.lang)
    text_menu = text_menu.replace("%forms_count%", str(forms_count))
    text_menu = text_menu.replace("%form_opens%", str(driver.opens_count))
    markup = await Ut.get_markup(
        mtype="inline", lang=driver.lang, key="driver_menu",
        additional_buttons=[
            AdditionalButtons(buttons={f"driver_change_form_status:{'off' if new_status else 'on'}": None})]
    )

    await Ut.delete_messages(user_id=uid)
    msg_notify = await callback.message.answer(text=text_notify)
    msg_menu = await callback.message.answer(text=text_menu, reply_markup=markup)

    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg_notify.message_id)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg_menu.message_id)
