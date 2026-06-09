from Scripts_Radiopico.ReadBinaryWeeroc import *
import pyqtgraph as pg
import numpy as np
from scipy.stats import gaussian_kde
from scipy.stats import exponnorm
from tools import *

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


def timeWalk_discrete_histogram(tof, num_points=100000):
    
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

if __name__ == "__main__":
    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
    #tof = emg_samples(mu=1000, sigma=200, tau=400, size=10000)

    tof = tof[tof < 50000]

    # -------------------------
    bin = 12.2
    x_histogram, y_histogram = histogram(tof, bin)
    y_histogram = y_histogram / np.max(y_histogram)

    # -------------------------
    
    # Integral 
    value, count, _ = integral_count(tof)

    # Smooth out the integral
    interpolated_value_small, interpolated_count_small = interpolate_xy(value, count, num_points=100000)
    interpolated_value_big, interpolated_count_big = interpolate_xy(value, count, num_points=1000000)

    # Differential
    derivate_sigmoid_small = np.gradient(interpolated_count_small, interpolated_value_small)
    derivate_sigmoid_big = np.gradient(interpolated_count_big, interpolated_value_big)

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

    scatter_histogram = pg.ScatterPlotItem(
        x=x_histogram,
        y=y_histogram,
        size=2,
        pen='m',
        brush='w',
        name=f"Histogram bin width={bin}"
    )

    scatter_integral_big = pg.ScatterPlotItem(
        x=interpolated_value_big,
        y=interpolated_count_big,
        size=2,
        pen='w',
        brush='w',
        name="Interpolated integral points=1000000"
    )

    scatter_binless_big = pg.ScatterPlotItem(
        x=interpolated_value_big,
        y=derivate_sigmoid_big,
        size=2,
        pen='r',
        brush='w',
        name="Bin less histogram points=1000000"
    )

    scatter_integral_small = pg.ScatterPlotItem(
        x=interpolated_value_small,
        y=interpolated_count_small,
        size=2,
        pen='w',
        brush='w',
        name="Interpolated integral points=100000"
    )

    scatter_binless_small = pg.ScatterPlotItem(
        x=interpolated_value_small,
        y=derivate_sigmoid_small,
        size=2,
        pen='g',
        brush='w',
        name="Bin less histogram points=100000"
    )

    plt_0.addItem(scatter_binless_big)
    plt_0.addItem(scatter_binless_small)


    app.exec()

