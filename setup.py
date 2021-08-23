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
    name='crspy',  # Required
    version='1.2.0',  # Required
    description='Toolbox for calibration and correction of Cosmic Ray Neutron Sensor data using globally available data sources',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    # url='',  # Optional
    author='Daniel Power',  # Optional
    author_email='daniel.power@bristol.ac.uk',  # Optional
    packages=find_packages(exclude=['example', 'data', 'docker']),  # Required
   # python_requires='==3.8',
    install_requires=[
        "numpy==1.21.2",
        "pandas==1.3.2",
        "matplotlib==3.4.3",
        "seaborn==0.11.2",
        "cdsapi==0.5.1",
        "xarray==0.19.0",
        "scipy==1.7.1",
        "netCDF4==1.5.7",
        "beautifulsoup4==4.9.3",
        "ipykernel==6.2.0"
    ],
)