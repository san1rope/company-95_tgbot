import logging
from typing import Union

from aiogram import Router, F, types, enums
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.keyboards.inline import CustomInlineMarkups
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "support_company")
@router.message(F.chat.type == enums.ChatType.PRIVATE, Command("support"))
async def support(callback: Union[types.CallbackQuery, types.Message], state: FSMContext):
    uid = callback.from_user.id
    if isinstance(callback, types.CallbackQuery):
        await callback.answer()
        callback = callback.message

    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()
    if company:
        ulang = company.lang

    else:
        driver = await DbDriver(tg_user_id=uid).select()
        if driver:
            ulang = company.lang

        else:
            data = await state.get_data()
            ulang = data["ulang"] if data.get("ulang") else Config.DEFAULT_LANG

    text = await Ut.get_message_text(key="company_support", lang=ulang)
    markup = await CustomInlineMarkups.support_btn(lang=ulang)

    msg = await callback.answer(text=text, reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
