# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 11:56:24 2020

@author: Daniel Power

This function was provided by Darin Desilets (HydroInnova) and adapted for use in SMOON.


Reference Pressure Calc (x0) from:
    Engineering ToolBox, (2003). Altitude above Sea Level and Air Pressure. [online] 
    Available at: https://www.engineeringtoolbox.com/air-altitude-pressure-d_462.html [Accessed 24/04/2020]. 
"""
import numpy as np

def betacoeff(p, lat, elev, r_c):
    """
    This will calculate the beta coefficient for each site. 
    
    Parameters:
        p = site average pressure (mb)
        lat = latitude (degrees)
        elev = site elevation (m)
        r_c = cutoff ridgitity (gv)
    """

    # --- elevation scaling ---
    
    # --- Gravity correction ---
    
    # constants
    rho_rck = 2670
    x0 = (101325*(1-2.25577*(10**-5)*elev)**5.25588)/100 # output in mb
    
    # variables
    z = -0.00000448211*p**3 + 0.0160234*p**2 - 27.0977*p+15666.1  
    
    # latitude correction
    g_lat = 978032.7*(1 + 0.0053024*(np.sin(np.radians(lat))**2)-0.0000058*(np.sin(np.radians(2*lat)))**2) 
    
    # free air correction
    del_free_air=-0.3087691*z
    
    # Bouguer correction
    del_boug=rho_rck*z*0.00004193
    
    g_corr = (g_lat + del_free_air + del_boug)/100000    
    
    # final gravity and depth
    g = g_corr/10
    x = p/g
    
    # --- elevation scaling ---
    
    # parameters
    n_1 = 0.01231386
    alpha_1 = 0.0554611
    k_1 = 0.6012159
    b0 = 4.74235E-06
    b1 = -9.66624E-07
    b2 = 1.42783E-09
    b3 = -3.70478E-09
    b4 = 1.27739E-09
    b5 = 3.58814E-11
    b6 = -3.146E-15
    b7 = -3.5528E-13
    b8 = -4.29191E-14
    
    
    # calculations
    term1 = n_1*(1+np.exp(-alpha_1*r_c**k_1))**-1*(x-x0)
    term2 = 0.5*(b0+b1*r_c+b2*r_c**2)*(x**2-x0**2)
    term3 = 0.3333*(b3+b4*r_c+b5*r_c**2)*(x**3-x0**3)
    term4 = 0.25*(b6+b7*r_c+b8*r_c**2)*(x**4-x0**4)
    
    beta = abs((term1 + term2 + term3 + term4)/(x0-x))
    
    return beta, x0
    
    
    """
    # --- latitude scaling ---
    
    # parameters
    alpha_lat = 9.694
    k_lat = 0.9954
    
    #calculation
    f_lat = 1/(1-np.exp(-alpha_lat*r_c**(-k_lat)))
    
    
    f_bar = np.exp((x0-x)*beta)
    
    F_scale = f_lat * f_bar
    """
