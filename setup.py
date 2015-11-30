#!/usr/bin/python

from setuptools import setup, find_packages
from cct import version
import os

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

d = 'cct/modules'
data_files = []
modules = filter(lambda x: os.path.isdir(os.path.join(d, x)), os.listdir(d))
for module in modules:
    path = 'cct/modules/%s/data' %module
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for f in files:
                data_files.append(os.path.join(root, f)[4:])

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
    install_requires = requirements,
    package_data = {'' : data_files}
)
