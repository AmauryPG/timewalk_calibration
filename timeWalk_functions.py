from tools import histogram, split_canal_by_first_value, fit_emg, calculate_fwhm
from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

def timeWalkCorrection_arithmetic(canals):
    nbrCanal = len(canals)

    rawToFCanals = []
    meanToFCanals = []

    for canal in canals:
        rawToFCanal = [p[1] for p in canal]

        rawToFCanals.append(rawToFCanal)
        meanToFCanals.append(np.mean(rawToFCanal))


    # Calculate the offset for each energy canal
    correction_coefficients_timewalk = meanToFCanals[-1] - meanToFCanals[:-1]

    # Add 0 offset for the highest energy canal
    correction_coefficients_timewalk = np.append(correction_coefficients_timewalk, 0)

    correctedToFCanals = []

    for index in range(nbrCanal):
        correctedToFCanals.append(rawToFCanals[index] + correction_coefficients_timewalk[index])

    return correction_coefficients_timewalk, correctedToFCanals

def timeWalkCorrection_kde(canals):
    nbrCanal = len(canals)

    rawToFCanals = []
    meanToFCanals = []

    for canal in canals:
        rawToFCanal = [p[1] for p in canal]

        rawToFCanals.append(rawToFCanal)
        meanToFCanals.append(np.mean(rawToFCanal))

    peaks = []

    for index in range(nbrCanal):

        my_kde = sns.kdeplot(rawToFCanals[index])
        line = my_kde.lines[0]
        x, y = line.get_data()

        index_peak_y = np.argmax(y)

        peaks.append(x[index_peak_y])

    # Calculate the offset for each energy canal
    correction_coefficients_timewalk = peaks[-1] - peaks[:-1]

    # Add 0 offset for the highest energy canal
    correction_coefficients_timewalk = np.append(correction_coefficients_timewalk, 0)

    correctedToFCanals = []

    for index in range(nbrCanal):
        correctedToFCanals.append(rawToFCanals[index] + correction_coefficients_timewalk[index])

    return correction_coefficients_timewalk, correctedToFCanals

def cutoff(tot, tof,
            lowerThresholdNoise,
            upperThresholdNoise,
            upperThresholdScattering,
            lowerThresholdScattering):
    
    # Convert everything to numpy arrays
    tot = np.asarray(tot, dtype=np.float64)
    tof = np.asarray(tof, dtype=np.float64)

    # Vectorized filtering
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

    return tof_filtered, tof_out_filtered, tot_filtered, tot_out_filtered

if __name__ == "__main__":

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    tofBin = 12
    nbrCanal = 8
    boolGraph = False

    tof_filtered, tof_out_filtered, tot_filtered, tot_out_filtered = cutoff(tot, tof, 2400, 35000, 7.5E4, 4E4)

    canalFiltered = []

    for i in range(len(tof_filtered)):
        canalFiltered.append((tot_filtered[i], tof_filtered[i]))

    rawCanals, rawToTCanals, rawToFCanals = split_canal_by_first_value(canalFiltered, nbrCanal)

    correction_coefficients_timewalk_arithmetic, correctedToFCanals_arithmetic = timeWalkCorrection_arithmetic(rawCanals)
    correction_coefficients_timewalk_kde, correctedToFCanals_kde = timeWalkCorrection_kde(rawCanals)

    correctedToF_arithmetic = []
    correctedToF_kde = []

    for index in range(nbrCanal):
        tot_ = rawToTCanals[index]
        
        correctedToF_arithmetic.extend(correctedToFCanals_arithmetic[index])
        correctedToF_kde.extend(correctedToFCanals_kde[index])

    # Histogram
    histogram_arithmeticX, histogram_arithmeticY = histogram(correctedToF_arithmetic, tofBin)
    histogram_kdeX, histogram_kdeY = histogram(correctedToF_kde, tofBin)

    # Fit
    params, fitHistogram_arithmeticY = fit_emg(histogram_arithmeticX, histogram_arithmeticY)
    params, fitHistogram_kdeY = fit_emg(histogram_kdeX, histogram_kdeY)

    # Extract parameters about histogram fit    
    peak_arithmetic = histogram_arithmeticX[np.argmax(fitHistogram_arithmeticY)]
    peak_kde = histogram_kdeX[np.argmax(fitHistogram_kdeY)]

    fwhm_arithmetic = calculate_fwhm(histogram_arithmeticX, fitHistogram_arithmeticY)
    fwhm_kde = calculate_fwhm(histogram_kdeX, fitHistogram_kdeY)


    if boolGraph:
        plt.figure()

        plt.plot(
            histogram_arithmeticX,
            fitHistogram_arithmeticY
        )

        plt.plot(
            histogram_kdeX,
            fitHistogram_kdeY
        )

        plt.scatter(
            histogram_arithmeticX,
            histogram_arithmeticY,
            label=f"Arithmetic",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

        plt.scatter(
            histogram_kdeX,
            histogram_kdeY,
            label=f"KDE",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

        plt.xlabel("ToF")
        plt.ylabel("Count")
        plt.title(f"Different time-walk correction methods bin width={tofBin}")
        
        plt.legend()
        plt.tight_layout()
        plt.show()
        #plt.savefig("img/combine/compare.png")