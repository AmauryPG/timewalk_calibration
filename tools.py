
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import exponnorm
import numpy as np
from scipy.interpolate import splprep, splev

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


def interpolate_xy(x, y, num_points=1000):
    """
    Interpolate (x, y) data onto a new evenly spaced x grid.

    Parameters
    ----------
    x : array-like
        Original x values.
    y : array-like
        Original y values.
    num_points : int
        Number of points in the interpolated result.

    Returns
    -------
    x_new : np.ndarray
        New x values.
    y_new : np.ndarray
        Interpolated y values.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    # Ensure x is sorted
    idx = np.argsort(x)
    x = x[idx]
    y = y[idx]

    x_new = np.linspace(x.min(), x.max(), num_points)
    y_new = np.interp(x_new, x, y)

    return x_new, y_new

from scipy.interpolate import UnivariateSpline

def smooth_interpolate(x, y, num_points=1000, smoothing=None):
    """
    Smooth and interpolate noisy (x, y) data.

    Parameters
    ----------
    x : array-like
        X values.
    y : array-like
        Y values.
    num_points : int
        Number of output points.
    smoothing : float or None
        Smoothing factor. Larger values give smoother curves.
        If None, scipy chooses a default.

    Returns
    -------
    x_new : np.ndarray
    y_new : np.ndarray
    """
    x = np.asarray(x)
    y = np.asarray(y)

    idx = np.argsort(x)
    x = x[idx]
    y = y[idx]

    spline = UnivariateSpline(x, y, s=smoothing)

    x_new = np.linspace(x.min(), x.max(), num_points)
    y_new = spline(x_new)

    return x_new, y_new

from scipy.signal import savgol_filter

def smooth_interpolate_savgol(
    x, y,
    num_points=1000,
    window=21,
    polyorder=3
):
    x = np.asarray(x)
    y = np.asarray(y)

    idx = np.argsort(x)
    x = x[idx]
    y = y[idx]

    y_smooth = savgol_filter(y, window, polyorder)

    x_new = np.linspace(x.min(), x.max(), num_points)
    y_new = np.interp(x_new, x, y_smooth)

    return x_new, y_new

def interpolate_least_square(x, y, points=1000):
    coefficients = np.polyfit(x, y, 1) 
    poly_func = np.poly1d(coefficients)

    x_new = np.linspace(np.min(x), np.max(x), points)
    y_new = poly_func(x_new)

    return x_new, y_new

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import exponnorm


def emg_pdf(x, amplitude, mu, sigma, tau):
    """
    Exponentially Modified Gaussian (EMG).

    Parameters
    ----------
    x : ndarray
    amplitude : float
        Overall scale factor.
    mu : float
        Gaussian mean.
    sigma : float
        Gaussian standard deviation.
    tau : float
        Exponential decay constant.

    Returns
    -------
    ndarray
    """
    K = tau / sigma
    return amplitude * exponnorm.pdf(
        x,
        K=K,
        loc=mu,
        scale=sigma
    )


def fit_emg(x, y):
    """
    Fit noisy EMG data.

    Parameters
    ----------
    x : ndarray
        X values.
    y : ndarray
        Y values.

    Returns
    -------
    popt : tuple
        (amplitude, mu, sigma, tau)
    pcov : ndarray
        Covariance matrix.
    y_fit : ndarray
        Fitted curve.
    """

    x = np.asarray(x)
    y = np.asarray(y)

    # Initial guesses
    amplitude0 = np.max(y)

    mu0 = x[np.argmax(y)]

    sigma0 = np.std(x) / 5

    # estimate asymmetry
    mean_x = np.sum(x * y) / np.sum(y)
    tau0 = max(mean_x - mu0, sigma0)

    p0 = [amplitude0, mu0, sigma0, tau0]

    bounds = (
        [0, np.min(x), 1e-6, 1e-6],
        [np.inf, np.max(x), np.inf, np.inf]
    )

    popt, pcov = curve_fit(
        emg_pdf,
        x,
        y,
        p0=p0,
        bounds=bounds,
        maxfev=20000
    )

    y_fit = emg_pdf(x, *popt)

    return popt, pcov, y_fit


def smooth_curve(x, y, num_points=1000, smoothing_factor=None):
    """
    Create a smooth continuous curve from scattered x,y data.

    Parameters
    ----------
    x : array-like
        X coordinates.
    y : array-like
        Y coordinates.
    num_points : int, optional
        Number of points in the output curve.
    smoothing_factor : float or None, optional
        Spline smoothing parameter (s).
        - s=0 passes through all points.
        - Larger values produce smoother curves.

    Returns
    -------
    x_smooth : ndarray
        Smooth x values.
    y_smooth : ndarray
        Smooth y values.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    # Sort by x
    idx = np.argsort(x)
    x = x[idx]
    y = y[idx]

    # Remove duplicate x values
    x_unique, unique_idx = np.unique(x, return_index=True)
    y_unique = y[unique_idx]

    spline = UnivariateSpline(
        x_unique,
        y_unique,
        s=smoothing_factor
    )

    x_smooth = np.linspace(x_unique.min(), x_unique.max(), num_points)
    y_smooth = spline(x_smooth)

    return x_smooth, y_smooth


def smooth_path(x, y, num_points=1000, smoothing=0):
    points = np.vstack([x, y])

    tck, _ = splprep(points, s=smoothing)
    u_new = np.linspace(0, 1, num_points)

    x_smooth, y_smooth = splev(u_new, tck)

    return np.array(x_smooth), np.array(y_smooth)