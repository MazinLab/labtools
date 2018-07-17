#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 18 14:25:26 2018

@author: clint


Use this code to estimate heat loads from stainless steel (316LN) between 
45mK and 4.3K

FOR USE WITH PICTURE-C

COURE paper:
https://www.sciencedirect.com/science/article/pii/S0011227508000428?via%3Dihub

coax-co information:
http://www.coax.co.jp/en/wcaxp/wp-content/themes/coax/pdf/General%20Catalogue%202018-2-5.pdf

"""
import numpy as np
import matplotlib.pyplot as plt
import sys


l = .1 #meters

Th = 4.5
Tc = .1
if (Th-Tc)<=0:
    print('\n\ncheck Th and Tc!\n\n')
    sys.exit()
nWires = 1.  #number of wires in the cable assembly
nPoints = 100  #number of temperature points to estimate the integral. 

#cross sectional areas
#   SC-033/50-SS-SS
#   0.33 mm diameter stainless coax
# 
#   stainless cross-sectional area = 8.87e-9 m^2
#   PFA cross-sectional area = 2.54e-8 m^2

a1 = 1.39e-8   #m^2

dT = (Th-Tc)/(nPoints-1)
T = np.arange(Tc,Th,dT)

k = 0.0556 * T**1.15   #W/m/K

#plt.plot(T,k,'.-')
#plt.show()

#now do a rough numerical integral of k from Tc to Th
ksum = np.sum(k*dT)
print(ksum)

#compute the heat load
Q = nWires * a1/l * ksum
print('Q is ', Q, 'W')


#calculate the conductance to compare with flex cable paper
G = a1*k*1e8   #uW*cm/K   converting W to uW and m to cm gives factor of 10^8
#plt.plot(T,G,'.')
plt.loglog(T,G,'.')
#plt.axis('square')
#plt.tight_layout()
plt.gcf().subplots_adjust(left=0.15)
plt.xlabel('temperature [K]')
plt.ylabel(r'G*length [$\mu$W*cm/K]')
plt.title('conductance of 316 stainless')
plt.show()

