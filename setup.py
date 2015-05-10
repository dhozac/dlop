#!/usr/bin/python -tt

from setuptools import setup

setup(
    name = 'dlop',
    version = '0.1',
    author = 'Daniel Hokka Zakrisson',
    author_email = 'daniel@hozac.com',
    license = "GPL",
    packages = ['dlop'],
    test_suite = 'dlop.tests',
    entry_points = {
        'console_scripts': [
            'dlop = dlop.ui:main',
        ],
    },
    install_requires = [
        "pyperclip",
    ],
)
