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
def pressfact_L(press, L, p0):
    """ Calculates the pressure correction coefficient. Site pressure, raw MOD, 
    mass attenuation length (L) and reference pressure (p0).

    Values are provided 
    
    """
    return np.exp((press - p0)/L)


#Different form that is used with a B coefficient (Hawdon et al., 2014)

def pressfact_B(press, B, p0):
    return  np.exp(B*(press-p0))


####################################################################################
#                                Humidity                                          #
####################################################################################
def es(temp):
    """ Calculate saturation vapour pressure (hPA) using average temperature
    Can be used to calculate actual vapour pressure (hPA) if using dew point temperature"""
    return 6.112*np.exp((17.67*temp)/(243.5+temp))

def rh(t, td):
    """ Use temperature (C) and dewpoint temperature (C) to calculate relative humidity (%)
    """
    return 100*np.exp((17.625*243.04*(td-t))/((243.04+t)*(243.04+td)))

def ea(es, RH):
    """ Uses saturation vapour pressure (es) with relative humidity (RH) to 
    produce vapour pressure calculation"""
    return es * (RH/100)

def dew2vap(dt):
    """
    Provides actual vapour pressure (kPA). Taken from Shuttleworth (2012) Eq 2.21 rearranged
    """
    return np.exp((0.0707*dt-0.49299)/(1+0.00421*dt))
    
def pv(ea, temp):
    """ Works out absolute humidity using temperature (C) and vapour pressure unit (Pascals)"""
    return ea/(461.5*(temp+273.15))

def humfact(pv, pv0):
    """
    Gives the factorial to multiply Neutron counts by.
    """
    return (1+0.0054*(pv-pv0))

def modh(mod, pv, pv0):
    """ Gives the processed moderated neutron count. Takes in the neutron
    count, absolute humditiy and a reference point absolute humidity. This
    ref could be average for the site for example"""
    return mod * (1+0.0054*(pv-pv0))

####################################################################################
#                              Solar Intensity                                     #
####################################################################################
def si(mod, inten):
    """ Simply takes the neutron count and divides by inten coeff"""
    return mod/inten

def fsol(jung_ref, jung_count):
    return jung_ref / jung_count

def RcCorr(Rc):
    """
    Takes cutoff ridgity of site (Rc) and gives the RcCorr value required to 
    account for the difference to Jungfraujoch.
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
    """ Works out the effect of above ground biomass on neutron counts.
    agbval units are kg per m^2 of above ground biomass. Taken from Baatz et al
    (2015)
    """
    return 1/(1-(0.009*agbval))