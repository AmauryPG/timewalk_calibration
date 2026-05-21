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

def split_paired_arrays(A, B, N):
    if len(A) != len(B):
        raise ValueError("A and B must have the same length")

    k, m = divmod(np.max(A), N)

    A_split = []
    B_split = []
    boundaries = [k * i for i in range(0, N + 1)]

    for i in range(N):
        mask = (A >= boundaries[i]) & (A < boundaries[i + 1])
        A_split.append(A[mask])
        B_split.append(B[mask])

    return A_split, B_split, k

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
        "~/Documents/data/measures/21_avril/data_section_2_Btot49_Btoa12_Gain10_Thr600_56V_Freq80000_240s.bin"
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

    print(f"Slope Before Correction : " + str(slope))

    print(f"Intercept Before Correction : " + str(intercept))

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
    nbrCanal = 8
    tot_canal, tof_canal, canal_split_value = split_paired_arrays(tot_filtered, tof_filtered, nbrCanal)

    plt.figure()

    plt.scatter(
        tot_filtered,
        tof_filtered,
        s=5,
        alpha=0.4,
        edgecolors="none",
        label='Data keep'
    )

    for i in range(nbrCanal):
        plt.axvline(
            x=canal_split_value * i,
            color='r',
            linestyle='--',
            label="Canal cutoff " + str(i)
        )

        plt.scatter(
            tot_canal[i],
            tof_canal[i],
            s=5,
            alpha=0.4,
            edgecolors="none",
            label='Canal ' + str(i)
        )

    plt.xlabel("ToT")
    plt.ylabel("ToF corrected")
    plt.title("Canal cutoff")   
    plt.savefig("canal_timewalk_canal.png")

    # -----------------------------
    tof_filtered_mean = np.mean(tof_filtered)
    tof_matrix = np.zeros(nbrCanal-1)
    N = [canal_split_value * i for i in range(1, nbrCanal)]

    for i in range(nbrCanal-1):
        no_highest_canal = np.sum(tof_canal[i] - tof_filtered_mean)

    highest_canal = np.sum(tof_canal[-1] - tof_filtered_mean)

    inverse_matrix = np.linalg.inv(no_highest_canal.reshape(-1, 1))

    correction_time_walk = np.dot(-highest_canal, inverse_matrix)
    
    correction = correction_time_walk / N
    correction = np.append(correction, 0)

    print(f"Correction values : " + str(correction))

    tof_corrected = np.array([])
    for i in range(nbrCanal):
        temp = tof_canal[i] + correction[i]
        tof_corrected = np.append(tof_corrected, temp)

    tot_filtered = tot_filtered[:-1]
    # -----------------------------
    # Linear regression
    # -----------------------------
    slope, intercept = np.polyfit(
        tot_filtered,
        tof_corrected,
        1
    )

    c_array = slope * tot_filtered + intercept

    print(f"Slope After Correction : " + str(slope))

    print(f"Intercept After Correction : " + str(intercept))

    # Optional sorting for clean line display
    sort_idx = np.argsort(tot_filtered)

    x_fit = tot_filtered[sort_idx]
    y_fit = c_array[sort_idx]

    plt.figure()

    plt.scatter(
        tot_filtered,
        tof_corrected,
        s=5,
        alpha=0.4,
        edgecolors="none",
        label='Canal ' + str(i)
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
    plt.savefig("canal_timewalk_corrected.png")