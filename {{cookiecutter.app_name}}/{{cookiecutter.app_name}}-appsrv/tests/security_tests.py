# -*- coding: utf-8 -*-

from security import (
    get_user_from_token
)
from tests import MyTestBase, bad_data_typevals_list
from db.converters import dict_from_row


class SecurityTestBase(MyTestBase):
    """
    Helper for all basic security stuff
    """
    def setUp(self):
        MyTestBase.setUp(self)

    def tearDown(self):
        MyTestBase.tearDown(self)


class GetUserFromTokenTests(SecurityTestBase):
    """
    Tests for the get_user_from_token method
    """
    def test_bad_values(self):
        """
        When giving anything but a basestring, get the appopriate value_error
        """
        self.datautils.create_session()
        for i in [x for x in bad_data_typevals_list if not isinstance(x, basestring)]:
            with self.assertRaises(ValueError) as e:
                get_user_from_token(i, 'valid_token_type')
            self.assertEqual(e.exception.args[0], 'dbsession should be a valid db session')
            with self.assertRaises(ValueError) as e:
                get_user_from_token(self.session, i)
            self.assertEqual(e.exception.args[0], 'token must be a valid basestring')

    def test_nonexistent_token(self):
        """
        If the token doesn't exist, we should get None
        """
        self.datautils.create_session()
        result = get_user_from_token(self.session, 'invalid_token')
        self.assertEqual(result, None)

    def test_get_user(self):
        """
        When the token is valid, get the right user
        """
        user = self.datautils.create_user()
        sess = self.datautils.create_session({'user_id': user.id})
        result = get_user_from_token(self.session, sess.token)
        self.assertEqual(dict_from_row(user), dict_from_row(result))

