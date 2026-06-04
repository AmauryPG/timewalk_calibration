from timeWalk_functions import *
from tools import *

if __name__ == "__main__":

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    nbrCanal = 8
    canalFiltered = []
    binWidth = 12

    threshold = 2400

    for i in range(size):
        if tot[i] > threshold and tot[i] < 4E4 and tof[i] < 4.5E4:
            canalFiltered.append((tot[i], tof[i]))

    rawCanals, rawToTCanals, rawToFCanals = split_canal_by_number(canalFiltered, nbrCanal)
    correction_coefficients_timewalk_kde, correctedToFCanals_kde = timeWalkCorrection_kde(rawCanals)
    correctedHistogramToF, correctedHistogramToF_canals = canals_to_histogram(correctedToFCanals_kde, binWidth=binWidth)

    print(f"Correction coefficients (kde): {correction_coefficients_timewalk_kde}")

    plt.close()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 6))

    for index in range(nbrCanal):
        ax1.scatter(rawToTCanals[index],
                    rawToFCanals[index],
                    label=f"Canal {index}",
                    s=5,
                    alpha=0.4,
                    edgecolors="none")
        
    ax1.set_xlabel("ToT")
    ax1.set_ylabel("ToF")
    ax1.set_title("Raw Data")
    ax1.legend()

    arr = np.array(rawToTCanals, dtype=object)

    for index in range(nbrCanal):
        ax2.scatter(rawToTCanals[index],
                    correctedToFCanals_kde[index],
                    label=f"Canal {index}",
                    s=5,
                    alpha=0.4,
                    edgecolors="none")
        
    ax2.set_xlabel("ToT")
    ax2.set_ylabel("ToF")
    ax2.set_title("Corrected Raw Data")
    ax2.legend()
    
    ax3.plot(
        correctedHistogramToF[0],
        correctedHistogramToF[1],
        label="Corrected Histogram",
    )

    originalHistogramX, originalHistogramY = histogram([p[1] for p in canalFiltered], binWidth=binWidth)

    ax3.plot(
        originalHistogramX,
        originalHistogramY,
        label="Original Histogram",
    )

    ax3.set_xlabel("ToF")
    ax3.set_ylabel("Count")
    ax3.set_title("Combined Histogram")
    ax3.legend()

    plt.show()