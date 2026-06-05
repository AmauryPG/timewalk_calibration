from tools import *
from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
from scipy.stats import gaussian_kde
from concurrent.futures import ProcessPoolExecutor, as_completed

def binless_histogram(data, n_grid=200, lam=0.01):
    """
    Binless histogram (TV-regularized density estimate).

    Parameters
    ----------
    data : array_like
        Input samples.
    n_grid : int
        Number of grid points.
    lam : float
        TV regularization strength.

    Returns
    -------
    x : ndarray
        Grid coordinates.
    pdf : ndarray
        Estimated density.
    """

    data = np.asarray(data)
    data = np.sort(data)

    xmin = data.min()
    xmax = data.max()

    x = np.linspace(xmin, xmax, n_grid)
    dx = x[1] - x[0]

    # empirical CDF sampled on grid
    z = np.searchsorted(data, x, side='right') / len(data)

    # cumulative integration operator
    A = np.tril(np.ones((n_grid, n_grid))) * dx

    # finite difference operator
    D = np.zeros((n_grid - 1, n_grid))
    for i in range(n_grid - 1):
        D[i, i] = -1.0
        D[i, i + 1] = 1.0

    def objective(u):
        fit = 0.5 * np.sum((A @ u - z) ** 2)
        tv = lam * np.sum(np.abs(D @ u))
        return fit + tv

    # initial guess: uniform density
    u0 = np.ones(n_grid)
    u0 /= np.sum(u0) * dx

    bounds = [(0.0, None)] * n_grid

    result = minimize(
        objective,
        u0,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 1000}
    )

    pdf = result.x

    # normalize
    #pdf /= np.trapezoid(pdf, x)

    return x, pdf

def timeWalkCorrection_binless(canals):
    nbrCanal = len(canals)

    rawToFCanals = []

    for canal in canals:
        rawToFCanal = [p[1] for p in canal]

        rawToFCanals.append(rawToFCanal)

    peaks = []

    for index in range(nbrCanal):

        x, y = binless_histogram(rawToFCanals[index])

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

    for canal in canals:
        rawToFCanal = [p[1] for p in canal]

        rawToFCanals.append(rawToFCanal)

    peaks = []

    for index in range(nbrCanal):

        kde = gaussian_kde(rawToFCanals[index])

        x = np.linspace(min(rawToFCanals[index]), max(rawToFCanals[index]), 1000)
        y = kde(x)

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

def get_params(canalsToF, tofBin):

    wholeArray = []

    for canal in canalsToF:
        wholeArray.extend(canal)

    histogram_x, histogram_y = histogram(
        wholeArray, tofBin
    )

    _, fithistogram_y = fit_emg(
        histogram_x,
        histogram_y
    )

    peak = histogram_x[np.argmax(fithistogram_y)]

    fwhm = calculate_fwhm(
        histogram_x,
        fithistogram_y
    )

    return fwhm, peak

def process_threshold(upperThresholdScattering,
                      tot,
                      tof,
                      tofBin,
                      nbrCanal):

    print(f"Processing upperThresholdScattering={upperThresholdScattering}...")

    tof_filtered, tof_out_filtered, tot_filtered, tot_out_filtered = cutoff(
        tot,
        tof,
        2400,
        35000,
        upperThresholdScattering,
        4E4
    )

    canalFiltered = [
        (tot_filtered[i], tof_filtered[i]) for i in range(len(tof_filtered))
    ]

    rawCanals, rawToTCanals, rawToFCanals = split_canal_by_number(
        canalFiltered,
        nbrCanal
    )

    _, correctedToFCanals_arithmetic = timeWalkCorrection_arithmetic(rawCanals)
    _, correctedToFCanals_kde = timeWalkCorrection_kde(rawCanals)
    _, correctedToFCanals_binless = timeWalkCorrection_binless(rawCanals)

    fwhm_original, peak_original = get_params(rawToFCanals, tofBin)
    fwhm_original_double, peak_original_double = get_params(rawToFCanals, 2*tofBin)
    fwhm_arithmetic, peak_arithmetic = get_params(correctedToFCanals_arithmetic, tofBin)
    fwhm_kde, peak_kde = get_params(correctedToFCanals_kde, tofBin)
    fwhm_binless, peak_binless = get_params(correctedToFCanals_binless, tofBin)

    return {
        f"original_{tofBin}": (
            upperThresholdScattering,
            fwhm_original,
            peak_original
        ),
        f"original_{2*tofBin}": (
            upperThresholdScattering,
            fwhm_original_double,
            peak_original_double
        ),
        "arithmetic": (
            upperThresholdScattering,
            fwhm_arithmetic,
            peak_arithmetic
        ),
        "kde": (
            upperThresholdScattering,
            fwhm_kde,
            peak_kde
        ),
        "binless": (
            upperThresholdScattering,
            fwhm_binless,
            peak_binless
        )
    }
if __name__ == "__main__":

    tot, tof, size = readBinaryWeerocFileWithPicoCalibrated(
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr700_56-65V_Freq80000_60s.bin"
    )

    tofBin = 12
    nbrCanal = 8

    parametersFitHistogram = {}

    thresholds = np.arange(4.5E4, 20E4, 1E3)

    with ProcessPoolExecutor() as executor:

        futures = {
            executor.submit(
                process_threshold,
                threshold,
                tot,
                tof,
                tofBin,
                nbrCanal
            ): threshold
            for threshold in thresholds
        }

        for future in as_completed(futures):

            threshold = futures[future]

            try:

                result = future.result()

                print(
                    f"Finished threshold={threshold:.0f}"
                )

                for method in result:
                    parametersFitHistogram.setdefault(method, []).append(result[method])

            except Exception as e:

                print(
                    f"Threshold {threshold:.0f} failed: {e}"
                )

    for method in parametersFitHistogram:
        parametersFitHistogram[method].sort(key=lambda x: x[0])

    np.savez(
        "parameters",
        param=parametersFitHistogram
    )

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(8, 6)
    )

    for methodName in parametersFitHistogram:

        threshold = [
            p[0]
            for p in parametersFitHistogram[methodName]
        ]

        fwhm = [
            p[1]
            for p in parametersFitHistogram[methodName]
        ]

        peak = [
            p[2]
            for p in parametersFitHistogram[methodName]
        ]

        ax1.scatter(
            threshold,
            fwhm,
            label=methodName
        )

        ax2.scatter(
            threshold,
            peak,
            label=methodName
        )

    ax1.set_xlabel("Threshold ToF [ps]")
    ax1.set_ylabel("FWHM [ps]")
    ax1.set_title(
        "Parameters on different time-walk correction methods, histogram bin=12.2 ps"
    )
    ax1.legend()

    ax2.set_xlabel("Threshold ToF [ps]")
    ax2.set_ylabel("ToF Peak [ps]")
    ax2.legend()

    plt.tight_layout()
    plt.savefig("img/combine/params.png")