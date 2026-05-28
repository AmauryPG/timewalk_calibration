from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import histogram
from scipy import stats
import math

def snr(a):
    a = np.asanyarray(a)
    m = a.mean(0)
    sd = a.std(axis = 0, ddof = 0)
    return np.where(sd == 0, 0, m / sd)

import random

def generate_noise(sample_data, size):
    """
    Generate noise with similar statistics as sample_data.

    Parameters
    ----------
    sample_data : list of numbers
        Example noise samples.
    size : int
        Number of noise samples to generate.

    Returns
    -------
    noise : list
        Generated noise signal.
    """

    if len(sample_data) == 0:
        return []

    # Mean
    mean = 0
    for x in sample_data:
        mean += x
    mean /= len(sample_data)

    # Standard deviation
    variance = 0
    for x in sample_data:
        variance += (x - mean) ** 2
    variance /= len(sample_data)

    std = variance ** 0.5

    # Generate Gaussian noise
    noise = []

    for _ in range(size):
        # Box-Muller transform
        u1 = random.random()
        u2 = random.random()

        z = (-2 * __import__("math").log(u1)) ** 0.5
        z *= __import__("math").cos(2 * __import__("math").pi * u2)

        noise.append(mean + std * z)

    return noise

def snr2(data):
    return (np.max(data) - np.min(data))/len(data)


def glrt(signal, noise_mean=0.0, noise_std=1.0):
    """
    Generalized Likelihood Ratio Test (GLRT)
    for detecting signal presence in Gaussian noise.

    Hypotheses:
        H0 : x = noise
        H1 : x = signal + noise

    Parameters
    ----------
    signal : list of float
        Observed samples.
    noise_mean : float
        Expected noise mean.
    noise_std : float
        Expected noise standard deviation.

    Returns
    -------
    glr : float
        Generalized likelihood ratio.
    log_glr : float
        Log-likelihood ratio.
    """

    N = len(signal)

    if N == 0:
        return 0.0, 0.0

    var = noise_std ** 2

    # ----- H0 likelihood -----
    # Noise only

    logL0 = 0.0

    for x in signal:
        logL0 += -0.5 * math.log(2 * math.pi * var)
        logL0 += -((x - noise_mean) ** 2) / (2 * var)

    # ----- H1 likelihood -----
    # Estimate unknown signal mean using MLE

    estimated_mean = sum(signal) / N

    logL1 = 0.0

    for x in signal:
        logL1 += -0.5 * math.log(2 * math.pi * var)
        logL1 += -((x - estimated_mean) ** 2) / (2 * var)

    # GLR
    log_glr = logL1 - logL0
    glr = math.exp(log_glr)

    return glr, log_glr

if __name__ == "__main__":

    emptyToT, emptyToF, size = readBinaryWeerocFileWithPicoCalibrated(
        "/home/daniel/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr667_56-15V_Freq80000_60s.bin"
    )

    validToT, validToF, size = readBinaryWeerocFileWithPicoCalibrated(
        "/home/daniel/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    tofBin = 12

    # Create the histogram
    histogramToFValidX, histogramToFValidY = histogram(validToF, tofBin)
    histogramToFEmptyX, histogramToFEmptyY = histogram(emptyToF, tofBin)

    simulationHistogramY = generate_noise(histogramToFEmptyY[:100], len(histogramToFEmptyX))

    plt.scatter(histogramToFValidX, histogramToFValidY, color='r', label='valid')
    plt.scatter(histogramToFEmptyX, simulationHistogramY, color='b', label='empty', marker='o')


    # Add labels and title
    plt.title('Basic Histogram')
    plt.xlabel('Values')
    plt.ylabel('Frequency')
    plt.legend()

    # SNR stats
    print(f"SIM   : {np.mean(np.array(simulationHistogramY))/np.var(np.array(simulationHistogramY))*100}")
    print(f"Empty : {np.mean(np.array(histogramToFEmptyY))/np.var(np.array(histogramToFEmptyY))*100}")
    print(f"Valid : {np.mean(np.array(histogramToFValidY))/np.var(np.array(histogramToFValidY))*100}")


    plt.show()