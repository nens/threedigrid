#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from __future__ import absolute_import
from setuptools import setup, find_packages

import codecs
import re
import os

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

lightweight_requirements = [
    'numpy>=1.13',
    'h5py>=2.7.1',
]

results_requirements = [
    'cftime>=1.0.1'
]

# for extra 'geo'
geo_requirements = [
    'Click>=6.0',
    'mercantile>=1.0.1',
    'pyproj>=1.9.5.1',
    'Shapely>=1.6.4',
    'geojson>=2.3.0',
]

setup_requirements = []

test_requirements = ['pytest==3.4.1']

setup(
    author="Lars Claussen",
    author_email='lars.claussen@nelen-schuurmans.nl',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
    ],
    description="Python package for the threedigrid administration",
    entry_points={
        'console_scripts': [
            '3digrid_explore=threedigrid.management.commands.kick:kick_start',
            '3digrid_export=threedigrid.management.commands.kick:export_to',
        ],
    },
    install_requires=lightweight_requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='threedigrid',
    name='threedigrid',
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={
        'geo': geo_requirements,
        'results': results_requirements,
    },
    url='https://github.com/nens/threedigrid',
    version=find_version("threedigrid", "__init__.py"),
    zip_safe=False,
)
