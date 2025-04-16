import logging
from typing import Union

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.handlers.driver.register_driver import RegistrationSteps
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import AfterStart, DriverRegistration
from tg_bot.misc.utils import Utils as Ut, call_functions, AdditionalButtons

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(AfterStart.ChooseRole, F.data == "driver_menu")
async def motd_message(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]

    text = await Ut.get_message_text(key="driver_reg_motd", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", lang=ulang,
                                 additional_buttons=[AdditionalButtons(buttons={"fill_data": None})])
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(DriverRegistration.MOTDMessage)


@router.callback_query(DriverRegistration.MOTDMessage)
async def choose_birth_year(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]

    dmodel = DriverForm()
    await state.update_data(
        dmodel=dmodel, status=0, call_function=choose_messangers_availabilities, motd_func=motd_message)

    await RegistrationSteps().birth_year(state=state, lang=ulang, data_model=dmodel)


async def choose_messangers_availabilities(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.birth_year = returned_data
    await state.update_data(dmodel=dmodel, selected_messangers=[], call_function=choose_car_types)

    await RegistrationSteps().messangers(state=state, data_model=dmodel, lang=ulang)


async def choose_car_types(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.messangers = returned_data
    await state.update_data(dmodel=dmodel, selected_car_types=[], call_function=choose_citizenships)

    await RegistrationSteps().car_types(state=state, data_model=dmodel, lang=ulang)


async def choose_citizenships(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.car_types = returned_data
    await state.update_data(dmodel=dmodel, selected_countries=[], call_function=choose_basis_of_stay)

    await RegistrationSteps().citizenships(state=state, data_model=dmodel, lang=ulang)


async def choose_basis_of_stay(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.citizenships = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_95_code)

    await RegistrationSteps().basis_of_stay(state=state, data_model=dmodel, lang=ulang)


async def choose_95_code(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.basis_of_stay = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_date_ready_to_start_work)

    await RegistrationSteps().availability_95_code(state=state, data_model=dmodel, lang=ulang)


async def choose_date_ready_to_start_work(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.availability_95_code = returned_data
    await state.update_data(dmodel=dmodel, call_function=indicate_language_skills)

    await RegistrationSteps().date_start_work(state=state, data_model=dmodel, lang=ulang)


async def indicate_language_skills(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.date_start_work = returned_data
    await state.update_data(dmodel=dmodel, languages_skills=[], call_function=indicate_job_experience)

    await RegistrationSteps().language_skills(state=state, data_model=dmodel, lang=ulang)


async def indicate_job_experience(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.language_skills = returned_data
    await state.update_data(dmodel=dmodel, job_experience=[], call_function=choose_need_internship)

    await RegistrationSteps().job_experience(state=state, data_model=dmodel, lang=ulang)


async def choose_need_internship(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.job_experience = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_unsuitable_countries)

    await RegistrationSteps().need_internship(state=state, data_model=dmodel, lang=ulang)


async def choose_unsuitable_countries(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.need_internship = returned_data
    await state.update_data(dmodel=dmodel, unsuitable_countries=[], call_function=choose_dangerous_goods)

    await RegistrationSteps().unsuitable_countries(state=state, data_model=dmodel, lang=ulang)


async def choose_dangerous_goods(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.unsuitable_countries = returned_data
    await state.update_data(dmodel=dmodel, dangerous_goods=[], call_function=write_expected_salary)

    await RegistrationSteps().dangerous_goods(state=state, data_model=dmodel, lang=ulang)


async def write_expected_salary(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.dangerous_goods = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_categories)

    await RegistrationSteps().expected_salary(state=state, data_model=dmodel, lang=ulang)


async def choose_categories(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.expected_salary = returned_data
    await state.update_data(dmodel=dmodel, categories=[], call_function=choose_country_driving_licence)

    await RegistrationSteps().categories_availability(state=state, data_model=dmodel, lang=ulang)


async def choose_country_driving_licence(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.categories_availability = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_country_current_live)

    await RegistrationSteps().country_driving_licence(state=state, data_model=dmodel, lang=ulang)


async def choose_country_current_live(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.country_driving_licence = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_work_type)

    await RegistrationSteps().country_driving_licence(state=state, data_model=dmodel, lang=ulang)


async def choose_work_type(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.country_current_live = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_cadence)

    await RegistrationSteps().work_type(state=state, data_model=dmodel, lang=ulang)


async def choose_cadence(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.work_type = returned_data
    await state.update_data(dmodel=dmodel, selected_cadence=[], call_function=choose_crew)

    await RegistrationSteps().cadence(state=state, data_model=dmodel, lang=ulang)


async def choose_crew(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.cadence = returned_data
    await state.update_data(dmodel=dmodel, call_function=choose_driver_gender)

    await RegistrationSteps().crew(state=state, data_model=dmodel, lang=ulang)


async def choose_driver_gender(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.crew = returned_data
    await state.update_data(dmodel=dmodel, call_function=write_phone_number)

    await RegistrationSteps().driver_gender(state=state, data_model=dmodel, lang=ulang)


async def write_phone_number(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.driver_gender = returned_data
    await state.update_data(dmodel=dmodel, call_function=write_name)

    await RegistrationSteps().phone_number(state=state, data_model=dmodel, lang=ulang)


async def write_name(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.phone_number = returned_data
    await state.update_data(dmodel=dmodel, call_function=form_confirmation)

    await RegistrationSteps().name(state=state, lang=ulang, data_model=dmodel)


async def form_confirmation(state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.name = returned_data
    await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_confirmation", lang=ulang)
    text = await dmodel.form_completion(title=text, lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="confirmation", lang=ulang)
    await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

    await state.set_state(DriverRegistration.FormConfirmation)


@router.callback_query(DriverRegistration.FormConfirmation)
async def registration_finish(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back":
        dmodel.name = None
        await state.update_data(dmodel=dmodel, call_function=form_confirmation)
        return await RegistrationSteps().name(state=state, data_model=dmodel, lang=ulang)

    elif cd == "confirm":
        form_price = await dmodel.calculate_form_data()
        result = await DbDriver(
            tg_user_id=uid, opens_count=0, form_price=form_price, lang=ulang, status=1,
            **(dmodel.model_dump())
        ).add()
        if result:
            text = await Ut.get_message_text(key="driver_reg_finish", lang=ulang)
            await Ut.send_step_message(user_id=uid, text=text)
            return await state.clear()

        else:
            text = await Ut.get_message_text(key="driver_reg_finish_error", lang=ulang)
            msg = await callback.message.answer(text=text)
            await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


call_functions.update({
    "birth_year": choose_birth_year, "phone_number": write_phone_number,
    "messangers": choose_messangers_availabilities, "car_types": choose_car_types, "citizenships": choose_citizenships,
    "basis_of_stay": choose_basis_of_stay, "95_code": choose_95_code,
    "date_start_work": choose_date_ready_to_start_work, "language_skills": indicate_language_skills,
    "job_experience": indicate_job_experience, "need_internship": choose_need_internship,
    "unsuitable_countries": choose_unsuitable_countries, "dangerous_goods": choose_dangerous_goods,
    "expected_salary": write_expected_salary, "categories": choose_categories,
    "country_driving_licence": choose_country_driving_licence, "country_current_live": choose_country_current_live,
    "work_type": choose_work_type, "cadence": choose_cadence, "crew": choose_crew,
    "driver_gender": choose_driver_gender,
    "name": write_name
})
