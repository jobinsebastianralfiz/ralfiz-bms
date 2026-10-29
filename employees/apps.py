from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    name = 'employees'

    def ready(self):
        from .utils import init_firebase
        init_firebase()

        from django.core.signals import request_started
        from django.db.models.signals import post_delete, post_save
        from . import work_calendar
        request_started.connect(work_calendar.clear, weak=False)
        for model in ('employees.Holiday', 'core.CompanySettings'):
            post_save.connect(work_calendar.clear, sender=model, weak=False)
            post_delete.connect(work_calendar.clear, sender=model, weak=False)
