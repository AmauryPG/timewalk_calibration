from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt
from tools import histogram, split_by_first_value_range, fit_emg, calculate_fwhm
from scipy.spatial import cKDTree
from scipy.stats import gaussian_kde
from concurrent.futures import ThreadPoolExecutor, as_completed

def compute_fwhm(x, y):
    """
    Compute FWHM from sampled curve.
    """

    half_max = np.max(y) / 2

    indices = np.where(y >= half_max)[0]

    if len(indices) < 2:
        return np.inf

    return x[indices[-1]] - x[indices[0]]


def find_offset_min_fwhm(
    array1,
    array2,
    offset_range=(0, 1500),
    step=1,
    grid_size=2000
):
    """
    Find offset minimizing FWHM of combined arrays.
    """

    array1 = np.asarray(array1).ravel()
    array2 = np.asarray(array2).ravel()

    offsets = np.arange(
        offset_range[0],
        offset_range[1],
        step
    )

    # Common evaluation grid
    xmin = min(array1.min(), array2.min()) + offset_range[0]
    xmax = max(array1.max(), array2.max()) + offset_range[1]

    xgrid = np.linspace(xmin, xmax, grid_size)

    fwhms = []

    for shift in offsets:

        combined = np.concatenate([
            array1,
            array2 + shift
        ])

        kde = gaussian_kde(combined)

        y = kde(xgrid)

        fwhm = compute_fwhm(xgrid, y)

        fwhms.append(fwhm)

    fwhms = np.array(fwhms)

    best_offset = offsets[np.argmin(fwhms)]

    return best_offset, offsets, fwhms

def find_index(array1, array2,
                offset_range=(-1000, 1000),
                step=1,
                radius=20):

    array1 = np.asarray(array1).ravel()
    array2 = np.asarray(array2).ravel()

    offsets = np.arange(
        offset_range[0],
        offset_range[1],
        step
    )

    # KDTree on reference array
    tree = cKDTree(array1[:, None])

    scores = np.zeros(len(offsets))

    for i, shift in enumerate(offsets):

        shifted = array2 + shift

        neighbors = tree.query_ball_point(
            shifted[:, None],
            r=radius
        )

        scores[i] = sum(len(n) for n in neighbors)

    best_offset = offsets[np.argmax(scores)]

    return best_offset, scores, offsets

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
    upperThresholdScattering = 4.3E4
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
    plt.savefig("img/convolution/whole_share_space.png")
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
    plt.savefig("img/convolution/cutoff_share_space.png")
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

    plt.savefig("img/convolution/histogram_cutoff")

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
    plt.savefig("img/convolution/mix_share_space.png")
    plt.close()

    # -----------------------------
    nbrCanal = 8

    main_event = []

    for i in range(len(tof_filtered)):
        main_event.append((tot_filtered[i], tof_filtered[i]))

    rawCanals = split_by_first_value_range(main_event, nbrCanal)

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
    plt.savefig("img/convolution/rawCanals.png")
    plt.close()


    # -----------------------------

    for index in range(nbrCanal):
        plt.figure()

        #tot_ = [p[0] for p in rawCanals[index]]
        tof_ = [p[1] for p in rawCanals[index]]
        idx = [i for i in range(len(rawCanals[index]))]

        plt.scatter(
            tof_,
            idx,
            label=f"Convulsion canal {index}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

        plt.xlabel("ToF")
        plt.ylabel("")        
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"img/convolution/convulsionCanals_{index}.png")

    # -----------------------------

    tof_highest_energy = np.array(
        [p[1] for p in rawCanals[-1]]
    )

    tof_corrected = []
    correction_offset = []


    def process_canal(index):

        tof_ = np.array(
            [p[1] for p in rawCanals[index]]
        )

        print(f"Running optimize algo for canal {index}")

        best_offset, fwhms, offsets = find_offset_min_fwhm(
            tof_,
            tof_highest_energy,
            offset_range=(0, 1500),
            step=1
        )

        print(f"Offset canal[{index}] : {best_offset}")

        temp_tof_corrected = tof_ + best_offset

        return index, best_offset, temp_tof_corrected


    with ThreadPoolExecutor(max_workers=12) as executor:

        futures = [
            executor.submit(process_canal, index)
            for index in range(nbrCanal)
        ]

        for future in as_completed(futures):

            index, best_offset, temp_tof_corrected = future.result()

            correction_offset.append((index, best_offset))

            tof_corrected.extend(temp_tof_corrected)
            
    plt.figure()

    # Sort by first element
    pairs_sorted = sorted(correction_offset, key=lambda x: x[0])

    print(pairs_sorted)

    # Extract second column
    array_1d = np.array([p[1] for p in pairs_sorted])

    for index in range(nbrCanal):

        tot_ = [p[0] for p in rawCanals[index]]
        tof_ = [p[1] for p in rawCanals[index]]

        plt.scatter(
            tot_,
            tof_ - array_1d[index],
            label=f"Convulsion canal {index}",
            s=5,
            alpha=0.4,
            edgecolors="none"
        )

    plt.xlabel("ToT")
    plt.ylabel("ToF")        
    plt.legend()
    plt.tight_layout()
    plt.savefig("img/convolution/correctedCanals.png")


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
    plt.title("Histogram Corrected vs Original")
    plt.savefig("img/convolution/histogram.png")

    print(f"Original FWHM  : {calculate_fwhm(histogramX, fitHistogram_y)}")
    print(f"Corrected FWHM : {calculate_fwhm(histogramCorrectedX, fitHistogramCorrected_y)}")
    print(f"Original peak  : {histogramX[np.argmax(fitHistogram_y)]}")
    print(f"Corrected peak : {histogramCorrectedX[np.argmax(fitHistogramCorrected_y)]}")

    # --------------------