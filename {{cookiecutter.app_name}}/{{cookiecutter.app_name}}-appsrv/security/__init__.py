# -*- coding: utf-8 -*-
from db import User, Session

from sqlalchemy.orm import Session as dbSession

def get_user_from_token(dbsession, token):
    """
    Get the associated user for a given token, if any
    :param dbsession: A text based session token
    :type dbsession: dbSession
    :param token: A text based session token
    :type token: basestring
    :return: The User model associated with the token, or None
    """
    if not isinstance(token, basestring):
        raise ValueError('token must be a valid basestring')
    if not isinstance(dbsession, dbSession):
        raise ValueError('dbsession should be a valid db session')
    user = dbsession.query(User).join(Session, Session.user_id == User.id).filter(Session.token == token).one_or_none()
    return user
