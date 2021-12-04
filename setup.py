#!/usr/bin/env python

import sys
from os import path

from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


install_requires = [
    "Django>=3.0"
]

# Require python 3.8
if sys.version_info.major != 3 and sys.version_info.minor < 8:
    sys.exit("'asgimod' requires Python >= 3.8")

setup(
    name="asgimod",
    version="0.1.1",
    author="Paaksing",
    author_email="paaksingtech@gmail.com",
    url="https://github.com/paaksing/asgimod",
    description="Package to make Django *usable* in async Python",
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=["Django", "asyncio", "async"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.8",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: English",
        "Framework :: Django :: 3.0",
    ],
    license="MIT",
    packages=find_packages(exclude=("testapp", "testproj")),
    zip_safe=True,
    install_requires=install_requires,
    include_package_data=True,
)
