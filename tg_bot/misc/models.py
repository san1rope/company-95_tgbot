from datetime import datetime
from typing import Optional, List, Dict, Union, Any

from aiogram.utils.markdown import hcode
from pydantic import BaseModel

from config import Config
from tg_bot.db_models.schemas import Driver, Company
from tg_bot.misc.utils import localization, corrections


class DriverForm(BaseModel):
    name: Optional[str] = None
    birth_year: Optional[int] = None
    phone_number: Optional[str] = None
    messangers: Optional[List[str]] = None
    car_types: Optional[List[str]] = None
    citizenships: Optional[List[str]] = None
    basis_of_stay: Optional[str] = None
    availability_95_code: Optional[str] = None
    date_stark_work: Optional[datetime] = None
    language_skills: Optional[List[str]] = None
    job_experience: Optional[List[str]] = None
    need_internship: Optional[str] = None
    unsuitable_countries: Optional[List[str]] = None
    dangerous_goods: Optional[List[str]] = None
    expected_salary: Optional[float] = None
    categories_availability: Optional[List[str]] = None
    country_driving_licence: Optional[str] = None
    country_current_live: Optional[str] = None
    work_type: Optional[str] = None
    cadence: Optional[List[str]] = None
    crew: Optional[str] = None
    driver_gender: Optional[str] = None

    @staticmethod
    async def code_to_text(input_localized_text: List[Dict[str, str]], code: str) -> Union[str, None]:
        for row in input_localized_text:
            for btn_text, callback_data in row.items():
                if callback_data == code:
                    return btn_text

    @staticmethod
    async def codes_to_text_checkboxes(input_localized_text: List[Dict[str, str]], codes: List[str]) -> List[str]:
        localized_text = []
        for buttons_data in input_localized_text:
            for btn_text, btn_cd in buttons_data.items():
                if btn_cd in codes:
                    localized_text.append(btn_text)

        return localized_text

    @classmethod
    async def codes_to_text_checkboxes_countries(cls, lang_inline_markups: Dict, codes: List[str]) -> List[str]:
        localized_text = []
        for markup_key in lang_inline_markups.keys():
            if "countries_" not in markup_key:
                continue

            localized_text.extend(
                await cls.codes_to_text_checkboxes(input_localized_text=lang_inline_markups[markup_key], codes=codes))

        return localized_text

    @classmethod
    async def code_to_text_country(cls, lang_inline_markups: Dict, code: str) -> Union[str, None]:
        for markup_key in lang_inline_markups.keys():
            if "countries_" not in markup_key:
                continue

            localized_value = await cls.code_to_text(input_localized_text=lang_inline_markups[markup_key], code=code)
            if localized_value:
                return localized_value

    @staticmethod
    async def codes_to_text_selectors(input_localized_text: List[Dict[str, str]], codes: List[str]) -> List[str]:
        localized_text = []

        rows, cols = {}, {}
        for row in input_localized_text:
            for btn_text, btn_cd in row.items():
                if "row:" in btn_cd:
                    rows[btn_cd.replace("row:", "")] = btn_text

                elif "col:" in btn_cd:
                    cols[btn_cd.replace("col:", "")] = btn_text

        for el in codes:
            row, col = el.split(":")
            localized_text.append(f"<b>{rows[row]}: {cols[col]}</b>")

        return localized_text

    async def form_completion(
            self, title: str, lang: str, db_model: Optional[Driver] = None, for_company: bool = False,
            hidden: bool = False
    ) -> str:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        lang_inline_markups = lang_data["markups"]["inline"]
        fcd = lang_data['misc']['form_completion_driver']

        model = db_model if db_model else self
        model_company = isinstance(model, Company)

        text = [f"{title}\n"]
        if (not model_company) and (not for_company) and (model.name is not None):
            text.append(f"<b>{hcode(fcd['name'])} {model.name}</b>")

        try:
            if (model.birth_year is not None) or (model.birth_year_left_edge is not None):
                if model_company:
                    value = f"{model.birth_year_left_edge}-{model.birth_year_right_edge}"

                else:
                    value = model.birth_year

                text.append(f"<b>{hcode(fcd['birth_year'])} {value}</b>")

        except AttributeError:
            pass

        if (not model_company) and (not for_company) and (model.phone_number is not None):
            text.append(f"<b>{hcode(fcd['phone_number'])} {model.phone_number}</b>")

        if (not model_company) and (model.messangers is not None):
            localized_text = await self.codes_to_text_checkboxes(
                input_localized_text=lang_inline_markups["messangers_availabilities"], codes=model.messangers)
            text.append(f"<b>{hcode(fcd['messangers'])} {', '.join(localized_text)}</b>")

        if model.car_types is not None:
            localized_text = await self.codes_to_text_checkboxes(
                input_localized_text=lang_inline_markups["car_types"], codes=model.car_types)
            text.append(f"<b>{hcode(fcd['car_types'])} {', '.join(localized_text)}</b>")

        if not hidden:
            if model.citizenships is not None:
                localized_text = await self.codes_to_text_checkboxes_countries(
                    lang_inline_markups=lang_inline_markups, codes=model.citizenships)
                text.append(f"<b>{hcode(fcd['citizenships'])} {', '.join(localized_text)}</b>")

            if model.basis_of_stay is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes(
                        input_localized_text=lang_inline_markups["basis_of_stay"], codes=model.basis_of_stay)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text(
                        input_localized_text=lang_inline_markups["basis_of_stay"], code=model.basis_of_stay)

                text.append(f"<b>{hcode(fcd['basis_of_stay'])} {localized_text}</b>")

            if model.availability_95_code is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes(
                        input_localized_text=lang_inline_markups["availability_95_code"],
                        codes=model.availability_95_code
                    )
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text(
                        input_localized_text=lang_inline_markups["availability_95_code"],
                        code=model.availability_95_code)

                text.append(f"<b>{hcode(fcd['availability_95_code'])} {localized_text}</b>")

            try:
                if (model.date_stark_work_left_edge is not None) or (model.date_stark_work is not None):
                    if model_company:
                        value = model.date_stark_work_left_edge.strftime(
                            "%d.%m.%Y") + " - " + model.date_stark_work_right_edge.strftime("%d.%m.%Y")

                    else:
                        value = model.date_stark_work.strftime('%d.%m.%Y')

                    text.append(f"<b>{hcode(fcd['date_stark_work'])} {value}</b>")

            except AttributeError:
                pass

            if model.language_skills is not None:
                localized_text = await self.codes_to_text_selectors(
                    input_localized_text=lang_inline_markups["language_skills"], codes=model.language_skills)
                text.append(f"<b>{hcode(fcd['language_skills'])}</b>")
                text.extend(localized_text)

            if model.job_experience is not None:
                localized_text = await self.codes_to_text_selectors(
                    input_localized_text=lang_inline_markups["job_experience"], codes=model.job_experience)
                text.append(f"<b>{hcode(fcd['job_experience'])}</b>")
                text.extend(localized_text)

            if model.need_internship is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes(
                        input_localized_text=lang_inline_markups["need_internship"], codes=model.need_internship)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text(
                        input_localized_text=lang_inline_markups["need_internship"], code=model.need_internship)

                text.append(f"<b>{hcode(fcd['need_internship'])} {localized_text}</b>")

            if model.unsuitable_countries is not None:
                localized_text = await self.codes_to_text_checkboxes_countries(
                    lang_inline_markups=lang_inline_markups, codes=model.unsuitable_countries)
                text.append(f"<b>{hcode(fcd['unsuitable_countries'])} {', '.join(localized_text)}</b>")

            if model.dangerous_goods is not None:
                localized_text = await self.codes_to_text_checkboxes(
                    input_localized_text=lang_inline_markups["dangerous_goods"], codes=model.dangerous_goods)
                text.append(f"<b>{hcode(fcd['dangerous_goods'])} {', '.join(localized_text)}</b>")

            try:
                if (model.expected_salary_left_edge is not None) or (model.expected_salary is not None):
                    if model_company:
                        value = f"€{model.expected_salary_left_edge} - €{model.expected_salary_right_edge}"

                    else:
                        value = f"€{model.expected_salary}"

                    text.append(f"<b>{hcode(fcd['expected_salary'])} {value}</b>")

            except AttributeError:
                pass

            if model.categories_availability is not None:
                localized_text = await self.codes_to_text_checkboxes(
                    input_localized_text=lang_inline_markups["categories_availability"],
                    codes=model.categories_availability
                )
                text.append(f"<b>{hcode(fcd['categories_availability'])} {', '.join(localized_text)}</b>")

            if model.country_driving_licence is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes_countries(
                        lang_inline_markups=lang_inline_markups, codes=model.country_driving_licence)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text_country(
                        lang_inline_markups=lang_inline_markups, code=model.country_driving_licence)

                text.append(f"<b>{hcode(fcd['country_driving_licence'])} {localized_text}</b>")

            if model.country_current_live is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes_countries(
                        lang_inline_markups=lang_inline_markups, codes=model.country_current_live)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text_country(
                        lang_inline_markups=lang_inline_markups, code=model.country_current_live)

                text.append(f"<b>{hcode(fcd['country_current_live'])} {localized_text}</b>")

            if model.work_type is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes(
                        input_localized_text=lang_inline_markups["work_types"], codes=model.work_type)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text(
                        input_localized_text=lang_inline_markups["work_types"], code=model.work_type)

                text.append(f"<b>{hcode(fcd['work_type'])} {localized_text}</b>")

            if model.cadence is not None:
                localized_text = await self.codes_to_text_checkboxes(
                    input_localized_text=lang_inline_markups["cadence"], codes=model.cadence)
                text.append(f"<b>{hcode(fcd['cadence'])} {', '.join(localized_text)}</b>")

            if model.crew is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes(
                        input_localized_text=lang_inline_markups["crew"], codes=model.crew)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text(
                        input_localized_text=lang_inline_markups["crew"], code=model.crew)

                text.append(f"<b>{hcode(fcd['crew'])} {localized_text}</b>")

            if model.driver_gender is not None:
                if model_company:
                    localized_text = await self.codes_to_text_checkboxes(
                        input_localized_text=lang_inline_markups["genders"], codes=model.driver_gender)
                    localized_text = ", ".join(localized_text)

                else:
                    localized_text = await self.code_to_text(
                        input_localized_text=lang_inline_markups["genders"], code=model.driver_gender)

                text.append(f"<b>{hcode(fcd['driver_gender'])} {localized_text}</b>")

            if len(text) > 6:
                text.append("\n<i>Нажмите `Скрыть анкету`, что-бы скрыть часть анкеты</i>")

        else:
            text.append("\n<i>Нажмите `Раскрыть анкету`, что-бы посмотреть всю анкету</i>")

        return "\n".join(text)

    async def calculate_form_data(self, db_model: Optional[Driver] = None) -> float:
        form_price = Config.BASE_FORM_PRICE

        model = db_model if db_model else self

        if not (model.car_types is None):
            curr_cor = corrections["car_types"]
            for sel_val in model.car_types:
                form_price += curr_cor[sel_val] if sel_val in curr_cor else 0

        if not (model.basis_of_stay is None):
            curr_cor = corrections["basis_of_stay"]
            form_price += curr_cor[model.basis_of_stay] if model.basis_of_stay in curr_cor else 0

        if not (model.availability_95_code is None):
            curr_cor = corrections["availability_95_code"]
            form_price += curr_cor[model.availability_95_code] if model.availability_95_code in curr_cor else 0

        if not (model.language_skills is None):
            curr_cor = corrections["language_skills"]
            for sel_val in model.language_skills:
                for curr_el, curr_value in curr_cor.items():
                    if curr_el == sel_val:
                        form_price += curr_value

                    elif "%least_one%" in curr_el:
                        row, col = sel_val.split(":")
                        if curr_el.split(':')[1] == col:
                            form_price += curr_value

        if not (model.job_experience is None):
            curr_cor = corrections["job_experience"]
            for sel_val in model.job_experience:
                for curr_el, curr_value in curr_cor.items():
                    if curr_el == sel_val:
                        form_price += curr_value

                    elif "%least_one%" in curr_el:
                        row, col = sel_val.split(":")
                        if curr_el.split(':')[1] == col:
                            form_price += curr_value

        if not (model.need_internship is None):
            curr_cor = corrections["need_internship"]
            form_price += curr_cor[model.need_internship] if model.need_internship in curr_cor else 0

        if not (model.unsuitable_countries is None):
            curr_cor = corrections["unsuitable_countries"]
            for curr_el, curr_value in curr_cor.items():
                if (curr_el == "%unselected%") and (not model.unsuitable_countries):
                    form_price += curr_value

        if not (model.dangerous_goods is None):
            curr_cor = corrections["dangerous_goods"]
            for sel_val in model.dangerous_goods:
                form_price += curr_cor[sel_val] if sel_val in curr_cor else 0

        if not (model.expected_salary is None):
            curr_cor = corrections["expected_salary"]
            for corr_el, corr_value in curr_cor.items():
                min_value, max_value = list(map(float, corr_el.split("-")))
                form_price += corr_value if min_value <= model.expected_salary <= max_value else 0

        if not (model.country_current_live is None):
            curr_cor = corrections["country_current_living"]
            for corr_el, corr_value in curr_cor.items():
                if "cont:" in corr_el:
                    cont = corr_el.replace("cont:", "")
                    lmi = localization[Config.DEFAULT_LANG]["markups"]["inline"]
                    flag = False
                    for m_name in lmi:
                        if f"countries_{cont}_" in m_name:
                            for buttons_data in lmi[m_name]:
                                for btn_cd in buttons_data.values():
                                    if btn_cd == self.country_current_live:
                                        form_price += corr_value
                                        flag = True
                                        break

                                if flag:
                                    break

                            if flag:
                                break

        if not (model.work_type is None):
            curr_cor = corrections["work_types"]
            form_price += curr_cor[model.work_type] if model.work_type in curr_cor else 0

        if not (model.cadence is None):
            curr_cor = corrections["cadence"]
            for sel_val in model.cadence:
                form_price += curr_cor[sel_val] if sel_val in curr_cor else 0

        return form_price
