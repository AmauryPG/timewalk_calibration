from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import histogram, split_by_first_value_range

def linear_regression(x, y):
    """
    Simple linear regression:
        y = m*x + b

    Returns:
        m -> slope
        b -> intercept
    """

    n = len(x)

    # Means
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    # Numerator and denominator
    numerator = 0.0
    denominator = 0.0

    for xi, yi in zip(x, y):
        numerator += (xi - x_mean) * (yi - y_mean)
        denominator += (xi - x_mean) ** 2

    # Slope
    m = numerator / denominator

    # Intercept
    b = y_mean - m * x_mean

    return m, b

if __name__ == "__main__":

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )
    tofBin = 12

    # Convert everything to numpy arrays
    tot = np.asarray(tot, dtype=np.float64)
    tof = np.asarray(tof, dtype=np.float64)

    lowerThresholdNoise = 2400
    upperThresholdNoise = 35000
    upperThresholdScattering = 4.2E4
    lowerThresholdScattering = 4E4

    # -----------------------------
    # Full scatter plot
    # -----------------------------
    plt.scatter(
        tot,
        tof,
        s=5,
        alpha=0.4,
        edgecolors="none"
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Share space")

    plt.axvline(
        x=lowerThresholdNoise,
        color='r',
        linestyle='--',
        label='Remove noise'
    )

    plt.axvline(
        x=upperThresholdNoise,
        color='r',
        linestyle='--',
        label='Remove peak'
    )

    plt.axhline(
        y=upperThresholdScattering,
        color='g',
        linestyle='--',
        label="Remove scattering"
    )

    plt.axhline(
        y=lowerThresholdScattering,
        color='b',
        linestyle='--',
        label="Remove pre events"
    )

    plt.xlim(0, 50000)
    plt.ylim(0, 200000)

    plt.legend()
    plt.tight_layout()
    plt.savefig("img/whole_share_space.png")
    plt.close()

    # -----------------------------
    # Vectorized filtering
    # -----------------------------
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

    # -----------------------------
    # Linear regression
    # -----------------------------
    slope, intercept = np.polyfit(
        tot_filtered,
        tof_filtered,
        1
    )

    c_array = slope * tot_filtered + intercept

    m, b = linear_regression(tot_filtered, tof_filtered)

    print(f"Slope : " + str(m))

    print(f"Intercept : " + str(b))

    # Optional sorting for clean line display
    sort_idx = np.argsort(tot_filtered)

    x_fit = tot_filtered[sort_idx]
    y_fit = c_array[sort_idx]

    # -----------------------------
    # Filtered points + fit
    # -----------------------------
    plt.figure()

    plt.scatter(
        tot_filtered,
        tof_filtered,
        s=5,
        alpha=0.4,
        edgecolors="none"
    )

    plt.plot(
        x_fit,
        y_fit,
        color='r',
        label='Linear fit'
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("ToF/ToT of main events")

    plt.legend()
    plt.tight_layout()
    plt.savefig("img/cutoff_share_space.png")
    plt.close()

    # -----------------------------
    # Histogram
    plt.figure()

    histogramX, histogramY = histogram(tof_filtered, tofBin)

    plt.scatter(
        histogramX,
        histogramY
    )
    plt.xlabel("Bin ToF")
    plt.ylabel("Count")
    plt.title("Histogram ToF for the main event")

    plt.savefig("img/histogram_cutoff")

    # -----------------------------
    # Keep / removed comparison
    # -----------------------------
    plt.figure()

    plt.scatter(
        tot_filtered,
        tof_filtered,
        s=5,
        alpha=0.4,
        edgecolors="none",
        label='Data keep'
    )

    plt.scatter(
        tot_out_filtered,
        tof_out_filtered,
        s=5,
        alpha=0.4,
        edgecolors="none",
        color='r',
        label='Data removed'
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Keep and remove data")

    plt.legend()
    plt.tight_layout()
    plt.savefig("img/mix_share_space.png")
    plt.close()

    # -----------------------------
    nbrCanal = 8

    main_event = []

    for i in range(len(tof_filtered)):
        main_event.append((tot_filtered[i], tof_filtered[i]))

    rawCanals = split_by_first_value_range(main_event, nbrCanal)

    plt.figure()

    canalsToF = []

    for index in range(nbrCanal):
        tot_ = [p[0] for p in rawCanals[index]]
        tof_ = [p[1] for p in rawCanals[index]]

        canalsToF.append(tof_)

        plt.scatter(
            tot_,
            tof_,
            label=f"Canal {index+1}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

    plt.plot(
        x_fit,
        y_fit,
        color='r',
        label='Linear fit'
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Canal splitted")
    
    plt.legend()
    plt.tight_layout()
    plt.savefig("img/rawCanals.png")
    plt.close()
    
    var_tof = []
    tof_mean = np.mean(tof_filtered)

    for canal in canalsToF:
        var_tof.append(np.sum(canal - tof_mean))

    var_tof = np.array(var_tof)
    var_tof_transpose = np.array([var_tof]).T

    canalWidth = (np.max(tot_filtered) - np.min(tot_filtered))/nbrCanal

    correction_coefficients = (-(var_tof[-1]/((nbrCanal-1) * canalWidth)) * np.linalg.pinv(var_tof_transpose[:-1]))[0]

    print(f"Correction coefficients : {correction_coefficients}")

    canalsToFCorrected = []

    for canalIndex in range(len(canalsToF[:-1])):
        canalsToFCorrected.append([x + correction_coefficients[canalIndex] for x in canalsToF[canalIndex]])

    canalsToFCorrected.append(canalsToF[-1])

    tof_corrected = []

    plt.figure()

    for index in range(nbrCanal):
        tot_ = [p[0] for p in rawCanals[index]]
        tof_ = canalsToFCorrected[index]

        tof_corrected.extend(tof_)
        
        plt.scatter(
            tot_,
            tof_,
            label=f"Canal {index+1}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )


    m, b = linear_regression(tot_filtered, tof_corrected)

    c_array = m * tot_filtered + b

    print(f"Slope : " + str(m))

    print(f"Intercept : " + str(b))

    # Optional sorting for clean line display
    sort_idx = np.argsort(tot_filtered)

    x_fit = tot_filtered[sort_idx]
    y_fit = c_array[sort_idx]

    plt.plot(
        x_fit,
        y_fit,
        label="correlation"
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Canal splitted corrected")
    
    plt.legend()
    plt.tight_layout()
    plt.savefig("img/correctedCanals.png")
    plt.close()

    plt.figure()

    plt.scatter(
        tot_filtered,
        tof_corrected,
        s=5,
        alpha=0.4,
        edgecolors="none"
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("WHole ToF corrected")

    plt.tight_layout()
    plt.savefig("img/wholeCorrectedCanals.png")
    plt.close()

    # ---------------------

    correctedHistogramX, correctedHistogramY = histogram(tof_corrected, tofBin)

    plt.figure()

    plt.scatter(
        correctedHistogramX,
        correctedHistogramY
    )

    plt.xlabel("Bin ToF")
    plt.ylabel("Count")
    plt.title("Histogram ToF for the main event")

    plt.savefig("img/histogram_cutoff_corrected")


    plt.figure()

    plt.scatter(
        histogramX,
        histogramY,
        label="Original"
    )

    plt.scatter(
        correctedHistogramX,
        correctedHistogramY,
        label="Corrected"
    )

    plt.xlabel("Bin ToF")
    plt.ylabel("Count")
    plt.title("Histogram ToF for the main event")

    plt.savefig("img/histogram_compare")