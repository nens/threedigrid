#!/usr/bin/env python

"""The setup script."""


import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

lightweight_requirements = [
    "numpy>=1.15",
    "h5py>=2.9",
    "six",
]

results_requirements = ["cftime>=1.0.1"]

# for extra 'geo'
geo_requirements = [
    "Click>=6.0",
    "mercantile>=1.0.4",
    "pyproj>=2.2",
    "Shapely>=1.6",
    "geojson>=2.4",
]

rpc_requirements = [
    "asyncio-rpc>=0.1.10",
]

setup_requirements = []

test_requirements = ["pytest==3.4.1"]

docs_requirements = [
    "sphinx~=7.2.6",
    "sphinx_rtd_theme>=2.0.0",
]

setup(
    author="Lars Claussen",
    author_email="info@nelen-schuurmans.nl",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
    ],
    description="Python package for the threedigrid administration",
    entry_points={
        "console_scripts": [
            "3digrid_explore=threedigrid.management.commands.kick:kick_start",
            "3digrid_export=threedigrid.management.commands.kick:export_to",
        ],
    },
    install_requires=lightweight_requirements,
    python_requires=">=3.8",
    license="BSD license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="threedigrid",
    name="threedigrid",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    extras_require={
        "geo": geo_requirements,
        "results": results_requirements,
        "rpc": rpc_requirements,
        "docs": docs_requirements,
    },
    url="https://github.com/nens/threedigrid",
    version=find_version("threedigrid", "__init__.py"),
    zip_safe=False,
)
