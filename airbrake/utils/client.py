from django.conf import settings
from django.core.urlresolvers import resolve
import sys
import urllib2
import traceback
from lxml import etree


class Client(object):
    API_URL = '%s://airbrake.io/notifier_api/v2/notices'
    ERRORS = {
        403: "Cannot use SSL",
        422: "Invalid XML sent to Airbrake",
        500: "Airbrake has braked too hard",
    }

    DEFAULTS = {
        'TIMEOUT': 5,
        'USE_SSL': False,
    }

    @property
    def url(self):
        scheme = 'http'
        if self.settings['USE_SSL']:
            scheme = 'https'

        return Client.API_URL % scheme

    @property
    def settings(self):
        if getattr(self, '_settings', None):
            return self._settings

        self._settings = Client.DEFAULTS
        self._settings.update(getattr(settings, 'AIRBRAKE', {}))
        return self._settings

    def notify(self, exception=None, request=None):
        headers = {
            'Content-Type': 'text/xml'
        }

        payload = self._generate_xml(exception=exception, request=request)
        req = urllib2.Request(self.url, payload, headers)
        resp = urllib2.urlopen(req, timeout=self.settings['TIMEOUT'])
        status = resp.getcode()

        if status == 200:
            return True
        elif status in Client.ERRORS:
            raise Exception(Client.ERRORS[status])

    def _generate_xml(self, exception=None, request=None):
        _,_,trace = sys.exc_info()
        notice_em = etree.Element('notice', version='2.0')

        tb = traceback.extract_tb(trace)

        api_key = etree.SubElement(notice_em, 'api-key').text = self.settings['API_KEY']

        notifier_em = etree.SubElement(notice_em, 'notifier')

        etree.SubElement(notifier_em, 'name').text = 'django-airbrake'
        etree.SubElement(notifier_em, 'version').text = '0.0.2'
        etree.SubElement(notifier_em, 'url').text = 'http://example.com'

        if request:
            request_em = etree.SubElement(notice_em, 'request')

            if request.is_secure():
                scheme = 'https'
            else:
                scheme = 'http'
            url = '%s://%s%s' % (scheme, request.get_host(),
                request.get_full_path())
            etree.SubElement(request_em, 'url').text = str(url)

            cb,_,_ = resolve(request.path)
            etree.SubElement(request_em, 'component').text = str(cb.__module__)
            etree.SubElement(request_em, 'action').text = str(cb.__name__)

            if len(request.POST):
                params_em = etree.SubElement(request_em, 'params')

                for key, val in request.POST.items():
                    var = etree.SubElement(params_em, 'var')
                    var.set('key', str(key))
                    var.text = str(val)

            session = request.session.items()
            if len(session):
                session_em = etree.SubElement(request_em, 'session')
                for key, val in session:
                    var = etree.SubElement(session_em, 'var')
                    var.set('key', str(key))
                    var.text = str(val)

            if exception:
                error_em = etree.SubElement(notice_em, 'error')

                etree.SubElement(error_em, 'class').text = str(exception.__class__.__name__)
                etree.SubElement(error_em, 'message').text = str(exception)

                backtrace_em = etree.SubElement(error_em, 'backtrace')

                for line in tb:
                    etree.SubElement(backtrace_em, 'line',
                        file=str(line[0]),
                        number=str(line[1]),
                        method=str(line[2]))

        env_em = etree.SubElement(notice_em, 'server-environment')

        etree.SubElement(env_em, 'environment-name').text = getattr(settings, 'ENVIRONMENT', 'development')

        return '<?xml version="1.0" encoding="UTF-8"?>%s' % etree.tostring(notice_em)
