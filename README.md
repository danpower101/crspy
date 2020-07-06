## Cosmic-Ray Sensor PYthon tool (crspy)
This tool can process Cosmic Ray Neutron Sensor data into soil moisture estimates. It is based on research conducted by many individuals and groups (see references). It is part of a PhD project at Bristol University by Daniel Power. 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Motivation
Cosmic-Ray Neutron Sensors measure fast neutrons, which after corrections and calibration, can be used to estimate field scale soil moisture. Sensors are located around the world and have been used for upwards of ten years giving a valuable source of information for hydrologists and beyond. Important improvements have been discovered in that time but may not have been implemented on historical data. This tool is designed to allow changes in processing and calibration to be easily implemented on data from around the globe, giving a uniform method in processing soil moisture estimates. This will allow effective analysis for Hydrological applications. 

## Features
The main features are general tidying, calibration and processing of CRNS data. Improvements will include automatic figures. 

- Tidy formatting of data
- Calibration with the new methodology of Schrön et al., (2017)
- Correction for Pressure (including mass attenuation length calc), Humidity, Solar intenisty and Above Ground Biomass.
- Quality Analysis module that allows users to identify issues with the data
- Output of hourly soil moisture estimates along with estimated error, running mean and savitsky-golay filtered means. 
- (WIP) Informative figures and analysis. 

## Code Example
(Coming Soon)

## Screenshots
(Coming Soon) Include logo/demo screenshot etc. 

## Installation
(Coming Soon)

## API Reference
(Coming Soon)

## Tests
(Coming Soon)

## How to use?
(Coming Soon)

## References and Credits
(Coming Soon - include all academic papers and people involved)



## License
MIT License
MIT © [D. Power](2020)


<p align="center"> <img width=20% src="https://github.com/danpower101/The_CRNS_Process/blob/master/Images/University_of_Bristol_logo.png">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img width=20% src="https://github.com/danpower101/The_CRNS_Process/blob/master/Images/WISECDTlogo.png">

