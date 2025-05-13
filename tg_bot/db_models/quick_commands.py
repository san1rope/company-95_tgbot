import logging
import traceback
from datetime import datetime
from typing import Optional, Union, List

from asyncpg import UniqueViolationError
from sqlalchemy import and_, func, select

from tg_bot.db_models.db_gino import db
from tg_bot.db_models.schemas import *

logger = logging.getLogger(__name__)


class DbDriver:
    def __init__(
            self, db_id: Optional[int] = None, tg_user_id: Optional[int] = None, opens_count: Optional[int] = None,
            form_price: Optional[float] = None, name: Optional[str] = None,
            birth_year: Optional[Union[int, List[int]]] = None, phone_number: Optional[str] = None,
            car_types: Optional[List[str]] = None, citizenships: Optional[List[str]] = None,
            basis_of_stay: Optional[Union[str, List[str]]] = None, availability_95_code: Optional[str] = None,
            date_start_work: Optional[Union[datetime, List[datetime]]] = None,
            language_skills: Optional[List[str]] = None,
            job_experience: Optional[List[str]] = None, unsuitable_countries: Optional[List[str]] = None,
            dangerous_goods: Optional[List[str]] = None, expected_salary: Optional[Union[float, List[float]]] = None,
            categories_availability: Optional[List[str]] = None, country_driving_licence: Optional[str] = None,
            country_current_live: Optional[str] = None, work_type: Optional[str] = None,
            cadence: Optional[List[str]] = None, crew: Optional[str] = None, driver_gender: Optional[str] = None,
            lang: Optional[str] = None, status: Optional[int] = None, messangers: Optional[List[str]] = None,
            need_internship: Optional[str] = None, stripe_product_id: Optional[str] = None,
            stripe_price_id: Optional[str] = None
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
        self.date_start_work = date_start_work
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
        self.stripe_product_id = stripe_product_id
        self.stripe_price_id = stripe_price_id

    async def add(self) -> Union[Driver, bool]:
        try:
            target = Driver(
                tg_user_id=self.tg_user_id, opens_count=self.opens_count, name=self.name, birth_year=self.birth_year,
                phone_number=self.phone_number, car_types=self.car_types, citizenships=self.citizenships,
                basis_of_stay=self.basis_of_stay, availability_95_code=self.availability_95_code,
                date_start_work=self.date_start_work, language_skills=self.language_skills,
                job_experience=self.job_experience, need_internship=self.need_internship,
                unsuitable_countries=self.unsuitable_countries, dangerous_goods=self.dangerous_goods,
                expected_salary=self.expected_salary, categories_availability=self.categories_availability,
                country_driving_licence=self.country_driving_licence, country_current_live=self.country_current_live,
                work_type=self.work_type, cadence=self.cadence, crew=self.crew, driver_gender=self.driver_gender,
                form_price=self.form_price, lang=self.lang, status=self.status, messangers=self.messangers,
                stripe_product_id=self.stripe_product_id, stripe_price_id=self.stripe_price_id
            )
            return await target.create()

        except UniqueViolationError as ex:
            logger.error(ex)
            return False

    async def select(self, viewed_drivers_id: Optional[List[int]] = None, count_records: bool = False
                     ) -> Union[Driver, List[Driver], bool, None]:
        try:
            q = Driver.query

            if viewed_drivers_id is None:
                if self.db_id is not None:
                    return await q.where(Driver.id == self.db_id).gino.first()

                elif self.tg_user_id is not None:
                    return await q.where(Driver.tg_user_id == self.tg_user_id).gino.first()

                elif self.status is not None:
                    return await q.where(Driver.status == self.status).gino.all()

                else:
                    return await q.gino.all()

            filters = [~Driver.id.in_(viewed_drivers_id)]
            if self.status is not None:
                filters.append(Driver.status == self.status)

            if self.birth_year and self.birth_year[0] and self.birth_year[1]:
                filters.append(Driver.birth_year >= self.birth_year[0])
                filters.append(Driver.birth_year <= self.birth_year[1])

            if self.car_types:
                filters.append(Driver.car_types.op("@>")(self.car_types))

            if self.citizenships:
                filters.append(Driver.citizenships.op("@>")(self.citizenships))

            if self.basis_of_stay:
                filters.append(Driver.basis_of_stay.in_(self.basis_of_stay))

            if self.availability_95_code:
                filters.append(Driver.availability_95_code.in_(self.availability_95_code))

            if self.date_start_work and self.date_start_work[0] and self.date_start_work[1]:
                filters.append(Driver.date_start_work >= self.date_start_work[0])
                filters.append(Driver.date_start_work <= self.date_start_work[1])

            if self.language_skills:
                filters.append(Driver.language_skills.op("@>")(self.language_skills))

            if self.job_experience:
                filters.append(Driver.job_experience.op("@>")(self.job_experience))

            if self.need_internship:
                filters.append(Driver.need_internship.in_(self.need_internship))

            if self.unsuitable_countries:
                filters.append(Driver.unsuitable_countries.op("@>")(self.unsuitable_countries))

            if self.expected_salary and self.expected_salary[0] and self.expected_salary[1]:
                filters.append(Driver.expected_salary >= self.expected_salary[0])
                filters.append(Driver.expected_salary <= self.expected_salary[1])

            if self.categories_availability:
                filters.append(Driver.categories_availability.op("@>")(self.categories_availability))

            if self.country_driving_licence:
                filters.append(Driver.country_driving_licence.in_(self.country_driving_licence))

            if self.country_current_live:
                filters.append(Driver.country_current_live.in_(self.country_current_live))

            if self.work_type:
                filters.append(Driver.work_type.in_(self.work_type))

            if self.cadence:
                filters.append(Driver.cadence.op("@>")(self.cadence))

            if self.dangerous_goods:
                filters.append(Driver.dangerous_goods.op("@>")(self.dangerous_goods))

            if self.crew:
                filters.append(Driver.crew.in_(self.crew))

            if self.driver_gender:
                filters.append(Driver.driver_gender.in_(self.driver_gender))

            if filters:
                q = q.where(and_(*filters))

            if count_records:
                count_query = select([func.count()]).select_from(q.alias('subq'))
                return await db.scalar(count_query)

            else:
                return await q.gino.first()

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
            paid_subscription: Optional[int] = None, lang: Optional[str] = None,
            birth_year_left_edge: Optional[int] = None, birth_year_right_edge: Optional[int] = None,
            car_types: Optional[List[str]] = None, citizenships: Optional[List[str]] = None,
            basis_of_stay: Optional[List[str]] = None, availability_95_code: Optional[List[str]] = None,
            date_start_work_left_edge: Optional[datetime] = None, date_start_work_right_edge: Optional[datetime] = None,
            language_skills: Optional[List[str]] = None, job_experience: Optional[List[str]] = None,
            need_internship: Optional[List[str]] = None, unsuitable_countries: Optional[List[str]] = None,
            expected_salary_left_edge: Optional[float] = None, expected_salary_right_edge: Optional[float] = None,
            categories_availability: Optional[List[str]] = None, dangerous_goods: Optional[List[str]] = None,
            country_driving_licence: Optional[List[str]] = None, work_type: Optional[List[str]] = None,
            country_current_live: Optional[List[str]] = None, cadence: Optional[List[str]] = None,
            crew: Optional[List[str]] = None, driver_gender: Optional[List[str]] = None,
            viewed_drivers: Optional[List[int]] = [], saved_drivers: Optional[List[int]] = [],
            stripe_customer_id: Optional[str] = None, open_drivers: Optional[List[int]] = [],
            stripe_subscribe_product_id: Optional[str] = None, stripe_subscribe_price_id: Optional[str] = None
    ):
        self.db_id = db_id
        self.tg_user_id = tg_user_id
        self.lang = lang
        self.paid_subscription = paid_subscription
        self.viewed_drivers = viewed_drivers
        self.birth_year_left_edge = birth_year_left_edge
        self.birth_year_right_edge = birth_year_right_edge
        self.car_types = car_types
        self.citizenships = citizenships
        self.basis_of_stay = basis_of_stay
        self.availability_95_code = availability_95_code
        self.date_start_work_left_edge = date_start_work_left_edge
        self.date_start_work_right_edge = date_start_work_right_edge
        self.language_skills = language_skills
        self.job_experience = job_experience
        self.need_internship = need_internship
        self.unsuitable_countries = unsuitable_countries
        self.expected_salary_left_edge = expected_salary_left_edge
        self.expected_salary_right_edge = expected_salary_right_edge
        self.categories_availability = categories_availability
        self.country_driving_licence = country_driving_licence
        self.country_current_live = country_current_live
        self.work_type = work_type
        self.cadence = cadence
        self.dangerous_goods = dangerous_goods
        self.crew = crew
        self.driver_gender = driver_gender
        self.saved_drivers = saved_drivers
        self.stripe_customer_id = stripe_customer_id
        self.open_drivers = open_drivers
        self.stripe_subscribe_product_id = stripe_subscribe_product_id
        self.stripe_subscribe_price_id = stripe_subscribe_price_id

    async def add(self) -> Union[Driver, bool]:
        try:
            target = Company(
                tg_user_id=self.tg_user_id, paid_subscription=self.paid_subscription, lang=self.lang,
                birth_year_left_edge=self.birth_year_left_edge, birth_year_right_edge=self.birth_year_right_edge,
                car_types=self.car_types, citizenships=self.citizenships, driver_gender=self.driver_gender,
                basis_of_stay=self.basis_of_stay, availability_95_code=self.availability_95_code,
                date_start_work_left_edge=self.date_start_work_left_edge, work_type=self.work_type,
                date_start_work_right_edge=self.date_start_work_right_edge, language_skills=self.language_skills,
                job_experience=self.job_experience, need_internship=self.need_internship,
                unsuitable_countries=self.unsuitable_countries, dangerous_goods=self.dangerous_goods,
                expected_salary_left_edge=self.expected_salary_left_edge,
                expected_salary_right_edge=self.expected_salary_right_edge,
                categories_availability=self.categories_availability, cadence=self.cadence,
                country_driving_licence=self.country_driving_licence, crew=self.crew,
                country_current_live=self.country_current_live, viewed_drivers=self.viewed_drivers,
                saved_drivers=self.saved_drivers, stripe_customer_id=self.stripe_customer_id,
                open_drivers=self.open_drivers, stripe_subscribe_product_id=self.stripe_subscribe_product_id,
                stripe_subscribe_price_id=self.stripe_subscribe_price_id
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


class DbPayment:
    def __init__(
            self, db_id: Optional[int] = None, creator_id: Optional[int] = None, amount: Optional[float] = None,
            p_type: Optional[str] = None, driver_id: Optional[str] = None, status: Optional[int] = None,
            invoice_url: Optional[str] = None, stripe_invoice_id: Optional[str] = None, system: Optional[str] = None,
            msg_to_delete: Optional[int] = None
    ):
        self.db_id = db_id
        self.status = status
        self.creator_id = creator_id
        self.amount = amount
        self.p_type = p_type
        self.driver_id = driver_id
        self.invoice_url = invoice_url
        self.stripe_invoice_id = stripe_invoice_id
        self.system = system
        self.msg_to_delete = msg_to_delete

    async def add(self) -> Union[Payment, bool]:
        try:
            target = Payment(
                creator_id=self.creator_id, amount=self.amount, type=self.p_type, driver_id=self.driver_id,
                status=self.status, invoice_url=self.invoice_url, stripe_invoice_id=self.stripe_invoice_id,
                system=self.system, msg_to_delete=self.msg_to_delete
            )
            return await target.create()

        except UniqueViolationError:
            logger.error(traceback.format_exc())
            return False

    async def select(self, status_with_selected_system: Optional[int] = None):
        try:
            q = Payment.query
            if self.db_id:
                return await q.where(Payment.id == self.db_id).gino.first()

            elif self.system:
                params = [Payment.system == self.system]
                if status_with_selected_system is not None:
                    params.append(Payment.status == self.status)

                return await q.where(and_(*params)).gino.all()

            elif self.creator_id and (self.status is None):
                return await q.where(Payment.creator_id == self.creator_id).gino.all()

            elif self.creator_id and (self.status is not None):
                return await q.where(
                    and_(Payment.creator_id == self.creator_id, Payment.status == self.status)).gino.first()

            elif self.status is not None:
                return await q.where(Payment.status).gino.all()

            elif self.p_type:
                return await q.where(Payment.type == self.p_type).gino.all()

            elif self.driver_id:
                return await q.where(Payment.driver_id == self.driver_id).gino.all()

            else:
                return await q.gino.all()

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
