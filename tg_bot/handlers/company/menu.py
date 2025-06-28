import logging
from typing import Union, Optional

from aiogram import Router, F, enums, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.filters.company import IsCompany
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.chat.type == enums.ChatType.PRIVATE, CommandStart(), IsCompany())
@router.callback_query(F.data == "back_from_driver_search")
async def show_menu(message: Union[types.Message, types.CallbackQuery], state: Optional[FSMContext] = None):
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    if isinstance(state, FSMContext):
        await state.clear()

    if isinstance(message, types.CallbackQuery):
        await message.answer()

    company = await DbCompany(tg_user_id=uid).select()
    forms_count = len(await DbDriver(status=1).select())
    text = await Ut.get_message_text(key="company_menu_text", lang=company.lang)
    text = text.replace("%forms_count%", str(forms_count))

    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_menu")
    await Ut.send_step_message(user_id=uid, texts=[text], markups=[markup])
