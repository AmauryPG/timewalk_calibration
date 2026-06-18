from scipy.stats import gaussian_kde
import numpy as np

def id(data, points=10000):

    sorted_data = np.sort(data)

    cumul_x = [sorted_data[0]]
    cumul_y = [1]

    # Ignore the first element
    for datum in sorted_data[1:]:
        if cumul_x[-1] == datum:
            cumul_y[-1] += 1
        else:
            cumul_x.append(datum)
            cumul_y.append(cumul_y[-1] + 1)

    smooth_x = np.linspace(np.min(cumul_x), np.max(cumul_x), points)
    smooth_y = np.interp(smooth_x, cumul_x, cumul_y)

    derivate = np.gradient(smooth_y, smooth_x)

    return smooth_x, derivate

def kde(data, points=1000):
    kde = gaussian_kde(data)

    histogram_x = np.linspace(min(data), max(data), points)
    histogram_y = kde(histogram_x)

    return histogram_x, histogram_y


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