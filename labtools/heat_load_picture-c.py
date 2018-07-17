# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 15:30:48 2016

@author: clint

Use this code for making heat load estimates for darkness or picture-c. 

Includes:
    SS tubes
    G10 stuctural supports
    G10 heat switch rod
    radiation



"""

import numpy as np
import matplotlib.pyplot as plt



#############################################################################

'''

# set up fill line dimensions (small SS tube)
SS_wall_thickness_1 = .02
stainless_od1 = .25*.0254 #m
stainless_id1 = (.25 - 2*SS_wall_thickness_1)*.0254 #m
#stainless_id1 = .12*25.4/1000 #m
stainless_A1 = np.pi*((stainless_od1/2)**2 - (stainless_id1/2)**2)  #meters^2
print 'cross-sectional area of a fill line (stainless_A1)', stainless_A1

# set up vent line dimensions (large SS tube)
SS_wall_thickness_2 = .020 # inches
stainless_od2 = .375*.0254 #m
stainless_id2 = (.375 - 2*SS_wall_thickness_2)*.0254 #m
#stainless_id2 = .135*25.4/1000 #m
stainless_A2 = np.pi*((stainless_od2/2)**2 - (stainless_id2/2)**2)  #meters^2
print 'cross-sectional area of a vent line (stainless_A2)', stainless_A2

stainlessA1 = 2*stainless_A1+stainless_A2  #multiply by 2 because there are two vents and two fills
print 'SS cross-sectional area [m^2]:   ' ,stainlessA1



big_SS_tube_OD = .75*.0254 #meters
big_SS_tube_length = 14.5*.0254 #meters
big_SS_tube_wall_thickness = .035*.0254 #meters
stainless_A1 = np.pi*((big_SS_tube_OD/2)**2 - (big_SS_tube_OD/2 - big_SS_tube_wall_thickness)**2) #meters^2
print 'stainless_A1:   ' ,stainless_A1
'''

#############################################################################
#calculate the cross-sectional area of the stainless steel tubes

vent_SS_tube_OD = .375*.0254 #meters
vent_SS_tube_length = 16.5*.0254 #meters
vent_SS_tube_wall_thickness = .02*.0254 #meters
stainless_A2 = np.pi*((vent_SS_tube_OD/2)**2 - (vent_SS_tube_OD/2 - vent_SS_tube_wall_thickness)**2) #meters^2
#print 'stainless_A2:   ' ,stainless_A2

fill_SS_tube_OD = .25*.0254 #meters
fill_SS_tube_length = 16.5*.0254 #meters
fill_SS_tube_wall_thickness = .02*.0254 #meters
stainless_A3 = np.pi*((fill_SS_tube_OD/2)**2 - (fill_SS_tube_OD/2 - fill_SS_tube_wall_thickness)**2) #meters^2
#print 'stainless_A3:   ' ,stainless_A3

areaSS = 2*(stainless_A2 + stainless_A3)#don't forget that there are two fill/vent lines, so multiply area by two!

#for the 77K to 4K load, just estimate the thermal conductivity with a straight
#line with slope c

Th = 77 #K
Tc = 4 #K
c = .107 #W/m/K/K
#thermal conductivity of SS approximated by 
# k_SS = cT
# http://cryogenics.nist.gov/MPropsMAY/304Stainless/304Stainless_rev.htm
QSS = areaSS/vent_SS_tube_length/2*c*(Th**2 - Tc**2) 
print 'thermal load from SS on 4K stage [W]:   ', QSS


#let's make an estimate of the thermal load from 300K to 77K via the stainless steel tubes
#make a plot of the SS thermal conductivity
# http://cryogenics.nist.gov/MPropsMAY/304Stainless/304Stainless_rev.htm
# list the coefficients, a through i
T = np.arange(4,300,1)
#print 'T is ', T
coeff = np.array([-1.4087,1.3982,0.2543, -0.626, 0.2334, 0.4256, -0.4658, 0.1650, -0.0199])
#print 'coeff is ', coeff
tempLogArray = np.array([np.power(np.log10(T),0),np.power(np.log10(T),1),np.power(np.log10(T),2),np.power(np.log10(T),3),np.power(np.log10(T),4),np.power(np.log10(T),5),np.power(np.log10(T),6),np.power(np.log10(T),7),np.power(np.log10(T),8)])
#print 'tempLogArray is \n', tempLogArray
for ii in range(np.shape(tempLogArray)[1]):
    tempLogArray[:,ii] = np.multiply(coeff,tempLogArray[:,ii])
kSS = np.power(10,np.sum(tempLogArray,axis=0))

Tc = 77
Th = 299
lowTindex = np.where(T==Tc)[0][0] #find the index of T = Tc
highTindex = np.where(T==Th)[0][0] #find the index of T = Th

#do a 4th order polyfit. This is overkill, but I'm just copying the code so it's easier this way :P
pSS = np.polyfit(T[lowTindex:highTindex],kSS[lowTindex:highTindex],4)

if 1:
    plt.figure(12)
    plt.plot(T,kSS,'o-',label='NIST data')
#    plt.plot(T[lowTindex:highTindex],p[0]*T[lowTindex:highTindex]**2 + p[1]*T[lowTindex:highTindex] + p[2],'r.-',label='quadratic fit')
    plt.plot(T[lowTindex:highTindex],pSS[0]*T[lowTindex:highTindex]**4 + pSS[1]*T[lowTindex:highTindex]**3 + pSS[2]*T[lowTindex:highTindex]**2 + pSS[3]*T[lowTindex:highTindex] + pSS[4],'r.-',label='quartic fit')    
    plt.xlabel('temp in Kelvin',fontsize=14)
    plt.ylabel('thermal conductivity [W/m/K]',fontsize=14)
    plt.title('SS thermal conductivity vs temperature',fontsize=14)
    plt.legend(loc=0)
    plt.show()

SS_length_300_77 = 1.625*.0254
QSS_77K_load = areaSS/SS_length_300_77*(pSS[0]*(Th**5-Tc**5)/5 + pSS[1]*(Th**4-Tc**4)/4 + pSS[2]*(Th**3-Tc**3)/3 + pSS[3]*(Th**2-Tc**2)/2 + pSS[4]*(Th - Tc))
print 'heat load from 300K to 77K via SS tubes is [W]', QSS_77K_load




###########################################################
#G10 supports, 77K to 4K
#g10_wall_thickness = .06
g10od = .5*.0254   #outer diameter in meters
#g10id = (.5-2*g10_wall_thickness)*25.4/1000   #meters
g10id = .375*.0254 #meters
g10A = 4*(np.pi*((g10od/2)**2 - (g10id/2)**2))  #meters^2, multiply by 4 because there are 4 rods
#print 'G10 cross-sectional area [m^2]:   ' ,g10A

'''
a = .002 #W/m/K/K
b = 0.14 #W/m/K
#thermal conductivity k of G10 is roughly approximated with 
# k_g10 = aT+b

c = .107 #W/m/K/K
#thermal conductivity of SS approximated by 
# k_SS = cT

Qg10=g10A/rod_length*(.5*a*(Th**2-Tc**2) + b*(Th-Tc))
print 'thermal load from G10 [W]:   ', Qg10

QSS = stainlessA/rod_length/2*c*(Th**2 - Tc**2)
print 'thermal load from SS [W]:   ', QSS
'''


#make a plot of the G10 thermal conductivity
# http://cryogenics.nist.gov/MPropsMAY/G-10%20CR%20Fiberglass%20Epoxy/G10CRFiberglassEpoxy_rev.htm
# list the coefficients, a through i
T = np.arange(4,300,1)
#print 'T is ', T
coeff = np.array([-4.1236,13.788,-26.068,26.272,-14.663,4.4954,-0.6905,0.0397,0,])
#print 'coeff is ', coeff
tempLogArray = np.array([np.power(np.log10(T),0),np.power(np.log10(T),1),np.power(np.log10(T),2),np.power(np.log10(T),3),np.power(np.log10(T),4),np.power(np.log10(T),5),np.power(np.log10(T),6),np.power(np.log10(T),7),np.power(np.log10(T),8)])
#print 'tempLogArray is \n', tempLogArray
for ii in range(np.shape(tempLogArray)[1]):
    tempLogArray[:,ii] = np.multiply(coeff,tempLogArray[:,ii])
kg10 = np.power(10,np.sum(tempLogArray,axis=0))
#print 'kg10 is \n', kg10

Tc = 4
Th = 77
lowTindex = np.where(T==Tc)[0][0] #find the index of T = Tc
highTindex = np.where(T==Th)[0][0] #find the index of T = Th

#do a 2nd order polyfit for 4K to 77K
p = np.polyfit(T[lowTindex:highTindex],kg10[lowTindex:highTindex],2)

if 0:
    plt.figure(1)
    plt.plot(T,kg10,'o-',label='NIST data')
    #plt.plot(T,a*T+b)
    plt.plot(T[lowTindex:highTindex],p[0]*T[lowTindex:highTindex]**2 + p[1]*T[lowTindex:highTindex] + p[2],'r.-',label='quadratic fit')
    plt.xlabel('temp in Kelvin',fontsize=14)
    plt.ylabel('thermal conductivity [W/m/K]',fontsize=14)
    plt.title('G10 thermal conductivity vs temperature',fontsize=14)
    plt.legend(loc=4)
    plt.show()


g10Length = 1.75*.0254 #1.75 inches convert to meters
g10Length_hiTc = 6.0*.0254 # 6 inches to meters
g10A_hiTc = 2*(0.6*.0254)*(0.1*.0254) # 2 supports, 0.6 x 0.1 inch cross section

Qg10_structural_support=g10A/g10Length*(p[0]*(Th**3-Tc**3)/3 + p[1]*(Th**2-Tc**2)/2 + p[2]*(Th - Tc))
Qg10_hiTc_support=g10A_hiTc/g10Length_hiTc*(p[0]*(Th**3-Tc**3)/3 + p[1]*(Th**2-Tc**2)/2 + p[2]*(Th - Tc))
Qg10 = Qg10_structural_support + Qg10_hiTc_support
print 'thermal load from G10 structural [W]:   ', Qg10_structural_support
print 'thermal load from G10 hiTc [W]:   ', Qg10_hiTc_support
print 'total thermal load from G10 supports (structural and hi-Tc) [W]:   ', Qg10


### heat switch rod
#OD 3/16" inch, ID = 1/8", length ~ 4 in
HS_rod_area = np.pi*((3.0/16*.0254/2)**2-(1.0/8*.0254/2)**2)
HS_rod_length = 4*.0254

Tc = 4
Th = 299
lowTindex = np.where(T==Tc)[0][0] #find the index of T = Tc
highTindex = np.where(T==Th)[0][0] #find the index of T = Th

p4 = np.polyfit(T[lowTindex:highTindex],kg10[lowTindex:highTindex],4)

if 0:
    plt.figure(2)
    plt.plot(T,kg10,'o-',label='NIST data')
    #plt.plot(T,a*T+b)
    #plt.plot(T,p2[0]*T**3 + p2[1]*T**2 + p2[2]*T + p2[3],'r.-',label='cubic fit')
    plt.plot(T,p4[0]*T**4 + p4[1]*T**3 + p4[2]*T**2 + p4[3]*T + p4[4],'r.-',label='quartic fit')
    plt.xlabel('temp in Kelvin',fontsize=14)
    plt.ylabel('thermal conductivity [W/m/K]',fontsize=14)
    plt.title('G10 thermal conductivity vs temperature',fontsize=14)
    plt.legend(loc=4)
    plt.show()

Q_g10_HS_rod = HS_rod_area/HS_rod_length*(p4[0]*(Th**5-Tc**5)/5 + p4[1]*(Th**4-Tc**4)/4 + p4[2]*(Th**3-Tc**3)/3 + p4[3]*(Th**2-Tc**2)/2 + p4[4]*(Th - Tc))

if 0:
    print "thermal load from G10 heat switch rod [W]:   ", Q_g10_HS_rod





#############################################################################
#G10 supports between 300K and 77K
#OD 1", ID .875", length 1.75"
big_G10_support_area = 5*np.pi*((1.0*.0254/2)**2 - (.875*.0254/2)**2) # area in m^2
big_G10_support_length = 1.75*.0254

Tc = 77
Th = 299
lowTindex = np.where(T==Tc)[0][0] #find the index of T = Tc
highTindex = np.where(T==Th)[0][0] #find the index of T = Th

p5 = np.polyfit(T[lowTindex:highTindex],kg10[lowTindex:highTindex],4)

if 0:
    plt.figure(3)
    plt.plot(T,kg10,'o-',label='NIST data')
    plt.plot(T,p5[0]*T**4 + p5[1]*T**3 + p5[2]*T**2 + p5[3]*T + p5[4],'r.-',label='quartic fit, 77 to 300K')
    plt.xlabel('temp in Kelvin',fontsize=14)
    plt.ylabel('thermal conductivity [W/m/K]',fontsize=14)
    plt.title('G10 thermal conductivity vs temperature',fontsize=14)
    plt.legend(loc=4)
    plt.show()


Q_big_G10_support = big_G10_support_area/big_G10_support_length*(p5[0]*(Th**5-Tc**5)/5 + p5[1]*(Th**4-Tc**4)/4 + p5[2]*(Th**3-Tc**3)/3 + p5[3]*(Th**2-Tc**2)/2 + p5[4]*(Th - Tc))
print "load from 300K to 77K through big G10 supports is: ", Q_big_G10_support





#############################################################################
#radiation loads
sigma = 5.56*10**-8  #stefan boltzmann constant in SI units
A4K = 0.813  #area of the 4K shell in m^2
A77K = 1.159  #area of the 77K shell in m^2
emmissivity = 0.09  #emmisssivity of aluminum

radLoad4K = sigma*A4K*(77**4 - 4**4)
radLoad77K = sigma*A77K*(300**4 - 77**4)

if 0:
    print "radiation load on 4K from 77K is: ", radLoad4K
    print "radiation load on 77K from 300K is: ", radLoad77K






