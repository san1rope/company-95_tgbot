import logging
from datetime import datetime
from typing import Optional, Union, Dict, List

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup

from config import Config
from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.db_models.schemas import Driver
from tg_bot.handlers.start import choose_role
from tg_bot.keyboards.inline import year_inline, calendar_inline
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import DriverRegistration
from tg_bot.misc.utils import Utils as Ut, call_functions

logger = logging.getLogger(__name__)
router = Router()


class RegistrationSteps:

    @staticmethod
    async def model_form_correct(title: str, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        if isinstance(data_model, DriverForm):
            title = await data_model.form_completion(title=title, lang=lang)

        elif isinstance(data_model, Driver):
            title = await DriverForm().form_completion(title=title, lang=lang, db_model=data_model)

        return title

    @staticmethod
    async def send_step_message(user_id: int, text: str, markup: Optional[InlineKeyboardMarkup] = None):
        await Ut.delete_messages(user_id=user_id)
        msg = await Config.BOT.send_message(chat_id=user_id, text=text, reply_markup=markup)
        await Ut.add_msg_to_delete(user_id=user_id, msg_id=msg.message_id)

    @staticmethod
    async def get_lang(state_data: Dict, user_id: int) -> str:
        if state_data["status"] == 0:
            lang = state_data["ulang"]

        elif state_data["status"] == 1:
            driver = await DbDriver(tg_user_id=user_id).select()
            lang = driver.lang

        else:
            lang = Config.DEFAULT_LANG

        return lang

    @classmethod
    async def name(cls, user_id: int, state: FSMContext, lang: str, call_function,
                   data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_write_name", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, add_btn="back")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.WriteName)

    @classmethod
    async def name_handler(cls, message: Union[types.Message, types.CallbackQuery], state: FSMContext):
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]

        if isinstance(message, types.CallbackQuery):
            await message.answer()

            cd = message.data
            if cd == "back" and status == 0:
                await choose_role(message=message, state=state)

            elif cd == "back" and status == 1:
                await data["function_for_back"](callback=message, state=state, from_reg_steps=True)

            return

        lang = await cls.get_lang(state_data=data, user_id=uid)

        name = message.text.strip()
        if not await Ut.is_valid_name(name=name):
            text = await Ut.get_message_text(key="wrong_name_format", lang=lang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        func_params = [uid, state, name]
        if status == 1:
            func_params.append("name")

        await data["call_function"](*func_params)

    @classmethod
    async def birth_year(cls, user_id: int, state: FSMContext, lang: str, call_function,
                         data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_choose_birth_year", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await year_inline(from_year=datetime.now(tz=Config.TIMEZONE).year - 42, lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseBirthYear)

    @classmethod
    async def birth_year_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        cd = callback.data
        lang = await cls.get_lang(state_data=data, user_id=uid)

        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.name = None
            await state.update_data(dmodel=dmodel)

            return await cls.name(
                user_id=uid, state=state, lang=lang, call_function=call_functions["birth_year"],
                data_model=dmodel
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            direction, old_from_year = cd.split(':')

            if direction == "left":
                old_from_year = int(old_from_year) - 25
                markup = await year_inline(from_year=old_from_year, lang=lang)
                return await callback.message.edit_reply_markup(reply_markup=markup)

            elif direction == "right":
                old_from_year = int(old_from_year) + 25
                if old_from_year > datetime.now(tz=Config.TIMEZONE).year - 18:
                    return

                markup = await year_inline(from_year=old_from_year, lang=lang)
                return await callback.message.edit_reply_markup(reply_markup=markup)

            else:
                return

        except ValueError:
            birth_year = int(cd)

        data = await state.get_data()
        func_params = [uid, state, birth_year]
        if status == 1:
            func_params.append("birth_year")

        return await data["call_function"](*func_params)

    @classmethod
    async def phone_number(cls, user_id: int, state: FSMContext, lang: str, call_function,
                           data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_write_contact_number", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, add_btn="back")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.WritePhoneNumber)

    @classmethod
    async def phone_number_handler(cls, message: [types.Message, types.CallbackQuery], state: FSMContext):
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        if isinstance(message, types.CallbackQuery):
            await message.answer()

            cd = message.data
            if cd == "back" and status == 0:
                dmodel: DriverForm = data["dmodel"]
                dmodel.birth_year = None
                await state.update_data(dmodel=dmodel)
                await cls.birth_year(
                    user_id=uid, state=state, lang=lang, call_function=call_functions["phone_number"], data_model=dmodel
                )

            elif cd == "back" and status == 1:
                await data["function_for_back"](callback=message, state=state, from_reg_steps=True)

            return

        phone_number = message.text.strip().replace("+", "")
        if not phone_number.isdigit():
            text = await Ut.get_message_text(key="wrong_phone_number_format", lang=lang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        func_params = [uid, state, phone_number]
        if status == 1:
            func_params.append("phone_number")

        return await data["call_function"](*func_params)

    @classmethod
    async def car_types(cls, user_id: int, state: FSMContext, lang: str, call_function,
                        data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_choose_car_type", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="car_types")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseCarType)

    @classmethod
    async def car_types_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)
        status = data["status"]

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.phone_number = None
            await state.update_data(dmodel=dmodel)
            return await cls.phone_number(
                user_id=uid, state=state, lang=lang, call_function=call_functions["car_types"], data_model=dmodel
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            selected_car_types: List[str] = data["selected_car_types"]

        except KeyError:
            selected_car_types = []
            await state.update_data(selected_car_types=selected_car_types)

        if cd != "back":
            markup = await Ut.get_markup(mtype="inline", key="car_types", lang=lang)
            if cd == "confirm":
                if not selected_car_types:
                    text = await Ut.get_message_text(key="wrong_confirm", lang=lang)
                    msg = await callback.message.answer(text=text)
                    return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

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

        func_params = [uid, state, selected_car_types]
        if status == 1:
            func_params[2] = ",".join(selected_car_types)
            func_params.append("car_types")

        return await data["call_function"](*func_params)

    @classmethod
    async def citizenships(cls, user_id: int, state: FSMContext, lang: str, call_function,
                           data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_choose_citizenship", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="continents")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseCitizenship)

    @classmethod
    async def citizenships_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.car_types = None
            await state.update_data(dmodel=dmodel, selected_car_types=[])
            return await cls.car_types(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["citizenships"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            selected_countries: List[str] = data["selected_countries"]

        except KeyError:
            selected_countries = []
            await state.update_data(selected_countries=selected_countries)

        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(mtype="inline", key=f"countries_{selected_continent}_1", lang=lang)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=selected_countries, text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=lang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=selected_countries,
                                                        text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=lang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=selected_countries,
                                                        text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(mtype="inline", key="continents", lang=lang)
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "confirm" == cd:
            if not selected_countries:
                text = await Ut.get_message_text(key="wrong_confirm", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        else:
            if cd == "0":
                return

            if cd in selected_countries:
                selected_countries.remove(cd)

            else:
                selected_countries.append(cd)

            await state.update_data(selected_countries=selected_countries)

            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{data['sp']}", lang=lang)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=selected_countries, text_placeholder="✅ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        func_params = [uid, state, selected_countries]
        if status == 1:
            func_params[2] = ",".join(selected_countries)
            func_params.append("citizenships")

        return await data["call_function"](*func_params)

    @classmethod
    async def basis_of_stay(cls, user_id: int, state: FSMContext, lang: str, call_function,
                            data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_basis_of_stay", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="basis_of_stay")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseBasisOfStay)

    @classmethod
    async def basis_of_stay_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = data["ulang"]
        status = data["status"]

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.citizenships = None
            await state.update_data(dmodel=dmodel, selected_countries=[])
            return await cls.citizenships(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["basis_of_stay"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("basis_of_stay")

        return await data["call_function"](*func_params)

    @classmethod
    async def availability_95_code(cls, user_id: int, state: FSMContext, lang: str, call_function,
                                   data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_availability_95_code", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="availability_95_code")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.Availability95Code)

    @classmethod
    async def availability_95_code_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.basis_of_stay = None
            await state.update_data(dmodel=dmodel)
            return await cls.basis_of_stay(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["95_code"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("availability_95_code")

        return await data["call_function"](*func_params)

    @classmethod
    async def date_stark_work(cls, user_id: int, state: FSMContext, lang: str, call_function,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_date_start_work", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await calendar_inline(date_time=datetime.now(tz=Config.TIMEZONE), lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseDateReadyToStartWork)

    @classmethod
    async def date_stark_work_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.availability_95_code = None
            await state.update_data(dmodel=dmodel)
            return await cls.availability_95_code(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["date_start_work"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        if "l:" in cd:
            date_time = datetime.strptime(cd.replace("l:", ""), "%d.%m.%Y")
            return await callback.message.edit_reply_markup(
                reply_markup=await calendar_inline(date_time=date_time, lang=lang))

        elif "r:" in cd:
            date_time = datetime.strptime(cd.replace("r:", ""), "%d.%m.%Y")
            return await callback.message.edit_reply_markup(
                reply_markup=await calendar_inline(date_time=date_time, lang=lang))

        elif "." in cd:
            func_params = [uid, state, datetime.strptime(cd, "%d.%m.%Y")]
            if status == 1:
                func_params.append("date_stark_work")

            return await data["call_function"](*func_params)

    @classmethod
    async def language_skills(cls, user_id: int, state: FSMContext, lang: str, call_function,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_language_skills", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="language_skills", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.IndicateLanguageSkills)

    @classmethod
    async def language_skills_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.date_stark_work = None
            await state.update_data(dmodel=dmodel)
            return await cls.date_stark_work(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["language_skills"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            languages_skills: List[str] = data["languages_skills"]

        except KeyError:
            languages_skills = []
            await state.update_data(languages_skills=languages_skills)

        if ":" in cd:
            cd_lang = cd.split(":")[0]
            for el in languages_skills.copy():
                if cd_lang in el:
                    languages_skills.remove(el)

            languages_skills.append(cd)
            await state.update_data(languages_skills=languages_skills)

            markup = await Ut.get_markup(mtype="inline", key="language_skills", lang=lang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=languages_skills, text_placeholder="🟢")

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

        elif "confirm" == cd:
            if len(languages_skills) < 3:
                text = await Ut.get_message_text(key="wrong_language_skills", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        func_params = [uid, state, languages_skills]
        if status == 1:
            func_params[2] = ",".join(languages_skills)
            func_params.append("language_skills")

        return await data["call_function"](*func_params)

    @classmethod
    async def job_experience(cls, user_id: int, state: FSMContext, lang: str, call_function,
                             data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_job_experience", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="job_experience", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.IndicateJobExperience)

    @classmethod
    async def job_experience_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.language_skills = None
            await state.update_data(dmodel=dmodel, languages_skills=[])
            return await cls.language_skills(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["job_experience"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        job_experience: List[str] = data["job_experience"]
        if ":" in cd:
            row_val = cd.split(":")[0]
            for el in job_experience.copy():
                if row_val in el:
                    job_experience.remove(el)

            job_experience.append(cd)
            await state.update_data(job_experience=job_experience)

            markup = await Ut.get_markup(mtype="inline", key="job_experience", lang=lang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=job_experience, text_placeholder="🟢")

            try:
                return await callback.message.edit_reply_markup(reply_markup=markup)

            except TelegramBadRequest:
                return

        elif "confirm" == cd:
            if len(job_experience) < 3:
                text = await Ut.get_message_text(key="wrong_job_experience", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            func_params = [uid, state, job_experience]
            if status == 1:
                func_params[2] = ",".join(job_experience)
                func_params.append("job_experience")

            return await data["call_function"](*func_params)

    @classmethod
    async def need_internship(cls, user_id: int, state: FSMContext, lang: str, call_function,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_need_internship", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="need_internship", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseNeedInternship)

    @classmethod
    async def need_internship_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.job_experience = None
            await state.update_data(dmodel=dmodel, job_experience=[])
            return await cls.job_experience(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["need_internship"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("need_internship")

        return await data["call_function"](*func_params)

    @classmethod
    async def unsuitable_countries(cls, user_id: int, state: FSMContext, lang: str, call_function,
                                   data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_unsuitable_countries", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="continents", add_btn="skip", add_btn_index=-1, lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseUnsuitableCountries)

    @classmethod
    async def unsuitable_countries_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.need_internship = None
            await state.update_data(dmodel=dmodel)
            return await cls.need_internship(
                user_id=uid, state=state, data_model=dmodel, lang=lang,
                call_function=call_functions["unsuitable_countries"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            unsuitable_countries: List[str] = data["unsuitable_countries"]

        except KeyError:
            unsuitable_countries = []
            await state.update_data(unsuitable_countries=unsuitable_countries)

        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{selected_continent}_1", add_btn="skip", add_btn_index=-1, lang=lang)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=unsuitable_countries, text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", add_btn="skip", add_btn_index=-1, lang=lang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=unsuitable_countries,
                                                        text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{prev_page}", add_btn="skip", add_btn_index=-1, lang=lang)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=unsuitable_countries,
                                                        text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(mtype="inline", key="continents", add_btn="skip", add_btn_index=-1, lang=lang)
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "confirm" == cd:
            if not unsuitable_countries:
                text = await Ut.get_message_text(key="wrong_confirm", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        elif "skip" == cd:
            unsuitable_countries = []

        else:
            if cd == "0":
                return

            if cd in unsuitable_countries:
                unsuitable_countries.remove(cd)

            else:
                unsuitable_countries.append(cd)

            await state.update_data(unsuitable_countries=unsuitable_countries)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{data['sp']}", add_btn="skip", add_btn_index=-1, lang=lang
            )
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=unsuitable_countries, text_placeholder="☑️ %btn.text%")

            return await callback.message.edit_reply_markup(reply_markup=markup)

        func_params = [uid, state, unsuitable_countries]
        if status == 1:
            func_params[2] = ",".join(unsuitable_countries)
            func_params.append("unsuitable_countries")

        return await data["call_function"](*func_params)

    @classmethod
    async def documents_availability(cls, user_id: int, state: FSMContext, lang: str, call_function,
                                     data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_documents_availability", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="documents_availability", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.SelectDocumentsAvailability)

    @classmethod
    async def documents_availability_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.unsuitable_countries = None
            await state.update_data(dmodel=dmodel, unsuitable_countries=[])
            return await cls.unsuitable_countries(
                user_id=uid, state=state, data_model=dmodel, lang=lang,
                call_function=call_functions["documents_availability"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            documents: List[str] = data["documents"]

        except KeyError:
            documents = []
            await state.update_data(documents=documents)

        markup = await Ut.get_markup(mtype="inline", key="documents_availability", lang=lang)
        if cd == "confirm":
            if not documents:
                text = await Ut.get_message_text(key="wrong_confirm", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            func_params = [uid, state, documents]
            if status == 1:
                func_params[2] = ",".join(documents)
                func_params.append("documents_availability")

            return await data["call_function"](*func_params)

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

    @classmethod
    async def expected_salary(cls, user_id: int, state: FSMContext, lang: str, call_function,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_expected_salary", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, add_btn="back")
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.WriteExpectedSalary)

    @classmethod
    async def expected_salary_handler(cls, message: [types.Message, types.CallbackQuery], state: FSMContext):
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        if isinstance(message, types.CallbackQuery):
            await message.answer()

            cd = message.data
            if cd == "back" and status == 0:
                dmodel: DriverForm = data["dmodel"]
                dmodel.documents_availability = None
                await state.update_data(dmodel=dmodel, documents=[])
                await cls.documents_availability(
                    user_id=uid, state=state, data_model=dmodel, lang=lang,
                    call_function=call_functions["expected_salary"]
                )

            elif cd == "back" and status == 1:
                return await data["function_for_back"](callback=message, state=state, from_reg_steps=True)

            return

        value = message.text.strip()
        if (not (await Ut.is_number(value))) or (float(value) < 0):
            text = await Ut.get_message_text(key="wrong_number", lang=lang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        value = float(value)
        if not (Config.SALARY_MIN <= value <= Config.SALARY_MAX):
            text = await Ut.get_message_text(key="wrong_salary_value_range", lang=lang)
            msg = await message.answer(
                text=text.replace("%value_min%", str(Config.SALARY_MIN)).replace("%value_max%", str(Config.SALARY_MAX)))
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        func_params = [uid, state, value]
        if status == 1:
            func_params.append("expected_salary")

        return await data["call_function"](*func_params)

    @classmethod
    async def categories_availability(cls, user_id: int, state: FSMContext, lang: str, call_function,
                                      data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_availability_categories", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="categories_availability", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseAvailabilityCategories)

    @classmethod
    async def categories_availability_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.expected_salary = None
            await state.update_data(dmodel=dmodel)
            return await cls.expected_salary(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["categories"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            categories = data["categories"]

        except KeyError:
            categories = []
            await state.update_data(categories=categories)

        markup = await Ut.get_markup(mtype="inline", key="categories_availability", lang=lang)
        if cd == "confirm":
            if not categories:
                text = await Ut.get_message_text(key="wrong_confirm", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            func_params = [uid, state, categories]
            if status == 1:
                func_params[2] = ",".join(categories)
                func_params.append("categories_availability")

            return await data["call_function"](*func_params)

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

    @classmethod
    async def country_driving_licence(cls, user_id: int, state: FSMContext, lang: str, call_function,
                                      data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_country_driving_license", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="continents", lang=lang, without_inline_buttons=["confirm"])
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseCountryDrivingLicense)

    @classmethod
    async def country_driving_licence_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.categories_availability = None
            await state.update_data(dmodel=dmodel, categories=[])
            return await cls.categories_availability(
                user_id=uid, state=state, data_model=dmodel, lang=lang,
                call_function=call_functions["country_driving_licence"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{selected_continent}_1", lang=lang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=lang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=lang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(
                mtype="inline", key="continents", lang=lang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        else:
            if cd == "0":
                return

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("country_driving_licence")

        return await data["call_function"](*func_params)

    @classmethod
    async def country_current_live(cls, user_id: int, state: FSMContext, lang: str, call_function,
                                   data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_country_current_living", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="continents", lang=lang, without_inline_buttons=["confirm"])
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseCountryCurrentLiving)

    @classmethod
    async def country_current_live_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.country_driving_licence = None
            await state.update_data(dmodel=dmodel)
            return await cls.country_driving_licence(
                user_id=uid, state=state, data_model=dmodel, lang=lang,
                call_function=call_functions["country_current_live"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{selected_continent}_1", lang=lang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            await state.update_data(sp=next_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=lang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            await state.update_data(sp=prev_page)
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=lang,
                without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        elif "to_continents" == cd:
            markup = await Ut.get_markup(
                mtype="inline", key="continents", lang=lang, without_inline_buttons=["confirm"])
            return await callback.message.edit_reply_markup(reply_markup=markup)

        else:
            if cd == "0":
                return

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("country_current_live")

        return await data["call_function"](*func_params)

    @classmethod
    async def work_type(cls, user_id: int, state: FSMContext, lang: str, call_function,
                        data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_work_type", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="work_types", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseWorkType)

    @classmethod
    async def work_type_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.country_current_live = None
            await state.update_data(dmodel=dmodel)
            return await cls.country_current_live(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["work_type"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("work_type")

        return await data["call_function"](*func_params)

    @classmethod
    async def cadence(cls, user_id: int, state: FSMContext, lang: str, call_function,
                      data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_choose_cadence", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="cadence", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.WriteCadence)

    @classmethod
    async def cadence_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.work_type = None
            await state.update_data(dmodel=dmodel)
            return await cls.work_type(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["cadence"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        try:
            selected_cadence: List = data["selected_cadence"]

        except KeyError:
            selected_cadence = []
            await state.update_data(selected_cadence=selected_cadence)

        markup = await Ut.get_markup(mtype="inline", key="cadence", lang=lang)
        flag = False
        if cd == "confirm":
            if not selected_cadence:
                text = await Ut.get_message_text(key="wrong_confirm", lang=lang)
                msg = await callback.message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        elif cd == "any":
            selected_cadence = ["any"]

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

        func_params = [uid, state, selected_cadence]
        if status == 1:
            func_params.append("cadence")

        return await data["call_function"](*func_params)

    @classmethod
    async def crew(cls, user_id: int, state: FSMContext, lang: str, call_function,
                   data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_crew", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="crew", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseCrew)

    @classmethod
    async def crew_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.cadence = None
            await state.update_data(dmodel=dmodel, selected_cadence=[])
            return await cls.cadence(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["crew"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("crew")

        return await data["call_function"](*func_params)

    @classmethod
    async def driver_gender(cls, user_id: int, state: FSMContext, lang: str, call_function,
                            data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_gender", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", key="genders", lang=lang)
        await cls.send_step_message(user_id=user_id, text=text, markup=markup)

        await state.update_data(call_function=call_function)

        await state.set_state(DriverRegistration.ChooseGender)

    @classmethod
    async def driver_gender_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        status = data["status"]
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data
        if cd == "back" and status == 0:
            dmodel: DriverForm = data["dmodel"]
            dmodel.crew = None
            await state.update_data(dmodel=dmodel)
            return await cls.crew(
                user_id=uid, state=state, data_model=dmodel, lang=lang, call_function=call_functions["driver_gender"]
            )

        elif cd == "back" and status == 1:
            return await data["function_for_back"](callback=callback, state=state, from_reg_steps=True)

        func_params = [uid, state, cd]
        if status == 1:
            func_params.append("crew")

        return await data["call_function"](*func_params)


router.message.register(RegistrationSteps.name_handler, DriverRegistration.WriteName)
router.callback_query.register(RegistrationSteps.name_handler, DriverRegistration.WriteName)
router.callback_query.register(RegistrationSteps.birth_year_handler, DriverRegistration.ChooseBirthYear)
router.message.register(RegistrationSteps.phone_number_handler, DriverRegistration.WritePhoneNumber)
router.callback_query.register(RegistrationSteps.phone_number_handler, DriverRegistration.WritePhoneNumber)
router.callback_query.register(RegistrationSteps.car_types_handler, DriverRegistration.ChooseCarType)
router.callback_query.register(RegistrationSteps.citizenships_handler, DriverRegistration.ChooseCitizenship)
router.callback_query.register(RegistrationSteps.basis_of_stay_handler, DriverRegistration.ChooseBasisOfStay)
router.callback_query.register(RegistrationSteps.availability_95_code_handler, DriverRegistration.Availability95Code)
router.callback_query.register(RegistrationSteps.date_stark_work_handler, DriverRegistration.ChooseDateReadyToStartWork)
router.callback_query.register(RegistrationSteps.language_skills_handler, DriverRegistration.IndicateLanguageSkills)
router.callback_query.register(RegistrationSteps.job_experience_handler, DriverRegistration.IndicateJobExperience)
router.callback_query.register(RegistrationSteps.need_internship_handler, DriverRegistration.ChooseNeedInternship)
router.callback_query.register(RegistrationSteps.unsuitable_countries_handler,
                               DriverRegistration.ChooseUnsuitableCountries)
router.callback_query.register(RegistrationSteps.documents_availability_handler,
                               DriverRegistration.SelectDocumentsAvailability)
router.callback_query.register(RegistrationSteps.expected_salary_handler, DriverRegistration.WriteExpectedSalary)
router.message.register(RegistrationSteps.expected_salary_handler, DriverRegistration.WriteExpectedSalary)
router.callback_query.register(RegistrationSteps.categories_availability_handler,
                               DriverRegistration.ChooseAvailabilityCategories)
router.callback_query.register(RegistrationSteps.country_driving_licence_handler,
                               DriverRegistration.ChooseCountryDrivingLicense)
router.callback_query.register(RegistrationSteps.country_current_live_handler,
                               DriverRegistration.ChooseCountryCurrentLiving)
router.callback_query.register(RegistrationSteps.work_type_handler, DriverRegistration.ChooseWorkType)
router.callback_query.register(RegistrationSteps.cadence_handler, DriverRegistration.WriteCadence)
router.callback_query.register(RegistrationSteps.crew_handler, DriverRegistration.ChooseCrew)
router.callback_query.register(RegistrationSteps.driver_gender_handler, DriverRegistration.ChooseGender)
