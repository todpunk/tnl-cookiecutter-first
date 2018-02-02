# -*- coding: utf-8 -*-

#The following was implemented following the suggestion found in the following
#url:
#http://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/database/sqlalchemy.html#importing-all-sqlalchemy-models
#import customer

import zope.sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, sessionmaker, configure_mappers
from sqlalchemy.schema import MetaData
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import (
    engine_from_config,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    BigInteger,
    LargeBinary,
    String,
    Text,
    TIMESTAMP,
    Table)

# Recommended naming convention used by Alembic, as various different database
# providers will autogenerate vastly different names making migrations more
# difficult. See: http://alembic.readthedocs.org/en/latest/naming.html
# NAMING_CONVENTION = {
#     "ix": 'ix_%(column_0_label)s',
#     "uq": "uq_%(table_name)s_%(column_0_name)s",
#     "ck": "ck_%(table_name)s_%(constraint_name)s",
#     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
#     "pk": "pk_%(table_name)s"
# }

# old version with schema
# metadata = MetaData(naming_convention=NAMING_CONVENTION, schema='pj')
# We might need to think about the naming conventions since sqlalchemy isn't generating this
#metadata = MetaData(naming_convention=NAMING_CONVENTION)
metadata = MetaData()
Base = declarative_base(metadata=metadata)


class MyBase(Base):
    """
    Class to provide a layer to accommodate specific methods we wanted to add.
    """

    # This permits us to extend Base.
    __abstract__ = True
    
    def _to_dict(self):
        """
        This method creates a dictionary representation of the mapped class.
        The dictionary includes all of the table columns and only the table
        columns.  This creates a copy of the self.__dict__ because deleting
        the _sa_instance_state eliminates that column from the __dict__ if
        a copy is not created.
        """
        return {x: y for x, y in self.__dict__.items() if not x.startswith('_')}


class User(MyBase):
    """
    A user of the system
    """
    
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)
    email = Column(String(254), nullable=False)
    password = Column(String(254), nullable=False)
    salt = Column(String(254), nullable=False)
    created = Column(DateTime, nullable=False, server_default='current_timestamp')
    origin = Column(Text)


class Session(MyBase):
    """
    Sessions are the logins of a particular user. The token authorizes them for a time.
    """
    
    __tablename__ = 'sessions'
    # __table_args__ = {u'schema': 'pj'}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    started = Column(TIMESTAMP, nullable=False, server_default='current_timestamp')
    lastactive = Column(TIMESTAMP, nullable=False, server_default='current_timestamp')
    token = Column(Text, nullable=False)


# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
configure_mappers()


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
    """
    Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)

    :param transaction_manager: The transaction manager you want to be used with sqlalchemy
    :param session_factory: the session factory we're instantiating

    """
    dbsession = session_factory()
    zope.sqlalchemy.register(
        dbsession, transaction_manager=transaction_manager)
    return dbsession


def includeme(config):
    """
    Initialize the model for a Pyramid app.

    Activate this setup using ``config.include('{{project}}.models')``.
    :param config: a pyramid config
    """
    settings = config.get_settings()

    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')

    session_factory = get_session_factory(get_engine(settings))
    config.registry['dbsession_factory'] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )

