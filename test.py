import numpy as np
from scipy.stats import exponnorm
from scipy.optimize import minimize_scalar

mu = 0
sigma = 1
tau = 2

K = tau / sigma

pdf = lambda x: exponnorm.pdf(x, K, loc=mu, scale=sigma)

res = minimize_scalar(
    lambda x: -pdf(x),
    bounds=(mu - 5*sigma, mu + 10*tau),
    method='bounded'
)

x_peak = res.x
y_peak = pdf(x_peak)

print(x_peak, y_peak)