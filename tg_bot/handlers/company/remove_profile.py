import asyncio
import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.filters.company import IsCompany
from tg_bot.handlers.company.menu import show_menu
from tg_bot.handlers.start import choose_language
from tg_bot.misc.states import RemoveProfile
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "remove_company_profile", IsCompany())
async def remove_profile_confirmation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(lang=company.lang, key="company_remove_my_profile_confirmation")
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="confirmation")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(RemoveProfile.RemoveConfirmation)


@router.callback_query(RemoveProfile.RemoveConfirmation)
async def remove_has_been_confirmed(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    cd = callback.data
    if cd == "back":
        await state.clear()
        return await show_menu(message=callback)

    company = await DbCompany(tg_user_id=uid).select()
    result = await DbCompany(tg_user_id=uid).remove()
    if result:
        text = await Ut.get_message_text(lang=company.lang, key="company_remove_my_profile_success")
        await Ut.send_step_message(user_id=uid, text=text)
        await asyncio.sleep(1.5)
        return await choose_language(message=callback, state=state)

    else:
        text = await Ut.get_message_text(lang=company.lang, key="company_remove_my_profile_error")
        await Ut.send_step_message(user_id=uid, text=text)
        await asyncio.sleep(1.5)
        return await show_menu(message=callback)
