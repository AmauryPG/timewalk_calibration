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
    pdf /= np.trapezoid(pdf, x)

    return x, pdf

import matplotlib.pyplot as plt

np.random.seed(0)

data = np.concatenate([
    np.random.normal(-1, 0.3, 500),
    np.random.normal( 1, 0.2, 500)
])

x, pdf = binless_histogram(data, n_grid=300, lam=0.02)

plt.hist(data, bins=40, density=True, alpha=0.3)
plt.plot(x, pdf, lw=2, color="red")
plt.show()