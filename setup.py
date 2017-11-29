import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

install_requires = [
    'hpfeeds',
    'greenlet',
    'gevent',
    'MySQL-python',
    'python-daemon',
]

dependancy_links = [
    '-e git+https://github.com/rep/evnet.git#egg=evnet-dev',
]

config = {
    'name':'artemis-storage',
    'description': 'A storage server for attachments received from the Artemis honeynet',
    'url':'https://github.com/WatchGuard-Threat-Lab/artemis-storage',
    'author':'Marc Laliberte',
    'version':'1.0.0',
    'install_requires': install_requires,
    'dependancy_links': dependancy_links,
    'license':'GPLv3',
}

setup(**config)
