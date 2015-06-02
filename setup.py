#!/usr/bin/python

from setuptools import setup, find_packages
from cct import version

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name = "cct",
    version = version.version,
    packages = find_packages(exclude=["tests"]),
    url = 'https://github.com/containers-tools/cct',
    download_url = "https://github.com/containers-tools/cct/archive/%s.tar.gz" % version.version,
    author = 'David Becvarik',
    description = 'Containers configuration tool',
    license='MIT',
    long_description = "",
    entry_points = {
        'console_scripts': ['cct=cct.cli.main:run'],
    },
    tests_require = ['mock', 'pytest', 'pytest-cov'],
    install_requires=requirements
)
