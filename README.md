# Cosmic-Ray Sensor PYthon tool (crspy)
This tool can process Cosmic Ray Sensor data into soil moisture estimates. It is based on research conducted by many individuals and groups (see references). It is part of a PhD project by Daniel Power funded by the Water Informatics, Science and Engineering (WISE CDT) at the University of Bristol - ESPRC Funding EP/L016214/1

Please note: this is a work in progress that is being updated regularly, so bugs or issues may be found. If you have any issues with crspy please do get in touch daniel.power@bristol.ac.uk

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Motivation
Cosmic-Ray Neutron Sensors measure fast neutrons, which after corrections and calibration, can be used to estimate field scale soil moisture. Sensors are located around the world and have been used for upwards of ten years giving a valuable source of information for hydrologists and beyond. Important improvements have been discovered in that time but may not have been implemented on historical data. This tool is designed to allow changes in processing and calibration to be easily implemented on data from around the globe, giving a uniform method in processing soil moisture estimates. This will allow effective analysis for Hydrological applications. 

# **Contents**

[**About**](https://github.com/danpower101/crspy/wiki/About)

A broad description of the tool and why it was written.

[**Getting Started**](https://github.com/danpower101/crspy/wiki/Getting-Started)

Begin here for a description of how to download and install crspy, as well as how to prepare your working directory.

[**Example Workflow**](https://github.com/danpower101/crspy/wiki/Example-Workflow)

The example workflow will walk through how to run this package using the provided examples. The links below provide specific guidance on each step.

### **Preliminary Steps**

Before processing data it is required to prepare your working environment. This includes signing up to global data products, saving some settings on your computer to allow easy access to these products and downloading some datasets to your working directory. These are all described below in separate mini walkthroughs. They should be tackled in the order presented to avoid issues:

1. [**Metadata**](https://github.com/danpower101/crspy/wiki/Metadata)
2. [**Meteorological Data (ERA5-Land)**](https://github.com/danpower101/crspy/wiki/ERA5-Land-Data)
3. [**Land Cover Data (ESA CCI)**](https://github.com/danpower101/crspy/wiki/Land-Cover-Data)
4. [**Above Ground Biomass Data (ESA CCI)**](https://github.com/danpower101/crspy/wiki/Above-Ground-Biomass-Data)
5. [**Fill metadata table**](https://github.com/danpower101/crspy/wiki/Fill-metadata-table)
6. [**Raw Timeseries Data**](https://github.com/danpower101/crspy/wiki/Raw-Timeseries-Data)
7. [**Calibration Data**](https://github.com/danpower101/crspy/wiki/Calibration-Data)



### **Processing the Data**

Once the preliminary steps have been completed the timeseries data can be processed

[**Processing Data**](https://github.com/danpower101/crspy/wiki/Processing-the-data) 



#### **What does it do?**

There are a lot of steps involved in the processing of neutron data to give us our outputs. A high level description has been provided to demonstrate what steps have been taken without having to look into the code. 

[**High level process description**](https://github.com/danpower101/crspy/wiki/High-level-process-description)



#### **What are the outputs?**

When setting up your working directory the folder structure is written out for you. Below are descriptions of these folders as well as descriptions of the outputs that will be written during the processing steps.

[**Description of folders**](tbc)

[**Description of outputs**](https://github.com/danpower101/crspy/wiki/Outputs)



### **Additional Information**

[**References**](https://github.com/danpower101/crspy/wiki/References)

## License
MIT License
MIT © [D. Power](2020)


<p align="center"> <img width=20% src="https://github.com/danpower101/The_CRNS_Process/blob/master/Images/University_of_Bristol_logo.png">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img width=20% src="https://github.com/danpower101/The_CRNS_Process/blob/master/Images/WISECDTlogo.png">
