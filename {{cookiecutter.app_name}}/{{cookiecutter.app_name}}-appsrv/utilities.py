# -*- coding: utf-8 -*-
"""
This file contains utility functions for use in the Pyramid view handling
"""

import hashlib
from os.path import exists
import datetime


def error_dict(error_type='generic_errors', errors=''):
    """
    Create a basic error dictionary for standard use with the intent of being passed to some other outside
    API or whatnot.
    :param type: A plural string without spaces that describes the errors.  Only one type of error should be sent.
    :param errors: A list of error strings describing the problems. A single string will be converted to a single item
    list containing that string.
    :return: A dictionary for the error to be passed.
    """
    if isinstance(errors, basestring):
        errors = [errors]
    if not isinstance(errors, list):
        raise TypeError('Type for "errors" must be a string or list of strings')
    if not all(isinstance(item, basestring) for item in errors):
        raise TypeError('Type for "errors" in the list must be a string')
    error = {'error_type': error_type,
             'errors': errors,
             }
    return error


def hash_password(password, salt):
    """
    Hashes a password with the sale and returns the hash
    :param password: a password string
    :type password: basestring
    :param salt: a salt hash
    :type salt: assumed to be bytes
    :return: a password digest, NOT a hex digest string
    """
    m = hashlib.sha512()
    m.update(password.encode('utf-8'))
    m.update(salt)
    return m.digest()


format_datetime = lambda timez, dt : timez.localize(dt).strftime("%Y-%m-%d %H:%M:%S")


def date_serializer(the_date, request):
    if isinstance(the_date, datetime.date):
        return str(the_date.isoformat())
    raise TypeError('Can not determine rendering for data given')


def time_serializer(the_time, request):
    if isinstance(the_time, datetime.time):
        return str(the_time.isoformat())
    raise TypeError('Can not determine rendering for data given')

