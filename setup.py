# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 10:23:06 2020

@author: vq18508
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

from io import open

here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='SMOON',  # Required
    version='0.1.0',  # Required
    description='Toolbox for calibration and correction of Cosmic Ray Neutron Sensor data',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    url='www.thedanpower.com',  # Optional
    author='Daniel Power',  # Optional
    author_email='daniel.power@bristol.ac.uk',  # Optional
    packages=find_packages(exclude=['example', 'data']),  # Required
#    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    install_requires=[
        "numpy>=1.18.1",
        "pandas>=1.0.3",
        "matplotlib>=3.2.0",
        "seaborn>=0.10.0",
        "cdsapi>=0.2.7",
        "xarray>=0.15.1",
        "scipy>=1.3.1",
        "netCDF4>=1.5.3"		
    ],
)