import logging
from copy import deepcopy
from datetime import datetime
from typing import Optional, Union, Dict, List, Any

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbDriver, DbCompany
from tg_bot.db_models.schemas import Driver
from tg_bot.keyboards.default import request_contact_default
from tg_bot.keyboards.inline import CustomInlineMarkups as Cim
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import DriverRegistration
from tg_bot.misc.utils import Utils as Ut, call_functions, AdditionalButtons, localization

logger = logging.getLogger(__name__)
router = Router()


class RegistrationSteps:

    @staticmethod
    async def model_form_correct(
            title: str, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None,
            hidden_status: Optional[bool] = None) -> str:
        if isinstance(data_model, DriverForm):
            title = await data_model.form_completion(title=title, lang=lang, hidden_status=hidden_status)

        elif isinstance(data_model, Driver):
            title = await DriverForm().form_completion(
                title=title, lang=lang, db_model=data_model, hidden_status=hidden_status)

        return title

    @staticmethod
    async def get_lang(state_data: Dict, user_id: int) -> str:
        status = state_data.get("status")
        if status == 0:
            lang = state_data["ulang"]

        elif status == 1:
            driver = await DbDriver(tg_user_id=user_id).select()
            lang = driver.lang

        elif status == 2:
            company = await DbCompany(tg_user_id=user_id).select()
            lang = company.lang

        else:
            lang = Config.DEFAULT_LANG

        return lang

    @staticmethod
    async def processing_back_btn(
            callback: types.CallbackQuery, state: FSMContext, lang: str, model_attr: str = None, function_for_back=None,
            next_function=None) -> bool:
        cd = callback.data
        if cd != "back":
            return False

        data = await state.get_data()
        status = data["status"]
        params = []
        if status == 0:
            dmodel: DriverForm = data.get("dmodel")
            if model_attr and dmodel:
                setattr(dmodel, model_attr, None)

            await state.update_data(dmodel=dmodel, function_for_back=function_for_back, call_function=next_function)

            if function_for_back == data["motd_func"]:
                params = {"callback": callback, "state": state}

            else:
                params = {"state": state, "lang": lang, "data_model": dmodel}

        elif status == 1:
            params = {"callback": callback, "state": state, "from_reg_steps": True}

        elif status == 2:
            params = {"message": state.key.user_id, "state": state}

        data = await state.get_data()
        await data["function_for_back"](**params)
        return True

    @staticmethod
    async def handler_finish(state: FSMContext, returned_value: Any, additional_field: str = None) -> bool:
        data = await state.get_data()

        func_params = [state, returned_value]
        if data["status"] in [1, 2]:
            func_params.append(additional_field)

        await data["call_function"](*func_params)
        return True

    @staticmethod
    async def processing_checkboxes(
            callback: types.CallbackQuery, state: FSMContext, lang: str, markup_key: str, error_msg_key: str,
            markup_without_buttons: List[str] = [], additional_buttons: List[AdditionalButtons] = []
    ) -> Union[list, bool]:
        cd = callback.data
        uid = callback.from_user.id
        data = await state.get_data()
        saved_data = data.get("saved_data") if "saved_data" in data else []
        hidden_status = data["hidden_status"] if data.get("hidden_status") is not None else None
        curr_selector_row = data.get("curr_selector_row")

        if callback.data == "confirm":
            if not saved_data:
                text = await Ut.get_message_text(key=error_msg_key, lang=lang)
                msg = await callback.message.answer(text=text)
                await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
                return False

        elif "row:" in cd or "col:" in cd or "hid_or_open_form" == cd:
            return False

        elif "selectors:" in markup_key and cd == "back_to_menu":
            selector_key = markup_key.split(":")[1]
            await state.update_data(curr_selector_row=None)
            markup = await Cim.selectors(lang=lang, data=saved_data, selector_key=selector_key)
            await callback.message.edit_reply_markup(reply_markup=markup)
            return False

        else:
            if cd == "0":
                return False

            if ":" in cd and "selectors:" in markup_key:
                selector_key = markup_key.split(":")[1]
                key, value = cd.split(":")
                if value == "set_value":
                    await state.update_data(curr_selector_row=key)
                    markup = await Cim.selector_cols(lang=lang, selector_key=selector_key, current_selector_row=key)
                    markup = await Ut.recognize_selected_values(
                        markup=markup, datalist=saved_data, text_placeholder="✅ %btn.text%")
                    await callback.message.edit_reply_markup(reply_markup=markup)
                    return False

                markup = await Cim.selector_cols(lang=lang, selector_key=selector_key, current_selector_row=key)

            else:
                markup = await Ut.get_markup(
                    mtype="inline", key=markup_key, lang=lang, additional_buttons=additional_buttons,
                    without_buttons=markup_without_buttons, hidden_status=hidden_status)

            if cd == "check":
                for block_buttons in markup.inline_keyboard:
                    for btn in block_buttons:
                        if btn.callback_data in [
                            "check", "uncheck", "confirm", "back", "skip", "hid_or_open_form"
                        ] or "row:" in btn.callback_data or "col:" in btn.callback_data:
                            continue

                        if btn.callback_data not in saved_data:
                            saved_data.append(btn.callback_data)

                        btn.text = f"✅ {btn.text}"

                await state.update_data(saved_data=saved_data)

            elif cd == "uncheck":
                await state.update_data(saved_data=[])

            elif cd == "skip":
                if cd in saved_data:
                    await state.update_data(saved_data=[])

                else:
                    saved_data = ["skip"]
                    await state.update_data(saved_data=saved_data)
                    for row in markup.inline_keyboard:
                        for btn in row:
                            if btn.callback_data in saved_data:
                                btn.text = f"✅ {btn.text}"

            else:
                if "skip" in saved_data:
                    saved_data.remove("skip")

                if cd in saved_data:
                    saved_data.remove(cd)

                else:
                    saved_data.append(cd)

                await state.update_data(saved_data=saved_data)
                for row in markup.inline_keyboard:
                    for btn in row:
                        if btn.callback_data in saved_data:
                            btn.text = f"✅ {btn.text}"

            try:
                await callback.message.edit_reply_markup(reply_markup=markup)
                return False

            except TelegramBadRequest:
                return False

        await state.update_data(saved_data=[])

        if "skip" in saved_data:
            saved_data.remove("skip")

        return saved_data

    @staticmethod
    async def processing_selector(
            callback: types.CallbackQuery, state: FSMContext, lang: str, selector_key: str, error_msg_key: str
    ) -> Union[list, bool]:
        cd = callback.data
        uid = callback.from_user.id
        data = await state.get_data()
        saved_data = data["saved_data"] if data.get("saved_data") else []
        curr_selector_row = data.get("curr_selector_row")

        if cd == "0":
            return False

        elif cd == "back_to_menu":
            await state.update_data(curr_selector_row=None)
            markup = await Cim.selectors(lang=lang, data=saved_data, selector_key=selector_key)
            await callback.message.edit_reply_markup(reply_markup=markup)
            return False

        elif cd == "confirm":
            if len(saved_data) < 3:
                text = await Ut.get_message_text(key=error_msg_key, lang=lang)
                msg = await callback.message.answer(text=text)
                await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
                return False

        elif ":" in cd:
            print(f"cd = {cd}")
            key, value = cd.split(":")

            if value == "set_value":
                await state.update_data(curr_selector_row=key)
                markup = await Cim.selector_cols(lang=lang, selector_key=selector_key, current_selector_row=key)
                await callback.message.edit_reply_markup(reply_markup=markup)

            elif key == curr_selector_row:
                for item in deepcopy(saved_data):
                    if curr_selector_row in item:
                        saved_data.remove(item)
                        break

                saved_data.append(cd)
                await state.update_data(saved_data=saved_data, curr_selector_row=None)

                markup = await Cim.selectors(lang=lang, data=saved_data, selector_key=selector_key)
                await callback.message.edit_reply_markup(reply_markup=markup)

            return False

        await state.update_data(saved_data=None)
        return saved_data

    @classmethod
    async def iteration_by_countries(cls, lang: str, entrance_data: List[Optional[str]], action: str,
                                     markup_key: Optional[str] = None):
        current_localization = localization[lang] if "lang" in localization else localization[Config.DEFAULT_LANG]
        inline_markups_data = current_localization["markups"]["inline"]

        if markup_key:
            for row in inline_markups_data[markup_key]:
                for value in row.values():
                    if (value in ["check", "uncheck", "confirm", "back", "skip", "0", "to_continents"]
                    ) or ("next_page" in value) or ("prev_page" in value):
                        continue

                    if action == "+" and value not in entrance_data:
                        entrance_data.append(value)

                    elif action == "-" and value in entrance_data:
                        entrance_data.remove(value)

        else:
            for markup_key, markup_data in inline_markups_data.items():
                if "countries_" not in markup_key:
                    continue

                entrance_data = await cls.iteration_by_countries(
                    lang=lang, entrance_data=entrance_data, action=action, markup_key=markup_key)

        return entrance_data

    @classmethod
    async def processing_countries_markup(
            cls, callback: types.CallbackQuery, state: FSMContext, lang: str, error_msg_key: str,
            without_inline_buttons: Optional[List[str]] = [], additional_buttons: List[AdditionalButtons] = [],
            choose_one_country: bool = False) -> Union[list, str, bool]:
        cd = callback.data
        uid = callback.from_user.id
        data = await state.get_data()
        saved_data = data["saved_data"] if data.get("saved_data") else []
        hidden_status = data.get("hidden_status") if "hidden_status" in data else None

        if "cont:" in cd:
            selected_continent = cd.replace('cont:', '')
            await state.update_data(sc=selected_continent, sp=1)

            markup = await Ut.get_markup(mtype="inline", key=f"countries_{selected_continent}_1", lang=lang,
                                         additional_buttons=additional_buttons)
            await state.update_data(markup=markup)
            markup = await Ut.get_markup(markup=markup, lang=lang, hidden_status=hidden_status)
            markup = await Ut.recognize_selected_values(
                markup=markup, datalist=saved_data, text_placeholder="✅ %btn.text%")

            await callback.message.edit_reply_markup(reply_markup=markup)
            return False

        elif "next_page:" in cd:
            next_page = int(cd.replace('next_page:', ''))
            markup = await Ut.get_markup(
                mtype="inline", key=f"countries_{data['sc']}_{next_page}", lang=lang,
                additional_buttons=additional_buttons, without_buttons=without_inline_buttons)
            await state.update_data(sp=next_page, markup=markup)
            markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=saved_data,
                                                        text_placeholder="✅ %btn.text%")

            await callback.message.edit_reply_markup(reply_markup=markup)
            return False

        elif "prev_page:" in cd:
            prev_page = int(cd.replace('prev_page:', ''))
            markup = await Ut.get_markup(mtype="inline", key=f"countries_{data['sc']}_{prev_page}", lang=lang,
                                         additional_buttons=additional_buttons, without_buttons=without_inline_buttons)
            await state.update_data(sp=prev_page, markup=markup)
            markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
            markup = await Ut.recognize_selected_values(markup=markup, datalist=saved_data,
                                                        text_placeholder="✅ %btn.text%")
            await callback.message.edit_reply_markup(reply_markup=markup)
            return False

        elif "to_continents" == cd:
            markup = await Ut.get_markup(mtype="inline", key="continents", lang=lang,
                                         additional_buttons=additional_buttons, without_buttons=without_inline_buttons)
            await state.update_data(markup=markup)
            markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
            await callback.message.edit_reply_markup(reply_markup=markup)
            await state.update_data(sc=None)
            return False

        elif "skip" == cd:
            saved_data = []

        elif "confirm" == cd:
            if not saved_data:
                text = await Ut.get_message_text(key=error_msg_key, lang=lang)
                msg = await callback.message.answer(text=text)
                await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)
                return False

        elif cd in ["check", "uncheck"]:
            sc = data.get("sc")
            markup_key = None
            if sc:
                markup_key = f"countries_{sc}_{data['sp']}"

            saved_data = await cls.iteration_by_countries(
                lang=lang, entrance_data=saved_data, action="+" if cd == "check" else "-", markup_key=markup_key)

            await state.update_data(saved_data=saved_data)

            if sc:
                markup = await Ut.get_markup(
                    mtype="inline", key=markup_key, lang=lang, additional_buttons=additional_buttons,
                    without_buttons=without_inline_buttons
                )
                await state.update_data(markup=markup)
                markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
                markup = await Ut.recognize_selected_values(
                    markup=markup, datalist=saved_data, text_placeholder="✅ %btn.text%")

                await callback.message.edit_reply_markup(reply_markup=markup)

            return False

        else:
            if cd == "0":
                return False

            if choose_one_country:
                saved_data = cd

            else:
                if cd in saved_data:
                    saved_data.remove(cd)

                else:
                    saved_data.append(cd)

                await state.update_data(saved_data=saved_data)

                markup = await Ut.get_markup(
                    mtype="inline", key=f"countries_{data['sc']}_{data['sp']}", lang=lang,
                    additional_buttons=additional_buttons, without_buttons=without_inline_buttons)
                await state.update_data(markup=markup)
                markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
                markup = await Ut.recognize_selected_values(
                    markup=markup, datalist=saved_data, text_placeholder="✅ %btn.text%")

                await callback.message.edit_reply_markup(reply_markup=markup)
                return False

        await state.update_data(saved_data=[])
        return saved_data

    @classmethod
    async def birth_year(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        status_secondary = data.get("status_secondary")
        if status == 2 or status_secondary == 2:
            msg_key = "company_filters_birth_year_1"
            status = 2
            function_for_back = data[
                "function_for_back_secondary"] if data.get("function_for_back_secondary") else data["function_for_back"]

        else:
            msg_key = "driver_reg_choose_birth_year"
            function_for_back = data.get("function_for_back")
            if status != 1:
                status = 0
                function_for_back = data["motd_func"]

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Cim.year(from_year=datetime.now(tz=Config.TIMEZONE).year - 42, lang=lang)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(min_year=None, status=status, function_for_back=function_for_back)
        await state.set_state(DriverRegistration.ChooseBirthYear)

    @classmethod
    async def birth_year_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        cd = callback.data
        lang = await cls.get_lang(state_data=data, user_id=uid)

        min_year = data["min_year"]
        status_secondary = data.get("status_secondary")
        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang,
            next_function=data["call_function"] if status_secondary else call_functions["birth_year"],
            model_attr=None if status_secondary else "name",
            function_for_back=cls.birth_year if status_secondary else data.get("motd_func")
        )
        if result:
            return

        if cd == "0":
            return

        try:
            direction, old_from_year = cd.split(':')

            if direction == "left":
                old_from_year = int(old_from_year) - 25
                if old_from_year + 25 < 1950:
                    return

                markup = await Cim.year(from_year=old_from_year, lang=lang)
                return await callback.message.edit_reply_markup(reply_markup=markup)

            elif direction == "right":
                old_from_year = int(old_from_year) + 25
                if old_from_year > datetime.now(tz=Config.TIMEZONE).year - 18:
                    return

                markup = await Cim.year(from_year=old_from_year, lang=lang)
                return await callback.message.edit_reply_markup(reply_markup=markup)

            else:
                return

        except ValueError:
            returned_value = int(cd)

        status = data["status"]
        if (status == 2) and (not min_year):
            await state.update_data(min_year=returned_value, function_for_back_secondary=data["function_for_back"],
                                    status_secondary=data["status"], function_for_back=cls.birth_year, status=0)

            text = await Ut.get_message_text(key="company_filters_birth_year_2", lang=lang)
            markup = await Cim.year(from_year=datetime.now(tz=Config.TIMEZONE).year - 42, lang=lang)
            return await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        elif (status == 2 or status_secondary == 2) and min_year:
            await state.update_data(
                function_for_back=data["function_for_back_secondary"], status=data["status_secondary"],
                status_secondary=None, function_for_back_secondary=None)
            if min_year > returned_value:
                returned_value = [returned_value, min_year]

            else:
                returned_value = [min_year, returned_value]

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="birth_year")

    @classmethod
    async def messangers(cls, state: FSMContext, lang: str,
                         data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_choose_messangers_availabilities", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="messangers_availabilities")
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(selected_messangers=[])
        await state.set_state(DriverRegistration.ChooseMessangersAvailabilities)

    @classmethod
    async def messangers_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, next_function=call_functions["messangers"],
            function_for_back=cls.birth_year, model_attr="birth_year")
        if result:
            return

        data_from_checkboxes = await cls.processing_checkboxes(
            callback=callback, state=state, lang=lang, markup_key="messangers_availabilities",
            error_msg_key="wrong_confirm"
        )
        if data_from_checkboxes is False:
            return

        await cls.handler_finish(state=state, returned_value=data_from_checkboxes, additional_field="messangers")

    @classmethod
    async def car_types(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        if status == 2:
            text_key = "company_filters_car_types"

        else:
            text_key = "driver_reg_choose_car_type"

        text = await Ut.get_message_text(key=text_key, lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="car_types")
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(selected_car_types=[])
        await state.set_state(DriverRegistration.ChooseCarType)

    @classmethod
    async def car_types_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.messangers,
            next_function=call_functions["car_types"], model_attr="messangers")
        if result:
            return

        data_from_checkboxes = await cls.processing_checkboxes(
            callback=callback, state=state, lang=lang, markup_key="car_types", error_msg_key="wrong_confirm"
        )
        if data_from_checkboxes is False:
            return

        await cls.handler_finish(state=state, returned_value=data_from_checkboxes, additional_field="car_types")

    @classmethod
    async def citizenships(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        if status == 2:
            msg_key = "company_filters_citizenships"
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        else:
            msg_key = "driver_reg_choose_citizenship"
            additional_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(mtype="inline", lang=lang, key="continents", additional_buttons=additional_buttons)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(selected_countries=[], hidden_status=None)
        await state.set_state(DriverRegistration.ChooseCitizenship)

    @classmethod
    async def citizenships_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.car_types,
            next_function=call_functions["citizenships"], model_attr="car_types")
        if result:
            return

        status = data["status"]
        if status == 2:
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        else:
            additional_buttons = []

        data_from_countries = await cls.processing_countries_markup(
            callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
            additional_buttons=additional_buttons
        )
        if data_from_countries is False:
            return

        await cls.handler_finish(state=state, returned_value=data_from_countries, additional_field="citizenships")

    @classmethod
    async def basis_of_stay(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = False

        if status == 2:
            text_key = "company_filters_basis_of_stay"
            additional_buttons = [
                AdditionalButtons(index=-1, action="new", buttons={"check": None, "uncheck": None}),
                AdditionalButtons(index=-1, action="new", buttons={"confirm": None})
            ]

        else:
            text_key = "driver_reg_basis_of_stay"
            additional_buttons = []

        text = await Ut.get_message_text(key=text_key, lang=lang)
        markup = await Ut.get_markup(
            mtype="inline", lang=lang, key="basis_of_stay", additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup, hidden_status=hidden_status)

        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseBasisOfStay)

    @classmethod
    async def basis_of_stay_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        cd = callback.data

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.citizenships,
            next_function=call_functions["basis_of_stay"], model_attr="citizenships")
        if result:
            return

        status = data["status"]
        if status == 2:
            additional_buttons = [
                AdditionalButtons(index=-1, action="new", buttons={"check": None, "uncheck": None}),
                AdditionalButtons(index=-1, action="new", buttons={"confirm": None})
            ]
            returned_value = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm", markup_key="basis_of_stay",
                additional_buttons=additional_buttons
            )
            if returned_value is False:
                return

        else:
            returned_value = cd

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="basis_of_stay")

    @classmethod
    async def availability_95_code(cls, state: FSMContext, lang: str,
                                   data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            text_key = "company_filters_95_code"
            additional_buttons = [AdditionalButtons(index=-1, action="new", buttons={"confirm": None})]

        else:
            text_key = "driver_reg_availability_95_code"
            additional_buttons = []

        text = await Ut.get_message_text(key=text_key, lang=lang)
        markup = await Ut.get_markup(
            mtype="inline", lang=lang, key="availability_95_code", additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup)

        markup = await Ut.get_markup(markup=markup, hidden_status=hidden_status, lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.Availability95Code)

    @classmethod
    async def availability_95_code_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.basis_of_stay,
            next_function=call_functions["95_code"], model_attr="basis_of_stay")
        if result:
            return

        status = data["status"]
        if status == 2:
            returned_value = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
                additional_buttons=[AdditionalButtons(index=-1, action="new", buttons={"confirm": None})],
                markup_key="availability_95_code"
            )
            if returned_value is False:
                return

        else:
            returned_value = callback.data

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="availability_95_code")

    @classmethod
    async def date_start_work(cls, state: FSMContext, lang: str,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        status_secondary = data.get("status_secondary")
        hidden_status = data.get("hidden_status")

        if status == 2 or status_secondary == 2:
            msg_key = "company_filters_date_start_work_1"
            status = 2
            function_for_back = data[
                "function_for_back_secondary"] if data.get("function_for_back_secondary") else data["function_for_back"]

        else:
            msg_key = "driver_reg_date_start_work"
            function_for_back = data.get("function_for_back")
            if status != 1:
                status = 0
                function_for_back = cls.name

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Cim.calendar(date_time=datetime.now(tz=Config.TIMEZONE), lang=lang)
        await state.update_data(title=text, markup=markup)

        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(date_start_work_left=None, status=status, function_for_back=function_for_back)
        await state.set_state(DriverRegistration.ChooseDateReadyToStartWork)

    @classmethod
    async def date_start_work_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        date_start_work_left = data["date_start_work_left"]
        status_secondary = data.get("status_secondary")
        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang,
            function_for_back=cls.date_start_work if status_secondary else cls.availability_95_code,
            next_function=data["call_function"] if status_secondary else call_functions["date_start_work"],
            model_attr=None if status_secondary else "availability_95_code"
        )
        if result:
            return

        cd = callback.data
        if "l:" in cd:
            date_time = datetime.strptime(cd.replace("l:", ""), "%d.%m.%Y")
            current_dt = datetime.now(tz=Config.TIMEZONE)
            if current_dt.year == date_time.year and current_dt.month == date_time.month:
                date_time = current_dt

            return await callback.message.edit_reply_markup(
                reply_markup=await Cim.calendar(date_time=date_time, lang=lang))

        elif "r:" in cd:
            date_time = datetime.strptime(cd.replace("r:", ""), "%d.%m.%Y")
            return await callback.message.edit_reply_markup(
                reply_markup=await Cim.calendar(date_time=date_time, lang=lang))

        elif "." in cd:
            returned_value = datetime.strptime(cd, "%d.%m.%Y")

            status = data["status"]
            if (status == 2) and (not date_start_work_left):
                await state.update_data(
                    date_start_work_left=returned_value, function_for_back=cls.date_start_work,
                    function_for_back_secondary=data["function_for_back"], status=0,
                    status_secondary=data["status"]
                )

                text = await Ut.get_message_text(key="company_filters_date_start_work_2", lang=lang)
                markup = await Cim.calendar(date_time=returned_value, lang=lang)
                return await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

            elif (status == 2 or status_secondary == 2) and date_start_work_left:
                await state.update_data(
                    function_for_back=data["function_for_back_secondary"], status=data["status_secondary"],
                    status_secondary=None, function_for_back_secondary=None)
                if date_start_work_left > returned_value:
                    returned_value = [returned_value, date_start_work_left]

                else:
                    returned_value = [date_start_work_left, returned_value]

            await cls.handler_finish(state=state, returned_value=returned_value, additional_field="date_start_work")

    @classmethod
    async def language_skills(cls, state: FSMContext, lang: str,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        if status == 2:
            msg_key = "company_filters_language_skills"

        else:
            msg_key = "driver_reg_language_skills"

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Cim.selectors(lang=lang, selector_key="languages_skills", data=[])
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(title=text, markup=markup, languages_skills=[])
        await state.set_state(DriverRegistration.IndicateLanguageSkills)

    @classmethod
    async def language_skills_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.date_start_work,
            next_function=call_functions["language_skills"], model_attr="date_start_work")
        if result:
            return

        status = data["status"]
        if status == 2:
            returned_data = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, markup_key="selectors:languages_skills",
                error_msg_key="wrong_job_experience"
            )
            if returned_data is False:
                return

        else:
            returned_data = await cls.processing_selector(
                callback=callback, state=state, lang=lang, selector_key="languages_skills",
                error_msg_key="wrong_language_skills"
            )
            if returned_data is False:
                return

        await cls.handler_finish(state=state, returned_value=returned_data, additional_field="language_skills")

    @classmethod
    async def job_experience(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        if status == 2:
            msg_key = "company_filters_job_experience"

        else:
            msg_key = "driver_reg_job_experience"

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Cim.selectors(lang=lang, selector_key="job_experience", data=[])
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(title=text, markup=markup, job_experience=[])
        await state.set_state(DriverRegistration.IndicateJobExperience)

    @classmethod
    async def job_experience_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.language_skills,
            next_function=call_functions["job_experience"], model_attr="language_skills")
        if result:
            return

        status = data["status"]
        if status == 2:
            returned_data = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, markup_key="selectors:job_experience",
                error_msg_key="wrong_job_experience"
            )
            if returned_data is False:
                return

        else:
            returned_data = await cls.processing_selector(
                callback=callback, state=state, lang=lang, selector_key="job_experience",
                error_msg_key="wrong_job_experience"
            )
            if returned_data is False:
                return

        await cls.handler_finish(state=state, returned_value=returned_data, additional_field="job_experience")

    @classmethod
    async def need_internship(cls, state: FSMContext, lang: str,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_need_internship"
            additional_buttons = [
                AdditionalButtons(index=-1, action="new", buttons={"check": None, "uncheck": None}),
                AdditionalButtons(index=-1, action="new", buttons={"confirm": None})
            ]

        else:
            msg_key = "driver_reg_need_internship"
            additional_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(
            mtype="inline", key="need_internship", lang=lang, additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseNeedInternship)

    @classmethod
    async def need_internship_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.job_experience,
            next_function=call_functions["need_internship"], model_attr="job_experience")
        if result:
            return

        status = data["status"]
        if status == 2:
            additional_buttons = [
                AdditionalButtons(index=-1, action="new", buttons={"check": None, "uncheck": None}),
                AdditionalButtons(index=-1, action="new", buttons={"confirm": None})
            ]
            returned_value = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm", markup_key="need_internship",
                additional_buttons=additional_buttons
            )
            if returned_value is False:
                return

        else:
            returned_value = callback.data

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="need_internship")

    @classmethod
    async def unsuitable_countries(cls, state: FSMContext, lang: str,
                                   data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_unsuitable_countries"
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        else:
            msg_key = "driver_reg_unsuitable_countries"
            additional_buttons = [AdditionalButtons(action="new", index=-1, buttons={"skip": None})]

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(
            mtype="inline", key="continents", lang=lang,
            without_buttons=["cont:north_america", "cont:south_america", "cont:africa", "cont:oceania"],
            additional_buttons=additional_buttons
        )
        await state.update_data(title=text, markup=markup, unsuitable_countries=[])

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseUnsuitableCountries)

    @classmethod
    async def unsuitable_countries_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.need_internship,
            next_function=call_functions["unsuitable_countries"], model_attr="need_internship")
        if result:
            return

        status = data["status"]
        if status == 2:
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        elif "asia" in callback.data or data.get("sc") == "asia":
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        else:
            additional_buttons = [AdditionalButtons(buttons={"skip": None})]

        data_from_countries = await cls.processing_countries_markup(
            callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
            without_inline_buttons=["cont:north_america", "cont:south_america", "cont:africa", "cont:oceania"],
            additional_buttons=additional_buttons
        )
        if data_from_countries is False:
            return

        await cls.handler_finish(
            state=state, returned_value=data_from_countries, additional_field="unsuitable_countries")

    @classmethod
    async def dangerous_goods(cls, state: FSMContext, lang: str,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_dangerous_goods"

        else:
            msg_key = "driver_reg_dangerous_goods"

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="dangerous_goods", lang=lang)
        await state.update_data(title=text, markup=markup, dangerous_goods=[])

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseDangerousGoods)

    @classmethod
    async def dangerous_goods_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.unsuitable_countries,
            next_function=call_functions["dangerous_goods"], model_attr="unsuitable_countries")
        if result:
            return

        data_from_checkboxes = await cls.processing_checkboxes(
            callback=callback, state=state, lang=lang, markup_key="dangerous_goods", error_msg_key="wrong_confirm"
        )
        if data_from_checkboxes is False:
            return

        await cls.handler_finish(state=state, returned_value=data_from_checkboxes, additional_field="dangerous_goods")

    @classmethod
    async def expected_salary(cls, state: FSMContext, lang: str,
                              data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_expected_salary"

        else:
            msg_key = "driver_reg_expected_salary"

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        text = text.replace("%salary_min%", str(Config.SALARY_MIN))
        text = text.replace("%salary_max%", str(Config.SALARY_MAX))
        markup = await Ut.get_markup(
            mtype="inline", lang=lang, additional_buttons=[AdditionalButtons(buttons={"back": None})])
        await state.update_data(title=text, markup=markup)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.WriteExpectedSalary)

    @classmethod
    async def expected_salary_handler(cls, message: [types.Message, types.CallbackQuery], state: FSMContext):
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        if isinstance(message, types.CallbackQuery):
            await message.answer()

            result = await cls.processing_back_btn(
                callback=message, state=state, lang=lang, function_for_back=cls.dangerous_goods,
                next_function=call_functions["expected_salary"], model_attr="dangerous_goods")
            if result:
                return

        value = message.text.strip()
        status = data["status"]
        if status == 2:
            if ("-" not in value) or (value.count("-") > 1):
                text = await Ut.get_message_text(key="wrong_salary_format", lang=lang)
                msg = await message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            salary_min, salary_max = value.split("-")
            if (not (await Ut.is_number(salary_min))) or (not (await Ut.is_number(salary_max))):
                text = await Ut.get_message_text(key="wrong_number", lang=lang)
                msg = await message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            salary_min, salary_max = float(salary_min), float(salary_max)
            if (not (Config.SALARY_MIN <= salary_min <= Config.SALARY_MAX)) or \
                    (not (Config.SALARY_MIN <= salary_max <= Config.SALARY_MAX)):
                text = await Ut.get_message_text(key="wrong_salary_value_range", lang=lang)
                text = text.replace("%value_min%", str(Config.SALARY_MIN))
                text = text.replace("%value_max%", str(Config.SALARY_MAX))
                msg = await message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            if salary_min > salary_max:
                value = [salary_max, salary_min]

            else:
                value = [salary_min, salary_max]

        else:
            if (not (await Ut.is_number(value))) or (float(value) < 0):
                text = await Ut.get_message_text(key="wrong_number", lang=lang)
                msg = await message.answer(text=text)
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            value = float(value)
            if not (Config.SALARY_MIN <= value <= Config.SALARY_MAX):
                text = await Ut.get_message_text(key="wrong_salary_value_range", lang=lang)
                msg = await message.answer(
                    text=text.replace("%value_min%", str(Config.SALARY_MIN)).replace("%value_max%",
                                                                                     str(Config.SALARY_MAX)))
                return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        await cls.handler_finish(state=state, returned_value=value, additional_field="expected_salary")

    @classmethod
    async def categories_availability(cls, state: FSMContext, lang: str,
                                      data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            text_key = "company_filters_categories"

        else:
            text_key = "driver_reg_availability_categories"

        text = await Ut.get_message_text(key=text_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="categories_availability", lang=lang)
        await state.update_data(title=text, markup=markup, categories=[])

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseAvailabilityCategories)

    @classmethod
    async def categories_availability_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.expected_salary,
            next_function=call_functions["categories"], model_attr="expected_salary")
        if result:
            return

        data_from_checkboxes = await cls.processing_checkboxes(
            callback=callback, state=state, lang=lang, markup_key="categories_availability",
            error_msg_key="wrong_confirm"
        )
        if data_from_checkboxes is False:
            return

        await cls.handler_finish(
            state=state, returned_value=data_from_checkboxes, additional_field="categories_availability")

    @classmethod
    async def country_driving_licence(cls, state: FSMContext, lang: str,
                                      data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_country_driving_license"
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        else:
            msg_key = "driver_reg_country_driving_license"
            additional_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="continents", lang=lang, additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup, sc=None, sp=None)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseCountryDrivingLicense)

    @classmethod
    async def country_driving_licence_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.categories_availability,
            next_function=call_functions["country_driving_licence"], model_attr="categories_availability"
        )
        if result:
            return

        status = data["status"]
        if status == 2:
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]
            data_from_countries = await cls.processing_countries_markup(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
                additional_buttons=additional_buttons
            )
            if data_from_countries is False:
                return

        else:
            data_from_countries = await cls.processing_countries_markup(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
                without_inline_buttons=["confirm"], choose_one_country=True
            )
            if data_from_countries is False:
                return

        await cls.handler_finish(state=state, returned_value=data_from_countries,
                                 additional_field="country_driving_licence")

    @classmethod
    async def country_current_live(cls, state: FSMContext, lang: str,
                                   data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_country_current_live"
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]

        else:
            msg_key = "driver_reg_country_current_living"
            additional_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="continents", lang=lang, without_buttons=["confirm"],
                                     additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup, sc=None, sp=None)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseCountryCurrentLiving)

    @classmethod
    async def country_current_live_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.country_driving_licence,
            next_function=call_functions["country_current_live"], model_attr="country_driving_licence")
        if result:
            return

        status = data["status"]
        if status == 2:
            additional_buttons = [AdditionalButtons(index=-2, action="new", buttons={"check": None, "uncheck": None})]
            data_from_countries = await cls.processing_countries_markup(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
                additional_buttons=additional_buttons
            )
            if data_from_countries is False:
                return

        else:
            data_from_countries = await cls.processing_countries_markup(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm",
                without_inline_buttons=["confirm"], choose_one_country=True
            )
            if data_from_countries is False:
                return

        await cls.handler_finish(
            state=state, returned_value=data_from_countries, additional_field="country_current_live")

    @classmethod
    async def work_type(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            text_key = "company_filters_work_type"
            additional_buttons = [AdditionalButtons(index=-1, action="new", buttons={"confirm": None})]

        else:
            text_key = "driver_reg_work_type"
            additional_buttons = []

        text = await Ut.get_message_text(key=text_key, lang=lang)
        markup = await Ut.get_markup(
            mtype="inline", key="work_types", lang=lang, without_buttons=["skip" if status == 2 else []],
            additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseWorkType)

    @classmethod
    async def work_type_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.country_current_live,
            next_function=call_functions["work_type"], model_attr="country_current_live"
        )
        if result:
            return

        status = data["status"]
        if status == 2:
            returned_value = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm", markup_key="work_types",
                additional_buttons=[AdditionalButtons(index=-1, action="new", buttons={"confirm": None})],
                markup_without_buttons=["skip"]
            )
            if returned_value is False:
                return

        else:
            returned_value = callback.data
            if returned_value == "skip":
                returned_value = ""

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="work_type")

    @classmethod
    async def cadence(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_cadence"
            without_buttons = ["skip"]

        else:
            msg_key = "driver_reg_choose_cadence"
            without_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="cadence", lang=lang, without_buttons=without_buttons)
        await state.update_data(title=text, markup=markup, selected_cadence=[])

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.WriteCadence)

    @classmethod
    async def cadence_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.work_type,
            next_function=call_functions["cadence"], model_attr="work_type")
        if result:
            return

        status = data["status"]
        if status == 2:
            without_buttons = ["skip"]

        else:
            without_buttons = []

        data_from_checkboxes = await cls.processing_checkboxes(
            callback=callback, state=state, lang=lang, markup_key="cadence", error_msg_key="wrong_confirm",
            markup_without_buttons=without_buttons
        )
        if data_from_checkboxes is False:
            return

        await cls.handler_finish(state=state, returned_value=data_from_checkboxes, additional_field="cadence")

    @classmethod
    async def crew(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_crew"
            additional_buttons = [AdditionalButtons(index=-1, action="new", buttons={"confirm": None})]
            without_buttons = ["skip"]

        else:
            msg_key = "driver_reg_crew"
            additional_buttons = []
            without_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="crew", lang=lang, additional_buttons=additional_buttons,
                                     without_buttons=without_buttons)
        await state.update_data(title=text, markup=markup)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseCrew)

    @classmethod
    async def crew_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.cadence,
            next_function=call_functions["crew"], model_attr="cadence")
        if result:
            return

        status = data["status"]
        if status == 2:
            returned_value = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm", markup_key="work_types",
                additional_buttons=[AdditionalButtons(index=-1, action="new", buttons={"confirm": None})],
                markup_without_buttons=["skip"]
            )
            if returned_value is False:
                return

        else:
            returned_value = callback.data

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="crew")

    @classmethod
    async def driver_gender(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        data = await state.get_data()
        status = data["status"]
        hidden_status = data.get("hidden_status")

        if status == 2:
            msg_key = "company_filters_driver_gender"
            additional_buttons = [AdditionalButtons(index=-1, action="new", buttons={"confirm": None})]

        else:
            msg_key = "driver_reg_gender"
            additional_buttons = []

        text = await Ut.get_message_text(key=msg_key, lang=lang)
        markup = await Ut.get_markup(mtype="inline", key="genders", lang=lang, additional_buttons=additional_buttons)
        await state.update_data(title=text, markup=markup)

        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model, hidden_status=hidden_status)
        markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.set_state(DriverRegistration.ChooseGender)

    @classmethod
    async def driver_gender_handler(cls, callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        result = await cls.processing_back_btn(
            callback=callback, state=state, lang=lang, function_for_back=cls.crew,
            next_function=call_functions["driver_gender"], model_attr="crew")
        if result:
            return

        status = data["status"]
        if status == 2:
            returned_value = await cls.processing_checkboxes(
                callback=callback, state=state, lang=lang, error_msg_key="wrong_confirm", markup_key="genders",
                additional_buttons=[AdditionalButtons(index=-1, action="new", buttons={"confirm": None})]
            )
            if returned_value is False:
                return

        else:
            returned_value = callback.data

        await cls.handler_finish(state=state, returned_value=returned_value, additional_field="crew")

    @classmethod
    async def phone_number(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_write_contact_number", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(
            mtype="inline", lang=lang, additional_buttons=[AdditionalButtons(buttons={"back": None})])
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        text = await Ut.get_message_text(key="driver_reg_request_contact", lang=lang)
        msg = await Config.BOT.send_message(chat_id=state.key.user_id, text=text,
                                            reply_markup=await request_contact_default(lang=lang))
        await Ut.add_msg_to_delete(user_id=state.key.user_id, msg_id=msg.message_id)

        await state.set_state(DriverRegistration.WritePhoneNumber)

    @classmethod
    async def phone_number_handler(cls, message: [types.Message, types.CallbackQuery], state: FSMContext):
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        if isinstance(message, types.CallbackQuery):
            await message.answer()

            result = await cls.processing_back_btn(
                callback=message, state=state, lang=lang, next_function=call_functions["phone_number"],
                function_for_back=cls.driver_gender, model_attr="driver_gender")
            if result:
                return

        else:
            if message.contact:
                phone_number = message.contact.phone_number.replace("+", "")

            else:
                phone_number = message.text.strip().replace("+", "")
                if not phone_number.isdigit():
                    text = await Ut.get_message_text(key="wrong_phone_number_format", lang=lang)
                    msg = await message.answer(text=text)
                    return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

                if not (10 <= len(phone_number) <= 15):
                    text = await Ut.get_message_text(key="phone_number_range_limit", lang=lang)
                    msg = await message.answer(text=text)
                    return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        await cls.handler_finish(state=state, returned_value=phone_number, additional_field="phone_number")

    @classmethod
    async def name(cls, state: FSMContext, lang: str, data_model: Optional[Union[DriverForm, Driver]] = None):
        text = await Ut.get_message_text(key="driver_reg_write_name", lang=lang)
        text = await cls.model_form_correct(title=text, lang=lang, data_model=data_model)
        markup = await Ut.get_markup(
            mtype="inline", lang=lang, additional_buttons=[AdditionalButtons(buttons={"back": None})])
        await Ut.send_step_message(user_id=state.key.user_id, text=text, markup=markup)

        await state.update_data(hidden_status=None)
        await state.set_state(DriverRegistration.WriteName)

    @classmethod
    async def name_handler(cls, message: Union[types.Message, types.CallbackQuery], state: FSMContext):
        uid = message.from_user.id
        await Ut.handler_log(logger, uid)

        data = await state.get_data()
        lang = await cls.get_lang(state_data=data, user_id=uid)

        if isinstance(message, types.CallbackQuery):
            await message.answer()
            result = await cls.processing_back_btn(
                callback=message, state=state, lang=lang, function_for_back=cls.phone_number,
                next_function=call_functions["name"], model_attr="phone_number")
            if result:
                return

        name = message.text.strip()
        if not await Ut.is_valid_name(name=name):
            text = await Ut.get_message_text(key="wrong_name_format", lang=lang)
            msg = await message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        await cls.handler_finish(state=state, returned_value=name, additional_field="name")


router.callback_query.register(RegistrationSteps.birth_year_handler, DriverRegistration.ChooseBirthYear)
router.message.register(RegistrationSteps.phone_number_handler, DriverRegistration.WritePhoneNumber)
router.callback_query.register(RegistrationSteps.phone_number_handler, DriverRegistration.WritePhoneNumber),
router.callback_query.register(RegistrationSteps.messangers_handler, DriverRegistration.ChooseMessangersAvailabilities)
router.callback_query.register(RegistrationSteps.car_types_handler, DriverRegistration.ChooseCarType)
router.callback_query.register(RegistrationSteps.citizenships_handler, DriverRegistration.ChooseCitizenship)
router.callback_query.register(RegistrationSteps.basis_of_stay_handler, DriverRegistration.ChooseBasisOfStay)
router.callback_query.register(RegistrationSteps.availability_95_code_handler, DriverRegistration.Availability95Code)
router.callback_query.register(RegistrationSteps.date_start_work_handler, DriverRegistration.ChooseDateReadyToStartWork)
router.callback_query.register(RegistrationSteps.language_skills_handler, DriverRegistration.IndicateLanguageSkills)
router.callback_query.register(RegistrationSteps.job_experience_handler, DriverRegistration.IndicateJobExperience)
router.callback_query.register(RegistrationSteps.need_internship_handler, DriverRegistration.ChooseNeedInternship)
router.callback_query.register(RegistrationSteps.unsuitable_countries_handler,
                               DriverRegistration.ChooseUnsuitableCountries)
router.callback_query.register(RegistrationSteps.dangerous_goods_handler,
                               DriverRegistration.ChooseDangerousGoods)
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
router.message.register(RegistrationSteps.name_handler, DriverRegistration.WriteName)
router.callback_query.register(RegistrationSteps.name_handler, DriverRegistration.WriteName)
