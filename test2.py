from scipy.spatial import cKDTree
import numpy as np
import matplotlib.pyplot as plt

def scatter_hist_with_offset(
    x,
    offset=0,
    bins=200,
    ax=None,
    color="tab:blue",
    alpha=0.6
):
    """
    Create a scatter-style histogram from a 1D array,
    where the y-axis is the bin count index and the x-axis
    is the original value.

    Parameters
    ----------
    x : array-like
        Input 1D array (ToF values)

    offset : int
        Offset applied to histogram indices (y-axis)

    bins : int
        Number of histogram bins

    ax : matplotlib axis
        Optional axis

    color : str
        Scatter color

    alpha : float
        Point transparency
    """

    x = np.asarray(x)

    # Histogram
    counts, edges = np.histogram(x, bins=bins)

    # Bin centers
    centers = 0.5 * (edges[:-1] + edges[1:])

    # Build scatter coordinates
    xs = []
    ys = []

    for i, c in enumerate(counts):

        if c == 0:
            continue

        # Repeat x-position according to count
        xs.extend([centers[i]] * c)

        # Apply vertical offset
        ys.extend(np.arange(c) + offset)

    xs = np.array(xs)
    ys = np.array(ys)

    # Plot
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(xs, ys, s=4, alpha=alpha, color=color)

    ax.set_xlabel("ToF")
    ax.set_ylabel("Index")

    return ax

# Example data
tof1 = np.random.normal(40800, 120, 4000)
tof2 = np.random.normal(41100, 120, 4000)

# Offsets to test
offsets = np.arange(-1000, 1000, 1)

tree = cKDTree(tof1[:, None])

scores = []

for shift in offsets:
    shifted = tof2 + shift

    neighbors = tree.query_ball_point(
        shifted[:, None],
        r=20
    )

    score = sum(len(n) for n in neighbors)

    scores.append(score)

best_offset = offsets[np.argmax(scores)]

print(best_offset)

fig, ax = plt.subplots(figsize=(10, 6))

# First distribution
scatter_hist_with_offset(
    tof1,
    offset=0,
    bins=300,
    ax=ax,
    color="tab:blue"
)

# Second distribution with index offset
scatter_hist_with_offset(
    tof2,
    offset=best_offset,
    bins=300,
    ax=ax,
    color="tab:red"
)

plt.show()