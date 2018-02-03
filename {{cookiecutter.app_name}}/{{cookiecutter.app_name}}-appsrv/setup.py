import os

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_requires = parse_requirements('requirements.txt', session=PipSession())

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
requires = [str(ir.req) for ir in install_requires]

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'readme.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

version = '0.0.1'

setup(name='{{cookiecutter.app_name}}Appsrv',
      version=version,
      description='{{cookiecutter.app_name}}Appsrv',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='{{cookiecutter.full_name}}',
      author_email='{{cookiecutter.email}}',
      url='{{cookiecutter.website}}',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = {{cookiecutter.app_name}}Appsrv:main
      [console_scripts]
      initialize_pyra_db = {{cookiecutter.app_name}}Appsrv.scripts.initializedb:main
      """,
      )
