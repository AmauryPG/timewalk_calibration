import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist

# Example data
tof1 = np.random.normal(40800, 120, 4000)
tof2 = np.random.normal(41100, 120, 4000)

# Offsets to test
offsets = np.arange(-1000, 1000, 1)

sigma = 20   # matching width
scores = []

for shift in offsets:

    shifted = tof2 + shift

    # pairwise distances
    d = cdist(tof1[:, None], shifted[:, None])

    # Gaussian overlap
    score = np.sum(np.exp(-(d**2)/(2*sigma**2)))

    scores.append(score)

scores = np.array(scores)

best_offset = offsets[np.argmax(scores)]

print("Best offset:", best_offset)

# Plot score curve
plt.plot(offsets, scores)
plt.axvline(best_offset, color='red')
plt.xlabel("Offset")
plt.ylabel("Overlap score")
plt.title("Offset optimization")
plt.show()