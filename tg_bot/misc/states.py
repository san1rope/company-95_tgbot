from aiogram.fsm.state import StatesGroup, State


class AfterStart(StatesGroup):
    ChooseLang = State()
    ChooseRole = State()


class DriverRegistration(StatesGroup):
    WriteName = State()
    ChooseBirthYear = State()
    WritePhoneNumber = State()
    ChooseCarType = State()
    ChooseCitizenship = State()
    ChooseBasisOfStay = State()
    Availability95Code = State()
    ChooseDateReadyToStartWork = State()
    IndicateLanguageSkills = State()
    IndicateJobExperience = State()
    ChooseNeedInternship = State()
    ChooseUnsuitableCountries = State()
    SelectDocumentsAvailability = State()
    WriteExpectedSalary = State()
    ChooseAvailabilityCategories = State()
    ChooseCountryDrivingLicense = State()
    ChooseCountryCurrentLiving = State()
    ChooseWorkType = State()
    WriteCadence = State()
    ChooseCrew = State()
    ChooseGender = State()
    FormConfirmation = State()
