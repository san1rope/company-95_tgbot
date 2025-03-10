from sqlalchemy import sql, Column, BigInteger, String, Integer, DateTime, Float

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
    messangers = Column(String)
    car_types = Column(String, nullable=False)
    citizenships = Column(String, nullable=False)
    basis_of_stay = Column(String, nullable=False)
    availability_95_code = Column(String, nullable=False)
    date_stark_work = Column(DateTime, nullable=False)
    language_skills = Column(String, nullable=False)
    job_experience = Column(String, nullable=False)
    need_internship = Column(String, nullable=False)
    unsuitable_countries = Column(String)
    dangerous_goods = Column(String, nullable=False)
    expected_salary = Column(Float, nullable=False)
    categories_availability = Column(String, nullable=False)
    country_driving_licence = Column(String, nullable=False)
    country_current_live = Column(String, nullable=False)
    work_type = Column(String, nullable=False)
    cadence = Column(String)
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
    f_car_types = Column(String)
    f_citizenships = Column(String)
    f_basis_of_stay = Column(String)
    f_availability_95_code = Column(String)
    f_date_stark_work = Column(String)
    f_language_skills = Column(String)
    f_job_experience = Column(String)
    f_need_internship = Column(String)
    f_unsuitable_countries = Column(String)
    f_expected_salary = Column(String)
    f_categories_availability = Column(String)
    f_country_driving_licence = Column(String)
    f_country_current_live = Column(String)
    f_work_type = Column(String)
    f_cadence = Column(String)
    f_dangerous_goods = Column(String)
    f_crew = Column(String)
    f_driver_gender = Column(String)

    query: sql.Select
