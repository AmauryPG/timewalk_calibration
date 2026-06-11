from Scripts_Radiopico.ReadBinaryWeeroc import *
import pyqtgraph as pg
import numpy as np
from scipy.stats import gaussian_kde
from scipy.stats import exponnorm
from tools import *
import matplotlib.pyplot as plt

def integral_count(array):
    integral = {}

    tof_sorted = np.sort(array)

    for index, event in enumerate(tof_sorted):
        if event in integral:
            integral[event] = integral[event] + 1
        else:
            integral[event] = index + 1

    value = list(integral.keys())
    count = list(integral.values())

    return value, count, integral


def discrete_histogram(tof, num_points=100000):
    
    # Integral 
    value, count, _ = integral_count(tof)

    # Smooth out the integral
    interpolated_value, interpolated_count = interpolate_xy(value, count, num_points=num_points)

    # Differential
    derivate_sigmoid = np.gradient(interpolated_count, interpolated_value)

    return interpolated_value, derivate_sigmoid


def cumulative_integral(x, y):
    """
    Compute cumulative integral of y with respect to x.

    Parameters
    ----------
    x : array-like
        X values.
    y : array-like
        Y values.

    Returns
    -------
    x_int : np.ndarray
        Same x values.
    y_int : np.ndarray
        Cumulative integral at each x.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    dx = np.diff(x)
    areas = 0.5 * (y[:-1] + y[1:]) * dx

    y_int = np.concatenate([[0], np.cumsum(areas)])

    return y_int

def emg_samples(mu, sigma, tau, size=10000):
    K = tau / sigma
    return exponnorm.rvs(K=K, loc=mu, scale=sigma, size=size)

def main_test_data():
    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
    #tof = emg_samples(mu=1000, sigma=200, tau=400, size=10000)

    tof = tof[tof < 50000]

    # -------------------------
    bin = 12.2
    x_histogram, y_histogram = histogram(tof, bin)
    #y_histogram = y_histogram / np.max(y_histogram)

    # -------------------------
    
    # Integral 
    value, count, _ = integral_count(tof)

    # Smooth out the integral
    number_points = 10000
    interpolated_value, interpolated_count = interpolate_xy(value, count, num_points=number_points)

    # Differential
    derivate_sigmoid = np.gradient(interpolated_count, interpolated_value)

    print(np.max(y_histogram) / np.max(derivate_sigmoid))

    derivate_sigmoid = derivate_sigmoid * bin

    # -------------------------


    app = pg.mkQApp()

    window = pg.GraphicsLayoutWidget(show=True, title="ToF Analysis")
    window.resize(1200, 800)

    plt_0 = window.addPlot(row=0, col=0, title="")
    
    plt_0.show()
    plt_0.showGrid(x = True, y = True)
    plt_0.addLegend()

    # set properties of the label for y axis
    plt_0.setLabel('left', 'Count', units ='A.U.')
    #plt_0.setLabel('left', 'Normalized Count', units ='A.U.')

    # set properties of the label for x axis
    plt_0.setLabel('bottom', 'ToF', units ='ps')

    scatter_binless = pg.ScatterPlotItem(
        x=interpolated_value,
        y=derivate_sigmoid,
        size=2,
        pen='r',
        brush='w',
        name=f"Bin less histogram points={number_points}"
    )

    scatter_integral = pg.ScatterPlotItem(
        x=interpolated_value,
        y=interpolated_count,
        size=2,
        pen='w',
        brush='w',
        name=f"Interpolated integral points={number_points}"
    )

    scatter_histogram = pg.ScatterPlotItem(
        x=x_histogram,
        y=y_histogram,
        size=2,
        pen='w',
        brush='w',
        name=f"Histogram bin={bin}"
    )


    plt_0.addItem(scatter_binless)
    plt_0.addItem(scatter_histogram)


    app.exec()

def main_method():
    K = 2.0        # Shape parameter (higher K means a longer exponential tail)
    loc = 20      # Mean of the underlying Gaussian component
    scale = 10   # Standard deviation of the underlying Gaussian component
    size = 100000    # Number of data points to generate

    bin = 2

    emg_dataset = exponnorm.rvs(K, loc=loc, scale=scale, size=size)
    id_histogram_x, id_histogram_y = discrete_histogram(emg_dataset, 100)
    id_histogram_y = id_histogram_y * bin

    index_coefficient = np.argmax(id_histogram_y)


    coefficient = id_histogram_y[index_coefficient]

    histogram_x, histogram_y = histogram(emg_dataset, bin)

    print(f"cof {coefficient}")
    print(f"peak id     : {np.max(id_histogram_y)}")
    print(f"peak hist   : {np.max(histogram_y)}")
    print(f"Ratio peaks : {np.max(histogram_y) / np.max(id_histogram_y)}")

    bin_edges = np.arange(min(emg_dataset), max(emg_dataset) + bin, bin)

    plt.hist(
        emg_dataset,
        bins=bin_edges, 
        color="r"
    )

    plt.scatter(
        id_histogram_x,
        id_histogram_y,
        label="ID method"
    )

    plt.plot(
        histogram_x,
        histogram_y,
        label=f"Histogram method bin={bin}"
    )
    

    plt.title("Exponentially Modified Gaussian (EMG) Dataset")
    plt.xlabel("Value")
    plt.ylabel("Count")
    plt.legend()
    plt.show()



if __name__ == "__main__":
    #main_test_data()
    main_method()