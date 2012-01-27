from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from airbrake.utils.client import Client

class AirbrakeNotifierMiddleware(object):
    def __init__(self):
        self.client = Client()

    def process_exception(self, request, exception):
        if not settings.DEBUG:
            self.client.notify(exception=exception, request=request)
