# -*- coding: utf-8 -*-
import datetime

from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import INTERVAL

from db import User, Session
from utilities import date_serializer, time_serializer
from views.base_views import app_base


def user(request):
    """
    This property will be added to the request, and for now it simply verifies if they
    are authenticated or not based on the token they provide.  If this fails, this property
    is None
    """
    request_token = 'invalid_token'
    if request.method == 'GET':
        if request.GET.get('token') is None:
            return None
        else:
            request_token = request.GET.get('token')
    elif request.method in ['PUT', 'POST', 'DELETE']:
        if 'token' not in request.json_body:
            return None
        else:
            request_token = request.json_body.get('token')

    dauser = request.dbsession.query(User)\
        .filter(Session.token == request_token)\
        .filter(Session.lastactive >= (func.current_timestamp() - cast('1 week', INTERVAL)))\
        .join(Session, Session.user_id == User.id)\
        .one_or_none()
    if dauser:
        session = request.dbsession.query(Session).filter(Session.token == request_token).one()
        session.lastactive = datetime.datetime.now()
        request.dbsession.flush()
    return dauser


def add_routes(config):
    config.add_route('app', '/app')
    config.add_route('api', '/api')


def add_views(config):
    config.add_view(app_base, route_name='app', renderer='templates/app_base.jinja2')
    config.add_view(app_base, route_name='api', renderer='templates/app_base.jinja2')


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['tm.commit_veto'] = 'pyramid_tm.default_commit_veto'
    session_factory = UnencryptedCookieSessionFactoryConfig('{{cookiecutter.project_slug}}session')
    config = Configurator(
        settings=settings,
        session_factory=session_factory,
    )
    config.include('pyramid_jinja2')
    config.include('pyramid_exclog')
    config.include('cornice')
    config.include('db')
    add_routes(config)
    add_views(config)

    # These modify the request to add db and user as methods, which once called are then reify values
    # subclassing/overriding the Request will be... problematic, as discovered the hard way
    config.add_request_method(callable=user,
                              name=None,
                              property=True,
                              reify=True
                              )

    # This should add an adapter for types normally we don't wrap in JSON
    json_renderer = JSON()
    json_renderer.add_adapter(datetime.date, date_serializer)
    json_renderer.add_adapter(datetime.time, time_serializer)
    config.add_renderer('json', json_renderer)

    config.scan()
    return config.make_wsgi_app()

# The following is all for intermediate testing purposes only, once we are ready to assign role based authentication
# to our actual endpoints all of this testing code can be refactored to use those views, though these views are
# entirely inaccessible to the web as they have no route, and they have no effects, so this doesn't cause any issues
# just leaving them in


# @authorized_roles()
# def unsecured_view(request):
#     return {}


# @authorized_roles(['MS_user'])
# def user_view(request):
#     return {}


# @authorized_roles(['NonexistentRole'])
# def forbidden_view(request):
#     return {}


# @authorized_roles(['MS_admin'])
# def admin_role_view(request):
#     return {}
