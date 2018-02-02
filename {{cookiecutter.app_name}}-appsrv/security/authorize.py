# -*- coding: utf-8 -*-
import base64

from functools import wraps
import hashlib
import hmac
from urllib import quote
from db import User
from pyramid.httpexceptions import HTTPForbidden

# This is for a partial "roles" implementation that needs a lot of adjustment
class authorized_roles(object):
    """
    For passing roles into the decorator, and returning a forbidden if the user does not have
    such a role
    """
    def __init__(self, roles=None):
        """
        Store the roles, or an empty list
        """
        if roles is None and not isinstance(roles, list):
            if isinstance(roles, basestring):
                roles = roles.split(',')
            else:
                roles = []
        self.roles = roles

    def __call__(self, func):
        """
        Returns a function that will only call the wrapped function if the user has an appropriate
        role passed originally to the decorator call (or if None, simply calls the function), if
        the role is missing, it returns an HTTP403Forbidden
        :param func: The function to wrap
        :return: The wrapped function
        """
        @wraps(func)
        def wrapped_func(request):
            if isinstance(request.user, User):
                user_roles = request.cust.roles.split(',')
            else:
                user_roles = None
            if len(self.roles) == 0 or ((user_roles is not None) and request.cust.has_role(self.roles)):
                return func(request)
            else:
                return HTTPForbidden()


        return wrapped_func


