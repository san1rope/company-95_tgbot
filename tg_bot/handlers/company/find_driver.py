import logging
from copy import deepcopy

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.handlers.company.payments_processing import PaymentsProcessing
from tg_bot.keyboards.inline import CustomInlineMarkups as Cim, ActionOnDriver, ActionsAfterBtnOpen
from tg_bot.misc.models import DriverForm
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "find_driver")
async def show_driver(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    params = {"tg_user_id": uid}
    params.update({
        "tg_user_id": uid, "birth_year": [company.birth_year_left_edge, company.birth_year_right_edge],
        "car_types": company.car_types, "citizenships": company.citizenships,
        "basis_of_stay": company.basis_of_stay,
        "availability_95_code": company.availability_95_code,
        "date_start_work": [company.date_start_work_left_edge, company.date_start_work_right_edge],
        "language_skills": company.language_skills, "job_experience": company.job_experience,
        "need_internship": company.need_internship, "unsuitable_countries": company.unsuitable_countries,
        "expected_salary": [company.expected_salary_left_edge, company.expected_salary_right_edge],
        "categories_availability": company.categories_availability,
        "country_driving_licence": company.country_driving_licence,
        "country_current_live": company.country_current_live,
        "work_type": company.work_type, "cadence": company.cadence, "dangerous_goods": company.dangerous_goods,
        "crew": company.crew, "driver_gender": company.driver_gender, "status": 1
    })

    viewed_drivers_id = deepcopy(company.viewed_drivers)
    viewed_drivers_id.extend(company.open_drivers)

    db_driver = DbDriver(**params)
    drivers = await db_driver.select(viewed_drivers_id=viewed_drivers_id)

    text_info_before_open = await Ut.get_message_text(lang=company.lang, key="company_text_before_driver_form")
    markup_info_before_open = await Ut.get_markup(lang=company.lang, mtype="inline", key="company_find_driver_menu")
    await Ut.send_step_message(user_id=uid, texts=[text_info_before_open], markups=[markup_info_before_open])

    for driver in drivers:
        text_driver = await Ut.get_message_text(lang=company.lang, key="company_driver_found")
        text_driver = text_driver.replace("%driver_id%", str(driver.id))
        text_driver = text_driver.replace("%driver_price%", str(driver.form_price))
        text_driver += "\n\n" + await DriverForm().form_completion(lang=company.lang, db_model=driver, for_company=True)
        markup = await Cim.find_driver_menu(lang=company.lang, driver_id=driver.id)
        msg = await callback.message.answer(text=text_driver, reply_markup=markup)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    count_drivers = (await db_driver.select(viewed_drivers_id=viewed_drivers_id, count_records=True)) - 3
    text = await Ut.get_message_text(lang=company.lang, key="company_text_after_driver_form")
    text = text.replace("%drivers_count%", str(count_drivers if count_drivers >= 0 else 0))
    msg = await callback.message.answer(text=text, reply_markup=markup_info_before_open)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


@router.callback_query(ActionOnDriver.filter(F.action == "save"))
async def save_driver(callback: types.CallbackQuery, callback_data: ActionOnDriver):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    if callback_data.driver_id in company.saved_drivers:
        text = await Ut.get_message_text(lang=company.lang, key="company_driver_already_saved")

    else:
        company.saved_drivers.append(callback_data.driver_id)
        await DbCompany(tg_user_id=uid).update(saved_drivers=company.saved_drivers)
        text = await Ut.get_message_text(lang=company.lang, key="company_driver_save")

    driver = await DbDriver(db_id=callback_data.driver_id).select()
    text_driver = await Ut.get_message_text(lang=company.lang, key="company_driver_found")
    text_driver = text_driver.replace("%driver_id%", str(driver.id))
    text_driver = text_driver.replace("%driver_price%", str(driver.form_price))
    text_driver += "\n\n" + await DriverForm().form_completion(lang=company.lang, db_model=driver, for_company=True)
    markup = await Cim.find_driver_menu(lang=company.lang, driver_id=driver.id)

    text += "\n\n" + text_driver

    await callback.message.edit_text(text=text, reply_markup=markup, disable_web_page_preview=True)


@router.callback_query(ActionOnDriver.filter(F.action == "open"))
async def open_driver(callback: types.CallbackQuery, callback_data: ActionOnDriver):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    if company.paid_subscription:
        text = await Ut.get_message_text(lang=company.lang, key="company_open_driver_subscribe_confirmation")
        text = text.replace("%opens_count%", str(company.paid_subscription))
        text = text.replace("%driver_id%", str(callback_data.driver_id))
        markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="confirmation")

        for row_data in markup.inline_keyboard:
            for i_btn in row_data:
                if i_btn.callback_data == "confirm":
                    i_btn.callback_data = ActionsAfterBtnOpen(
                        action="open_with_subscribe", driver_id=callback_data.driver_id).pack()

                elif i_btn.callback_data == "back":
                    i_btn.callback_data = ActionsAfterBtnOpen(
                        action="back_to_form", driver_id=callback_data.driver_id).pack()

    else:
        text = await Ut.get_message_text(lang=company.lang, key="company_pay_for_driver_choose_payment_system")
        markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_choose_payment_system")

        for row_data in markup.inline_keyboard:
            for i_btn in row_data:
                if i_btn.callback_data == "back":
                    i_btn.callback_data = ActionsAfterBtnOpen(
                        action="back_to_form", driver_id=callback_data.driver_id).pack()

                else:
                    i_btn.callback_data = ActionsAfterBtnOpen(
                        action="choose_payment_system", driver_id=callback_data.driver_id,
                        additional_data=i_btn.callback_data
                    ).pack()

    await callback.message.edit_text(text=text, reply_markup=markup, disable_web_page_preview=True)


@router.callback_query(ActionsAfterBtnOpen.filter(F.action == "back_to_form"))
async def back_to_form(callback: types.CallbackQuery, callback_data: ActionsAfterBtnOpen):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    driver = await DbDriver(db_id=int(callback_data.driver_id)).select()
    text_driver = await Ut.get_message_text(lang=company.lang, key="company_driver_found")
    text_driver = text_driver.replace("%driver_id%", str(driver.id))
    text_driver = text_driver.replace("%driver_price%", str(driver.form_price))
    text_driver += "\n\n" + await DriverForm().form_completion(lang=company.lang, db_model=driver, for_company=True)
    markup = await Cim.find_driver_menu(lang=company.lang, driver_id=driver.id)

    await callback.message.edit_text(text=text_driver, reply_markup=markup, disable_web_page_preview=True)


@router.callback_query(ActionsAfterBtnOpen.filter(F.action == "open_with_subscribe"))
async def open_with_subscribe_confirmation(callback: types.CallbackQuery, callback_data: ActionsAfterBtnOpen):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    driver = await DbDriver(db_id=int(callback_data.data)).select()
    company.open_drivers.append(driver.id)
    if driver.id in company.saved_drivers:
        company.saved_drivers.remove(driver.id)

    await DbCompany(db_id=company.id).update(
        open_drivers=company.open_drivers, saved_drivers=company.saved_drivers)

    await DbDriver(db_id=driver.id).update(opens_count=driver.opens_count + 1)
    text = await Ut.get_message_text(lang=company.lang, key="pay_for_driver_success")
    text += "\n\n" + await DriverForm().form_completion(lang=company.lang, db_model=driver)

    msg = await callback.message.edit_text(text=text, reply_markup=None, disable_web_page_preview=True)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


@router.callback_query(ActionsAfterBtnOpen.filter(F.action == "choose_payment_system"))
async def payment_system_selected(callback: types.CallbackQuery, state: FSMContext, callback_data: ActionsAfterBtnOpen):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(lang=company.lang, key="payment_in_creating_process")
    await Ut.send_step_message(user_id=uid, texts=[text])

    await state.update_data(function_for_back=show_driver, type="open_driver",
                            current_driver_id=int(callback_data.driver_id))

    payment_method = getattr(PaymentsProcessing, callback_data.additional_data)
    await payment_method(callback=callback, state=state)
