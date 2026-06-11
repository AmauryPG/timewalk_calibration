import numpy as np
from tools import *
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter

from timeWalk_discret import *
from timeWalk_functions import *

tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
    "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
)

lowerToFThreshold = 7.5E4

app = pg.mkQApp()

window = pg.GraphicsLayoutWidget(show=True, title="ToF Analysis")
window.resize(1200, 800)

plt_0 = window.addPlot(row=0, col=0, title="")

for threshold in np.arange(lowerToFThreshold, np.max(tof), 1E4):
    #cut_tof = tof[tof < threshold]
    threshold = pg.InfiniteLine(
        pos=0.5,
        angle=90,      # vertical line
        movable=True,
        pen='r'
    )

    plt_0.addItem(threshold)