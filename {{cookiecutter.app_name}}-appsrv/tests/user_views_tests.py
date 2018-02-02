# -*- coding: utf-8 -*-
import hashlib
from copy import deepcopy

from email_validator import validate_email, EmailNotValidError

from tests import MyPyramidTestBase, bad_data_typevals_list
from views.user_views import users_post_view, user_id_get_view, user_id_put_view
from db import Session, User
from db.converters import dict_from_row
from utilities import error_dict

removals = ['password', 'salt']

class AccountViewsTestBase(MyPyramidTestBase):
    """
    Helper for all account view stuffs
    """
    def setUp(self):
        MyPyramidTestBase.setUp(self)

    def tearDown(self):
        MyPyramidTestBase.tearDown(self)


class UsersPostViewsTest(AccountViewsTestBase):
    """
    Tests for the createAccount post view
    """
    def setUp(self):
        AccountViewsTestBase.setUp(self)
        self.new_account = {
            'username': 'newuser',
            'email':    'newuser@example.com',
            'password': 'newpass',
        }

    def test_missing_parameters(self):
        """
        If we don't pass in all the required parameters, get an error
        """
        self.assertEqual(0, self.session.query(User).count())
        for i in ['username', 'email', 'password']:
            self.request.json_body = deepcopy(self.new_account)
            del self.request.json_body[i]
            result = users_post_view(self.request)['d']
            self.assertEqual(result, error_dict('api_errors', 'username, email, and password are all required string fields'))
        self.request.json_body = {}
        result = users_post_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'username, email, and password are all required string fields'))
        self.request.json_body = {'username': 'justuser'}
        result = users_post_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'username, email, and password are all required string fields'))

    def test_bad_parameters(self):
        """
        If we don't pass in all the right types, get an error
        """
        self.assertEqual(0, self.session.query(User).count())
        for i in ['username', 'email', 'password']:
            self.request.json_body = deepcopy(self.new_account)
            for val in [x for x in bad_data_typevals_list if not isinstance(x, basestring)]:
                self.request.json_body[i] = val
                result = users_post_view(self.request)['d']
                self.assertEqual(result, error_dict('api_errors',
                                                    'username, email, and password are all required string fields'))

    def test_username_taken(self):
        """
        If we try to create an account that is in use, get an api error
        """
        self.datautils.create_user({'username': 'newuser'})
        self.assertEqual(1, self.session.query(User).count())
        self.request.json_body = deepcopy(self.new_account)
        result = users_post_view(self.request)['d']
        self.assertEqual(result, error_dict('verification_error',
                                            'username already in use: %s' % self.new_account['username']))

    def test_get_user_and_token_after_creation(self):
        """
        If we create a user, we should get a user and a session back
        """
        self.request.json_body = deepcopy(self.new_account)
        result = users_post_view(self.request)['d']
        session = self.session.query(Session).one()
        user = self.session.query(User).one()
        expected = dict_from_row(user, remove_fields=removals)
        expected['session'] = dict_from_row(session, remove_fields=removals)
        self.assertEqual(result, expected)

    def test_password_is_hashed(self):
        """
        If we create a user, their password should be a hash
        """
        self.request.json_body = deepcopy(self.new_account)
        result = users_post_view(self.request)['d']
        user = self.session.query(User).one()
        expected = dict_from_row(user, remove_fields=removals)
        session = self.session.query(Session).one()
        expected['session'] = dict_from_row(session, remove_fields=removals)
        self.assertEqual(result, expected)
        user = self.session.query(User).one()
        self.assertNotEqual(user.password, self.new_account['password'])

    def test_username_in_use(self):
        """
        If we provide a username that is in use, get True
        """
        self.request.json_body = {'username': 'testuser'}
        self.datautils.create_user({'username': 'testuser', 'password': 'testpass'})
        result = users_post_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('verification_error', 'username already in use: testuser'))

    def test_username_not_in_use(self):
        """
        If we provide a username that is not in use, get False
        """
        self.request.json_body = {'username': 'newuser'}
        self.datautils.create_user({'username': 'testuser', 'password': 'testpass'})
        result = users_post_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'username, email, and password are all required string fields'))


class UserIDGetViewTest(AccountViewsTestBase):
    """
    Tests for the user_id get view
    """
    def test_no_user(self):
        """
        If we try to get info without a login, get an error back
        """
        self.request.user = None
        result = user_id_get_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'not authenticated for this request'))

    def test_no_user_matchdict(self):
        """
        If we try to get info a login but not the same ID in the url, get an error back
        """
        user = self.datautils.create_user()
        self.request.matchdict = {'user_id': user.id + 4}
        self.request.user = user
        result = user_id_get_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'not authenticated for this request'))

    def test_good_user(self):
        """
        If we use good info, get the user back
        """
        user = self.datautils.create_user()
        self.request.user = user
        self.request.matchdict = {'user_id': int(user.id)}
        result = user_id_get_view(self.request)['d']
        expected = {
            'id': user.id,
            'username': user.username,
            'created': user.created,
            'email': user.email,
        }
        self.assertEqual(result, expected)


class UserIDPutViewTest(AccountViewsTestBase):
    """
    Tests for the user_id put view
    """
    def setUp(self):
        AccountViewsTestBase.setUp(self)
        self.request.user = self.datautils.create_user()
        self.request.matchdict = {'user_id': int(self.request.user.id)}
        self.good_dict = {
            'email': 'thing@thing.com',
        }

    def test_not_logged_in(self):
        """
        If we aren't logged in, get an api error
        """
        self.request.user = None
        result = user_id_put_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'not authenticated for this request'))

    def test_wrong_id(self):
        """
        If we don't use the right id in the url, get an api error
        """
        self.request.matchdict = {'user_id': int(self.request.user.id)+4}
        self.request.json_body = {}
        result = user_id_put_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'not authenticated for this request'))

    def test_bad_emails(self):
        """
        If we pass a bad email, get an error about it
        """
        bad_email = 'invalid@spaced domain.com'
        email_result = {}
        try:
            validate_email(bad_email) # validate and get info
            self.fail('Validate email did not raise exception, fix the test')
        except EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            email_result = error_dict('api_errors', 'email invalid: %s' % e)

        self.request.json_body = deepcopy(self.good_dict)
        self.request.json_body['email'] = bad_email
        result = user_id_put_view(self.request)['d']
        self.assertEqual(result, email_result)
        self.assertNotEqual(result, {})

        self.request.json_body = deepcopy(self.good_dict)
        self.request.json_body['email'] = 234234  # Not a string
        result = user_id_put_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'email invalid: must be a string'))

    def test_good_data(self):
        """
        If we pass good data, get "OK" and see the stuff changed
        """
        self.assertNotEqual(self.request.user.email, self.good_dict['email'])
        self.request.json_body = deepcopy(self.good_dict)
        result = user_id_put_view(self.request)['d']
        self.assertEqual(result, dict_from_row(self.request.user, remove_fields=removals))
        self.assertEqual(self.request.user.email, self.good_dict['email'])

    def test_bad_password_type(self):
        """
        If we pass in anything but a string, get an error indicating so
        """
        for val in [x for x in bad_data_typevals_list if not isinstance(x, basestring) and x is not None]:
            self.request.json_body = deepcopy(self.good_dict)
            self.request.json_body['password'] = val
            result = user_id_put_view(self.request)['d']
            self.assertEqual(result, error_dict('api_errors', 'password must be a string'))

    def test_invalid_password(self):
        """
        If we give a string of insufficient complexity, error
        """
        self.request.json_body = deepcopy(self.good_dict)
        invalids = ['5horT']
        for val in invalids:
            self.request.json_body['password'] = val
            result = user_id_put_view(self.request)['d']
            self.assertEqual(result, error_dict('api_errors', 'password must be at least 8 characters'))

    def test_valid_password(self):
        """
        When we match the appropriate guidelines, the password should be changed
        """
        newpass = 'Just Complex Enough'
        m = hashlib.sha512()
        m.update(newpass.encode('utf-8'))
        m.update(self.request.user.salt)
        hashed =  m.digest()
        self.request.json_body = deepcopy(self.good_dict)
        self.assertNotEqual(self.request.user.password, hashed)
        self.request.json_body['password'] = newpass
        result = user_id_put_view(self.request)['d']
        self.assertEqual(result, dict_from_row(self.request.user, remove_fields=removals))
        self.assertEqual(self.request.user.password, hashed)


