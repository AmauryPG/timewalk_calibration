from Scripts_Radiopico.ReadBinaryWeeroc import *
import pyqtgraph as pg
import numpy as np
from scipy.stats import gaussian_kde
from scipy.stats import exponnorm
from tools import *

def timeWalk_discrete_histogram(tof):
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
    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
    #tof = emg_samples(mu=1000, sigma=200, tau=400, size=10000)

    # -------------------------
    value, count, sigmoid = timeWalk_discrete_histogram(tof)

    interpolated_value, interpolated_count = interpolate_xy(value, count, num_points=10000)

    # -------------------------
    derivate_sigmoid = np.gradient(interpolated_count, interpolated_value)
    

    # -------------------------
    kde = gaussian_kde(tof)

    x_kde, y_kde =  histogram(tof, 12.2)
    

    # -------------------------
    binless_value, binless_count = smooth_path(interpolated_value, derivate_sigmoid, smoothing=20)
    binless_count = binless_count / np.max(binless_count)

    # -------------------------

    app = pg.mkQApp()

    window = pg.GraphicsLayoutWidget(show=True, title="ToF Analysis")
    window.resize(1200, 800)

    plt_0 = window.addPlot(row=0, col=0, title="")
    
    plt_0.show()
    plt_0.showGrid(x = True, y = True)
    plt_0.addLegend()

    # set properties of the label for y axis
    plt_0.setLabel('left', 'Vertical Values', units ='y')

    # set properties of the label for x axis
    plt_0.setLabel('bottom', 'ToF', units ='ps')

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
        name="Histogram classic bin=12.2ps"
    )

    scatter_binless_derivate_sigmoid = pg.PlotDataItem(
        x=binless_value,
        y=binless_count,
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

    plt_0.addItem(scatter_sigmoid)
    plt_0.addItem(scatter_kde)
    plt_0.addItem(scatter_derivate_sigmoid)
    plt_0.addItem(scatter_binless_derivate_sigmoid)

    peak = x_kde[np.argmax(y_kde)]
    peak_estimated = binless_value[np.argmax(binless_count)]

    plt_0.addLine(x=peak, pen=pg.mkPen('r', width=3))
    plt_0.addLine(x=peak_estimated, pen=pg.mkPen('g', width=3))
    
    print(f"Real peak : {peak}")
    print(f"Estimated peak : {peak_estimated}")

    print(f"FWHM Real     : {calculate_fwhm(binless_value, binless_count)}")
    print(f"FWHM Estimate : {calculate_fwhm(x_kde, y_kde)}")

    app.exec()

