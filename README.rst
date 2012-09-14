Fedmsg WSGI Middleware (Notifications)
======================================

Installation
------------

You could install it yourself with `pip`::

    $ pip install fedmsg_middleware

Or you could add ``fedmsg_middleware`` to the list of required packages in the
``setup.py`` file of your project.

Usage in TurboGears 2
---------------------

Simply edit ``myapp/config/middleware.py`` and add the following to
``make_app(...)``::

    # Wrap your base TurboGears 2 application with custom middleware here
    import fedmsg_middleware
    app = fedmsg_middleware.make_middleware(app)

Usage in Pyramid
----------------

Edit ``myapp/__init__.py`` and replace the ``return config.make_wsgi_app()``
line with the following::

    import fedmsg_middleware
    app = config.make_wsgi_app()
    app = fedmsg_middleware.make_middleware(app)
    return app

Usage in a PasteDeploy pipeline
-------------------------------

You can enable it in your PasteDeploy pipeline like so::

    [pipeline:main]
    pipeline =
        fedmsg_middleware
        my-app

    [filter:fedmsg_middleware]
    use = egg:fedmsg_middleware
    topic = org.fedoraproject.prod.koji.*

    [app:myapp]
    ...

Get the source
--------------

The code and bug tracker live over at
http://github.com/ralphbean/fedmsg_middleware.
Please fork and improve!
