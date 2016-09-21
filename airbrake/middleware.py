from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.deprecation import MiddlewareMixin
from airbrake.utils.client import Client

class AirbrakeNotifierMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        self.client = Client()

        super(AirbrakeNotifierMiddleware, self).__init__(*args, **kwargs)

    def process_exception(self, request, exception):
        if hasattr(settings, 'AIRBRAKE') and not settings.AIRBRAKE.get('DISABLE', False):
            self.client.notify(exception=exception, request=request)
