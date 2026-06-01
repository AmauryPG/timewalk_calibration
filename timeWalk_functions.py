from tools import histogram, split_canal_by_first_value, fit_emg, calculate_fwhm
from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


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

    parametersFitHistogram = {}

    for upperThresholdScattering in np.arange(4.5E4, 20E4, 1E3):
        tof_filtered, tof_out_filtered, tot_filtered, tot_out_filtered = cutoff(tot, tof, 2400, 35000, upperThresholdScattering, 4E4)

        canalFiltered = []

        for i in range(len(tof_filtered)):
            canalFiltered.append((tot_filtered[i], tof_filtered[i]))

        rawCanals, rawToTCanals, rawToFCanals = split_canal_by_first_value(canalFiltered, nbrCanal)

        correction_coefficients_timewalk_arithmetic, correctedToFCanals_arithmetic = timeWalkCorrection_arithmetic(rawCanals)
        correction_coefficients_timewalk_kde, correctedToFCanals_kde = timeWalkCorrection_kde(rawCanals)
        correction_coefficients_timewalk_binless, correctedToFCanals_binless = timeWalkCorrection_binless(rawCanals)

        correctedToF_arithmetic = []
        correctedToF_kde = []
        correctedToF_binless = []

        for index in range(nbrCanal):
            tot_ = rawToTCanals[index]
            
            correctedToF_arithmetic.extend(correctedToFCanals_arithmetic[index])
            correctedToF_kde.extend(correctedToFCanals_kde[index])
            correctedToF_binless.extend(correctedToFCanals_binless[index])

        # Histogram
        histogram_arithmeticX, histogram_arithmeticY = histogram(correctedToF_arithmetic, tofBin)
        histogram_kdeX, histogram_kdeY = histogram(correctedToF_kde, tofBin)
        histogram_binlessX, histogram_binlessY = histogram(correctedToF_binless, tofBin)

        # Fit
        _, fitHistogram_arithmeticY = fit_emg(histogram_arithmeticX, histogram_arithmeticY)
        _, fitHistogram_kdeY = fit_emg(histogram_kdeX, histogram_kdeY)
        _, fitHistogram_binlessY = fit_emg(histogram_binlessX, histogram_binlessY)

        # Extract parameters about histogram fit    
        peak_arithmetic = histogram_arithmeticX[np.argmax(fitHistogram_arithmeticY)]
        peak_kde = histogram_kdeX[np.argmax(fitHistogram_kdeY)]
        peak_binless = histogram_binlessX[np.argmax(fitHistogram_binlessY)]

        fwhm_arithmetic = calculate_fwhm(histogram_arithmeticX, fitHistogram_arithmeticY)
        fwhm_kde = calculate_fwhm(histogram_kdeX, fitHistogram_kdeY)
        fwhm_binless = calculate_fwhm(histogram_binlessX, fitHistogram_binlessY)

        parametersFitHistogram.setdefault("arithmetic", []).append((upperThresholdScattering, fwhm_arithmetic, peak_arithmetic))  
        parametersFitHistogram.setdefault("kde", []).append((upperThresholdScattering, fwhm_kde, peak_kde))  
        parametersFitHistogram.setdefault("binless", []).append((upperThresholdScattering, fwhm_binless, peak_binless))  


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

            plt.scatter(
                histogram_binlessX,
                histogram_binlessY,
                label=f"Binless",
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

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

    np.savez("parameters", parametersFitHistogram)

    for methodName in parametersFitHistogram:

        threshold = [p[0] for p in parametersFitHistogram[methodName]]
        fwhm = [p[1] for p in parametersFitHistogram[methodName]]
        peak = [p[2] for p in parametersFitHistogram[methodName]]

        ax1.scatter(
            threshold,
            fwhm,
            label=f"{methodName}"
        )

        ax2.scatter(
            threshold,
            peak,
            label=f"{methodName}"
        )

    ax1.set_xlabel("Threshold ToF [ps]")
    ax1.set_ylabel("FWHM [ps]")
    ax1.set_title(f"Parameters on different time-walk correction methods, histogram bin=12.2ps")
    ax1.legend()

    ax2.set_xlabel("Threshold ToF [ps] ")
    ax2.set_ylabel("ToF Peak [ps]")
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig("img/combine/params.png")