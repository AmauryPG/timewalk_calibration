from Scripts_Radiopico.ReadBinaryWeeroc import *
import numpy as np
import matplotlib.pyplot as plt


def offsetTimeWalk(lowerX, upperX, wholeX):

    lowerXNP = np.asarray(lowerX, dtype=np.float64)
    upperXNP = np.asarray(upperX, dtype=np.float64)
    X = np.asarray(wholeX, dtype=np.float64)

    k0 = len(lowerXNP)
    meanX = np.mean(X)
    k = -np.sum(upperXNP - meanX) / (k0 * np.sum(lowerXNP - meanX))

    return k

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
        "/home/daniel/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr600_56V_Freq80000_240s.bin"
    )

    # Convert everything to numpy arrays
    tot = np.asarray(tot, dtype=np.float64)
    tof = np.asarray(tof, dtype=np.float64)

    lowerThresholdNoise = 2400
    upperThresholdScattering = 4.5E4
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
    plt.savefig("whole_share_space.png")
    plt.close()

    # -----------------------------
    # Vectorized filtering
    # -----------------------------
    mask = (
        (tot > lowerThresholdNoise) &
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

    print(f"Slope : " + str(slope))
    print(f"Slope R: " + str(m))

    print(f"Intercept : " + str(intercept))
    print(f"Intercept R: " + str(b))

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
    plt.title("Point real events")

    plt.legend()
    plt.tight_layout()
    plt.savefig("cutoff_share_space.png")
    plt.close()

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
    plt.savefig("mix_share_space.png")
    plt.close()

    # -----------------------------
    canalCutoff = (max(tot_filtered) - min(tot_filtered)) // 2

    plt.figure()

    plt.axvline(
        x=canalCutoff,
        color='r',
        linestyle='--',
        label="Canal cutoff"
    )

    plt.scatter(
        tot_filtered,
        tof_filtered,
        s=5,
        alpha=0.4,
        edgecolors="none",
        label='Data keep'
    )

    plt.plot(
        x_fit,
        y_fit,
        color='r',
        label='Linear fit'
    )

    plt.xlabel("ToT")
    plt.ylabel("ToF corrected")
    plt.title("Canal cutoff")   
    plt.savefig("canal_timewalk_canal.png")

    tot_lower = np.array([])
    tof_lower = np.array([])
    tot_upper = np.array([])
    tof_upper = np.array([])

    for i in range(len(tot_filtered)):
        if tot_filtered[i] < canalCutoff:
            tot_lower = np.append(tot_lower, tot_filtered[i])
            tof_lower = np.append(tof_lower, tof_filtered[i])
        else:
            tot_upper = np.append(tot_upper, tot_filtered[i])
            tof_upper = np.append(tof_upper, tof_filtered[i])

    # -----------------------------
    correctionFactor = offsetTimeWalk(tof_lower, tof_upper, tof_filtered)

    print(f"Correction factor: {correctionFactor}")

    tof_corrected = np.append((tof_lower + correctionFactor), tof_upper)

    slope, intercept = np.polyfit(
        tot_filtered,
        tof_corrected,
        1
    )

    c_array = slope * tot_filtered + intercept

    m, b = linear_regression(tot_filtered, tof_corrected)

    print(f"Slope : " + str(slope))
    print(f"Slope R: " + str(m))

    print(f"Intercept : " + str(intercept))
    print(f"Intercept R: " + str(b))

    # Optional sorting for clean line display
    sort_idx = np.argsort(tot_filtered)

    x_fit = tot_filtered[sort_idx]
    y_fit = c_array[sort_idx]
    
    plt.figure()

    plt.axvline(
        x=canalCutoff,
        color='r',
        linestyle='--',
        label="Canal cutoff"
    )

    plt.scatter(
        tot_filtered,
        tof_corrected,
        s=5,
        alpha=0.4,
        edgecolors="none",
        label='Data keep'
    )


    plt.plot(
        x_fit,
        y_fit,
        color='r',
        label='Linear fit'
    )


    plt.xlabel("ToT")
    plt.ylabel("ToF corrected")
    plt.title("Corrected time walk")   
    plt.savefig("canal_timewalk_correction.png")