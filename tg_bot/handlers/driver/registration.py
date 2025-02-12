import logging
from typing import Union

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.handlers.driver_registration import RegistrationSteps
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import AfterStart, DriverRegistration
from tg_bot.misc.utils import Utils as Ut, call_functions

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
    markup = await Ut.get_markup(mtype="inline", lang=ulang, add_btn="fill_data")
    await RegistrationSteps.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(DriverRegistration.MOTDMessage)


@router.callback_query(DriverRegistration.MOTDMessage)
async def write_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]

    dmodel = DriverForm()
    await state.update_data(dmodel=dmodel, status=0)

    await RegistrationSteps().name(
        user_id=uid, state=state, lang=ulang, call_function=choose_birth_year, data_model=dmodel
    )


async def choose_birth_year(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.name = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().birth_year(
        user_id=tg_user_id, state=state, call_function=write_phone_number, data_model=dmodel, lang=ulang
    )


async def write_phone_number(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.birth_year = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().phone_number(
        user_id=tg_user_id, state=state, call_function=choose_car_types, data_model=dmodel, lang=ulang
    )


async def choose_car_types(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.phone_number = returned_data
    await state.update_data(dmodel=dmodel, selected_car_types=[])

    await RegistrationSteps().car_types(
        user_id=tg_user_id, state=state, call_function=choose_citizenships, data_model=dmodel, lang=ulang
    )


async def choose_citizenships(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.car_types = returned_data
    await state.update_data(dmodel=dmodel, selected_countries=[])

    await RegistrationSteps().citizenships(
        user_id=tg_user_id, state=state, call_function=choose_basis_of_stay, data_model=dmodel, lang=ulang
    )


async def choose_basis_of_stay(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.citizenships = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().basis_of_stay(
        user_id=tg_user_id, state=state, call_function=choose_95_code, data_model=dmodel, lang=ulang
    )


async def choose_95_code(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.basis_of_stay = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().availability_95_code(
        user_id=tg_user_id, state=state, call_function=choose_date_ready_to_start_work, data_model=dmodel, lang=ulang
    )


async def choose_date_ready_to_start_work(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.availability_95_code = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().date_stark_work(
        user_id=tg_user_id, state=state, call_function=indicate_language_skills, data_model=dmodel, lang=ulang
    )


async def indicate_language_skills(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.date_stark_work = returned_data
    await state.update_data(dmodel=dmodel, languages_skills=[])

    await RegistrationSteps().language_skills(
        user_id=tg_user_id, state=state, call_function=indicate_job_experience, data_model=dmodel, lang=ulang
    )


async def indicate_job_experience(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.language_skills = returned_data
    await state.update_data(dmodel=dmodel, job_experience=[])

    await RegistrationSteps().job_experience(
        user_id=tg_user_id, state=state, call_function=choose_need_internship, data_model=dmodel, lang=ulang
    )


async def choose_need_internship(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.job_experience = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().need_internship(
        user_id=tg_user_id, state=state, call_function=choose_unsuitable_countries, data_model=dmodel, lang=ulang
    )


async def choose_unsuitable_countries(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.need_internship = returned_data
    await state.update_data(dmodel=dmodel, unsuitable_countries=[])

    await RegistrationSteps().unsuitable_countries(
        user_id=tg_user_id, state=state, call_function=choose_documents_availability, data_model=dmodel, lang=ulang
    )


async def choose_documents_availability(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.unsuitable_countries = returned_data
    await state.update_data(dmodel=dmodel, documents=[])

    await RegistrationSteps().documents_availability(
        user_id=tg_user_id, state=state, call_function=write_expected_salary, data_model=dmodel, lang=ulang
    )


async def write_expected_salary(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.documents_availability = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().expected_salary(
        user_id=tg_user_id, state=state, call_function=choose_categories, data_model=dmodel, lang=ulang
    )


async def choose_categories(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.expected_salary = returned_data
    await state.update_data(dmodel=dmodel, categories=[])

    await RegistrationSteps().categories_availability(
        user_id=tg_user_id, state=state, call_function=choose_country_driving_licence, data_model=dmodel, lang=ulang
    )


async def choose_country_driving_licence(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.categories_availability = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().country_driving_licence(
        user_id=tg_user_id, state=state, call_function=choose_country_current_live, data_model=dmodel, lang=ulang
    )


async def choose_country_current_live(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]


    dmodel.country_driving_licence = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().country_driving_licence(
        user_id=tg_user_id, state=state, call_function=choose_work_type, data_model=dmodel, lang=ulang
    )


async def choose_work_type(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]


    dmodel.country_current_live = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().work_type(
        user_id=tg_user_id, state=state, call_function=choose_cadence, data_model=dmodel, lang=ulang
    )


async def choose_cadence(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.work_type = returned_data
    await state.update_data(dmodel=dmodel, selected_cadence=[])

    await RegistrationSteps().cadence(
        user_id=tg_user_id, state=state, call_function=choose_crew, data_model=dmodel, lang=ulang
    )


async def choose_crew(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.cadence = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().crew(
        user_id=tg_user_id, state=state, call_function=choose_driver_gender, data_model=dmodel, lang=ulang
    )


async def choose_driver_gender(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.crew = returned_data
    await state.update_data(dmodel=dmodel)

    await RegistrationSteps().driver_gender(
        user_id=tg_user_id, state=state, call_function=form_confirmation, data_model=dmodel, lang=ulang
    )


async def form_confirmation(tg_user_id: int, state: FSMContext, returned_data: Union[str, int]):
    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    dmodel.driver_gender = returned_data
    await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_confirmation", lang=ulang)
    text = await dmodel.form_completion(title=text, lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="confirmation", lang=ulang)
    await RegistrationSteps.send_step_message(user_id=tg_user_id, text=text, markup=markup)

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
        dmodel.driver_gender = None
        await state.update_data(dmodel=dmodel)
        return await RegistrationSteps().driver_gender(
            user_id=uid, state=state, call_function=form_confirmation, data_model=dmodel, lang=ulang
        )

    elif cd == "confirm":
        form_price = await dmodel.calculate_form_data()
        result = await DbDriver(
            tg_user_id=uid, opens_count=0, form_price=form_price, lang=ulang, status=1,
            **(await dmodel.form_data_to_dict())
        ).add()
        if result:
            text = await Ut.get_message_text(key="driver_reg_finish", lang=ulang)
            await RegistrationSteps.send_step_message(user_id=uid, text=text)
            return await state.clear()

        else:
            text = await Ut.get_message_text(key="driver_reg_finish_error", lang=ulang)
            msg = await callback.message.answer(text=text)
            await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


call_functions.update({
    "name": write_name, "birth_year": choose_birth_year, "phone_number": write_phone_number,
    "car_types": choose_car_types, "citizenships": choose_citizenships, "basis_of_stay": choose_basis_of_stay,
    "95_code": choose_95_code, "date_start_work": choose_date_ready_to_start_work,
    "language_skills": indicate_language_skills, "job_experience": indicate_job_experience,
    "need_internship": choose_need_internship, "unsuitable_countries": choose_unsuitable_countries,
    "documents_availability": choose_documents_availability, "expected_salary": write_expected_salary,
    "categories": choose_categories, "country_driving_licence": choose_country_driving_licence,
    "country_current_live": choose_country_current_live, "work_type": choose_work_type, "cadence": choose_cadence,
    "crew": choose_crew, "driver_gender": choose_driver_gender
})
