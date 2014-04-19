import httplib
import logging
from utils.exceptions import HttpRequestException

LOG = logging.getLogger(__name__)


class HttpRequestHandler(object):
    def __init__(self, url, auth_token):
        """ Initialize the Http Request Handler.

        :param url: url of the request recipient
        :param auth_token: authentication token to pass
        in the x-auth-token header
        """
        self.auth_token = auth_token
        address = url.split("http://")[1].split(":")
        self.conn = httplib.HTTPConnection(host=address[0], port=address[1])

    def _send_request(self, method, url, headers, body,
                     ignore_result_body=False):
        """Perform an HTTP request.

        :param method: the HTTP method to use
        :param url: the URL to send request to
        :param headers: request header
        :param body: request body
        :param ignore_result_body: the body of the result will be ignored
        """
        if self.auth_token:
            headers.setdefault('x-auth-token', self.auth_token)

        LOG.debug('\n%(method)s request to: http://%(server)s:%(port)s'
                  '%(url)s \nheaders: %(headers)s'
                  % {'method': method,
                     'server': self.conn.host,
                     'port': self.conn.port,
                     'url': url,
                     'headers': repr(headers)})
        self.conn.request(method, url, body, headers)

        response = self.conn.getresponse()
        # process response
        code = response.status
        code_description = httplib.responses[code]
        logging.debug('Response: %(code)s %(description)s'
                      % {'code': code,
                         'description': code_description})

        if code is not 200:
            raise HttpRequestException(code, code_description, response.read())

        if ignore_result_body:
            # consume response in order to perform another request
            # in the case of ignoring response body
            response.read()
        return response