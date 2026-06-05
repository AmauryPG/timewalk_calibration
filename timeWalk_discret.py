from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import *
from scipy.stats import gaussian_kde
from scipy.stats import exponnorm

def round_to_nearest_step(values, step):
    """
    Round values to nearest multiple of step.
    """

    return np.round(values / step) * step


def emg_curve(mu, sigma, tau, xmin=None, xmax=None, n=1000):
    """
    Generate an exponentially modified Gaussian (EMG) curve.

    Parameters
    ----------
    mu : float
        Mean of the Gaussian component.
    sigma : float
        Standard deviation of the Gaussian component.
    tau : float
        Decay constant of the exponential component.
    xmin, xmax : float, optional
        Plot range. If None, chosen automatically.
    n : int
        Number of points.

    Returns
    -------
    x, y : np.ndarray
        Coordinates of the EMG PDF.
    """

    K = tau / sigma

    if xmin is None:
        xmin = mu - 5 * sigma

    if xmax is None:
        xmax = mu + 5 * sigma + 5 * tau

    x = np.linspace(xmin, xmax, n)
    y = exponnorm.pdf(x, K=K, loc=mu, scale=sigma)

    return x, y

def emg_samples(mu, sigma, tau, size=10000):
    K = tau / sigma
    return exponnorm.rvs(K=K, loc=mu, scale=sigma, size=size)

if __name__ == "__main__":

    
    tot, data, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
    
    '''
    tofBin = 12
    tofStep = 0.5
    plt.scatter(
        tof,
        [p for p in range(len(tof))],
        label = "Raw Data"
    )

    sorted_tof = np.sort(tof)
    discrete_counts = { rounded_s: 0 for rounded_s in np.arange(round_to_nearest_step(sorted_tof[0], tofStep), round_to_nearest_step(sorted_tof[-1], tofStep) + 1, tofStep) }

    for s in sorted_tof:
        rounded_s = float(round_to_nearest_step(s, tofStep))

        discrete_counts[rounded_s] += 1
    
    plt.scatter(
        list(discrete_counts.keys()),
        list(discrete_counts.values()),
        label = "Cumulative Counts",
        color = "red"
    )
    '''

    tofStep = 0.5
    #data = emg_samples(mu=1000, sigma=200, tau=300, size=10000)

    kde = gaussian_kde(data)

    x_kde = np.linspace(min(data), max(data), 1000)
    y_kde =  kde(x_kde)
    y_kde = (y_kde / np.max(y_kde))

    '''
    plt.scatter(
        data,
        [p for p in range(len(data))],
        label = "Raw Data",
        alpha = 0.5,
        s = 5,
        edgecolors = "none"
    )
    '''

    plt.scatter(
        x_kde,
        y_kde,
        label = "KDE",
        color = "red",
        alpha = 0.5,
        s = 5,
        edgecolors = "none"
    )

    sorted_tof = np.sort(data)
    discrete_counts = { rounded_s: 0 for rounded_s in np.arange(round_to_nearest_step(sorted_tof[0], tofStep), round_to_nearest_step(sorted_tof[-1], tofStep) + 1, tofStep) }

    for s in sorted_tof:
        rounded_s = float(round_to_nearest_step(s, tofStep))

        discrete_counts[rounded_s] += 1

    cumulative_counts = np.cumsum(list(discrete_counts.values()))

    plt.scatter(
        list(discrete_counts.keys()),
        cumulative_counts/np.max(cumulative_counts),
        label = "Normalized Cumulative Counts (Cumsum)",
        alpha = 0.5,
        s = 5,
        edgecolors = "none"
    )

    derivative = np.diff(y_kde) / np.diff(x_kde)
    normale_derivative = derivative/np.max(derivative)

    plt.scatter(
        x_kde[:-1],
        normale_derivative,
        label = "Normalized Derivative of Cumulative Counts",
    )

    threshold = -0.008

    peak_index = None

    for index, value in enumerate(normale_derivative[:100]):
        print(f"{x_kde[index]} : {value}")
        
        if value < threshold:
            peak_index = index
            break


    peak_estimated_x = x_kde[peak_index]

    print("Estimated Peak ToF:", peak_estimated_x)
    print("KDE Peak ToF:", x_kde[np.argmax(y_kde)])
    print(f"Difference between estimated peak and true peak: {abs(peak_estimated_x - x_kde[np.argmax(y_kde)])}")



    plt.ylabel("Y")
    plt.xlabel("ToF")
    plt.legend()
    plt.grid(True)
    plt.savefig("peak_finder.png")