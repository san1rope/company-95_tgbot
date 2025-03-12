import logging
import asyncio
from typing import Union, Optional, List, Any

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.filters.company import IsCompany
from tg_bot.handlers.company.menu import show_menu
from tg_bot.handlers.driver.register_driver import RegistrationSteps
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import CompanyFilters
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(IsCompany(), F.data == "filters")
async def selected_filters_btn(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="company_filters", lang=company.lang)
    text = await DriverForm().form_completion(title=text, lang=company.lang, db_model=company)
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_filters")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(CompanyFilters.ChooseFilterMenuBtn)


@router.callback_query(CompanyFilters.ChooseFilterMenuBtn)
async def processing_filters_menu(message: [types.CallbackQuery, types.Message], state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        cd = message.data
        if cd == "back":
            await state.clear()
            return await show_menu(message=message)

    else:
        cd = ""
        uid = message

    company = await DbCompany(tg_user_id=uid).select()
    if cd == "show_filters" or isinstance(message, int):
        text = await Ut.get_message_text(key="company_filters_choose_param", lang=company.lang)
        markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="filter_params_1")
        await Ut.send_step_message(user_id=uid, text=text, markup=markup)

        return await state.set_state(CompanyFilters.ChooseParam)

    elif cd == "reset_filters":
        text = await Ut.get_message_text(key="company_reset_filters_confirmation", lang=company.lang)
        markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="confirmation")
        await Ut.send_step_message(user_id=uid, text=text, markup=markup)

        await state.set_state(CompanyFilters.ResetFiltersConfirmation)


@router.callback_query(CompanyFilters.ResetFiltersConfirmation)
async def reset_filters_has_completed(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    cd = callback.data
    if cd == "back":
        return await selected_filters_btn(callback=callback, state=state)

    company = await DbCompany(tg_user_id=uid).select()
    result = await DbCompany(tg_user_id=uid).update(
        birth_year_left_edge=None, birth_year_right_edge=None, car_types=None, citizenships=None, basis_of_stay=None,
        availability_95_code=None, date_stark_work_left_edge=None, date_stark_work_right_edge=None,
        language_skills=None, job_experience=None, need_internship=None, unsuitable_countries=None,
        expected_salary_left_edge=None, expected_salary_right_edge=None, categories_availability=None,
        country_driving_licence=None, country_current_live=None, work_type=None, cadence=None, dangerous_goods=None,
        crew=None, driver_gender=None
    )
    if result:
        text = await Ut.get_message_text(key="company_reset_filters_completed", lang=company.lang)
        await Ut.send_step_message(user_id=uid, text=text)

        await asyncio.sleep(1)
        await selected_filters_btn(callback=callback, state=state)

    else:
        text = await Ut.get_message_text(lang=company.lang, key="company_reset_filters_error")
        msg = await callback.message.answer(text=text)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


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

    elif "back" == cd:
        return await selected_filters_btn(callback=callback, state=state)

    else:
        await state.update_data(status=2, function_for_back=processing_filters_menu, call_function=param_has_changed)

        reg_method = getattr(RegistrationSteps, cd)
        await reg_method(state=state, lang=company.lang)


async def param_has_changed(state: FSMContext, returned_data: Union[str, int, List[Any]], field_name: str):
    uid = state.key.user_id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    if field_name == "birth_year":
        year_left, year_right = returned_data
        result = await DbCompany(tg_user_id=uid).update(
            birth_year_left_edge=year_left, birth_year_right_edge=year_right)

    elif field_name == "date_stark_work":
        date_left, date_right = returned_data
        result = await DbCompany(tg_user_id=uid).update(
            date_stark_work_left_edge=date_left, date_stark_work_right_edge=date_right)

    elif field_name == "expected_salary":
        summ_left, summ_right = returned_data
        result = await DbCompany(tg_user_id=uid).update(
            expected_salary_left_edge=summ_left, expected_salary_right_edge=summ_right)

    else:
        result = await DbCompany(tg_user_id=uid).update(**{field_name: returned_data})

    if result:
        text = await Ut.get_message_text(key="company_filters_param_changed", lang=company.lang)
        await Ut.send_step_message(user_id=uid, text=text)

        await asyncio.sleep(1)
        await processing_filters_menu(message=uid, state=state)

    else:
        text = await Ut.get_message_text(key="company_filters_error_filter_params_changed", lang=company.lang)
        msg = await Config.BOT.send_message(chat_id=uid, text=text)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
