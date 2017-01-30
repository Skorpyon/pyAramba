# -*- coding: utf-8 -*-
# !/usr/bin/env python

from setuptools import setup

setup(
    name='pyAramba',
    version='0.1',
    description='API wrapper for Aramba SMS gateway <http://www.aramba.ru>',
    author='Anton Trishenkov',
    author_email='anton.trishenkov@gmail.com',
    license='LICENSE.txt',
    url='http://git.astracode.ru/astracode/pyAramba.git',
    long_description=open('README.md', encoding='utf-8').read(),
    packages=['pyAramba', ],
    install_requires=[
              'requests >= 2.11',
          ],
    classifiers=[
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Development Status :: 3 - Alpha',
          'Topic :: Utilities',
          'Programming Language :: Python :: 3',
        ],
)