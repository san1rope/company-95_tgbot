import asyncio
import logging
from typing import Optional

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.handlers.company.menu import show_menu
from tg_bot.misc.models import DriverForm
from tg_bot.misc.payments_processing import PaymentsProcessing
from tg_bot.misc.states import CompanyFindDriver
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "find_driver")
async def show_driver(callback: types.CallbackQuery, state: FSMContext, retry: bool = False,
                      driver_id: Optional[int] = None):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    params = {"tg_user_id": uid}
    if not driver_id:
        params.update({
            "tg_user_id": uid, "birth_year": [company.birth_year_left_edge, company.birth_year_right_edge],
            "car_types": company.car_types, "citizenships": company.citizenships,
            "basis_of_stay": company.basis_of_stay,
            "availability_95_code": company.availability_95_code,
            "date_stark_work": [company.date_stark_work_left_edge, company.date_stark_work_right_edge],
            "language_skills": company.language_skills, "job_experience": company.job_experience,
            "need_internship": company.need_internship, "unsuitable_countries": company.unsuitable_countries,
            "expected_salary": [company.expected_salary_left_edge, company.expected_salary_right_edge],
            "categories_availability": company.categories_availability,
            "country_driving_licence": company.country_driving_licence,
            "country_current_live": company.country_current_live,
            "work_type": company.work_type, "cadence": company.cadence, "dangerous_goods": company.dangerous_goods,
            "crew": company.crew, "driver_gender": company.driver_gender
        })

    driver = await DbDriver(**params).select(viewed_drivers_id=company.viewed_drivers)
    if not driver:
        if retry and len(company.viewed_drivers) > 0:
            text = await Ut.get_message_text(lang=company.lang, key="company_find_driver_end")
            await Ut.send_step_message(user_id=uid, text=text)
            await asyncio.sleep(1.5)

            await DbCompany(tg_user_id=uid).update(viewed_drivers=[])

        elif retry and len(company.viewed_drivers) == 0:
            text = await Ut.get_message_text(lang=company.lang, key="company_drivers_list_none")
            await Ut.send_step_message(user_id=uid, text=text)
            await asyncio.sleep(1.5)

            return await show_menu(message=callback)

        return await show_driver(callback=callback, state=state, retry=True)

    company.viewed_drivers.append(driver.id)
    await DbCompany(tg_user_id=uid).update(viewed_drivers=company.viewed_drivers)
    await state.update_data(current_driver=driver.id)

    text = await Ut.get_message_text(key="company_driver_found", lang=company.lang)
    text = text.replace("%form_price%", str(driver.form_price))
    text = await DriverForm().form_completion(title=text, lang=company.lang, db_model=driver)
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_driver_found_menu")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(CompanyFindDriver.ActionOnDriver)


@router.callback_query(CompanyFindDriver.ActionOnDriver)
async def action_on_driver(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    current_driver_id = data["current_driver"]
    company = await DbCompany(tg_user_id=uid).select()

    cd = callback.data
    if cd == "back":
        await state.clear()
        return await show_menu(message=callback)

    elif cd == "next_driver":
        return await show_driver(callback=callback, state=state)

    elif cd == "previous_driver":
        if len(company.viewed_drivers) == 1:
            text = await Ut.get_message_text(key="company_wrong_previous_driver", lang=company.lang)
            msg = await callback.message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        company.viewed_drivers = company.viewed_drivers[:-2]
        await DbCompany(tg_user_id=uid).update(viewed_drivers=company.viewed_drivers)
        return await show_driver(callback=callback, state=state)

    elif cd == "save_driver":
        if current_driver_id in company.saved_drivers:
            text = await Ut.get_message_text(lang=company.lang, key="company_driver_already_saved")

        else:
            company.saved_drivers.append(current_driver_id)
            await DbCompany(tg_user_id=uid).update(saved_drivers=company.saved_drivers)
            text = await Ut.get_message_text(lang=company.lang, key="company_driver_save")

        msg = await callback.message.answer(text=text)
        return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    elif cd == "open_driver":
        text = await Ut.get_message_text(lang=company.lang, key="company_pay_for_driver_choose_payment_system")
        markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_choose_payment_system")
        await Ut.send_step_message(user_id=uid, text=text, markup=markup)

        return await state.set_state(CompanyFindDriver.ChoosePaymentSystem)


@router.callback_query(CompanyFindDriver.ChoosePaymentSystem)
async def select_payment_system(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    cd = callback.data
    if cd == "back":
        await DbCompany(tg_user_id=uid).update(viewed_drivers=company.viewed_drivers[:-1])
        return await show_driver(callback=callback, state=state, driver_id=uid)

    payment_method = getattr(PaymentsProcessing, cd)
    await payment_method(callback=callback, state=state)
