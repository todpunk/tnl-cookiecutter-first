# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime
from uuid import uuid4

from cornice import Service
from email_validator import validate_email, EmailNotValidError

from db import Session, User
from utilities import error_dict, hash_password

# Sphinx doc stuff
from db.converters import dict_from_row

users_desc = """
Work with users or accounts
"""
users_svc = Service(name='users', path='/api/users', description=users_desc)

user_id_desc = """
Work with a specific user by id
"""
user_id_svc = Service(name='user', path='/api/user/{user_id:\d+}', description=user_id_desc)


removals = ['password', 'salt']

recovery_template = """
Hi %s,

Your account password has been reset in response to a valid forgotten password request.
Please use the following temporary password to log in, and then change your password immediately:

%s

For any questions, don't hesitate to contact us at support@phonejanitor.com

- Our Team
{{cookiecutter.website}}
We Have a Clever Slogan!
"""

def username_in_use(username, dbsession):
    """
    Returns true if a username exists
    :param username: a string username
    :param dbsession: a db session
    :return: True if a username exists, otherwise False
    """
    exists = dbsession.query(User).filter(User.username == username.lower()).one_or_none()
    return exists is not None



@users_svc.post()
def users_post_view(request):
    username = request.json_body.get('username')
    if not isinstance(username, basestring):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'username, email, and password are all required string fields')}
    if username_in_use(request.json_body['username'], request.dbsession):
        request.response.status = 400
        return {'d': error_dict('verification_error', 'username already in use: %s' % request.json_body['username'])}

    requires = ['email', 'password']
    if not all(field in request.json_body for field in requires) \
       or not all(isinstance(request.json_body.get(field), basestring) for field in request.json_body):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'username, email, and password are all required string fields')}

    user = User()
    user.salt = os.urandom(256)
    user.password = hash_password(request.json_body['password'], user.salt)
    user.username = request.json_body['username'].lower()
    user.email = request.json_body['email'].lower()
    user.origin = request.json_body.get('origin', None)
    user.authpin = '123456'

    request.dbsession.add(user)
    request.dbsession.flush()
    request.dbsession.refresh(user)

    s = Session()
    s.owner = user.id
    s.token = str(uuid4())
    request.dbsession.add(s)
    request.dbsession.flush()
    request.dbsession.refresh(s)
    result = dict_from_row(user, remove_fields=removals)
    result['session'] = dict_from_row(s, remove_fields=removals)

    return {'d': result}


@users_svc.put()
def users_put_view(request):
    """
    Used for forgotten password requests
    """
    # TODO Make tests for this
    # TODO Make this a temporary reset link thing instead of actually resetting passwords to random
    if request.user is not None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'you are already logged in, ignoring')}
    username = request.json_body.get('username')
    email = request.json_body.get('email')
    if not isinstance(username, basestring) or not isinstance(email, basestring):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'username and email are required string fields')}
    user = request.dbsession.query(User).filter(User.username == username.lower()).one_or_none()
    if user is None or user.email != email.lower():
        request.response.status = 400
        return {'d': error_dict('api_errors', 'invalid state found')}
    uid = uuid4()
    newpass = uid.hex
    user.salt = os.urandom(256)
    user.password = hash_password(newpass, user.salt)

    # This needs to be written to whatever queues/sends an email out.
    # send_email.apply_async((user.email, "{{cookiecutter.app_name}} password recovery", recovery_template %(username, newpass)))
    return {'d': 'recovery email sent'}

@user_id_svc.get()
def user_id_get_view(request):
    if request.user is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'not authenticated for this request')}
    if not request.matchdict.get('user_id') or int(request.matchdict.get('user_id')) != request.user.id:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'not authenticated for this request')}
    user = request.user
    result = dict_from_row(user, remove_fields=removals)
    return {'d': result}


@user_id_svc.put()
def user_id_put_view(request):
    if request.user is None:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'not authenticated for this request')}
    if not request.matchdict.get('user_id') or int(request.matchdict.get('user_id')) != request.user.id:
        request.response.status = 400
        return {'d': error_dict('api_errors', 'not authenticated for this request')}
    valid_types = {
        'email': basestring,
        'pin': basestring,
        'timezone': datetime,
        'infoemails': bool,
    }
    email = request.json_body.get('email')
    authpin = request.json_body.get('authpin')
    timezone = request.json_body.get('timezone')
    infoemails = request.json_body.get('infoemails')
    if not isinstance(email, basestring):
        request.response.status = 400
        return {'d': error_dict('api_errors', 'email invalid: must be a string')}
    try:
        v = validate_email(email) # validate and get info
        email = v["email"] # replace with normalized form
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        request.response.status = 400
        return {'d': error_dict('api_errors', 'email invalid: %s' % e)}
    password = request.json_body.get('password')
    # Password must be optional, since they don't know the old value
    if password is not None:
        if not isinstance(password, basestring):
            request.response.status = 400
            return {'d': error_dict('api_errors', 'password must be a string')}
        if len(password) < 8:
            request.response.status = 400
            return {'d': error_dict('api_errors', 'password must be at least 8 characters')}
        request.user.password = hash_password(password, request.user.salt)

    request.user.email = email

    request.dbsession.flush()
    request.dbsession.refresh(request.user)
    return {'d': dict_from_row(request.user, remove_fields=removals)}

