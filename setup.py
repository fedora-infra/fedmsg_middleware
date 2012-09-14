from setuptools import setup, find_packages
import sys, os

f = open('README.rst')
long_description = f.read()
f.close()

version = '0.0.1'

setup(name='fedmsg_middleware',
      version=version,
      description="WSGI middleware for display fedmsg messages.",
      long_description=long_description,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
      ],
      author='Ralph Bean',
      author_email='rbean@redhat.com',
      url='http://github.com/ralphbean/fedmsg_middleware',
      license='LGPLv2+',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'webob',
          'weberror',
          'BeautifulSoup<4.0a1',
          'moksha.wsgi',
      ],
      entry_points="""
      [paste.filter_app_factory]
      middleware = fedmsg_middleware:make_middleware
      main = fedmsg_middleware:make_middleware
      """,
      )
