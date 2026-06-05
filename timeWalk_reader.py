import numpy as np
import matplotlib.pyplot as plt

parametersFitHistogram = np.load('parameters.npz', allow_pickle=True)

print("Available arrays:", parametersFitHistogram.files)

param = parametersFitHistogram['param'].item()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

for methodName in param.keys():
    if methodName != "original_12" and methodName != "original_24":
        continue

    print(f"Method: {methodName}")

    threshold = [p[0] for p in param[methodName]]
    fwhm = [p[1] for p in param[methodName]]
    peak = [p[2] for p in param[methodName]]

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

    ax1.ticklabel_format(style='plain', axis='y')
    ax1.ticklabel_format(useOffset=False)

plt.tight_layout()

plt.show()