"""
Author: Daniel Power - University of Bristol
Email: daniel.power@bristol.ac.uk

These functions will calculate correction coefficients for raw fast neutron data. Below are the
references for each calculation. 

It will include corrections for:

-Pressure
-Humidity:
    Rosolem et al.(2013)
-Solar Intensity:

-Above ground biomass:
    Baatz et al., (2015)
"""
# Required packages
import numpy as np

####################################################################################
#                                Pressure                                          #
####################################################################################
# Different form that is used with a B coefficient (Hawdon et al., 2014)


def pressfact_B(press, B, p0):
    """pressfact_B corrects neutrons for pressure changes

    Parameters
    ----------
    press : float
        pressure (mb)
    B : float
        beta coefficient e.g. 0.007
    p0 : int
        reference pressure (mb)

    Returns
    -------
    float
        number to multiply neutron counts by to correct
    """
    return np.exp(B*(press-p0))


####################################################################################
#                                Humidity                                          #
####################################################################################
def es(temp):
    """es Calculate saturation vapour pressure (hPA) using average temperature
    Can be used to calculate actual vapour pressure (hPA) if using dew point temperature    

    Parameters
    ----------
    temp : float  
        temperature (C)

    Returns
    -------
    float 
        saturation vapour pressure (hPA) 
    """
    return 6.112*np.exp((17.67*temp)/(243.5+temp))


def rh(t, td):
    """rh Use temperature (C) and dewpoint temperature (C) to calculate relative humidity (%)

    Parameters
    ----------
    t : float   
        temperature (C)
    td : float
        dewpoint temperature (C)

    Returns
    -------
    float
        relative humidity (%)
    """
    return 100*np.exp((17.625*243.04*(td-t))/((243.04+t)*(243.04+td)))


def ea(es, RH):
    """ea Uses saturation vapour pressure (es - converted to Pascals) with relative humidity (RH) to 
    produce actual vapour pressure (Pascals)

    Parameters
    ----------
    es : float
        saturation vapour pressure (Pascal)
    RH : float
        relative humidity (%)

    Returns
    -------
    float
        actual vapour pressure (Pascals)
    """
    return es * (RH/100)


def dew2vap(dt):
    """dew2vap  gives vapour pressure (kPA). Taken from Shuttleworth (2012) Eq 2.21 rearranged

    Parameters
    ----------
    dt : float 
        dewpoint temperature (C)

    Returns
    -------
    float
        vapour pressure (kPA)
    """
    return np.exp((0.0707*dt-0.49299)/(1+0.00421*dt))


def pv(ea, temp):
    """pv works out absolute humidity using temperature (C) and vapour pressure unit (Pascals)

    Parameters
    ----------
    ea : float  
        Vapour Presure (Pascals)
    temp : float
        temperature (C)

    Returns
    -------
    float
        absolute humidity (ouput as kg/m^3)
    """
    return ea/(461.5*(temp+273.15))


def humfact(pv, pv0):
    """humfact gives the factorial to multiply Neutron counts by

    Parameters
    ----------
    pv : float 
        absolute humidity
    pv0 : float
        reference absolute humidity

    Returns
    -------
    float
        factor to multiply neutrons by
    """
    return (1+0.0054*(pv-pv0))


def modh(mod, pv, pv0):
    """modh gives the neutron count once corrected for humidity

    Parameters
    ----------
    mod : int
        neutron count
    pv : float
        absolute humidity
    pv0 : float
        reference absolute humidity

    """
    return mod * (1+0.0054*(pv-pv0))

####################################################################################
#                              Incoming Cosmic-Ray Intensity                       #
####################################################################################


def si(mod, inten):
    """ Simply takes the neutron count and divides by inten coeff"""
    return mod/inten


def finten(jung_ref, jung_count):
    """finten correction for incoming neutron intensity

    Parameters
    ----------
    jung_ref : float
        reference neutron count at JUNG (usually 01/05/2011)
    jung_count : float
        count at time[0]

    """
    return jung_ref / jung_count


def RcCorr(Rc):
    """RcCorr takes cutoff ridgity of site (Rc) and gives the RcCorr value required to 
    account for the difference to Jungfraujoch.

    Parameters
    ----------
    Rc : float
        cutoff ridgidity of site

    """
    return -0.075*(Rc-4.49)+1


####################################################################################
#                            Above Ground Biomass                                  #
####################################################################################
"""

This adjusts the neutrons for above ground biomass. It is using the
formula from Baatz et al., (2015). 

Tian et al (2016) uses mod and unmod and also has a list of AGB methods -
need to review and consider...

Need to consider data availability world wide. 

agb = Above Ground Biomass (kg dry above ground biomass per m^2)
Citations:
    
    Baatz, R., H. R. Bogena, H.-J. Hendricks Franssen, J. A. Huisman, C. Montzka, 
    and H. Vereecken (2015), 
    An empirical vegetation correction for soil water content quantification using 
    cosmic ray probes, Water Resour. Res., 51, 2030–2046, doi:10.1002/ 2014WR016443.
    
"""


def agb(agbval):
    """agb Works out the effect of above ground biomass on neutron counts.
    agbval units are kg per m^2 of above ground biomass. Taken from Baatz et al
    (2015)

    Parameters
    ----------
    agbval : float
        above ground biomass value (kg/m2)

    """
    return 1/(1-(0.009*agbval))
