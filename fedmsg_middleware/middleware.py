
import BeautifulSoup
import webob

from moksha.common.lib.helpers import get_moksha_appconfig
from moksha.wsgi.widgets.api import get_moksha_socket
from moksha.wsgi.widgets.api import LiveWidget
from tw2.jqplugins.gritter import gritter_resources

truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))


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

        def add_payload(payload):
            payload = BeautifulSoup.BeautifulSoup(payload)
            soup.html.body.insert(len(soup.html.body), payload)

        socket = get_moksha_socket(self.config)

        add_payload(PopupNotification.display())
        add_payload(socket().display())

        resp.body = str(soup.prettify())
        return resp


class PopupNotification(LiveWidget):
    topic = "*"
    onmessage = """
    (function(json){
        // Use the modname for the title
        var title = json.topic.split('.')[3];

        var body = '...';
        $.gritter.add({'title': title, 'text': body});
    })(json);
    """
    resources = LiveWidget.resources + gritter_resources
    backend = "websocket"

    # Don't actually produce anything when you call .display() on this widget.
    inline_engine_name = "mako"
    template = ""


def make_middleware(app=None, *args, **kw):
    app = FedmsgMiddleware(app, *args, **kw)
    return app
