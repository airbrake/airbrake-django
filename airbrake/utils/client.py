from django.conf import settings
from django.core.urlresolvers import resolve
import sys
import urllib2
import traceback
from lxml import etree
from airbrake.utils.decorators import async


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

    @async
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

        tb_dict = {}
        tb = traceback.extract_tb(trace)

        if tb:
            tb = tb[0]
            tb_dict['filename'] = tb[0]
            tb_dict['line_number'] = tb[1]
            tb_dict['function_name'] = tb[2]

        etree.SubElement(notice_em, 'api-key').text(self.settings['API_KEY'])

        notifier_em = etree.SubElement(notice, 'notifier')

        etree.SubElement(notifier_em, 'name').text('django-airbrake')
        etree.SubElement(notifier_em, 'version').text('0.0.2')
        etree.SubElement(notifier_em, 'url').text('')

        if request:
            resquest_em = etree.SubElement(notice_em, 'request')

            if request.is_secure():
                scheme = 'https'
            else:
                scheme = 'http'
            url = '%s://%s%s' % (scheme, request.get_host(),
                request.get_full_path())
            etree.SubElement(request_em, 'url').text(url)

            cb,_,_ = resolve(request.path)
            etree.SubElement(request_em, 'component').text(cb.__module__)
            etree.SubElement(request_em, 'action').text(cb.__name__)

            if len(request.POST):
                params_em = etree.SubElement(request_em, 'params')

                for key, val in request.POST.items():
                    etree.SubElement(params_em, 'var', key=key).text(val)

            session = request.session.items()
            if len(session):
                session_em = etree.SubElement(request_em, 'session')
                for key, val in session.items():
                    etree.SubElement(session_em, 'var', key=key).text(val)

            cgi_em = etree.SubElement(request_em, 'cgi-data')
            for key, val in request.META.items():
                etree.SubElement(cgi_em, 'var', key=key).text(val)

            # xml << ('environment-name', self.settings['ENVIRONMENT'])

            if exception:
                error_em = etree.SubElement(notice_em, 'error')

                etree.SubElement(error_em, 'class').text(exception.__class__.__name__)
                etree.SubElement(error_em, 'message').text(str(exception))

                backtrace_em = etree.SubElement(error_em, 'backtrace')

                etree.SubElement(backtrace_em, 'line',
                    file=tb_dict.get('filename', 'unknown'),
                    number=tb_dict.get('line_number', 'unknown'),
                    method=tb_dict.get('function_name', 'unknown'))

        return etree.tostring(notice_em)
