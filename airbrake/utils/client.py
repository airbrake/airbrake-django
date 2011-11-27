from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import resolve
import sys
import urllib2
import traceback
from xmlbuilder import XMLBuilder
from airbrake.decorators import async


class Client(object):
    API_URL = '%s://airbrake.io/notifier_api/v2/notices'
    ERRORS = {
        403: "Cannot use SSL",
        422: "Invalid XML sent to Airbrake",
        500: "Airbrake has braked too hard",
    }

    @property
    def url(self):
        scheme = 'http'
        if getattr(settings, 'AIRBRAKE_USE_SSL', False):
            scheme = 'https'

        return Client.API_URL % scheme

    @async
    def send(self, request, exception):
        headers = {
            'Content-Type': 'text/xml'
        }

        payload = self._generate_xml(request, exception)
        req = urllib2.Request(self.url, payload, headers)
        resp = urllib2.urlopen(req,
            timeout=getattr(settings, 'AIRBRAKE_TIMEOUT', 5))
        status = resp.getcode()

        if status == 200:
            return True
        elif status in Client.ERRORS:
            raise Exception(Client.ERRORS[status])

    def _generate_xml(self, request, exception):
        _,_,trace = sys.exc_info()
        
        xml = XMLBuilder()
        
        tb_dict = {}
        tb = traceback.extract_tb(trace)
        
        if tb:
            tb = tb[0]
            tb_dict['filename'] = tb[0]
            tb_dict['line_number'] = tb[1]
            tb_dict['function_name'] = tb[2]
        
        site = Site.objects.get_current()
        with xml.notice(version = 2.0):
            xml << ('api-key', settings.AIRBRAKE_API_KEY)
            with xml.notifier:
                xml << ('name', site.name)
                xml << ('version', '0.0.1')
                xml << ('url', site.domain)
            with xml.request:
                if request.is_secure():
                    scheme = 'https'
                else:
                    scheme = 'http'
                url = '%s://%s%s' % (scheme, request.get_host(),
                    request.get_full_path())
                xml << ('url', url)

                cb,_,_ = resolve(request.path)
                xml << ('component', cb.__module__)
                xml << ('action', cb.__name__)

                if len(request.POST):
                    with xml.params:
                        for key, val in request.POST.items():
                            xml << ('var', str(val), {'key': key})

                session = request.session.items()
                if len(session):
                    with xml.session:
                        for key, val in session.items():
                            xml << ('var', str(val), {'key': key})

                with xml('cgi-data'):
                    for key, val in request.META.items():
                        xml << ('var', str(val), {'key':key})

            with xml('server-environment'):
                xml << ('environment-name', settings.AIRBRAKE_ENVIRONMENT)
            with xml.error:
                xml << ('class', exception.__class__.__name__)
                xml << ('message', str(exception))
                with xml.backtrace:
                    xml << ('line', {
                        'file':tb_dict.get('filename', 'unknown'),
                        'number':tb_dict.get('line_number', 'unknown'),
                        'method':tb_dict.get('function_name', 'unknown')
                    })

        return str(xml)
