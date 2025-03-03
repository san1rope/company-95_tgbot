import logging
import traceback
from datetime import datetime
from typing import Optional, Union, List

from asyncpg import UniqueViolationError

from tg_bot.db_models.schemas import *

logger = logging.getLogger(__name__)


class DbDriver:
    def __init__(
            self, db_id: Optional[int] = None, tg_user_id: Optional[int] = None, opens_count: Optional[int] = None,
            form_price: Optional[float] = None, name: Optional[str] = None, birth_year: Optional[int] = None,
            phone_number: Optional[str] = None, car_types: Optional[str] = None, citizenships: Optional[str] = None,
            basis_of_stay: Optional[str] = None, availability_95_code: Optional[str] = None,
            date_stark_work: Optional[datetime] = None, language_skills: Optional[str] = None,
            job_experience: Optional[str] = None, need_internship: Optional[str] = None,
            unsuitable_countries: Optional[str] = None, dangerous_goods: Optional[str] = None,
            expected_salary: Optional[float] = None, categories_availability: Optional[str] = None,
            country_driving_licence: Optional[str] = None, country_current_live: Optional[str] = None,
            work_type: Optional[str] = None, cadence: Optional[str] = None, crew: Optional[str] = None,
            driver_gender: Optional[str] = None, lang: Optional[str] = None, status: Optional[int] = None,
            messangers: Optional[str] = None
    ):
        self.db_id = db_id
        self.tg_user_id = tg_user_id
        self.lang = lang
        self.opens_count = opens_count
        self.form_price = form_price
        self.name = name
        self.birth_year = birth_year
        self.phone_number = phone_number
        self.messangers = messangers
        self.car_types = car_types
        self.citizenships = citizenships
        self.basis_of_stay = basis_of_stay
        self.availability_95_code = availability_95_code
        self.date_stark_work = date_stark_work
        self.language_skills = language_skills
        self.job_experience = job_experience
        self.need_internship = need_internship
        self.unsuitable_countries = unsuitable_countries
        self.dangerous_goods = dangerous_goods
        self.expected_salary = expected_salary
        self.categories_availability = categories_availability
        self.country_driving_licence = country_driving_licence
        self.country_current_live = country_current_live
        self.work_type = work_type
        self.cadence = cadence
        self.crew = crew
        self.driver_gender = driver_gender
        self.status = status

    async def add(self) -> Union[Driver, bool]:
        try:
            target = Driver(
                tg_user_id=self.tg_user_id, opens_count=self.opens_count, name=self.name, birth_year=self.birth_year,
                phone_number=self.phone_number, car_types=self.car_types, citizenships=self.citizenships,
                basis_of_stay=self.basis_of_stay, availability_95_code=self.availability_95_code,
                date_stark_work=self.date_stark_work, language_skills=self.language_skills,
                job_experience=self.job_experience, need_internship=self.need_internship,
                unsuitable_countries=self.unsuitable_countries, dangerous_goods=self.dangerous_goods,
                expected_salary=self.expected_salary, categories_availability=self.categories_availability,
                country_driving_licence=self.country_driving_licence, country_current_live=self.country_current_live,
                work_type=self.work_type, cadence=self.cadence, crew=self.crew, driver_gender=self.driver_gender,
                form_price=self.form_price, lang=self.lang, status=self.status, messangers=self.messangers
            )
            return await target.create()

        except UniqueViolationError as ex:
            logger.error(ex)
            return False

    async def select(self) -> Union[Driver, List[Driver], bool, None]:
        try:
            q = Driver.query
            if not (self.db_id is None):
                return await q.where(Driver.id == self.db_id).gino.first()

            elif not (self.tg_user_id is None):
                return await q.where(Driver.tg_user_id == self.tg_user_id).gino.first()

            elif not (self.status is None):
                return await q.where(Driver.status == self.status).gino.all()

            else:
                return await q.gino.all()

        except Exception as ex:
            logger.error(ex)
            return False

    async def update(self, **kwargs) -> bool:
        try:
            if not kwargs:
                return False

            target = await self.select()
            return await target.update(**kwargs).apply()

        except Exception:
            logger.error(traceback.format_exc())
            return False

    async def remove(self) -> Union[bool, List[bool]]:
        try:
            target = await self.select()
            if isinstance(target, list):
                results = []
                for i in target:
                    results.append(await i.delete())

                return results

            elif isinstance(target, Driver):
                return await target.delete()

        except Exception:
            logger.error(traceback.format_exc())
            return False


class DbCompany:
    def __init__(
            self, db_id: Optional[int] = None, tg_user_id: Optional[int] = None,
            paid_subscription: Optional[int] = None, lang: Optional[str] = None, f_birth_year: Optional[int] = None,
            f_car_types: Optional[str] = None, f_citizenships: Optional[str] = None,
            f_basis_of_stay: Optional[str] = None, f_availability_95_code: Optional[str] = None,
            f_date_stark_work: Optional[str] = None, f_language_skills: Optional[str] = None,
            f_job_experience: Optional[str] = None, f_need_internship: Optional[str] = None,
            f_unsuitable_countries: Optional[str] = None, f_expected_salary: Optional[str] = None,
            f_categories_availability: Optional[str] = None, f_country_driving_licence: Optional[str] = None,
            f_country_current_live: Optional[str] = None, f_work_type: Optional[str] = None,
            f_cadence: Optional[str] = None, f_crew: Optional[str] = None, f_driver_gender: Optional[str] = None,
    ):
        self.db_id = db_id
        self.tg_user_id = tg_user_id
        self.lang = lang
        self.paid_subscription = paid_subscription
        self.f_birth_year = f_birth_year
        self.f_car_types = f_car_types
        self.f_citizenships = f_citizenships
        self.f_basis_of_stay = f_basis_of_stay
        self.f_availability_95_code = f_availability_95_code
        self.f_date_stark_work = f_date_stark_work
        self.f_language_skills = f_language_skills
        self.f_job_experience = f_job_experience
        self.f_need_internship = f_need_internship
        self.f_unsuitable_countries = f_unsuitable_countries
        self.f_expected_salary = f_expected_salary
        self.f_categories_availability = f_categories_availability
        self.f_country_driving_licence = f_country_driving_licence
        self.f_country_current_live = f_country_current_live
        self.f_work_type = f_work_type
        self.f_cadence = f_cadence
        self.f_crew = f_crew
        self.f_driver_gender = f_driver_gender

    async def add(self) -> Union[Driver, bool]:
        try:
            target = Company(
                tg_user_id=self.tg_user_id, paid_subscription=self.paid_subscription, lang=self.lang,
                f_birth_year=self.f_birth_year, f_car_types=self.f_car_types, f_citizenships=self.f_citizenships,
                f_basis_of_stay=self.f_basis_of_stay, f_availability_95_code=self.f_availability_95_code,
                f_date_stark_work=self.f_date_stark_work, f_language_skills=self.f_language_skills,
                f_job_experience=self.f_job_experience, f_need_internship=self.f_need_internship,
                f_unsuitable_countries=self.f_unsuitable_countries, f_expected_salary=self.f_expected_salary,
                f_categories_availability=self.f_categories_availability,
                f_country_driving_licence=self.f_country_driving_licence,
                f_country_current_live=self.f_country_current_live, f_work_type=self.f_work_type,
                f_cadence=self.f_cadence, f_crew=self.f_crew, f_driver_gender=self.f_driver_gender
            )
            return await target.create()

        except UniqueViolationError as ex:
            logger.error(ex)
            return False

    async def select(self) -> Union[Company, List[Company], bool, None]:
        try:
            if self.db_id:
                return await Company.query.where(Company.id == self.db_id).gino.first()

            elif self.tg_user_id:
                return await Company.query.where(Company.tg_user_id == self.tg_user_id).gino.first()

            else:
                return await Company.query.gino.all()

        except Exception:
            logger.error(traceback.format_exc())
            return False

    async def update(self, **kwargs) -> bool:
        try:
            if not kwargs:
                return False

            target = await self.select()
            return await target.update(**kwargs).apply()

        except Exception:
            logger.error(traceback.format_exc())
            return False

    async def remove(self) -> Union[bool, List[bool]]:
        try:
            target = await self.select()
            if isinstance(target, list):
                results = []
                for i in target:
                    results.append(await i.delete())

                return results

            elif isinstance(target, Company):
                return await target.delete()

        except Exception:
            logger.error(traceback.format_exc())
            return False
