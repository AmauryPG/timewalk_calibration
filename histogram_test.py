from histogram_methods import *
from Scripts_Radiopico.ReadBinaryWeeroc import *
import sys

import matplotlib.pyplot as plt

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Need the file path")
        exit(1)

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(sys.argv[1])

    fig, axes = plt.subplots(2, 1, figsize=(10, 4))

    axes[0].set_xlabel("ToF")
    axes[0].set_ylabel("Count")
    axes[1].set_xlabel("ToF")
    axes[1].set_ylabel("Normalized Count")

    histogram_data = []

    classical_histogram_x, classical_histogram_y = histogram(tof, 12.2)
    #kde_histogram_x, kde_histogram_y = kde(tof)
    id_histogram_x, id_histogram_y = id(tof)

    histogram_data.append(("Classical Histogram", classical_histogram_x, classical_histogram_y))
    #histogram_data.append(("KDE Histogram", kde_histogram_x, kde_histogram_y))
    histogram_data.append(("ID Histogram", id_histogram_x, id_histogram_y))

    for data in histogram_data:
        axes[0].scatter(
            data[1],
            data[2],
            label=data[0]
        )

        axes[1].scatter(
                data[1],
                data[2] / np.max(data[2]),
                label=data[0]
            )

    axes[0].legend(loc="best")
    axes[1].legend(loc="best")
    plt.show()