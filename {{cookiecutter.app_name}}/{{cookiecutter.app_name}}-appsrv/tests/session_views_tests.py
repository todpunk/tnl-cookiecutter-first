# -*- coding: utf-8 -*-

from datetime import datetime

from dateutil.relativedelta import relativedelta

from pjAppsrv.tests import PJPyramidTestBase
from pjAppsrv.views.session_views import (
    sessions_post_view,
    sessions_delete_view, sessions_put_view)
from pjDb import Session
from pjDb.converters import dict_from_row
from pjLib.utilities import error_dict


class SessionViewsTestBase(PJPyramidTestBase):
    """
    Helper for all session view stuffs
    """
    def setUp(self):
        PJPyramidTestBase.setUp(self)
        self.request.user = None

    def tearDown(self):
        PJPyramidTestBase.tearDown(self)


class SessionsPostViewsTest(SessionViewsTestBase):
    """
    Tests for the sessions post view
    """
    def test_already_logged_in(self):
        """
        If we try to start a session while we're already logged in, get the token we used
        """
        self.request.user = self.datautils.create_user()
        oursession = self.datautils.create_session({'user_id': self.request.user.id})
        self.request.json_body = {'token': oursession.token}
        result = sessions_post_view(self.request)['d']
        self.assertEqual(result, dict_from_row(oursession))

    def test_no_username(self):
        """
        When we don't give a username, we get an error back about not having a username
        """
        self.request.json_body = {'foo': 'a'}
        result = sessions_post_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid username provided'))

    def test_no_password(self):
        """
        When we don't give a password, we get an error back about not having a password
        """
        self.request.json_body = {'username': 'a'}
        result = sessions_post_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid password provided'))

    def test_bad_credentials(self):
        """
        With a properly formed request, but with bad values (like an incorrect password), get the appropriate error
        """
        self.request.json_body = {'username': 'testuser', 'password': 'badpass'}
        self.datautils.create_user({'username': 'testuser'})
        result = sessions_post_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid username provided'))

    def test_nonexistent_user(self):
        """
        With a properly formed request, but with a nonexistent user, get the appropriate error
        """
        self.request.json_body = {'username': 'testuser', 'password': 'testpass'}
        result = sessions_post_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'no valid username provided'))

    def test_locked_account(self):
        """
        Get the lock message if the account is locked, but we get the credentials right, get the lock message
        """
        self.request.json_body = {'username': 'testuser', 'password': 'testpass'}
        self.datautils.create_user({'username': 'testuser', 'password': 'testpass', 'lockmessage': 'test lock message'})
        result = sessions_post_view(self.request)['d']
        self.assertEqual(result, error_dict('account_lock', 'test lock message'))

    def test_return_token(self):
        """
        The happy path should return the token object
        """
        self.request.json_body = {'username': 'testuser', 'password': 'testpass', 'origin': 'testorigin'}
        self.request.user = self.datautils.create_user(self.request.json_body)
        c_id = self.request.user.id
        result = sessions_post_view(self.request)['d']
        self.session.flush()
        self.assertEqual(self.session.query(Session).count(), 1)
        s = self.session.query(Session).filter(Session.user_id == c_id).one_or_none()
        self.assertIsNotNone(s)
        s = dict_from_row(s)
        s['origin'] = 'testorigin'
        self.assertEqual(result, s)


class SessionsDeleteViewsTest(SessionViewsTestBase):
    """
    Tests for the sessions delete view
    """
    def setUp(self):
        SessionViewsTestBase.setUp(self)
        self.request.user = self.datautils.create_user()

    def test_no_user(self):
        """
        If we try to get info without a login, get an error back
        """
        self.request.user = None
        result = sessions_delete_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'not authenticated for this request'))

    def test_no_token_provided(self):
        """
        If we do not provide a token, get an error
        """
        self.request.json_body = {}
        self.datautils.create_user({'username': 'testuser', 'password': 'testpass'})
        result = sessions_delete_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid token provided'))

    def test_nonexistent_token_provided(self):
        """
        If the token doesn't exist, say so
        """
        self.request.json_body = {'token': 'badtoken'}
        self.datautils.create_session()
        self.datautils.create_session()
        result = sessions_delete_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid token provided'))

    def test_non_our_token_provided(self):
        """
        If the token exists but isn't ours, say so
        """
        self.request.json_body = {'token': 'badtoken'}
        self.datautils.create_session()
        self.datautils.create_session()
        result = sessions_delete_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid token provided'))

    def test_good_token(self):
        """
        If the token is valid, return {} and the token should be deleted
        """
        s = self.datautils.create_session()
        self.assertEqual(self.session.query(Session).filter(Session.id == s.id).count(), 1)
        self.request.json_body = {'token': s.token}
        result = sessions_delete_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})
        self.assertEqual(self.session.query(Session).filter(Session.id == s.id).count(), 0)


class SessionsPutViewsTest(SessionViewsTestBase):
    """
    Tests for the sessions put view
    """
    def setUp(self):
        SessionViewsTestBase.setUp(self)
        self.request.user = self.datautils.create_user()

    def test_no_user(self):
        """
        If we try to get info without a login, get an error back
        """
        self.request.user = None
        result = sessions_put_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'not authenticated for this request'))

    def test_expired_token_provided(self):
        """
        If the token is expired, say so, and delete it
        """
        weeks_ago = datetime.now() - relativedelta(weeks=6)
        s = self.datautils.create_session({
            'lastactive': weeks_ago,
            'started': weeks_ago,
            'user_id': self.request.user.id})
        self.assertEqual(self.session.query(Session).count(), 1)
        self.assertEqual(s.started, s.lastactive)
        self.assertEqual(s.started, weeks_ago)
        self.request.json_body = {'token': s.token}
        result = sessions_put_view(self.request)['d']
        self.assertEqual(result, error_dict('api_errors', 'no valid token provided'))
        self.assertEqual(self.session.query(Session).count(), 0)

    def test_nonexistent_token_provided(self):
        """
        If the token doesn't exist, say so
        """
        self.request.json_body = {'token': 'badtoken'}
        self.datautils.create_session()
        self.datautils.create_session()
        result = sessions_put_view(self.request)['d']
        self.assertIsInstance(result, dict)
        self.assertEqual(result, error_dict('api_errors', 'no valid token provided'))

    def test_good_token(self):
        """
        If the token is valid, return the token and we the timestamp is updated
        """
        days_ago = datetime.now() - relativedelta(days=4)
        self.request.user.origin = 'testorigin'
        s = self.datautils.create_session({
            'lastactive': days_ago,
            'started': days_ago,
            'user_id': self.request.user.id})
        self.assertEqual(self.session.query(Session).count(), 1)
        self.assertEqual(s.started, s.lastactive)
        self.request.json_body = {'token': s.token}
        result = sessions_put_view(self.request)['d']
        self.session.flush()
        self.session.refresh(s)
        self.assertIsInstance(result, dict)
        s_dict = dict_from_row(s)
        s_dict['origin'] = 'testorigin'
        self.assertEqual(result, s_dict)
        self.assertNotEqual(s.started, s.lastactive)
        self.assertTrue(s.lastactive > datetime.now() - relativedelta(hours=1))

