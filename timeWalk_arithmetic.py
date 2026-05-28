from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import histogram, split_canal_by_first_value, fit_emg, calculate_fwhm


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
    upperThresholdScattering = 7.5E4
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
    plt.savefig("img/arithmetic/whole_share_space.png")
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
    
    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("ToF/ToT of main events")

    plt.tight_layout()
    plt.savefig("img/arithmetic/cutoff_share_space.png")
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

    plt.savefig("img/arithmetic/histogram_cutoff")

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
    plt.savefig("img/arithmetic/mix_share_space.png")
    plt.close()

    # -----------------------------
    nbrCanal = 8

    main_event = []

    for i in range(len(tof_filtered)):
        main_event.append((tot_filtered[i], tof_filtered[i]))

    rawCanals = split_canal_by_first_value(main_event, nbrCanal)

    plt.figure()

    canalsToF = []

    meanToT = []
    meanToF = []

    for index in range(nbrCanal):
        tot_ = [p[0] for p in rawCanals[index]]
        tof_ = [p[1] for p in rawCanals[index]]

        canalsToF.append(tof_)

        meanToT.append(tot_[len(tot_)//2])
        meanToF.append(np.mean(tof_))

        plt.scatter(
            tot_,
            tof_,
            label=f"Canal {index+1}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Canal splitted")
    
    plt.legend()
    plt.tight_layout()
    plt.savefig("img/arithmetic/rawCanals.png")
    plt.close()

    plt.figure()
    
    for index in range(nbrCanal):

        plt.scatter(
            meanToT[index],
            meanToF[index],
            label=f"Mean Canal {index+1}",
        )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Canal splitted")
    
    plt.legend()
    plt.tight_layout()
    plt.savefig("img/arithmetic/meansCanals.png")
    plt.close()


    correction = meanToF[-1] - meanToF[:-1]
    correction = np.append(correction, 0)

    print(f"Correction : {correction}")
    
    plt.figure()

    tof_corrected = []
    
    for index in range(nbrCanal):
        tot_ = [p[0] for p in rawCanals[index]]
        tof_ = [p[1] for p in rawCanals[index]]

        tof_corrected.extend(tof_ + correction[index])

        plt.scatter(
            tot_,
            tof_ - correction[index],
            label=f"Canal {index+1}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Canal splitted Corrected")
    plt.savefig("img/arithmetic/correctedCanals.png")

    np.savez('data_tof_arithmetic.npz', array1=tof_corrected)

    histogramCorrectedX, histogramCorrectedY = histogram(tof_corrected, tofBin)
    histogramX, histogramY = histogram(tof_filtered, tofBin)

    # Fit
    params, fitHistogram_y = fit_emg(histogramX, histogramY)
    params, fitHistogramCorrected_y = fit_emg(histogramCorrectedX, histogramCorrectedY)

    plt.figure()

    plt.plot(
        histogramCorrectedX,
        fitHistogramCorrected_y,
        label="Fit corrected"
    )

    plt.plot(
        histogramX,
        fitHistogram_y,
        label="Fit original"
    )

    plt.scatter(
        histogramCorrectedX,
        histogramCorrectedY,
        label="Corrected"
    )

    plt.scatter(
        histogramX,
        histogramY,
        label="Original"
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.legend()
    plt.title("Histogram with Arithmetic Alignment Corrected vs Original")
    plt.savefig("img/arithmetic/histogram.png")

    print(f"Original FWHM  : {calculate_fwhm(histogramX, fitHistogram_y)}")
    print(f"Corrected FWHM : {calculate_fwhm(histogramCorrectedX, fitHistogramCorrected_y)}")
    print(f"Original peak  : {histogramX[np.argmax(fitHistogram_y)]}")
    print(f"Corrected peak : {histogramCorrectedX[np.argmax(fitHistogramCorrected_y)]}")

    # --------------------

