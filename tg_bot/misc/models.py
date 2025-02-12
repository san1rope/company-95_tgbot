from datetime import datetime
from typing import Optional, List, Dict, Union, Any

from aiogram.utils.markdown import hcode
from pydantic import BaseModel

from config import Config
from tg_bot.db_models.schemas import Driver
from tg_bot.misc.utils import localization, corrections


class DriverForm(BaseModel):
    tg_user_id: Optional[int] = None
    name: Optional[str] = None
    birth_year: Optional[int] = None
    phone_number: Optional[str] = None
    car_types: Optional[List[str]] = None
    citizenships: Optional[List[str]] = None
    basis_of_stay: Optional[str] = None
    availability_95_code: Optional[str] = None
    date_stark_work: Optional[datetime] = None
    language_skills: Optional[List[str]] = None
    job_experience: Optional[List[str]] = None
    need_internship: Optional[str] = None
    unsuitable_countries: Optional[List[str]] = None
    documents_availability: Optional[List[str]] = None
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

    async def form_completion(self, title: str, lang: str, db_model: Optional[Driver] = None) -> str:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        lang_inline_markups = lang_data["markups"]["inline"]
        fcd = lang_data['misc']['form_completion_driver']

        model = db_model if db_model else self

        text = [f"{title}\n"]
        if not (model.name is None):
            text.append(f"<b>{hcode(fcd['name'])} {model.name}</b>")

        if not (model.birth_year is None):
            text.append(f"<b>{hcode(fcd['birth_year'])} {model.birth_year}</b>")

        if not (model.phone_number is None):
            text.append(f"<b>{hcode(fcd['phone_number'])} {model.phone_number}</b>")

        if not (model.car_types is None):
            model.car_types = model.car_types.split(',') if isinstance(model.car_types, str) else model.car_types
            localized_text = await self.codes_to_text_checkboxes(
                input_localized_text=lang_inline_markups["car_types"], codes=model.car_types)
            text.append(f"<b>{hcode(fcd['car_types'])} {', '.join(localized_text)}</b>")

        if not (model.citizenships is None):
            model.citizenships = model.citizenships.split(',') if isinstance(model.citizenships,
                                                                             str) else model.citizenships
            localized_text = await self.codes_to_text_checkboxes_countries(
                lang_inline_markups=lang_inline_markups, codes=model.citizenships)
            text.append(f"<b>{hcode(fcd['citizenships'])} {', '.join(localized_text)}</b>")

        if not (model.basis_of_stay is None):
            localized_value = await self.code_to_text(
                input_localized_text=lang_inline_markups["basis_of_stay"], code=model.basis_of_stay)
            text.append(f"<b>{hcode(fcd['basis_of_stay'])} {localized_value}</b>")

        if not (model.availability_95_code is None):
            localized_value = await self.code_to_text(
                input_localized_text=lang_inline_markups["availability_95_code"], code=model.availability_95_code)
            text.append(f"<b>{hcode(fcd['availability_95_code'])} {localized_value}</b>")

        if not (model.date_stark_work is None):
            text.append(f"<b>{hcode(fcd['date_stark_work'])} {model.date_stark_work.strftime('%d.%m.%Y')}</b>")

        if not (model.language_skills is None):
            model.language_skills = model.language_skills.split(',') if isinstance(model.language_skills,
                                                                                   str) else model.language_skills
            localized_text = await self.codes_to_text_selectors(
                input_localized_text=lang_inline_markups["language_skills"], codes=model.language_skills)
            text.append(f"<b>{hcode(fcd['language_skills'])}</b>")
            text.extend(localized_text)

        if not (model.job_experience is None):
            model.job_experience = model.job_experience.split(',') if isinstance(model.job_experience,
                                                                                 str) else model.job_experience
            localized_text = await self.codes_to_text_selectors(
                input_localized_text=lang_inline_markups["job_experience"], codes=model.job_experience)
            text.append(f"<b>{hcode(fcd['job_experience'])}</b>")
            text.extend(localized_text)

        if not (model.need_internship is None):
            localized_value = await self.code_to_text(
                input_localized_text=lang_inline_markups["need_internship"], code=model.need_internship)
            text.append(f"<b>{hcode(fcd['need_internship'])} {localized_value}</b>")

        if not (model.unsuitable_countries is None):
            model.unsuitable_countries = model.unsuitable_countries.split(',') if isinstance(
                model.unsuitable_countries,str) else model.unsuitable_countries
            localized_text = await self.codes_to_text_checkboxes_countries(
                lang_inline_markups=lang_inline_markups, codes=model.unsuitable_countries)
            text.append(f"<b>{hcode(fcd['unsuitable_countries'])} {', '.join(localized_text)}</b>")

        if not (model.documents_availability is None):
            model.documents_availability = model.documents_availability.split(',') if isinstance(
                model.documents_availability, str) else model.documents_availability
            localized_text = await self.codes_to_text_checkboxes(
                input_localized_text=lang_inline_markups["documents_availability"], codes=model.documents_availability)
            text.append(f"<b>{hcode(fcd['documents_availability'])} {', '.join(localized_text)}</b>")

        if not (model.expected_salary is None):
            text.append(f"<b>{hcode(fcd['expected_salary'])} €{model.expected_salary}</b>")

        if not (model.categories_availability is None):
            localized_text = await self.codes_to_text_checkboxes(
                input_localized_text=lang_inline_markups["categories_availability"],
                codes=model.categories_availability
            )
            text.append(f"<b>{hcode(fcd['categories_availability'])} {', '.join(localized_text)}</b>")

        if not (model.country_driving_licence is None):
            localized_value = await self.code_to_text_country(
                lang_inline_markups=lang_inline_markups, code=model.country_driving_licence)
            text.append(f"<b>{hcode(fcd['country_driving_licence'])} {localized_value}</b>")

        if not (model.country_current_live is None):
            localized_value = await self.code_to_text_country(
                lang_inline_markups=lang_inline_markups, code=model.country_current_live)
            text.append(f"<b>{hcode(fcd['country_current_live'])} {localized_value}</b>")

        if not (model.work_type is None):
            localized_value = await self.code_to_text(
                input_localized_text=lang_inline_markups["work_types"], code=model.work_type)
            text.append(f"<b>{hcode(fcd['work_type'])} {localized_value}</b>")

        if not (model.cadence is None):
            model.cadence = model.cadence.split(',') if isinstance(model.cadence, str) else model.cadence
            localized_text = await self.codes_to_text_checkboxes(
                input_localized_text=lang_inline_markups["cadence"], codes=model.cadence)
            text.append(f"<b>{hcode(fcd['cadence'])} {', '.join(localized_text)}</b>")

        if not (model.crew is None):
            localized_value = await self.code_to_text(input_localized_text=lang_inline_markups["crew"], code=model.crew)
            text.append(f"<b>{hcode(fcd['crew'])} {localized_value}</b>")

        if not (model.driver_gender is None):
            localized_value = await self.code_to_text(
                input_localized_text=lang_inline_markups["genders"], code=model.driver_gender)
            text.append(f"<b>{hcode(fcd['driver_gender'])} {localized_value}</b>")

        return "\n".join(text)

    async def calculate_form_data(self) -> float:
        form_price = Config.BASE_FORM_PRICE

        if not (self.car_types is None):
            curr_cor = corrections["car_types"]
            for sel_val in self.car_types:
                form_price += curr_cor[sel_val] if sel_val in curr_cor else 0

        if not (self.basis_of_stay is None):
            curr_cor = corrections["basis_of_stay"]
            form_price += curr_cor[self.basis_of_stay] if self.basis_of_stay in curr_cor else 0

        if not (self.availability_95_code is None):
            curr_cor = corrections["availability_95_code"]
            form_price += curr_cor[self.availability_95_code] if self.availability_95_code in curr_cor else 0

        if not (self.language_skills is None):
            curr_cor = corrections["language_skills"]
            for sel_val in self.language_skills:
                for curr_el, curr_value in curr_cor.items():
                    if curr_el == sel_val:
                        form_price += curr_value

                    elif "%least_one%" in curr_el:
                        row, col = sel_val.split(":")
                        if curr_el.split(':')[1] == col:
                            form_price += curr_value

        if not (self.job_experience is None):
            curr_cor = corrections["job_experience"]
            for sel_val in self.job_experience:
                for curr_el, curr_value in curr_cor.items():
                    if curr_el == sel_val:
                        form_price += curr_value

                    elif "%least_one%" in curr_el:
                        row, col = sel_val.split(":")
                        if curr_el.split(':')[1] == col:
                            form_price += curr_value

        if not (self.need_internship is None):
            curr_cor = corrections["need_internship"]
            form_price += curr_cor[self.need_internship] if self.need_internship in curr_cor else 0

        if not (self.unsuitable_countries is None):
            curr_cor = corrections["unsuitable_countries"]
            for curr_el, curr_value in curr_cor.items():
                if (curr_el == "%unselected%") and (not self.unsuitable_countries):
                    form_price += curr_value

        if not (self.documents_availability is None):
            curr_cor = corrections["documents_availability"]
            for sel_val in self.documents_availability:
                form_price += curr_cor[sel_val] if sel_val in curr_cor else 0

        if not (self.expected_salary is None):
            curr_cor = corrections["expected_salary"]
            for corr_el, corr_value in curr_cor.items():
                min_value, max_value = list(map(float, corr_el.split("-")))
                form_price += corr_value if min_value <= self.expected_salary <= max_value else 0

        if not (self.country_current_live is None):
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

        if not (self.work_type is None):
            curr_cor = corrections["work_types"]
            form_price += curr_cor[self.work_type] if self.work_type in curr_cor else 0

        if not (self.cadence is None):
            curr_cor = corrections["cadence"]
            for sel_val in self.cadence:
                form_price += curr_cor[sel_val] if sel_val in curr_cor else 0

        return form_price

    async def form_data_to_dict(self) -> Dict[str, Any]:
        out_data = {}

        if not (self.name is None):
            out_data["name"] = self.name

        if not (self.birth_year is None):
            out_data["birth_year"] = self.birth_year

        if not (self.phone_number is None):
            out_data["phone_number"] = self.phone_number

        if not (self.car_types is None):
            out_data["car_types"] = ",".join(self.car_types)

        if not (self.citizenships is None):
            out_data["citizenships"] = ",".join(self.citizenships)

        if not (self.basis_of_stay is None):
            out_data["basis_of_stay"] = self.basis_of_stay

        if not (self.availability_95_code is None):
            out_data["availability_95_code"] = self.availability_95_code

        if not (self.date_stark_work is None):
            out_data["date_stark_work"] = self.date_stark_work

        if not (self.language_skills is None):
            out_data["language_skills"] = ",".join(self.language_skills)

        if not (self.job_experience is None):
            out_data["job_experience"] = ",".join(self.job_experience)

        if not (self.need_internship is None):
            out_data["need_internship"] = self.need_internship

        if not (self.unsuitable_countries is None):
            out_data["unsuitable_countries"] = ",".join(self.unsuitable_countries)

        if not (self.documents_availability is None):
            out_data["documents_availability"] = ",".join(self.documents_availability)

        if not (self.expected_salary is None):
            out_data["expected_salary"] = self.expected_salary

        if not (self.categories_availability is None):
            out_data["categories_availability"] = ",".join(self.categories_availability)

        if not (self.country_driving_licence is None):
            out_data["country_driving_licence"] = self.country_driving_licence

        if not (self.country_current_live is None):
            out_data["country_current_live"] = self.country_current_live

        if not (self.work_type is None):
            out_data["work_type"] = self.work_type

        if not (self.cadence is None):
            out_data["cadence"] = ",".join(self.cadence)

        if not (self.crew is None):
            out_data["crew"] = self.crew

        if not (self.driver_gender is None):
            out_data["driver_gender"] = self.driver_gender

        return out_data
