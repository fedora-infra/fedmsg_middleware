
import BeautifulSoup
import datetime
import webob

from moksha.common.lib.helpers import get_moksha_appconfig

truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))


def asbool(s):
    """ Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is any of ``t``, ``true``, ``y``, ``on``, or ``1``, otherwise
    return the boolean value ``False``.  If ``s`` is the value ``None``,
    return ``False``.  If ``s`` is already one of the boolean values ``True``
    or ``False``, return it."""
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    s = str(s).strip()
    return s.lower() in truthy


class FedmsgMiddleware(object):
    """ WSGI middleware that injects a moksha socket for fedmsg popups """

    def __init__(self, app, config=None):
        """ Configuration arguments are documented in README.rst """

        self.app = app
        self.config = config

        if not self.config:
            self.config = get_moksha_appconfig()

    def __call__(self, environ, start_response):
        """ Process a request. """

        req = webob.Request(environ)
        resp = req.get_response(self.app, catch_exc_info=True)

        if self.should_inject(req, resp):
            resp = self.inject(resp)

        return resp(environ, start_response)

    def should_inject(self, req, resp):
        """ Determine if this request should be modified.  Boolean. """

        if resp.status != "200 OK":
            return False

        content_type = resp.headers.get('Content-Type', 'text/plain').lower()
        if not 'html' in content_type:
            return False

        return True

    def inject(self, resp):
        """ Inject notification machinery into this response!

        Insert javascript into the <head> tag.
        """

        soup = BeautifulSoup.BeautifulSoup(resp.body)

        if not soup.html:
            return resp

        if not soup.html.head:
            soup.html.insert(0, BeautifulSoup.Tag(soup, "head"))


        from moksha.wsgi.widgets.api import get_moksha_socket
        socket = get_moksha_socket(self.config)

        payload = socket().display()
        payload = BeautifulSoup.BeautifulSoup(payload)
        soup.html.body.insert(len(soup.html.body), payload)

        resp.body = str(soup.prettify())
        return resp


def make_middleware(app=None, *args, **kw):
    """ Given an app, return that app wrapped in RaptorizeMiddleware """
    app = FedmsgMiddleware(app, *args, **kw)
    return app
