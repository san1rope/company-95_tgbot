from aiogram.fsm.state import StatesGroup, State


class AfterStart(StatesGroup):
    ChooseLang = State()
    ChooseRole = State()


class DriverRegistration(StatesGroup):
    MOTDMessage = State()
    WriteName = State()
    ChooseBirthYear = State()
    WritePhoneNumber = State()
    ChooseMessangersAvailabilities = State()
    ChooseCarType = State()
    ChooseCitizenship = State()
    ChooseBasisOfStay = State()
    Availability95Code = State()
    ChooseDateReadyToStartWork = State()
    IndicateLanguageSkills = State()
    IndicateJobExperience = State()
    ChooseNeedInternship = State()
    ChooseUnsuitableCountries = State()
    ChooseDangerousGoods = State()
    WriteExpectedSalary = State()
    ChooseAvailabilityCategories = State()
    ChooseCountryDrivingLicense = State()
    ChooseCountryCurrentLiving = State()
    ChooseWorkType = State()
    WriteCadence = State()
    ChooseCrew = State()
    ChooseGender = State()
    FormConfirmation = State()


class CompanyRegistration(StatesGroup):
    MOTDMessage = State()


class DriverFormStates(StatesGroup):
    ChooseAction = State()
    FormResetConfirmation = State()
    ChooseFieldToEdit = State()


class CompanyFilters(StatesGroup):
    ChooseFilterMenuBtn = State()
    ChooseParam = State()
    ResetFiltersConfirmation = State()


class CompanyFindDriver(StatesGroup):
    ActionOnDriver = State()
