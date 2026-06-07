from Scripts_Radiopico.ReadBinaryWeeroc import *
import pyqtgraph as pg
import numpy as np
from scipy.stats import gaussian_kde
from scipy.stats import exponnorm
from tools import *

def timeWalk_discrete(tof):
    returnArray = {}

    tof_sorted = np.sort(tof)

    for index, event in enumerate(tof_sorted):
        if event in returnArray:
            returnArray[event] = returnArray[event] + 1
        else:
            returnArray[event] = index + 1

    value = list(returnArray.keys())
    count = list(returnArray.values())

    return value, count, returnArray


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
    #tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
    #    "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    #)
    tof = emg_samples(mu=1000, sigma=200, tau=400, size=10000)

    # -------------------------
    value, count, sigmoid = timeWalk_discrete(tof)

    interpolated_value, interpolated_count = interpolate_xy(value, count)

    # -------------------------
    derivate_sigmoid = np.gradient(interpolated_count, interpolated_value)
    

    # -------------------------
    integral_sigmoid = cumulative_integral(interpolated_count, interpolated_value)

    # -------------------------
    kde = gaussian_kde(tof)

    x_kde = np.linspace(min(tof), max(tof), 10000)
    y_kde =  kde(x_kde)
    

    # -------------------------
    binless_value, binless_count = smooth_interpolate_savgol(interpolated_value, derivate_sigmoid)

    # -------------------------

    app = pg.mkQApp()

    plt = pg.PlotWidget()
    plt.show()
    plt.showGrid(x = True, y = True)
    plt.addLegend()

    # set properties of the label for y axis
    plt.setLabel('left', 'Vertical Values', units ='y')

    # set properties of the label for x axis
    plt.setLabel('bottom', 'ToF', units ='ps')

    scatter_sigmoid = pg.ScatterPlotItem(
        x=interpolated_value,
        y=interpolated_count / np.max(interpolated_count),
        size=2,
        pen='g',
        brush='w',
        name="sigmoid"
    )

    scatter_kde = pg.ScatterPlotItem(
        x=x_kde,
        y=y_kde / np.max(y_kde),
        size=2,
        pen='r',
        brush='w',
        name="kde sigmoid"
    )

    scatter_binless_derivate_sigmoid = pg.PlotDataItem(
        x=binless_value,
        y=binless_count / np.max(binless_count),
        pen='m',
        name="interpolated derived sigmoid"
    )

    scatter_derivate_sigmoid = pg.ScatterPlotItem(
        x=interpolated_value,
        y=derivate_sigmoid / np.max(derivate_sigmoid),
        size=2,
        pen='m',
        brush='w',
        name="derived sigmoid"
    )

    scatter_integral_sigmoid = pg.ScatterPlotItem(
        x=interpolated_value,
        y=integral_sigmoid / np.max(integral_sigmoid),
        size=2,
        pen='w',
        brush='w',
        name="integral sigmoid"
    )


    plt.addItem(scatter_sigmoid)
    plt.addItem(scatter_kde)
    plt.addItem(scatter_derivate_sigmoid)
    plt.addItem(scatter_integral_sigmoid)
    plt.addItem(scatter_binless_derivate_sigmoid)

    peak = x_kde[np.argmax(y_kde)]
    peak_estimated = binless_value[np.argmax(binless_count)]

    plt.addLine(x=peak, pen=pg.mkPen('r', width=3))
    plt.addLine(x=peak_estimated, pen=pg.mkPen('g', width=3))
    
    print(f"Real peak : {peak}")
    print(f"Estimated peak : {peak_estimated}")

    app.exec()

