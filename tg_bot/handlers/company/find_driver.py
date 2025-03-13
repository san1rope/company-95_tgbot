import logging

from aiogram import Router, F, types

from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "find_driver")
async def show_driver(callback: types.CallbackQuery, retry: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    driver = await DbDriver(
        tg_user_id=uid, birth_year=[company.birth_year_left_edge, company.birth_year_right_edge],
        car_types=company.car_types, citizenships=company.citizenships, basis_of_stay=company.basis_of_stay,
        availability_95_code=company.availability_95_code,
        date_stark_work=[company.date_stark_work_left_edge, company.date_stark_work_right_edge],
        language_skills=company.language_skills, job_experience=company.job_experience,
        need_internship=company.need_internship, unsuitable_countries=company.unsuitable_countries,
        expected_salary=[company.expected_salary_left_edge, company.expected_salary_right_edge],
        categories_availability=company.categories_availability,
        country_driving_licence=company.country_driving_licence, country_current_live=company.country_current_live,
        work_type=company.work_type, cadence=company.cadence, dangerous_goods=company.dangerous_goods,
        crew=company.crew, driver_gender=company.driver_gender
    ).select(viewed_drivers_id=company.viewed_drivers)
    if not driver:
        if retry:
            text = await Ut.get_message_text(lang=company.lang, key="")
            markup = await Ut.get_markup(mtype="inline", lang=company.lang)
            await Ut.send_step_message(user_id=uid, text=text)
