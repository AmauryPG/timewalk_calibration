from Scripts_Radiopico.ReadBinaryWeeroc import *
import pyqtgraph as pg
import numpy as np
from scipy.stats import gaussian_kde

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

if __name__ == "__main__":
    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
    
    value, count, sigmoid = timeWalk_discrete(tof)
    normale_count = count / np.max(count)

    derivate_sigmoid = np.gradient(count, value)
    normale_derivate_sigmoid = derivate_sigmoid / np.max(derivate_sigmoid)

    kde = gaussian_kde(tof)

    x_kde = np.linspace(min(tof), max(tof), 10000)
    y_kde =  kde(x_kde)
    y_kde = (y_kde / np.max(y_kde))

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
        x=value,
        y=normale_count,
        size=2,
        pen='g',
        brush='w',
        name="sigmoid"
    )

    scatter_kde = pg.ScatterPlotItem(
        x=x_kde,
        y=y_kde,
        size=2,
        pen='r',
        brush='w',
        name="derived sigmoid"
    )

    scatter_derivate_sigmoid = pg.ScatterPlotItem(
        x=value,
        y=normale_derivate_sigmoid,
        size=2,
        pen='m',
        brush='w',
        name="derived sigmoid"
    )

    plt.addItem(scatter_sigmoid)
    plt.addItem(scatter_kde)
    plt.addItem(scatter_derivate_sigmoid)
    plt.addLine(x=x_kde[np.argmax(y_kde)], pen=pg.mkPen('r', width=3))

    app.exec()

