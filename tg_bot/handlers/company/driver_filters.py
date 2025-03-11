import logging
import asyncio
from typing import Union, Optional

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.filters.company import IsCompany
from tg_bot.handlers.company.menu import show_menu
from tg_bot.handlers.driver.register_driver import RegistrationSteps
from tg_bot.misc.states import CompanyFilters
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(IsCompany(), F.data == "filters")
async def selected_filters_btn(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="", lang=company.lang)
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_filters")


@router.callback_query(IsCompany(), F.data == "show_filters")
async def show_filters(callback: Optional[Union[types.CallbackQuery, int]], state: FSMContext):
    if isinstance(callback, types.CallbackQuery):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

    else:
        uid = callback

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="company_filters_choose_param", lang=company.lang)
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="filter_params_1")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(CompanyFilters.ChooseParam)


@router.callback_query(CompanyFilters.ChooseParam)
async def show_param_options(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    cd = callback.data
    if "next_page:" in cd:
        next_page = int(cd.replace('next_page:', ''))
        markup = await Ut.get_markup(mtype="inline", key=f"filter_params_{next_page}", lang=company.lang)
        return await callback.message.edit_reply_markup(reply_markup=markup)

    elif "prev_page:" in cd:
        prev_page = int(cd.replace('prev_page:', ''))
        markup = await Ut.get_markup(mtype="inline", key=f"filter_params_{prev_page}", lang=company.lang)
        return await callback.message.edit_reply_markup(reply_markup=markup)

    elif "back_to_menu" == cd:
        return await show_menu(message=callback)

    else:
        await state.update_data(status=2, function_for_back=show_filters, call_function=param_has_changed)

        reg_method = getattr(RegistrationSteps, cd)
        await reg_method(state=state, lang=company.lang)


async def param_has_changed(state: FSMContext, returned_data: Union[str, int], field_name: str):
    uid = state.key.user_id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    result = await DbCompany(tg_user_id=uid).update(**{f"f_{field_name}": returned_data})
    if result:
        text = await Ut.get_message_text(key="company_filters_param_changed", lang=company.lang)
        await Ut.send_step_message(user_id=uid, text=text)

        await asyncio.sleep(1)

        await show_filters(callback=uid, state=state)

    else:
        text = await Ut.get_message_text(key="company_filters_error_filter_params_changed", lang=company.lang)
        msg = await Config.BOT.send_message(chat_id=uid, text=text)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
