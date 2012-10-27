
import BeautifulSoup
import webob
import json

import fedmsg.config
import fedmsg.text as t

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

        # Initialize fedmsg its own config in /etc/fedmsg.d/
        self.fedmsg_config = fedmsg.config.load_config(None, [])
        t.make_processors(**self.fedmsg_config)

    def __call__(self, environ, start_response):
        """ Process a request. """

        req = webob.Request(environ)

        if self.should_respond(req):
            # Is this an ajax request asking for fedmsg.text information?
            # If so.. forget everything else and just handle that before anyone
            # else notices ;o
            resp = self.serve_response(req)
            return resp(environ, start_response)

        # This middleware does its dirty work in one of two ways.  If pre_inject
        # is False, then it waits for the wrapped app to do all of its work and
        # render all of its HTML response, then it dirtily injects the HTML and
        # javascript for the popup notification *and* the moksha socket directly
        # into the response.
        # If pre_inject is True, then we assume that the wrapped_app *already
        # uses* moksha and a live moksha socket in some capacity and will be
        # providing it on the page.  If we didn't distinguish between these two
        # cases, then our middleware could accidentally inject a *second* moksha
        # socket on top of the one already written out by the app.  They fight
        # at runtime and .. doom.
        pre_inject = self.config.get('pre_inject', False)

        pre_inject = True # TODO -- remove this

        if pre_inject:
            # If pre_inject is true, then we don't create our own
            # moksha_socket.. we only register our fancy popup notification
            # widget with the moksha middleware.
            PopupNotification.display()

        # Pass the request on to the app that we wrap.
        resp = req.get_response(self.app, catch_exc_info=True)

        # Should we modify their response and inject both our notif widget and
        # the moksha_socket?  We'll do so in a hopefully delicate manner that
        # doesn't disturb other javascript (like jQuery).
        if not pre_inject and self.should_inject(req, resp):
            resp = self.inject(resp)

        return resp(environ, start_response)

    def should_respond(self, req):
        """ Determine if this is an AJAX request for fedmsg.text metadata """
        return req.environ['PATH_INFO'] == "/__fedmsg.text__"

    def serve_response(self, req):
        """ Translate a fedmsg message into metadata for gritter. """
        msg = json.loads(req.GET['json'])

        proc = t.msg2processor(msg)
        text = """<a href="{link}" target="_blank">{text}</a>""".format(
            text=t.msg2subtitle(msg, proc, **self.fedmsg_config),
            link=t.msg2link(msg, proc, **self.fedmsg_config),
        )
        metadata = dict(
            title="fedmsg -> " + t.msg2title(msg, proc, **self.fedmsg_config),
            text=text,
            image=t.msg2secondary_icon(msg, proc, **self.fedmsg_config),
            time=10000,  # 10 seconds until messages disappear
        )

        resp = webob.Response(
            content_type='application/json',
            body=json.dumps(metadata),
        )
        return resp

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
        // Make an ajax request to get the fedmsg.text metadata and use that
        // metadata to make the gritter popup.
        $.ajax("/__fedmsg.text__", {
                data: {json: JSON.stringify(json)},
                success: $.gritter.add,
        });
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
