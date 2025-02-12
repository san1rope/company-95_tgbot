from .driver import *
from .start import router as r_start
from .driver_registration import router as r_driver_registration

routers = [r_menu, r_start, r_registration, r_change_form_status, r_my_form, r_driver_registration]
