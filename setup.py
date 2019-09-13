#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 11:52:15 2019

@author: slo
"""

from setuptools import setup, find_packages

import regularflow

setup(
      name='regularflow',
      version=regularflow.__version__,
      packages=find_packages(),
      author="_Rollo (slohan SAINTE-CROIX)",
      author_email="None",
      description="API for regulate circulation",
      long_description=open('README.md').read(),
      include_package_data=True,
      url="https://gitlab.com/_Rollo/regularflow",
      )