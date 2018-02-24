# -*- coding: utf-8 -*-
import binascii
from datetime import datetime, timedelta
from uuid import uuid4

from cornice import Service

from pjDb import Session, User
from pjLib.utilities import error_dict, hash_password

# Sphinx doc stuff
from pjDb.converters import dict_from_row

sessions_desc = """
Work with sessions for user accounts
"""
sessions_svc = Service(name='sessions', path='/api/sessions', description=sessions_desc)

@sessions_svc.post()
def sessions_post_view(request):
    """
    This will begin a new session given a username and password
    """
    if request.user is not None and request.json_body.get('token') is not None:
        # Our request validated their token, so just get that token
        return {'d': dict_from_row(request.dbsession.query(Session)\
                                   .filter(Session.token == request.json_body['token']).one())}
    username = request.json_body.get('username')
    if username is None or not isinstance(username, basestring):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid username provided')}
    password = request.json_body.get('password')
    if password is None or not isinstance(password, basestring):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid password provided')}
    user = request.dbsession.query(User).filter(User.username == username.lower()).one_or_none()
    if user is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid username provided')}

    salted_pass = binascii.b2a_hex(hash_password(password, user.salt))

    if binascii.b2a_hex(user.password) != salted_pass:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid username provided')}

    if user.lockmessage is not None:
        request.response.status = 400
        return {'d': error_dict('account_lock', user.lockmessage)}

    new_token = str(uuid4())

    new_session = Session()
    new_session.user_id = user.id
    new_session.token = new_token
    request.dbsession.add(new_session)
    request.dbsession.flush()
    request.dbsession.refresh(new_session)

    since = datetime.now() - timedelta(weeks=2)
    request.dbsession.query(Session)\
        .filter(Session.lastactive <= since)\
        .filter(Session.user_id == user.id)\
        .delete()

    result = dict_from_row(new_session)
    result['origin'] = user.origin
    return {'d': result}


@sessions_svc.delete()
def sessions_delete_view(request):
    if request.user is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'not authenticated for this request')}
    token = request.json_body.get('token')
    if token is None or not isinstance(token, basestring):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid token provided')}
    s = request.dbsession.query(Session).filter(Session.token == token).one_or_none()
    if s is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid token provided')}

    request.dbsession.delete(s)
    request.dbsession.flush()

    return {'d': {}}


@sessions_svc.put()
def sessions_put_view(request):
    if request.user is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'not authenticated for this request')}
    token = request.json_body.get('token')
    s = request.dbsession.query(Session).filter(Session.token == token,
                                                Session.user_id == request.user.id).one_or_none()
    if s is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid token provided')}

    expiration_value = timedelta(weeks=2)
    if (datetime.now() - s.lastactive) > expiration_value:
        request.dbsession.delete(s)
        request.response.status = 400
        return {'d': error_dict('api_errors', 'no valid token provided')}

    s.lastactive = datetime.now()
    request.dbsession.flush()

    result = dict_from_row(s)
    result['origin'] = request.user.origin
    return {'d': result}
