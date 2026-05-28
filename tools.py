
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import exponnorm

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

def histogram(data, binWidth):
    """
    Create a histogram from a 1D array using a fixed bin width.

    Parameters
    ----------
    data : list of numbers
        Input values.
    binWidth : float
        Width of each bin.

    Returns
    -------
    counts : list
        Histogram counts.
    edges : list
        Bin edges.
    """

    if len(data) == 0:
        return [], []

    # Find min and max
    min_val = data[0]
    max_val = data[0]

    for x in data:
        if x < min_val:
            min_val = x
        if x > max_val:
            max_val = x

    # Number of bins
    bins = int((max_val - min_val) / binWidth) + 1

    # Initialize counts
    counts = [0] * bins

    # Fill histogram
    for x in data:
        index = int((x - min_val) / binWidth)

        # Safety clamp
        if index >= bins:
            index = bins - 1

        counts[index] += 1

    # Bin edges
    edges = []
    for i in range(bins + 1):
        edges.append(min_val + i * binWidth)

    return edges[:-1], counts

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