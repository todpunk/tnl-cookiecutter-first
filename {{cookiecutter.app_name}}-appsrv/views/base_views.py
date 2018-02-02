# -*- coding: utf-8 -*-
import hashlib
import ujson

from sqlalchemy.orm import Session as dbSession

from db.converters import array_of_dicts_from_array_of_models
from pyramid.exceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPFound


def app_base(request):
    """
    This should render the required HTML to start the Angular application.  It is the only entry point for
    the pyramid UI via Angular
    :param request: A pyramid request object, default for a view
    :return: A dictionary of variables to be rendered into the template
    """
    dev_endpoints = ['localhost', '0.0.0.0', '127.0.', '192.168.', '10.19.', 'dev.squizzlezig.com']
    is_dev = False
    for point in dev_endpoints:
        if request.host.split(':', 1)[0].startswith(point) or request.remote_addr.startswith(point):
            is_dev = True
    return { 'is_dev': is_dev, 'some_key': request.registry.settings['some_key']}


def notfound_view(request):
    """
    For when Pyramid is passed a url it can not route
    """
    return HTTPNotFound('The url could not be found.')


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_utilities_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""


