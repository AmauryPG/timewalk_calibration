from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import *

def round_to_nearest_step(values, step):
    """
    Round values to nearest multiple of step.
    """

    return np.round(values / step) * step

if __name__ == "__main__":

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
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

    cumulative_counts = np.cumsum(list(discrete_counts.values()))

    plt.scatter(
        list(discrete_counts.keys()),
        cumulative_counts,
        label = "Cumulative Counts (Cumsum)",
        color = "green"
    )

    plt.ylabel("Y")
    plt.xlabel("ToF")
    plt.savefig("scatter_plot.png")