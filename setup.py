#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'numpy>=1.13',
    'h5py>=2.7.1',
    'mercantile>=1.0.1',
    'pyproj>=1.9.5.1',
    'Shapely>=1.6.4',
    'geojson>=2.3.0'
]

setup_requirements = []

test_requirements = ['pytest==3.4.1', ]

setup(
    author="Lars Claussen",
    author_email='lars.claussen@nelen-schuurmans.nl',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    description="Python package for the threedigrid administration",
    entry_points={
        'console_scripts': [
            'threedigrid=threedigrid.cli:main',
        ],
    },
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='threedigrid',
    name='threedigrid',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/nens/threedigrid',
    version='0.1.1.dev0',
    zip_safe=False,
)
