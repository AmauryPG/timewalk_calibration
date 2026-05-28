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

def timeWalkCorrection_kde(events):
    rawToFCanals = [p[1] for p in events]

    peaks = []

    for index in range(len(events)):

        my_kde = sns.kdeplot(rawToFCanals[index])
        line = my_kde.lines[0]
        x, y = line.get_data()

        index_peak_y = np.argmax(y)

        peaks.append(x[index_peak_y])

    # Calculate the offset for each energy canal
    correction_timewalk = peaks[-1] - peaks[:-1]

    # Add 0 offset for the highest energy canal
    correction_timewalk = np.append(correction_timewalk, 0)

    correctedToFCanals = rawToFCanals + correction_timewalk

    return correction_timewalk, correctedToFCanals

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

    tof_filtered, tof_out_filtered, tot_filtered, tot_out_filtered = cutoff(tot, tof, 2400, 35000, 7.5E4, 4E4)

    canalFiltered = []

    for i in range(len(tof_filtered)):
        canalFiltered.append((tot_filtered[i], tof_filtered[i]))

    rawCanals, rawToTCanals, rawToFCanals = split_canal_by_first_value(canalFiltered, nbrCanal)

    correction_coefficients_timewalk, correctedToFCanals = timeWalkCorrection_arithmetic(rawCanals)

    correctedToF = []

    for index in range(nbrCanal):
        tot_ = rawToTCanals[index]
        tof_ = correctedToFCanals[index]

        correctedToF.extend(tof_)

        plt.scatter(
            tot_, 
            tof_,
            label=f"Canal {index}, Offset {correction_coefficients_timewalk[index]}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )
    
    plt.xlabel("ToT")
    plt.ylabel("ToF")
    plt.title("Time-Walk Corrected")
    
    plt.legend()
    plt.tight_layout()
    plt.savefig("img/combine/correctedCanals.png")
    plt.close()