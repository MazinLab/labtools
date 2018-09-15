"""
Author:    Jenny Smith
Date:      Sept 10, 2018

This is a script to profile the thresholding + baseline filter step in the readout.
It is meant to be used with one board. 114 was arbitrarily chosen for the test.

"""

import sys, os, time, datetime, struct, math
import calendar, warnings, inspect, ConfigParser
import numpy as np
import scipy.special
import casperfpga, socket, binascii
from mkidreadout.channelizer.binTools import castBin
from mkidreadout.utils.readDict import readDict
from mkidreadout.channelizer.Roach2Controls import Roach2Controls
from mkidreadout.channelizer.RoachStateMachine import RoachStateMachine

roachnumber = 114
config = ConfigParser.ConfigParser()
config.read('/mnt/data0/BF/20180911/templarconfthresh.cfg') #use the latest cfg file

FPGAParamFile = config.get('Roach '+str(roachnumber), 'FPGAParamFile')
ip = config.get('Roach '+str(roachnumber), 'ipaddress')

#initialize board object
board=Roach2Controls(ip, FPGAParamFile)

#define snap function (copied from RoachStateMachine)
def getPhaseFromSnap(channel):
	"""This function grabs the phase timestream from the snapblock
	INPUTS:
	       channel - the i'th frequency in the frequency list
	OUTPUTS:
 	      phaseSnap - list of phase in radians"""

	print "r"+str(roachnumber)+": ch"+str(channel)+" Getting phase snap"
	try:
            phaseSnapDict = board.takePhaseSnapshotOfFreqChannel(channel)
	except:
            traceback.print_exc()
            return
	return phaseSnapDict['phase']


#connect
board.connect()

#semi-random parameters
nFreqs=900
loFreq = 5.e9
spacing = 2.e6
freqList = np.arange(loFreq-nFreqs/2.*spacing, loFreq+nFreqs/2.*spacing, spacing)
freqList += np.random.uniform(-spacing, spacing, nFreqs)
freqList = np.sort(freqList)
attenList = np.random.randint(23, 33, nFreqs)

#these need to be called before creating DDS frequencies
board.setLOFreq(loFreq)
board.generateResonatorChannels(freqList)
board.generateFftChanSelection()
board.loadChanSelection()

#Create and interweave DDS frequencies
board.generateDdsTones()

#load DDS LUT
board.loadDdsLUT()

#Set Thresholds (copied from RoachStateMachine)
threshSig = 4.0
nSnap = 1

thresh = []
for i in range(nFreqs):
    data= []
    for k in range(nSnap):
        data.append(getPhaseFromSnap(i))
    thresh.append(-1*np.std(data)*threshSig)
for i in range(nFreqs):
    board.setThreshByFreqChannel(thresh[i], i)