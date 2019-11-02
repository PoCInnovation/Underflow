#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 11:52:15 2019

@author: slo
"""

from setuptools import setup, find_packages


__version__ = "1.1.2"

try:
    # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:
    # for pip <= 9.0.3
    from pip.req import parse_requirements

def load_requirements(fname):
    reqs = parse_requirements(fname, session="test")
    return [str(ir.req) for ir in reqs]

setup(
      name='regularflow',
      install_requires=load_requirements("./requirements.txt"),
      version=__version__,
      packages=find_packages(),
      author=" Roloman (slohan SAINTE-CROIX) ",
      author_email="None",
      description="API for regulate circulation",
      long_description=open('README.md').read(),
      include_package_data=True,
      url="https://gitlab.com/_Rollo/regularflow",
      )
