import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import os, sys, glob
import phaseHistFitting as pfit
import tables
from mkidcore.headers import ObsFileCols

class FIRFilter:
    
    def __init__(self, filterCoeffFile=None, normalize=True):
        self.normalize = normalize
        if filterCoeffFile is not None:
            self.loadFilterFromFile(filterCoeffFile)


    def loadFilterFromFile(self, filterCoeffFile):
        self.filterCoeffs = np.loadtxt(filterCoeffFile)
        if self.normalize:
            self.filterCoeffs /= np.sum(self.filterCoeffs)

    def filterData(self, dataStream):
        return np.convolve(dataStream, self.filterCoeffs)

class DCBaselineFilter:
    
    def __init__(self, band='hp'):
        self.band = band

    def filterData(self, dataStream):
        if self.band=='hp':
            return dataStream - np.median(dataStream)
        elif self.band=='lp':
            return np.median(dataStream)
        else:
            return '&(*&%&*(($^$*)())()^&*(^&*'

class IirFilter:
    def __init__(self,criticalFreqHz=100,sampleFreqHz=1e6,order=2,btype='lowpass',numCoeffs=None,denomCoeffs=None,zeros=None,poles=None,gain=None):
        self.sampleFreqHz = sampleFreqHz
        self.nyquistFreqHz = sampleFreqHz / 2.
        if numCoeffs is None and zeros is None and poles is None:
            self.criticalFreqHz = criticalFreqHz
            self.order = order
            self.criticalW = criticalFreqHz/self.nyquistFreqHz
            self.ftype = 'butter'
            self.btype = btype
            self.numCoeffs,self.denomCoeffs = scipy.signal.iirfilter(self.order,self.criticalW,btype=self.btype,ftype=self.ftype,output='ba')
            self.zeros,self.poles,self.gain = scipy.signal.iirfilter(self.order,self.criticalW,btype=self.btype,ftype=self.ftype,output='zpk')
        elif numCoeffs is not None:
            self.order = len(denomCoeffs)
            self.numCoeffs = numCoeffs
            self.denomCoeffs = denomCoeffs
            self.zeros,self.poles,self.gain = scipy.signal.tf2zpk(numCoeffs,denomCoeffs)
        else:
            self.numCoeffs,self.denomCoeffs = scipy.signal.zpk2tf(zeros,poles,gain)

    def freqResp(self,**kwargs):
        afreqs,freqResp = scipy.signal.freqz(self.numCoeffs,self.denomCoeffs,**kwargs)
        sampledFreqsHz = afreqs * self.nyquistFreqHz / np.pi
        freqRespDb = 20.*np.log10(np.abs(freqResp))
        return {'sampledFreqsHz':sampledFreqsHz,'freqRespDb':freqRespDb,'freqResp':freqResp}

    def filterData(self,data):
        filteredData = scipy.signal.lfilter(self.numCoeffs,self.denomCoeffs,data)
        return filteredData

    def plotFreqResponse(self,ax=None,showMe=True,label=None,**kwargs):
        freqRespDict = self.freqResp(**kwargs)
        if ax == None:
            fig,ax = plt.subplots(1,1)
        ax.plot(freqRespDict['sampledFreqsHz'] / 1.e3,freqRespDict['freqRespDb'],label=label)
        ax.set_xlabel('freq (kHz)')
        ax.set_ylabel('filter response (dB)')
        if showMe:
            plt.show()

    def save(self,path=''):
        fullPath = os.path.abspath(path)
        
        if os.path.basename(fullPath) == '' or os.path.isdir(fullPath):
            filename = '{}Iir{}Hz.csv'.format(self.btype,self.criticalFreqHz)
            fullPath = os.path.join(fullPath,filename)
        header = '{} {} IIR, criticalFreq = {} Hz, sampleFreq = {} Hz \n numeratorCoeffs\ndenomenatorCoeffs'.format(self.ftype,self.btype,self.criticalFreqHz,self.sampleFreqHz)
        
        writer = csv.writer(open(fullPath, "w"))
        writer.writerow(['criticalFreqHz',self.criticalFreqHz])
        writer.writerow(['sampleFreqHz',self.sampleFreqHz])
        writer.writerow(['btype',self.btype])
        writer.writerow(['ftype',self.ftype])

        writer.writerow(['numCoeffs',self.numCoeffs])
        writer.writerow(['denomCoeffs',self.denomCoeffs])

class FilterStack:
    """
    Class for applying a series of filters + triggering. Will (eventually) work with (downconverted)
    IQ data in addition to phase.
    """

    def __init__(self, streamType='phase'):
        if streamType != 'phase' and streamType != 'iq':
            raise Exception('data must be either phase or iq!')
        elif streamType == 'iq':
            raise Exception('IQ data not implemented yet!')

        self.streamType = streamType
        self.phaseFilterList = [] #list of filter objects


    def filterPhaseStream(self, phaseStream):
        for filt in self.phaseFilterList:
            phaseStream = filt.filterData(phaseStream)
        return phaseStream

    def addPhaseFilter(self, filterObj):
        self.phaseFilterList.append(filterObj)

def detectPhasePulses(data,threshold=None,nSigmaThreshold=3.,deadtime=10,nNegDerivChecks=10,negDerivLenience=1, bNegativePulses = True):
    #deadtime in ticks (us)
    if bNegativePulses:
        data = np.array(data)
    else:
        data = -np.array(data) #flip to negative pulses

    if threshold is None:
        threshold = np.median(data)-nSigmaThreshold*np.std(data)
    derivative = np.diff(data)
    peakHeights = []
    t = 0
    negDeriv = derivative <= 0
    posDeriv = np.logical_not(negDeriv)
   
    triggerBooleans = data[nNegDerivChecks:-2] < threshold

    negDerivChecksSum = np.zeros(len(negDeriv[0:-nNegDerivChecks-1]))
    for i in range(nNegDerivChecks):
        negDerivChecksSum += negDeriv[i:i-nNegDerivChecks-1]
    peakCondition0 = negDerivChecksSum >= nNegDerivChecks-negDerivLenience
    peakCondition1 = np.logical_and(posDeriv[nNegDerivChecks:-1],posDeriv[nNegDerivChecks+1:]) #two positive derivative checks, like in firmware
    peakCondition01 = np.logical_and(peakCondition0,peakCondition1)
    peakBooleans = np.logical_and(triggerBooleans,peakCondition01)
        
    try:
        peakIndices = np.where(peakBooleans)[0]+nNegDerivChecks
        i = 0
        p = peakIndices[i]
        while p < peakIndices[-1]:
            peakIndices = peakIndices[np.logical_or(peakIndices-p > deadtime , peakIndices-p <= 0)]#apply deadtime
            i+=1
            if i < len(peakIndices):
                p = peakIndices[i]
            else:
                p = peakIndices[-1]
    except IndexError:
        return {'peakIndices':np.array([]),'peakHeights':np.array([])}
        
    if bNegativePulses:
        peakHeights = data[peakIndices]
    else:
        peakHeights = -data[peakIndices] #flip back to positive sign
    peakIndices=peakIndices.astype(int)    
    return {'peakIndices':peakIndices,'peakHeights':peakHeights}

def fitResList(folder, firCoeffFile, useBaseline=True, nBinsPhaseHist=150):
    filtStack = FilterStack('phase')
    optimalFilter = FIRFilter(firCoeffFile, normalize=False)
    filtStack.addPhaseFilter(optimalFilter)

    nNegDeriv = 10
    nPosDeriv = 2
    negDerivLenience = 1
    deadtime = 10
    sigThresh = 3.3

    figList = []
    axList = []

    if useBaseline:
        f=2*np.sin(np.pi*criticalFreqHz/sampleRate)
        Q=.75
        q=1./Q
        print 'Kf',f,'Kq',q
        hpSvf = IirFilter(sampleFreqHz=sampleRate,numCoeffs=np.array([1,-2,1]),denomCoeffs=np.array([1+f**2, f*q-2,1-f*q]))
        filtStack.addPhaseFilter(hpSvf) 

    for phaseSnapFile in glob.iglob(os.path.join(folder, '*.npz')):
        phaseStreamDict = np.load(phaseSnapFile)
        phaseStream = 180/np.pi*phaseStreamDict[phaseStreamDict.keys()[0]]
        filteredPhase = filtStack.filterPhaseStream(phaseStream)
        peakDict = detectPhasePulses(filteredPhase, nSigmaThreshold=sigThresh, nNegDerivChecks=nNegDeriv, negDerivLenience=negDerivLenience, deadtime=deadtime)
        phaseHist, _, phaseHistBinCenters, popt, pcov = pfit.fitPhaseHist(peakDict['peakHeights'], nBinsPhaseHist, 'gaussianExpTail')
        
        resLabel = phaseSnapFile.split('/')[-1].split('_')[2]

        print resLabel
        print 'Energy Resolution:', popt[1]/(popt[2]*2.355)
        print 'Center:', popt[1]
        print 'Sigma:', popt[2]
        print 'Standard Dev (NOT sigma from fit):', np.std(peakDict['peakHeights'])
        print ''

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.hist(peakDict['peakHeights'], bins=nBinsPhaseHist)
        ax.plot(phaseHistBinCenters, pfit.gaussianExpTail(phaseHistBinCenters, *popt))
        ax.set_title(resLabel)
        ax.text(-20, 300, 'R = ' + str(popt[1]/(popt[2]*2.355)))
        figList.append(fig)
        axList.append(ax)

    plt.show()
        
class PhaseStreamProcesser:
    
    def __init__(folder=None, fileName=None):
        if not(folder is None or fileName is None):
            raise Exception('Must specify either a folder or filename, not both!')
        elif folder is not None and fileName is not none:
            raise Exception('Must specify either a folder or filename')

        if folder is not None:
            self.folder = folder
            self.loadFolder()
        else:
            self.fileName = fileName
            self.loadFile()

        self.filtStack = FilterStack('phase')
        self.filtStack.addFIRFilter('/mnt/data0/SDR/Projects/Filters/unity50.txt')

    def loadFolder(self):
        fileList = glob.glob(os.path.join(self.folder, '*.npz'))
        self.resIDList = np.zeros(len(fileList))

        for i, fileName in enumerate(fileList):
            phasetStreamDict = np.load(fileName)
            phaseStream = phaseStreamDict[phaseStreamDict.keys()[0]]*180/np.pi
            if i==0:
                self.phaseStreamList = np.zeros((len(fileList)), len(phaseStream))
            self.phaseStreamList[i,:] = phaseStream
            self.resIDList[i] = int(phaseSnapFile.split('/')[-1].split('_')[2][3:])

    def addSVFBaseline(self, criticalFreqHz=200, sampleRate=1.e6, Q=0.75):
        f = 2*np.sin(np.pi*criticalFreqHz/sampleRate)
        q = 1./Q
        print 'Kf',f,'Kq',q
        hpSvf = IirFilter(sampleFreqHz=sampleRate,numCoeffs=np.array([1,-2,1]),denomCoeffs=np.array([1+f**2, f*q-2,1-f*q]))
        self.filtStack.addPhaseFilter(hpSvf)
    
    def addDCBaseline(self):
        self.filtStack.addPhaseFilter(DCBaselineFilter('hp'))

    def addFIRFilter(self, firCoeffFile, normalize=False):
        self.filtStack.addPhaseFilter(FIRFilter(firCoeffFile, normalize=normalize))

    def filterAndTriggerPhase(self, sigThresh=3.0, nNegDeriv=10, nPosDeriv=2, negDerivLenience=1, deadtime=10):
        self.peakDictList = []
        for i in range(len(self.resIDList)):
            filteredPhase = self.filtStack.filterPhaseStream(self.phaseStreamList[i,:])
            peakDict = detectPhasePulses(filteredPhase, nSigmaThreshold=sigThresh, nNegDerivChecks=nNegDeriv, negDerivLenience=negDerivLenience, deadtime=deadtime)
            self.peakDictList.append(peakDict)


    def makeH5File(self, path, bmData):
        hfile = tables.open_file(path, mode='w', title='sw_trig_photons')
        photonGroup = hfile.create_group('/', 'Photons')
        bmGroup = hfile.create_group('/', 'Beammap')
        photonTable = hfile.create_table(photonGroup, 'ObsFileCols', 'Photon List')

        for i in range(len(self.resIDList)):
            peakHeights = self.peakDictList[i]['peakHeights']
            peakIndices = self.peakDictList[i]['peakIndices']
            resIDs = self.resIDList[i]*np.ones(len(peakHeights))
            tableArray = np.zeros((len(peakHeights), 5))
            tableArray[:,0] = resIDs
            tableArray[:,1] = peakIndices
            tableArray[:,2] = peakHeights
            tableArray[:,3] = 1
            tableArray[:,4] = 1
            photonTable.append(tableArray)
            

            
            

if __name__=='__main__':
    #fitResList('/mnt/data0/Darkness/20180816/phasesnaps/112_opt_filt_phase/', '/mnt/data0/SDR/Projects/Filters/unity50.txt', False)
    #phaseSnapFile = '/mnt/data0/Darkness/20180816/phasesnaps/112_opt_filt_phase/snap_112_resID70011_20180817-130001.npz'
    #phaseSnapFile = '/mnt/data0/Darkness/20180816/phasesnaps/112/snap_112_resID70011_20180817-124330.npz'
    #phaseSnapFile = '/mnt/data0/Darkness/20180820/phasesnaps/snap_112_resID70011_20180820-181056.npz'
    phaseSnapFile = '/mnt/data0/BF/20180913/phasesnaps/Optimal_980/snap_112_resID70424_20180913-182338.npz'
    #phaseSnapFile = '/mnt/data0/Darkness/20180816/phasesnaps/112/snap_112_resID70002_20180817-123937.npz' #unity filtered stream
    #firCoeffFile = '/mnt/data0/SDR/Projects/Filters/matched50_15.0us.txt'
    firCoeffFile = '/mnt/data0/SDR/Projects/Filters/unity50.txt'
    #firCoeffFile = '/mnt/data0/Darkness/20180816/phasesnaps/112/70011_opt_filt.txt'
    sampleRate = 1e6 # 1 MHz
    criticalFreqHz = 200 #Hz

    f=2*np.sin(np.pi*criticalFreqHz/sampleRate)
    Q=.75
    q=1./Q
    print 'Kf',f,'Kq',q

    nNegDeriv = 10
    nPosDeriv = 2
    negDerivLenience = 1
    deadtime = 10
    sigThresh = 5.3

    nBinsPhaseHist = 150

    phaseStreamDict = np.load(phaseSnapFile)
    phaseStream = 180/np.pi*phaseStreamDict[phaseStreamDict.keys()[0]]
    
    filtStack = FilterStack('phase')
    optimalFilter = FIRFilter(firCoeffFile, normalize=False)
    hpSvf = IirFilter(sampleFreqHz=sampleRate,numCoeffs=np.array([1,-2,1]),denomCoeffs=np.array([1+f**2, f*q-2,1-f*q]))
    meanBaselineFilt = DCBaselineFilter()
    filtStack.addPhaseFilter(optimalFilter)
    filtStack.addPhaseFilter(hpSvf) 
    #filtStack.addPhaseFilter(meanBaselineFilt)

    filteredPhase = filtStack.filterPhaseStream(phaseStream)
    baseline = optimalFilter.filterData(phaseStream) - hpSvf.filterData(optimalFilter.filterData(phaseStream))

    peakDict = detectPhasePulses(filteredPhase, nSigmaThreshold=sigThresh, nNegDerivChecks=nNegDeriv, negDerivLenience=negDerivLenience, deadtime=deadtime)
    #peakHeights = peakDict['peakHeights']
    #phaseHist, binEdges = np.histogram(peakHeights, bins=nBinsPhaseHist)
    #binCenters = np.diff(binEdges)/2 + binEdges[:-1]
    #p0=[np.max(phaseHist), binCenters[np.argmax(phaseHist)], np.std(peakHeights), phaseHist[-1], binCenters[-1],  2*np.std(peakHeights)]
    #fig = plt.figure()
    #ax = fig.add_subplot(111)
    #ax.hist(peakDict['peakHeights'], bins=nBinsPhaseHist)
    #ax.plot(binCenters, pfit.gaussianExpTail(binCenters, *p0))
    #plt.show()

    phaseHist, _, phaseHistBinCenters, popt, pcov = pfit.fitPhaseHist(peakDict['peakHeights'], nBinsPhaseHist, 'gaussianExpTail')

    R = popt[1]/(popt[2]*2.355)

    print 'Energy Resolution:', popt[1]/(popt[2]*2.355)
    print 'Center:', popt[1]
    print 'Sigma:', popt[2]
    print 'Standard Dev (NOT sigma from fit):', np.std(peakDict['peakHeights'])

    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111)
    ax1.hist(peakDict['peakHeights'], bins=nBinsPhaseHist)
    ax1.plot(phaseHistBinCenters, pfit.gaussianExpTail(phaseHistBinCenters, *popt))
    ax1.set_xlim(-140,-20)
    ax1.set_title('Pix 70011, FW Flipped Opt Filt  w/ svf baseline; R = ' + str(R))

    fig2 = plt.figure()
    ax2 = fig2.add_subplot(111)
    ax2.plot(baseline)

    fig3 = plt.figure()
    ax3 = fig3.add_subplot(111)
    ax3.plot(filteredPhase)
    ax3.plot(peakDict['peakIndices'], peakDict['peakHeights'], '.')

    fig4 = plt.figure()
    ax4 = fig4.add_subplot(111)
    ax4.plot(optimalFilter.filterCoeffs)

    plt.show()

   

