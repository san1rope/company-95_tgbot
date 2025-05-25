import asyncio
import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbDriver, DbCompany
from tg_bot.handlers.company.menu import show_menu as show_menu_company
from tg_bot.handlers.driver.menu import show_menu as show_menu_driver
from tg_bot.misc.states import ChangeLang
from tg_bot.misc.utils import Utils as Ut, AdditionalButtons

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "change_language")
async def show_lang_options(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    driver = await DbDriver(tg_user_id=uid).select()
    if driver:
        ulang = driver.lang
        user_role = "driver"

    else:
        company = await DbCompany(tg_user_id=uid).select()
        ulang = company.lang
        user_role = "company"

    await state.update_data(user_role=user_role)

    text = await Ut.get_message_text(key="choose_lang", lang=ulang)
    markup = await Ut.get_markup(
        mtype="inline", key="choose_lang", lang=ulang, additional_buttons=[AdditionalButtons(buttons={"back": None})])
    await Ut.send_step_message(user_id=uid, texts=[text], markups=[markup])

    await state.set_state(ChangeLang.ChooseLang)


@router.callback_query(ChangeLang.ChooseLang)
async def lang_is_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    user_role = data["user_role"]

    cd = callback.data
    if cd == "back":
        await state.clear()
        if user_role == "company":
            return await show_menu_company(message=callback)

        elif user_role == "driver":
            return await show_menu_driver(message=callback)

        return

    if user_role == "company":
        back_func = show_menu_company
        await DbCompany(tg_user_id=uid).update(lang=cd)

    elif user_role == "driver":
        back_func = show_menu_driver
        await DbDriver(tg_user_id=uid).update(lang=cd)

    else:
        return

    text = await Ut.get_message_text(lang=cd, key="language_has_been_changed")
    await Ut.send_step_message(user_id=uid, texts=[text])
    await asyncio.sleep(1.5)

    await state.clear()
    await back_func(message=callback)
