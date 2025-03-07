from .driver import *
from .company import *
from .start import router as r_start

routers = [
    r_menu, r_company_menu, r_start, r_new_driver, r_new_company, r_register_driver, r_change_form_status, r_my_form,
    r_driver_filters
]
