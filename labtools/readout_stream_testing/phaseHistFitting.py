import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as spo
import scipy.special as spfun
import scipy.stats as sps


def gaussian(data, scale, center, sigma):
    return scale*np.exp(-(data-center)**2/(2*sigma**2))

def gaussianExpTail(data, scale, center, sigma, tailScale, tailCenter, tailDecay):
    return scale*np.exp(-(data-center)**2/(2*sigma**2)) + tailScale*np.exp((data-tailCenter)/tailDecay)

def expModGaussian(data, scale, center, sigma, lmda):
    return scale*np.exp(lmda/2*(2*center + lmda*sigma**2 - 2*data))*spfun.erfc((center + lmda*sigma**2 - data)/(np.sqrt(2)*sigma))

def expModGaussianExpTail(data, scale, center, sigma, lmda, tailScale, tailCenter, tailDecay):
    return expModGaussian(data, scale, center, sigma, lmda) + tailScale*np.exp((data-tailCenter)/tailDecay)

def fitPhaseHist(peakHeights, nBins=100, fitFunction='gaussianExpTail'):
    phaseHist, binEdges = np.histogram(peakHeights, bins=nBins)
    binCenters = np.diff(binEdges)/2 + binEdges[:-1]
    sigma = np.sqrt(phaseHist)
    sigma[sigma==0] = 2
    if fitFunction=='gaussian':
        popt, pcov = spo.curve_fit(gaussian, binCenters, phaseHist, p0=[np.max(phaseHist), 
            binCenters[np.argmax(phaseHist)], np.std(peakHeights)], sigma=sigma)
    elif fitFunction=='gaussianExpTail':
        popt, pcov = spo.curve_fit(gaussianExpTail, binCenters, phaseHist, p0=[np.max(phaseHist),
            binCenters[np.argmax(phaseHist)], np.std(peakHeights)/2, phaseHist[-1], binCenters[-1],
            2*np.std(peakHeights)], sigma=sigma)
    elif fitFunction=='expModGaussian':
        popt, pcov = spo.curve_fit(expModGaussian, binCenters, phaseHist, p0=[np.max(phaseHist),
            binCenters[np.argmax(phaseHist)] - np.std(peakHeights)*pow(sps.skew(peakHeights)/2, 1./3), 
                np.std(peakHeights)*np.sqrt(1 - pow(sps.skew(peakHeights)/2, 2./3)), 1/np.std(peakHeights)*2/pow(sps.skew(peakHeights)/2, 2./3)], sigma=sigma)
    elif fitFunction=='expModGaussianExpTail':
        popt, pcov = spo.curve_fit(expModGaussianExpTail, binCenters, phaseHist, p0=[np.max(phaseHist),
            binCenters[np.argmax(phaseHist)], np.std(peakHeights), np.std(peakHeights)/2, phaseHist[-1], 
            binCenters[-1], 2*np.std(peakHeights)], sigma=sigma)

    return phaseHist, binEdges, binCenters, popt, pcov
