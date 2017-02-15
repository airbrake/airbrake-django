from django.conf import settings
try:
    # MiddlewareMixin is not available anymore in Django 1.8.7
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
from airbrake.utils.client import Client


class AirbrakeNotifierMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        self.client = Client()

        super(AirbrakeNotifierMiddleware, self).__init__(*args, **kwargs)

    def process_exception(self, request, exception):
        if hasattr(settings, 'AIRBRAKE') and not settings.AIRBRAKE.get('DISABLE', False):
            self.client.notify(exception=exception, request=request)
