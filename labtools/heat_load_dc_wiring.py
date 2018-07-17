#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 11:57:32 2017

@author: clint
"""

#use this code to estimate the heat load from copper wires of length l and 
#diameter D between a high temperature of Th and a low temp of Tc

# VERY THIN WIRES, FOR USE WITH THERMOMETRY

import numpy as np
import matplotlib.pyplot as plt

#copper wires
if 1:
    print '\n\nheat load for copper wires\n\n'
    l = 0.6 #meters
    D = 79e-6  #meters. http://www.cmr-direct.com/en/woven-loom/cmr-cwl-12cu-5m
    Th = 77.
    Tc = 4.
    nWires = 12.  #number of wires in the cable assembly
    
    #im not sure what the RRR is, so I'm going to use the highest RRR = 500 listed
    #to estimate the maximum heat load i would see with this wiring
    #http://cryogenics.nist.gov/MPropsMAY/OFHC%20Copper/OFHC_Copper_rev.htm
    
    if 1:
        #following coefficients good from 4 to 300 K. Cu, RRR = 500
        print 'using RRR = 500'
        a = 2.8075
        b = -0.54074
        c = -1.2777
        d = 0.15362
        e = 0.36444
        f = -0.02105
        g = -0.051727
        h = 0.0012226
        i = 0.0030964
    
    else:
        #following coefficients good from 4 to 300 K. Cu, RRR = 50
        print 'using RRR = 50'
        a = 1.8743
        b = -0.41538
        c = -0.6018
        d = 0.13294
        e = 0.26426
        f = -0.0219
        g = -0.051276
        h = 0.0014871
        i = 0.003723
    
    
    dT = .1
    T = np.arange(Tc,Th,dT)
    
    k = 10**((a + c*T**0.5 + e*T + g*T**1.5 + i*T**2)/(1 + b*T**0.5 + d*T + f*T**1.5 + h*T**2))
    
    plt.plot(T,k,'.-')
    plt.show()
    
    #now do a rough numerical integral of k from Tc to Th
    ksum = np.sum(k*dT)
    print(ksum)
    
    #compute the heat load
    A = np.pi*(D/2)**2 #cross-sectional area of 1 wire
    Q = nWires * A/l * ksum
    print('Q is ', Q, 'W')
    

#BeCu wires
if 1:
    print '\n\nBeCu wiring\n\n'
    l = 0.6 #meters
    D = 150e-6  #meters.
    Th = 77.
    Tc = 4.
    nWires = 36.  #number of wires in the cable assembly
    
    #im not sure what the RRR is, so I'm going to use the highest RRR = 500 listed
    #to estimate the maximum heat load i would see with this wiring
    #http://cryogenics.nist.gov/MPropsMAY/OFHC%20Copper/OFHC_Copper_rev.htm
    
    
    
    #following coefficients good from 2-80 K, Be Cu
    #http://cryogenics.nist.gov/MPropsMAY/Beryllium%20Copper/BerylliumCopper_rev.htm
    
    a = -0.50015
    b = 1.93190
    c = -1.69540
    d = 0.71218
    e = 1.27880
    f = -1.61450
    g = 0.68722
    h = -0.10501
    i = 0
    
    
    dT = .1
    T = np.arange(Tc,Th,dT)
    
    k = np.power(10,a + b*np.log10(T) + c*np.log10(T)**2 + d*np.log10(T)**3 + e*np.log10(T)**4 + f*np.log10(T)**5 + g*np.log10(T)**6 + h*np.log10(T)**7 + i*np.log10(T)**8)
    
    plt.plot(T,k,'.-')
    plt.show()
    
    #now do a rough numerical integral of k from Tc to Th
    ksum = np.sum(k*dT)
    print(ksum)
    
    #compute the heat load
    A = np.pi*(D/2)**2 #cross-sectional area of 1 wire
    Q = nWires * A/l * ksum
    print 'Q is ', Q, 'W'
    
    
