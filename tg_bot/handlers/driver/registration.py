import logging
from typing import List, Union
from datetime import datetime

from aiogram import Router, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.keyboards.inline import year_inline, calendar_inline
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import DriverRegistration, AfterStart
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(AfterStart.ChooseRole, F.data == "driver_menu")
async def write_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]

    dmodel = DriverForm(
        tg_user_id=uid, name=None, birth_year=None, phone_number=None, car_types=None, citizenships=None,
        basis_of_stay=None, availability_95_code=None, date_stark_work=None, language_skills=None, job_experience=None,
        need_internship=None, unsuitable_countries=None, documents_availability=None, expected_salary=None,
        categories_availability=None, country_driving_licence=None, country_current_live=None, work_type=None,
        cadence=None, crew=None, driver_gender=None
    )
    await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_write_name", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang))
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.WriteName)


@router.message(DriverRegistration.WriteName)
async def choose_birth_year(message: [types.Message, types.CallbackQuery], state: FSMContext):
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message

    else:
        name = message.text.strip()
        if not await Ut.is_valid_name(name=name):
            text = await Ut.get_message_text(key="wrong_name_format", lang=ulang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        dmodel.name = name
        await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_choose_birth_year", lang=ulang)
    markup = await year_inline(from_year=datetime.now(tz=Config.TIMEZONE).year - 42, lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseBirthYear)


@router.callback_query(DriverRegistration.ChooseBirthYear)
async def write_phone_number(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.name = None
        await state.update_data(dmodel=dmodel)
        return await write_name(callback=callback, state=state)

    if cd != "back":
        try:
            direction, old_from_year = cd.split(':')

            if direction == "left":
                old_from_year = int(old_from_year) - 25
                markup = await year_inline(from_year=old_from_year, lang=ulang)
                return await callback.message.edit_reply_markup(reply_markup=markup)

            elif direction == "right":
                old_from_year = int(old_from_year) + 25
                if old_from_year > datetime.now(tz=Config.TIMEZONE).year - 18:
                    return

                markup = await year_inline(from_year=old_from_year, lang=ulang)
                return await callback.message.edit_reply_markup(reply_markup=markup)

            else:
                return

        except ValueError:
            birth_year = int(cd)

        dmodel.birth_year = birth_year
        await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_write_contact_number", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", add_btn="back", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.WritePhoneNumber)


@router.message(DriverRegistration.WritePhoneNumber)
@router.callback_query(DriverRegistration.WritePhoneNumber)
async def choose_car_type(message: [types.Message, types.CallbackQuery], state: FSMContext,
                          from_back_btn: bool = False):
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        cd = message.data
        if cd == "back" and not from_back_btn:
            dmodel.birth_year = None
            await state.update_data(dmodel=dmodel)
            return await choose_birth_year(message=message, state=state)

        message = message.message

    else:
        phone_number = message.text.strip().replace("+", "")
        if not phone_number.isdigit():
            text = await Ut.get_message_text(key="wrong_phone_number_format", lang=ulang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        dmodel.phone_number = str(phone_number)
        await state.update_data(dmodel=dmodel, selected_car_types=[])

    text = await Ut.get_message_text(key="driver_reg_choose_car_type", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="car_types", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseCarType)


@router.callback_query(DriverRegistration.ChooseCarType)
async def choose_citizenship(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.phone_number = None
        await state.update_data(dmodel=dmodel)
        return await write_phone_number(callback=callback, state=state, from_back_btn=True)

    selected_car_types: List = data["selected_car_types"]
    if cd != "back":
        markup = await Ut.get_markup(mtype="inline", key="car_types", lang=ulang)
        if cd == "confirm":
            if not selected_car_types:
                text = await Ut.get_message_text(key="wrong_confirm", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.car_types = selected_car_types
            selected_countries = []
            await state.update_data(dmodel=dmodel, selected_countries=selected_countries)

        else:
            if cd == "check":
                for block_buttons in markup.inline_keyboard:
                    for btn in block_buttons:
                        if btn.callback_data in ["check", "uncheck", "confirm", "back"]:
                            continue

                        if btn.callback_data not in selected_car_types:
                            selected_car_types.append(btn.callback_data)

                        btn.text = f"✅ {btn.text}"

                await state.update_data(selected_car_types=selected_car_types)

            elif cd == "uncheck":
                await state.update_data(selected_car_types=[])

            else:
                if cd in selected_car_types:
                    selected_car_types.remove(cd)

                else:
                    selected_car_types.append(cd)

                for row in markup.inline_keyboard:
                    for btn in row:
                        if btn.callback_data in selected_car_types:
                            btn.text = f"✅ {btn.text}"

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

    text = await Ut.get_message_text(key="driver_reg_choose_citizenship", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="continents", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    return await state.set_state(DriverRegistration.ChooseCitizenship)


@router.callback_query(DriverRegistration.ChooseCitizenship)
async def choose_basis_of_stay(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    logger.info(f"Handler called. {choose_basis_of_stay.__name__}. user_id={uid}")

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.car_types = None
        await state.update_data(dmodel=dmodel, selected_car_types=[])
        return await choose_car_type(message=callback, state=state, from_back_btn=True)

    if cd != "back":
        selected_countries: List[str] = data["selected_countries"]
        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(mtype="inline", key=f"countries_{selected_continent}_1", lang=ulang)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=selected_countries, text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=ulang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=selected_countries,
                                                        text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=ulang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=selected_countries,
                                                        text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(mtype="inline", key="continents", lang=ulang)
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "confirm" == cd:
            if not selected_countries:
                text = await Ut.get_message_text(key="wrong_confirm", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.citizenships = selected_countries
            await state.update_data(dmodel=dmodel)

        else:
            if cd == "0":
                return

            if cd in selected_countries:
                selected_countries.remove(cd)

            else:
                selected_countries.append(cd)

            await state.update_data(selected_countries=selected_countries)

            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{data['sp']}", lang=ulang)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=selected_countries, text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

    text = await Ut.get_message_text(key="driver_reg_basis_of_stay", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="basis_of_stay", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    return await state.set_state(DriverRegistration.ChooseBasisOfStay)


@router.callback_query(DriverRegistration.ChooseBasisOfStay)
async def code_95_availability(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.citizenships = None
        await state.update_data(dmodel=dmodel, selected_countries=[])
        return await choose_citizenship(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        dmodel.basis_of_stay = cd
        await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_availability_95_code", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="availability_95_code", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.Availability95Code)


@router.callback_query(DriverRegistration.Availability95Code)
async def choose_date_ready_to_start_work(callback: types.CallbackQuery, state: FSMContext,
                                          from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.basis_of_stay = None
        await state.update_data(dmodel=dmodel)
        return await choose_basis_of_stay(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        dmodel.availability_95_code = cd
        await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_date_start_work", lang=ulang)
    markup = await calendar_inline(date_time=datetime.now(tz=Config.TIMEZONE), lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseDateReadyToStartWork)


@router.callback_query(DriverRegistration.ChooseDateReadyToStartWork)
async def indicate_language_skills(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.availability_95_code = None
        await state.update_data(dmodel=dmodel)
        return await code_95_availability(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        if "l:" in cd:
            date_time = datetime.strptime(cd.replace("l:", ""), "%d.%m.%Y")
            return await callback.message.edit_reply_markup(
                reply_markup=await calendar_inline(date_time=date_time, lang=ulang))

        elif "r:" in cd:
            date_time = datetime.strptime(cd.replace("r:", ""), "%d.%m.%Y")
            return await callback.message.edit_reply_markup(
                reply_markup=await calendar_inline(date_time=date_time, lang=ulang))

        elif "." in cd:
            dmodel.date_stark_work = datetime.strptime(cd, "%d.%m.%Y")
            await state.update_data(dmodel=dmodel, languages_skills=[])

    text = await Ut.get_message_text(key="driver_reg_language_skills", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="language_skills", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.IndicateLanguageSkills)


@router.callback_query(DriverRegistration.IndicateLanguageSkills)
async def choose_job_experience(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.date_stark_work = None
        await state.update_data(dmodel=dmodel)
        return await choose_date_ready_to_start_work(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        languages_skills: List[str] = data["languages_skills"]
        if ":" in cd:
            cd_lang = cd.split(":")[0]
            for el in languages_skills.copy():
                if cd_lang in el:
                    languages_skills.remove(el)

            languages_skills.append(cd)
            await state.update_data(languages_skills=languages_skills)

            markup = await Ut.get_markup(mtype="inline", key="language_skills", lang=ulang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=languages_skills, text_placeholder="🟢")

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

        elif "confirm" == cd:
            if len(languages_skills) < 3:
                text = await Ut.get_message_text(key="wrong_language_skills", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.language_skills = languages_skills
            await state.update_data(dmodel=dmodel, job_experience=[])

    text = await Ut.get_message_text(key="driver_reg_job_experience", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="job_experience", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.IndicateJobExperience)


@router.callback_query(DriverRegistration.IndicateJobExperience)
async def choose_need_internship(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.language_skills = None
        await state.update_data(dmodel=dmodel, languages_skills=[])
        return await indicate_language_skills(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        job_experience: List[str] = data["job_experience"]
        if ":" in cd:
            row_val = cd.split(":")[0]
            for el in job_experience.copy():
                if row_val in el:
                    job_experience.remove(el)

            job_experience.append(cd)
            await state.update_data(job_experience=job_experience)

            markup = await Ut.get_markup(mtype="inline", key="job_experience", lang=ulang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=job_experience, text_placeholder="🟢")

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

        elif "confirm" == cd:
            if len(job_experience) < 3:
                text = await Ut.get_message_text(key="wrong_job_experience", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.job_experience = job_experience
            await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_need_internship", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="need_internship", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseNeedInternship)


@router.callback_query(DriverRegistration.ChooseNeedInternship)
async def choose_unsuitable_countries(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.job_experience = None
        await state.update_data(dmodel=dmodel, job_experience=[])
        return await choose_job_experience(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        dmodel.need_internship = cd
        await state.update_data(dmodel=dmodel, unsuitable_countries=[])

    text = await Ut.get_message_text(key="driver_reg_unsuitable_countries", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="continents", add_btn="skip", add_btn_index=-1, lang=ulang)
    print(f"ikm = {markup.inline_keyboard}")
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseUnsuitableCountries)


@router.callback_query(DriverRegistration.ChooseUnsuitableCountries)
async def select_document_availability(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.need_internship = None
        await state.update_data(dmodel=dmodel)
        return await choose_need_internship(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        unsuitable_countries: List[str] = data["unsuitable_countries"]
        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{selected_continent}_1", add_btn="skip", add_btn_index=-1, lang=ulang)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=unsuitable_countries, text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", add_btn="skip", add_btn_index=-1, lang=ulang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=unsuitable_countries,
                                                        text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{prev_page}", add_btn="skip", add_btn_index=-1, lang=ulang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=unsuitable_countries,
                                                        text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(mtype="inline", key="continents", add_btn="skip", add_btn_index=-1, lang=ulang)
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "confirm" == cd:
            if not unsuitable_countries:
                text = await Ut.get_message_text(key="wrong_confirm", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.unsuitable_countries = unsuitable_countries

        elif "skip" == cd:
            dmodel.unsuitable_countries = []

        else:
            if cd == "0":
                return

            if cd in unsuitable_countries:
                unsuitable_countries.remove(cd)

            else:
                unsuitable_countries.append(cd)

            await state.update_data(unsuitable_countries=unsuitable_countries)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{data['sp']}", add_btn="skip", add_btn_index=-1, lang=ulang
            )
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=unsuitable_countries, text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        await state.update_data(dmodel=dmodel, documents=[])

    text = await Ut.get_message_text(key="driver_reg_documents_availability", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="documents_availability", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    return await state.set_state(DriverRegistration.SelectDocumentsAvailability)


@router.callback_query(DriverRegistration.SelectDocumentsAvailability)
async def write_expected_salary(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.unsuitable_countries = None
        await state.update_data(dmodel=dmodel, unsuitable_countries=[])
        return await choose_unsuitable_countries(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        documents: List[str] = data["documents"]
        markup = await Ut.get_markup(mtype="inline", key="documents_availability", lang=ulang)
        if cd == "confirm":
            if not documents:
                text = await Ut.get_message_text(key="wrong_confirm", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.documents_availability = documents
            await state.update_data(dmodel=dmodel)

        else:
            if cd == "check":
                for block_buttons in markup.inline_keyboard:
                    for btn in block_buttons:
                        if btn.callback_data in ["check", "uncheck", "confirm", "back"]:
                            continue

                        if btn.callback_data not in documents:
                            documents.append(btn.callback_data)

                        btn.text = f"✅ {btn.text}"

                await state.update_data(documents=documents)

            elif cd == "uncheck":
                await state.update_data(documents=[])

            else:
                if cd in documents:
                    documents.remove(cd)

                else:
                    documents.append(cd)

                for row in markup.inline_keyboard:
                    for btn in row:
                        if btn.callback_data in documents:
                            btn.text = f"✅ {btn.text}"

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

    text = await Ut.get_message_text(key="driver_reg_expected_salary", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", lang=ulang, add_btn="back")
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.WriteExpectedSalary)


@router.message(DriverRegistration.WriteExpectedSalary)
@router.callback_query(DriverRegistration.WriteExpectedSalary)
async def select_categories(message: Union[types.Message, types.CallbackQuery], state: FSMContext,
                            from_back_btn: bool = False):
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        cd = message.data
        if cd == "back" and not from_back_btn:
            dmodel.documents_availability = None
            await state.update_data(dmodel=dmodel, documents=[])
            return await select_document_availability(callback=message, state=state, from_back_btn=True)

        message = message.message

    else:
        value = message.text.strip()
        if (not (await Ut.is_number(value))) or (float(value) < 0):
            text = await Ut.get_message_text(key="wrong_number", lang=ulang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        value = float(value)
        if not (Config.SALARY_MIN <= value <= Config.SALARY_MAX):
            text = await Ut.get_message_text(key="wrong_salary_value_range", lang=ulang)
            msg = await message.answer(
                text=text.replace("%value_min%", str(Config.SALARY_MIN)).replace("%value_max%", str(Config.SALARY_MAX)))
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        dmodel.expected_salary = value
        await state.update_data(dmodel=dmodel, categories=[])

    text = await Ut.get_message_text(key="driver_reg_availability_categories", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="categories_availability", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseAvailabilityCategories)


@router.callback_query(DriverRegistration.ChooseAvailabilityCategories)
async def choose_country_driving_license(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.expected_salary = None
        await state.update_data(dmodel=dmodel)
        return await write_expected_salary(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        categories = data["categories"]
        markup = await Ut.get_markup(mtype="inline", key="categories_availability", lang=ulang)
        if cd == "confirm":
            if not categories:
                text = await Ut.get_message_text(key="wrong_confirm", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.categories_availability = categories
            await state.update_data(dmodel=dmodel)

        else:
            if cd == "check":
                for block_buttons in markup.inline_keyboard:
                    for btn in block_buttons:
                        if btn.callback_data in ["check", "uncheck", "confirm", "back"]:
                            continue

                        if btn.callback_data not in categories:
                            categories.append(btn.callback_data)

                        btn.text = f"✅ {btn.text}"

                await state.update_data(categories=categories)

            elif cd == "uncheck":
                await state.update_data(categories=[])

            else:
                if cd in categories:
                    categories.remove(cd)

                else:
                    categories.append(cd)

                for row in markup.inline_keyboard:
                    for btn in row:
                        if btn.callback_data in categories:
                            btn.text = f"✅ {btn.text}"

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

    text = await Ut.get_message_text(key="driver_reg_country_driving_license", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="continents", lang=ulang, without_inline_buttons=["confirm"])
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseCountryDrivingLicense)


@router.callback_query(DriverRegistration.ChooseCountryDrivingLicense)
async def choose_country_current_live(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.categories_availability = None
        await state.update_data(dmodel=dmodel, categories=[])
        return await select_categories(message=callback, state=state, from_back_btn=True)

    if cd != "back":
        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{selected_continent}_1", lang=ulang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=ulang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=ulang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(
                mtype="inline", key="continents", lang=ulang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        else:
            if cd == "0":
                return

            dmodel.country_driving_licence = cd
            await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_country_current_living", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="continents", lang=ulang, without_inline_buttons=["confirm"])
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseCountryCurrentLiving)


@router.callback_query(DriverRegistration.ChooseCountryCurrentLiving)
async def choose_work_type(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.country_driving_licence = None
        await state.update_data(dmodel=dmodel)
        return await choose_country_driving_license(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{selected_continent}_1", lang=ulang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=ulang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=ulang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(
                mtype="inline", key="continents", lang=ulang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        else:
            if cd == "0":
                return

            dmodel.country_current_live = cd
            await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_work_type", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="work_types", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(
        text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseWorkType)


@router.callback_query(DriverRegistration.ChooseWorkType)
async def choose_cadence(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.country_current_live = None
        await state.update_data(dmodel=dmodel)
        return await choose_country_current_live(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        dmodel.work_type = cd
        await state.update_data(dmodel=dmodel, selected_cadence=[])

    text = await Ut.get_message_text(key="driver_reg_choose_cadence", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="cadence", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.WriteCadence)


@router.callback_query(DriverRegistration.WriteCadence)
async def choose_crew(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.work_type = None
        await state.update_data(dmodel=dmodel)
        return await choose_work_type(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        selected_cadence: List = data["selected_cadence"]
        markup = await Ut.get_markup(mtype="inline", key="cadence", lang=ulang)
        flag = False
        if cd == "confirm":
            if not selected_cadence:
                text = await Ut.get_message_text(key="wrong_confirm", lang=ulang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            dmodel.cadence = selected_cadence
            await state.update_data(dmodel=dmodel)

        elif cd == "any":
            dmodel.cadence = ["any"]
            await state.update_data(dmodel=dmodel)

        else:
            if cd in selected_cadence:
                selected_cadence.remove(cd)

            else:
                selected_cadence.append(cd)

            for row in markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data in selected_cadence:
                        btn.text = f"✅ {btn.text}"

            flag = True

        try:
            if flag:
                return await callback.message.edit_reply_markup(reply_markup=markup)

        except TelegramBadRequest:
            return

    text = await Ut.get_message_text(key="driver_reg_crew", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="crew", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseCrew)


@router.callback_query(DriverRegistration.ChooseCrew)
async def choose_gender(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back" and not from_back_btn:
        dmodel.cadence = None
        await state.update_data(dmodel=dmodel, selected_cadence=[])
        return await choose_cadence(callback=callback, state=state, from_back_btn=True)

    if cd != "back":
        dmodel.crew = cd
        await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_gender", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="genders", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(DriverRegistration.ChooseGender)


@router.callback_query(DriverRegistration.ChooseGender)
async def form_confirmation(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]
    dmodel: DriverForm = data["dmodel"]

    cd = callback.data
    if cd == "back":
        dmodel.crew = None
        await state.update_data(dmodel=dmodel)
        return await choose_crew(callback=callback, state=state, from_back_btn=True)

    dmodel.driver_gender = cd
    await state.update_data(dmodel=dmodel)

    text = await Ut.get_message_text(key="driver_reg_confirmation", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="confirmation", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await callback.message.answer(text=await dmodel.form_completion(title=text, lang=ulang), reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

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
        return await choose_gender(callback=callback, state=state, from_back_btn=True)

    elif cd == "confirm":
        form_price = await dmodel.calculate_form_data()
        result = await DbDriver(
            tg_user_id=uid, opens_count=0, form_price=form_price, lang=ulang, status=1,
            **(await dmodel.form_data_to_dict())
        ).add()
        if result:
            text = await Ut.get_message_text(key="driver_reg_finish", lang=ulang)
            await Ut.delete_messages(user_id=uid)
            msg = await callback.message.answer(text=text)
            await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
            return await state.clear()

        else:
            text = await Ut.get_message_text(key="driver_reg_finish_error", lang=ulang)
            msg = await callback.message.answer(text=text)
            await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
