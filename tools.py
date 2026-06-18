
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import exponnorm
import re

def extractWeerocParameters(filename):
    # Extract section
    index_start = re.search("section", filename)
    index_end = re.search("_", filename[index_start.end() + 1:])

    index_section_beginning = index_start.end() + 1
    index_section_ending = index_start.end() + index_end.start() + 1

    section = float(filename[index_section_beginning:index_section_ending])

    # Extract gain
    index_start = re.search("Gain", filename)
    index_end = re.search("_", filename[index_start.end():])

    index_gain_beginning = index_start.end()
    index_gain_ending = index_start.end() + index_end.start()

    gain = float(filename[index_gain_beginning:index_gain_ending])

    # Extract threshold
    index_start = re.search("Thr", filename)
    index_end = re.search("_", filename[index_start.end():])

    index_threshold_beginning = index_start.end()
    index_threshold_ending = index_start.end() + index_end.start()

    threshold = float(filename[index_threshold_beginning:index_threshold_ending].replace("-", "."))

    # Extract biais
    index_start = index_threshold_ending+1
    index_end = re.search("V", filename[index_threshold_ending:])

    index_gain_beginning = index_start
    index_gain_ending = index_start + index_end.start() - 1 

    biais = float(filename[index_gain_beginning:index_gain_ending].replace("-", "."))

    # Extract frequency
    index_start = re.search("Freq", filename)
    index_end = re.search("_", filename[index_start.end():])

    index_frequency_beginning = index_start.end()
    index_frequency_ending = index_start.end() + index_end.start()

    frequency = float(filename[index_frequency_beginning:index_frequency_ending].replace("-", "."))

    # Extract duration 
    index_start = index_frequency_ending
    index_end = re.search("s", filename[index_frequency_ending:])

    index_frequency_beginning = index_start + 1
    index_frequency_ending = index_start + index_end.start()

    duration = float(filename[index_frequency_beginning:index_frequency_ending].replace("-", "."))

    return section, gain, threshold, biais, frequency, duration

def canals_to_histogram(canals, binWidth):
    canal_histogram = []
    all_event_raw = []

    for canal in canals:
        all_event_raw.extend(canal)

        edges_canal, counts_canal = histogram(canal, binWidth)

        canal_histogram.append((edges_canal, counts_canal))
    
    edges_all_canals, counts_all_canals = histogram(all_event_raw, binWidth)

    return (edges_all_canals, counts_all_canals), canal_histogram

def split_canal_by_number(arr, n):
    number_events = len(arr)
    events_per_canal = number_events // n

    buckets = [[] for _ in range(n)]
    bucketsToF = [[] for _ in range(n)]
    bucketsToT = [[] for _ in range(n)]
    current_canal = 0

    arr_sorted = sorted(arr, key=lambda x: x[0])

    for item in arr_sorted:
        buckets[current_canal].append(item)
        bucketsToT[current_canal].append(item[0])
        bucketsToF[current_canal].append(item[1])

        if len(buckets[current_canal]) >= events_per_canal and current_canal < n - 1:
            current_canal += 1

    return buckets, bucketsToT, bucketsToF

def split_canal_by_first_value(arr, n):
    first_values = [x[0] for x in arr]

    min_val = min(first_values)
    max_val = max(first_values)

    step = (max_val - min_val) / n

    buckets = [[] for _ in range(n)]
    bucketsToF = [[] for _ in range(n)]
    bucketsToT = [[] for _ in range(n)]

    for item in arr:
        value = item[0]

        index = int((value - min_val) / step)

        # Put max value in last bucket
        if index == n:
            index = n - 1

        buckets[index].append(item)
        bucketsToT[index].append(item[0])
        bucketsToF[index].append(item[1])

    return buckets, bucketsToT, bucketsToF

def emg_function(x, amplitude, mu, sigma, tau):
    """
    Exponentially Modified Gaussian (EMG)
    """
    K = tau / sigma
    return amplitude * exponnorm.pdf(x, K, loc=mu, scale=sigma)


def fit_emg(x, y):
    """
    Fit EMG to x/y data

    Returns:
        popt : fitted parameters
        fitted_y : fitted curve
    """

    # Initial guesses
    amplitude0 = np.max(y)
    mu0 = x[np.argmax(y)]
    sigma0 = np.std(x)
    tau0 = sigma0

    p0 = [amplitude0, mu0, sigma0, tau0]

    # Fit
    popt, pcov = curve_fit(
        emg_function,
        x,
        y,
        p0=p0,
        maxfev=10000
    )

    fitted_y = emg_function(x, *popt)

    return popt, fitted_y

def calculate_fwhm(x, y):
    """
    Calculate Full Width at Half Maximum (FWHM)

    Parameters
    ----------
    x : array-like
        X values
    y : array-like
        Y values

    Returns
    -------
    fwhm : float
        Full width at half maximum
    """

    x = np.array(x)
    y = np.array(y)

    half_max = np.max(y) / 2

    # Find indices where signal crosses half max
    indices = np.where(y >= half_max)[0]

    if len(indices) < 2:
        return None

    left_idx = indices[0]
    right_idx = indices[-1]

    # Linear interpolation for better precision

    # Left crossing
    x1, x2 = x[left_idx - 1], x[left_idx]
    y1, y2 = y[left_idx - 1], y[left_idx]

    left_cross = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1)

    # Right crossing
    x1, x2 = x[right_idx], x[right_idx + 1]
    y1, y2 = y[right_idx], y[right_idx + 1]

    right_cross = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1)

    fwhm = right_cross - left_cross

    return fwhm