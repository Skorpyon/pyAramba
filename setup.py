# -*- coding: utf-8 -*-
# !/usr/bin/env python

from distutils.core import setup

setup(
    name='pyAramba',
    version='0.1',
    description='API wrapper for Aramba SMS gateway <http://www.aramba.ru>',
    author='Anton Trishenkov',
    author_email='anton.trishenkov@gmail.com',
    license='LICENSE.txt',
    url='http://git.astracode.ru/astracode/pyAramba.git',
    long_description=open('README.md').read(),
    packages=['pyAramba', ],
)