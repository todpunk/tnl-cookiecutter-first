# -*- coding: utf-8 -*-

from unittest import TestCase
from datetime import datetime
from pyramid import testing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from datautils import DataUtils

def get_type_array():
    """
    This is just an array of types that will be used for testing but probably needs to move somewhere else
    """
    return ['a',1,1.0,1.9999999999999999,[],{},(),object]

bad_data_typevals_list = [
    'string',
    u'unicode string',
    21,
    0,
    None,
    4.2,
    {},
    [],
    -8,
    ('', ''),
    object(),
    get_type_array,  # a function
    datetime.now(),
]

engine = None
Session = None


class MyTestBase(TestCase):
    """
    This should be the basis of all tests, with further overrides
    provided by child classes.  This should keep some basic functionality in
    mind and make test writing efficient
    """

    @classmethod
    def setUpClass(cls):
        global engine
        global Session
        dbport = '5432'
        dbname = '{{cookiecutter.testdbname}}'
        uri = 'postgresql+psycopg2://dbuser@127.0.0.1:%s/%s' % (dbport, dbname)
        cls.db_url = uri
        if engine is None:
            engine = create_engine(uri)
            Session = scoped_session(sessionmaker(bind=engine))
        cls.factory_sessions = Session
        cls.class_session = Session()

    @classmethod
    def tearDownClass(cls):
        cls.class_session.rollback()

    def setUp(self):
        # We want a per-test session within the class-wide session, like a layered burrito
        self.session = self.class_session
        self.session.begin_nested()
        self.datautils = DataUtils(self.session)

    def tearDown(self):
        self.session.rollback()

    def create_customer(self, extra_data=None):
        """
        Creates a customer for testing.
        """
        return self.datautils.create_user(extra_data)


class MyPyramidTestBase(MyTestBase):
    """
    Helper specifically for pyramid layer of testing, providing requests and sessions and
    all that is good in those worlds.
    Note that we do not create a user by default.
    """

    def setUp(self):
        MyTestBase.setUp(self)
        self.config = testing.setUp()
        self.config.include('pyramid_jinja2')
        self.request = testing.DummyRequest()
        self.request.dbsession = self.session

    def tearDown(self):
        testing.tearDown()
        MyTestBase.tearDown(self)

