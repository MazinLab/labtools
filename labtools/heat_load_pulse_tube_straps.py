#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 11:57:32 2017

@author: clint
"""

#use this code to estimate the heat load from copper wires of length l and 
#diameter D between a high temperature of Th and a low temp of Tc

#VERY THICK WIRES, FOR PULSE TUBE HEAT SINKS IN PICTURE-C

import numpy as np
import matplotlib.pyplot as plt
import sys


l = 1.25*25.4/1000 #meters
D = .005  #meters. http://www.cmr-direct.com/en/woven-loom/cmr-cwl-12cu-5m
Th = 77.1
Tc = 77.
if (Th-Tc)<=0:
    print('\n\ncheck Th and Tc!\n\n')
    sys.exit()
nWires = 14.  #number of wires in the cable assembly
nPoints = 100  #number of temperature points to estimate the integral. 

#im not sure what the RRR is, so I'm going to use the highest RRR = 500 listed
#to estimate the maximum heat load i would see with this wiring
#http://cryogenics.nist.gov/MPropsMAY/OFHC%20Copper/OFHC_Copper_rev.htm

if 0:
    #following coefficients are valid from 4 to 300 K. RRR = 500
    a = 2.8075
    b = -0.54074
    c = -1.2777
    d = 0.15362
    e = 0.36444
    f = -0.02105
    g = -0.051727
    h = 0.0012226
    i = 0.0030964

if 1:
    #following coefficients are valid from 4 to 300 K. RRR = 100
    a = 2.2154
    b = -0.47461
    c = -0.88068
    d = 0.13871
    e = 0.29505
    f = -0.02043
    g = -0.04831
    h = 0.001281
    i = 0.003207

dT = (Th-Tc)/(nPoints-1)
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