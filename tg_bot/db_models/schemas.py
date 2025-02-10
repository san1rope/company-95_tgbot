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
    car_types = Column(String, nullable=False)
    citizenships = Column(String, nullable=False)
    basis_of_stay = Column(String, nullable=False)
    availability_95_code = Column(String, nullable=False)
    date_stark_work = Column(DateTime, nullable=False)
    language_skills = Column(String, nullable=False)
    job_experience = Column(String, nullable=False)
    need_internship = Column(String, nullable=False)
    unsuitable_countries = Column(String)
    documents_availability = Column(String, nullable=False)
    expected_salary = Column(Float, nullable=False)
    categories_availability = Column(String, nullable=False)
    country_driving_licence = Column(String, nullable=False)
    country_current_live = Column(String, nullable=False)
    work_type = Column(String, nullable=False)
    cadence = Column(String, nullable=False)
    crew = Column(String, nullable=False)
    driver_gender = Column(String, nullable=False)

    query: sql.Select


class Company(TimedBaseModel):
    __tablename__ = "companies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_user_id = Column(BigInteger, nullable=False, primary_key=True)

    query: sql.Select
