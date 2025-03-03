import logging
from typing import Union

from aiogram import Router, F, enums, types
from aiogram.filters import CommandStart

from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.filters.driver import IsDriver
from tg_bot.misc.utils import Utils as Ut, AdditionalButtons

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.chat.type == enums.ChatType.PRIVATE, CommandStart(), IsDriver())
async def show_menu(message: Union[types.Message, types.CallbackQuery]):
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message

    driver = await DbDriver(tg_user_id=uid).select()
    forms_count = len(await DbDriver(status=1).select())

    text = await Ut.get_message_text(key="driver_menu_text", lang=driver.lang)
    text = text.replace("%forms_count%", str(forms_count))
    text = text.replace("%form_opens%", str(driver.opens_count))
    markup = await Ut.get_markup(
        mtype="inline", lang=driver.lang, key="driver_menu",
        additional_buttons=[AdditionalButtons(buttons={'off' if driver.status else 'on': None})]
    )
    await Ut.delete_messages(user_id=uid)
    msg = await message.answer(text=text, reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
