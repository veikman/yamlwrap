# -*- coding: utf-8 -*-

import os
from setuptools import setup

# Allow setup.py to be run from any path.
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(name='vedm',
      version='0.5.1',
      author='Viktor Eikman',
      author_email='viktor@eikman.se',
      description='Reusable Django miscellania',
      url='viktor.eikman.se',
      packages=['vedm', 'vedm.management', 'vedm.management.commands', 'vedm.migrations', 'vedm.util'],
      include_package_data=True,
      )

