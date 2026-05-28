from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import histogram, split_by_first_value_range, fit_emg, calculate_fwhm


if __name__ == "__main__":

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "/home/daniel/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    integral_tot = []
    integral_tof = []

    cumulative_tot = 0
    cumulative_tof = 0

    upperThresholdNoise = 35000

    for i in range(len(tot)):
        cumulative_tof += tof[i]
        cumulative_tot += tot[i]

        integral_tof.append(cumulative_tof)
        integral_tot.append(cumulative_tot)

    x = [i for i in range(len(tot))]

    plt.scatter(
        tot,
        integral_tof,
        s=5,
        alpha=0.4,
        edgecolors="none"
    )

    #plt.axhline(y=np.log10(upperThresholdNoise))

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    #plt.savefig("img/integral/tot")
    plt.show()

    plt.figure()

    plt.scatter(
        tof,
        integral_tot,
        s=5,
        alpha=0.4,
        edgecolors="none"
    )

    plt.xlabel("ToF")
    plt.ylabel("ToT")
    plt.savefig("img/integral/tof")

    plt.figure()


    plt.scatter(
        np.log10(integral_tot),
        np.log10(integral_tof),
        s=5,
        alpha=0.4,
        edgecolors="none"
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.savefig("img/integral/combine")
