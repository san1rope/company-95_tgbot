from .driver import *
from .company import *
from .start import router as r_start
from .supportive import router as r_supportive
from .change_lang import router as r_change_lang

routers = [
    r_menu, r_company_menu, r_start, r_supportive, r_new_driver, r_new_company, r_register_driver, r_change_form_status,
    r_my_form, r_driver_filters, r_find_driver, r_saved_drivers, r_opened_drivers, r_payments_processing, r_subscription,
    r_change_lang, r_remove_profile
]
