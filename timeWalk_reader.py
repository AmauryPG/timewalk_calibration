import numpy as np
import matplotlib.pyplot as plt

with np.load('parameters.npz') as parametersFitHistogram:
    print("Available arrays:", parametersFitHistogram.files)

    print(parametersFitHistogram['arr_0'])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

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
    plt.show()