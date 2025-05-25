import logging
from typing import Union

from aiogram import Router, F, types, enums
from aiogram.filters import Command
from pyexpat.errors import messages

from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.keyboards.inline import CustomInlineMarkups
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "support_company")
@router.message(F.chat.type == enums.ChatType.PRIVATE, Command("support"))
async def support(callback: Union[types.CallbackQuery, types.Message]):
    uid = callback.from_user.id
    if isinstance(callback, types.CallbackQuery):
        await callback.answer()
        callback = callback.message

    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="company_support", lang=company.lang)
    markup = await CustomInlineMarkups.support_btn(lang=company.lang)

    msg = await callback.answer(text=text, reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
