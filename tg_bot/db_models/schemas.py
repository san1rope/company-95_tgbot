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

    stripe_product_id = Column(String)
    stripe_price_id = Column(String)

    name = Column(String, nullable=False)
    birth_year = Column(Integer, nullable=False)
    phone_number = Column(String, nullable=False)
    messangers = Column(ARRAY(String))
    car_types = Column(ARRAY(String), nullable=False)
    citizenships = Column(ARRAY(String), nullable=False)
    basis_of_stay = Column(String, nullable=False)
    availability_95_code = Column(String, nullable=False)
    date_start_work = Column(DateTime, nullable=False)
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
    viewed_drivers = Column(ARRAY(Integer))
    saved_drivers = Column(ARRAY(Integer))
    open_drivers = Column(ARRAY(Integer))

    stripe_customer_id = Column(String)

    birth_year_left_edge = Column(Integer)
    birth_year_right_edge = Column(Integer)
    car_types = Column(ARRAY(String))
    citizenships = Column(ARRAY(String))
    basis_of_stay = Column(ARRAY(String))
    availability_95_code = Column(ARRAY(String))
    date_start_work_left_edge = Column(DateTime)
    date_start_work_right_edge = Column(DateTime)
    language_skills = Column(ARRAY(String))
    job_experience = Column(ARRAY(String))
    need_internship = Column(ARRAY(String))
    unsuitable_countries = Column(ARRAY(String))
    expected_salary_left_edge = Column(Float)
    expected_salary_right_edge = Column(Float)
    categories_availability = Column(ARRAY(String))
    country_driving_licence = Column(ARRAY(String))
    country_current_live = Column(ARRAY(String))
    work_type = Column(ARRAY(String))
    cadence = Column(ARRAY(String))
    dangerous_goods = Column(ARRAY(String))
    crew = Column(ARRAY(String))
    driver_gender = Column(ARRAY(String))

    query: sql.Select


class Payment(TimedBaseModel):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    system = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    creator_id = Column(BigInteger, nullable=False, primary_key=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    driver_id = Column(BigInteger)
    invoice_url = Column(String)
    msg_to_delete = Column(Integer)

    stripe_invoice_id = Column(String)

    query: sql.Select
