# -*- coding: utf-8 -*-
"""Application packaging."""

import os
from setuptools import setup
import yamldoc as subject

# Allow setup.py to be run from any path.
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(name=subject.__name__,
      version=subject.__version__,
      author='Viktor Eikman',
      author_email='viktor@eikman.se',
      description='Reusable Django miscellania',
      url='http://viktor.eikman.se',
      packages=['yamldoc', 'yamldoc.management', 'yamldoc.management.commands',
                'yamldoc.migrations', 'yamldoc.util'],
      install_requires=['markdown', 'Ovid', 'PyYaml', 'pyaml', 'unidecode'],
      include_package_data=True,
      )
