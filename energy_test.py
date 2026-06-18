from histogram_methods import *
from Scripts_Radiopico.ReadBinaryWeeroc import *
import sys
import re
from tools import *

import matplotlib.pyplot as plt



if __name__ == "__main__":

    path = "/home/pala2402/Téléchargements/FWHM_test/"
    directory_path = Path(path)

    files = []

    plt.figure()
    bin = 12.2

    plt.xlabel("ToT")
    plt.ylabel("Count")

    for filePath in directory_path.iterdir():
        if(filePath.suffix != ".bin"):
            continue

        file = str(filePath)

        splitted_file = file.split("/")
        filename = splitted_file[-1]

        print(f"Filename : {filename}")
        section, gain, threshold, biais, frequency, duration = extractWeerocParameters(filename)

        if section != 2:
            continue

        if gain != 8:
            continue

        if duration != 60:
            continue

        print(f"Processing : Section={section}, Gain={gain}, Threshold={threshold}, Biais={biais}, Frequency={frequency}, Duration={duration}")

        tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(file)        

        histogram_data = []

        classical_histogram_x, classical_histogram_y = histogram(tot, bin)

        plt.scatter(
            classical_histogram_x,
            np.log10(np.array(classical_histogram_y) + 1),
            label=f"Biais={biais}, Threshold={threshold}, Gain={gain}, Number of Events={size}"
        )



    plt.legend(loc="best")
    plt.show()