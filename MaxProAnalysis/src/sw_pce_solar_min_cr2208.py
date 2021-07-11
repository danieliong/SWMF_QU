#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 11:11:14 2021

@author: ajivani
"""
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd
import itertools
import os
import re

from sklearn import linear_model as lm
import chaospy as cp

import gsa_utils

from matplotlib.backends.backend_pdf import PdfPages


# %% Define params, distributions
BrMin = cp.Uniform(-1, 1)
BrFactor_ADAPT = cp.Uniform(-1, 1)
nChromoSi_AWSoM = cp.Uniform(-1, 1)
PoyntingFluxPerBSi = cp.Uniform(-1, 1)
LperpTimeSqrtBSi = cp.Uniform(-1, 1)
StochasticExponent = cp.Uniform(-1, 1)
rMinWaveReflection = cp.Uniform(-1, 1)


# %% Build for ADAPT and AWSoM

pce_inputs = ['BrMin', 'BrFactor_ADAPT', 'nChromoSi_AWSoM', 'PoyntingFluxPerBSi', 'LperpTimesSqrtBSi', 'StochasticExponent', 'rMinWaveReflection']

distribution = cp.J(BrMin, BrFactor_ADAPT, nChromoSi_AWSoM, PoyntingFluxPerBSi, LperpTimeSqrtBSi, StochasticExponent, rMinWaveReflection)


polynomial_order = 2

# %% process data

ips_ops = pd.read_csv("./data/MaxPro_inputs_outputs_event_list_2021_04_16_09.txt")


np_less_than_100 = np.loadtxt("./Outputs/QoIs/code_v_2021_05_17/event_list_2021_04_16_09/np_less_than_hundred.txt", dtype='int')

removed_runs = np.setdiff1d(np.array(range(200)) + 1, np_less_than_100)
ips_ops_successful = ips_ops.drop(labels = removed_runs - 1, axis=0)



selected_ips = ips_ops_successful[pce_inputs]
lb = np.array([5.0, 0.54, 2e17, 0.3e6, 0.3e5, 0.1, 1])
ub = np.array([10.0, 2.7, 5e18, 1.1e6, 3e5, 0.34, 1.2])

selected_ips_std = 2 * (selected_ips - 0.5 * (lb + ub)).multiply(1/(ub - lb))
samples = np.array(selected_ips_std)
samples = samples.T

# %% get sobol and interaction indices for individual QoIs
qoi = "Np"

simFileName = os.path.join("./Outputs/QoIs/code_v_2021_05_17/event_list_2021_04_16_09", qoi + "Sim_earth.txt")


# simFileName = os.path.join("./data/code_v_2021_05_17/event_list_2021_04_16_09", qoi + "Sim_earth_trimmed_shifted.txt")

qoiArray = np.loadtxt(simFileName)
qoiArrayS = np.delete(qoiArray, removed_runs - 1, axis=1)


m, n = qoiArrayS.shape
evaluations = qoiArrayS.T[:, 0:m]



polynomial_expansion = cp.generate_expansion(polynomial_order, distribution, normed=True)


model = lm.Lasso(alpha = 0.2, fit_intercept=False)

model_approximation = cp.fit_regression(polynomial_expansion, samples, evaluations, model=model)

mean = cp.E(model_approximation, distribution)
var = cp.Var(
     model_approximation, distribution)

# calculate sobol indices (main effects)
sobol_indices = cp.Sens_m(model_approximation, distribution)
sobol_indices = pd.DataFrame(sobol_indices.T)
sobol_indices.columns = ['BrMin', 'BrFactor', 'nChromoSi', 'PoyntingFlux', 'Lperp', 'StochExp', 'rMinWaveRefl']
coordinates = np.linspace(1, m, num=m)
# %%
# Calculate order 2 interactions
interaction_effects = cp.Sens_m2(model_approximation, distribution)


# %% Make barplot
figBar, axBar = plt.subplots(1, figsize=(12, 10))
gsa_utils.sobol_indices_barplot(sobol_indices, qoi, ax=axBar)
figBar.legend(sobol_indices.columns, frameon=False, ncol=7, loc="lower center")