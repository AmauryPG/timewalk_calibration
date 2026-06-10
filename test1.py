import numpy as np
from tools import *
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter

from timeWalk_discret import *
from timeWalk_functions import *

def unitTest_extract_params(function, tof):
    histogramLike_x, histogramLike_y = function(tof)

    peak = histogramLike_x[np.argmax(histogramLike_y)]
    fwhm = calculate_fwhm(histogramLike_x, histogramLike_y)

    return peak, fwhm, histogramLike_x, histogramLike_y

palette = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # olive
    "#17becf",  # cyan
]

def test_1(tof, tot, listTest):

    app = pg.mkQApp()

    window = pg.GraphicsLayoutWidget(show=True, title="ToF Analysis")
    window.resize(1200, 800)

    plt_0 = window.addPlot(row=0, col=0, title="")
    plt_1 = window.addPlot(row=1, col=0, title="")
    
    plt_0.show()
    plt_0.showGrid(x = True, y = True)
    legend_0 = plt_0.addLegend()
    legend_0.setBrush(pg.mkBrush(255, 255, 255, 255)) 
    legend_0.setPen(pg.mkPen(0, 0, 0, 255))
    legend_0.setLabelTextColor(pg.mkColor('k'))

    plt_0.setLabel('left', 'Count', units ='A.U.')
    plt_0.setLabel('bottom', 'ToF', units ='ps')

    plt_1.show()
    plt_1.showGrid(x = True, y = True)

    legend_1 = plt_1.addLegend()
    legend_1.setBrush(pg.mkBrush(255, 255, 255, 255)) 
    legend_1.setPen(pg.mkPen(0, 0, 0, 255))
    legend_1.setLabelTextColor(pg.mkColor('k'))

    plt_1.setLabel('left', 'Count Normalized', units ='A.U.')
    plt_1.setLabel('bottom', 'ToF', units ='ps')

    params = {}

    for index, testFunction in enumerate(listTest):
        tempPeak, tempFWHM, x, y = unitTest_extract_params(testFunction, tof)

        color = palette[index % len(palette)]

        scatter_histogram = pg.ScatterPlotItem(
            x, 
            y,
            name=f"{testFunction.__name__}",
            brush=color,
            pen=color
        )

        scatter_histogram_normalized = pg.ScatterPlotItem(
            x, 
            y/np.max(y),
            name=f"{testFunction.__name__}",
            brush=color,
            pen=color
        )

        plt_0.addItem(scatter_histogram)
        plt_1.addItem(scatter_histogram_normalized)

        params[testFunction.__name__] = (tempPeak, tempFWHM)
    
    exporter = ImageExporter(window.scene())

    exporter.parameters()['width'] = 2000  # optional, controls resolution

    exporter.export('whole_histograms.png')

    with open("test1.txt", "w", encoding="utf-8") as FILE:
        header = f"{'Histogram Method':<30} | {'Peak':<8} : {'FWHM':<8}"

        print(header)
        FILE.write(header)
        FILE.write("\n")

        for param in params:
            result = f"{param:<30} | {params[param][0]:.2f} : {params[param][1]:.2f}"
            print(result)
            FILE.write(result)
            FILE.write("\n")

def test_2(tof, tot, listTest):

    lowerToFThreshold = 7.5E4

    app = pg.mkQApp()

    window = pg.GraphicsLayoutWidget(show=True, title="ToF Analysis")
    window.resize(1200, 800)

    plt_0 = window.addPlot(row=0, col=0, title="")
    plt_1 = window.addPlot(row=1, col=0, title="")
    
    plt_0.show()
    plt_0.showGrid(x = True, y = True)
    legend_0 = plt_0.addLegend()
    legend_0.setBrush(pg.mkBrush(255, 255, 255, 255)) 
    legend_0.setPen(pg.mkPen(0, 0, 0, 255))
    legend_0.setLabelTextColor(pg.mkColor('k'))

    plt_0.setLabel('left', 'FWHM', units ='ps')
    plt_0.setLabel('bottom', 'Threshold ToF', units ='ps')

    plt_1.show()
    plt_1.showGrid(x = True, y = True)

    legend_1 = plt_1.addLegend()
    legend_1.setBrush(pg.mkBrush(255, 255, 255, 255)) 
    legend_1.setPen(pg.mkPen(0, 0, 0, 255))
    legend_1.setLabelTextColor(pg.mkColor('k'))

    plt_1.setLabel('left', 'Peak', units ='ps')
    plt_1.setLabel('bottom', 'Threshold ToF', units ='ps')


    for index, testFunction in enumerate(listTest):
        color = palette[index % len(palette)]

        thresholds = []
        fwhm_list = []
        peak_list = []

        print(f"Processing method {testFunction.__name__}")

        for threshold in np.arange(lowerToFThreshold, np.max(tof), 1E4):
            cut_tof = tof[tof < threshold]
            
            print(f"Processing threshold : {threshold}")

            tempPeak, tempFWHM, x, y = unitTest_extract_params(testFunction, cut_tof)

            thresholds.append(threshold)
            fwhm_list.append(tempFWHM)
            peak_list.append(tempPeak)

        
        scatter_peaks = pg.ScatterPlotItem(
            thresholds, 
            peak_list,
            name=f"{testFunction.__name__}",
            brush=color,
            pen=color
        )

        scatter_fwhm = pg.ScatterPlotItem(
            thresholds, 
            fwhm_list,
            name=f"{testFunction.__name__}",
            brush=color,
            pen=color
        )

        plt_0.addItem(scatter_fwhm)
        plt_1.addItem(scatter_peaks)

    app.exec()


if __name__ == "__main__":
    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    listTest = [histogram, discrete_histogram, kde_histogram, binless_histogram]

    test_1(tof, tot, listTest)
    test_2(tof, tot, listTest)
    