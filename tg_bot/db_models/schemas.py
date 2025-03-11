from sqlalchemy import sql, Column, BigInteger, String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import ARRAY

from tg_bot.db_models.db_gino import TimedBaseModel


class Driver(TimedBaseModel):
    __tablename__ = "drivers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_user_id = Column(BigInteger, nullable=False, primary_key=True)
    lang = Column(String, nullable=False)
    opens_count = Column(Integer, nullable=False)
    form_price = Column(Float, nullable=False)
    status = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    birth_year = Column(Integer, nullable=False)
    phone_number = Column(String, nullable=False)
    messangers = Column(ARRAY(String))
    car_types = Column(ARRAY(String), nullable=False)
    citizenships = Column(ARRAY(String), nullable=False)
    basis_of_stay = Column(String, nullable=False)
    availability_95_code = Column(String, nullable=False)
    date_stark_work = Column(DateTime, nullable=False)
    language_skills = Column(ARRAY(String), nullable=False)
    job_experience = Column(ARRAY(String), nullable=False)
    need_internship = Column(String, nullable=False)
    unsuitable_countries = Column(ARRAY(String))
    dangerous_goods = Column(ARRAY(String), nullable=False)
    expected_salary = Column(Float, nullable=False)
    categories_availability = Column(ARRAY(String), nullable=False)
    country_driving_licence = Column(String, nullable=False)
    country_current_live = Column(String, nullable=False)
    work_type = Column(String, nullable=False)
    cadence = Column(ARRAY(String))
    crew = Column(String, nullable=False)
    driver_gender = Column(String, nullable=False)

    query: sql.Select


class Company(TimedBaseModel):
    __tablename__ = "companies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_user_id = Column(BigInteger, nullable=False, primary_key=True)
    lang = Column(String, nullable=False)
    paid_subscription = Column(Integer)

    f_birth_year = Column(String)
    f_car_types = Column(ARRAY(String))
    f_citizenships = Column(ARRAY(String))
    f_basis_of_stay = Column(ARRAY(String))
    f_availability_95_code = Column(ARRAY(String))
    f_date_stark_work = Column(String)
    f_language_skills = Column(ARRAY(String))
    f_job_experience = Column(ARRAY(String))
    f_need_internship = Column(ARRAY(String))
    f_unsuitable_countries = Column(ARRAY(String))
    f_expected_salary = Column(String)
    f_categories_availability = Column(ARRAY(String))
    f_country_driving_licence = Column(ARRAY(String))
    f_country_current_live = Column(ARRAY(String))
    f_work_type = Column(ARRAY(String))
    f_cadence = Column(ARRAY(String))
    f_dangerous_goods = Column(ARRAY(String))
    f_crew = Column(ARRAY(String))
    f_driver_gender = Column(ARRAY(String))

    query: sql.Select
