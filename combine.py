import numpy as np
import matplotlib.pyplot as plt
from tools import histogram, split_by_first_value_range, fit_emg, calculate_fwhm
from Scripts_Radiopico.ReadBinaryWeeroc import *

if __name__ == "__main__":
    files = [
        "data_tof_arithmetic.npz",
        "data_tof_kde.npz"
    ]

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    # Convert everything to numpy arrays
    tot = np.asarray(tot, dtype=np.float64)
    tof = np.asarray(tof, dtype=np.float64)

    lowerThresholdNoise = 2400
    upperThresholdNoise = 35000
    upperThresholdScattering = 4.3E4
    lowerThresholdScattering = 4E4

    mask = (
        (tot > lowerThresholdNoise) &
        (tot < upperThresholdNoise) &
        (tof < upperThresholdScattering) &
        (tof > lowerThresholdScattering)
    )

    tot_filtered = tot[mask]
    tof_filtered = tof[mask]

    tot_out_filtered = tot[~mask]
    tof_out_filtered = tof[~mask]

    tofBin = 12.2

    tof_arrays = []

    for file in files:
        temp_data = np.load(file)

        tof_arrays.append(temp_data["array1"])

    histogramX, histogramY = histogram(tof_filtered, tofBin)
    params, fitHistogram_y = fit_emg(histogramX, histogramY)
    
    plt.plot(
        histogramX,
        fitHistogram_y,
        label="Fit original"
    )

    plt.scatter(
        histogramX,
        histogramY,
    )

    # Displays 'corrected' data
    for index, tof_corrected in enumerate(tof_arrays):

        histogramCorrectedX, histogramCorrectedY = histogram(tof_corrected, tofBin)

        # Fit
        params, fitHistogramCorrected_y = fit_emg(histogramCorrectedX, histogramCorrectedY)

        plt.plot(
            histogramCorrectedX,
            fitHistogramCorrected_y,
            label=f"Fit corrected [{files[index]}]"
        )

        plt.scatter(
            histogramCorrectedX,
            histogramCorrectedY,
        )

        print(f"Corrected peak [{files[index]}]: {histogramCorrectedX[np.argmax(fitHistogramCorrected_y)]}")
        print(f"Corrected FWHM [{files[index]}]: {calculate_fwhm(histogramCorrectedX, fitHistogramCorrected_y)}")


    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.legend()
    plt.title("Histogram with Different Alignment Methods Corrected vs Original")
    plt.savefig("img/combine/histogram.png")

    print(f"Original FWHM  : {calculate_fwhm(histogramX, fitHistogram_y)}")
    print(f"Original peak  : {histogramX[np.argmax(fitHistogram_y)]}")