from django.conf import settings
try:
    # MiddlewareMixin is not available on older versions of Django
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
from airbrake.utils.client import Client


class AirbrakeNotifierMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        self.client = Client()

        super(AirbrakeNotifierMiddleware, self).__init__(*args, **kwargs)

    def process_exception(self, request, exception):
        if (hasattr(settings, 'AIRBRAKE') and
                not settings.AIRBRAKE.get('DISABLE', False) and
                not isinstance(exception, settings.AIRBRAKE.get('FILTERED_EXCEPTIONS', tuple()))):
            self.client.notify(exception=exception, request=request)
