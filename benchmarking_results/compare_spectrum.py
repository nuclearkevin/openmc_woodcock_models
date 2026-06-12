#!/usr/bin/env python3

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

CASES = {
  'jezebel' : [''],
  'lwr' : ['fresh_pincell'],
  'sfr' : ['fresh_pincell'],
  'htgr' : ['fresh_compact']
}

CASE_LABELS = {
  'jezebel/' : 'Jezebel',
  'lwr/fresh_pincell' : 'LWR Pincell',
  'sfr/fresh_pincell' : 'SFR Pincell',
  'htgr/fresh_compact' : 'HTGR Compact ($15\\%$ PF)'
}

def plot_spectrum(case, particle, path, particles, active, inactive, algorithm):
  if particle == 'photon':
    delta_df   = pd.read_csv(f'./{path}/coupled_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/coupled_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
  else:
    delta_df   = pd.read_csv(f'./{path}/single_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/single_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')

  energy_delta  = delta_df['lower_edges'].to_numpy()
  energy_delta = np.append(energy_delta, delta_df['upper_edges'].to_numpy()[-1])
  delta_mean = delta_df['mean'].to_numpy()
  delta_three_sigma = 3.0 * delta_df['sigma'].to_numpy()

  energy_surface  = surface_df['lower_edges'].to_numpy()
  energy_surface = np.append(energy_surface, surface_df['upper_edges'].to_numpy()[-1])
  surface_mean = surface_df['mean'].to_numpy()
  surface_three_sigma = 3.0 * surface_df['sigma'].to_numpy()

  spec_fig, spec_ax = plt.subplots()
  spec_ax.step(energy_delta[:-1], delta_mean / np.diff(energy_delta), where='post', label = 'Delta Tracking Mean', color='tab:blue')
  spec_ax.fill_between(energy_delta[:-1], (delta_mean - delta_three_sigma) / np.diff(energy_delta),
                        (delta_mean + delta_three_sigma) / np.diff(energy_delta), facecolor='tab:blue', alpha=0.5,
                        label = 'Delta Tracking $3\\sigma$', step='post')
  spec_ax.step(energy_surface[:-1], surface_mean / np.diff(energy_surface), where='post', label = 'Surface Tracking Mean', color='tab:orange')
  spec_ax.fill_between(energy_surface[:-1], (surface_mean - surface_three_sigma) / np.diff(energy_surface),
                        (surface_mean + surface_three_sigma) / np.diff(energy_surface), facecolor='tab:orange', alpha=0.5,
                        label = 'Surface Tracking $3\\sigma$', step='post')
  spec_ax.set_xscale('log')
  spec_ax.set_yscale('log')
  spec_ax.set_xlabel('Energy (eV)')
  spec_ax.set_ylabel(f'{particle.capitalize()} Flux (particles-cm / eV-src)')
  spec_ax.grid()
  spec_ax.legend()
  spec_ax.set_title(f'{CASE_LABELS[path]} - 100000 Particles per Batch')
  spec_fig.savefig(f'./figures/spectra/{case}_{particle}_spectrum_comp.png')
  plt.close()

def l2_err_spectrum(particle, path, particles, active, inactive, algorithm):
  if particle == 'photon':
    delta_df   = pd.read_csv(f'./{path}/coupled_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/coupled_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
  else:
    delta_df   = pd.read_csv(f'./{path}/single_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/single_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')

  return np.sqrt(np.sum(np.pow(delta_df['mean'].to_numpy() - surface_df['mean'].to_numpy(), 2.0)))

def linf_err_spectrum(particle, path, particles, active, inactive, algorithm):
  if particle == 'photon':
    delta_df   = pd.read_csv(f'./{path}/coupled_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/coupled_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
  else:
    delta_df   = pd.read_csv(f'./{path}/single_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/single_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')

  return np.max(np.abs(delta_df['mean'].to_numpy() - surface_df['mean'].to_numpy()))

def plot_error_l2_spectrum():
  data = {}
  for particle in ['neutron', 'photon']:
    first = ''
    sim_type = 'coupled' if particle == 'photon' else 'single'
    fig, ax = plt.subplots()
    data[particle] = {}
    num_proc = 0
    for case in CASES.keys():
      for subcase in CASES[case]:
        path = f'{case}/{subcase}'
        data[particle][case] = []
        for particles in [1000, 10000, 100000]:
          data[particle][case].append(l2_err_spectrum(particle, path, particles, 1000, 100, 'history'))
        ax.scatter([1000, 10000, 100000], data[particle][case], label=CASE_LABELS[path], zorder=3)

        # Add a line for sqrt(N) convergence.
        mid = (data[particle][case][0] / np.sqrt(10.0) +  data[particle][case][1] + data[particle][case][2] * np.sqrt(10.0)) / 3.0
        sqrt_n = [mid * np.sqrt(10.0), mid, mid / np.sqrt(10.0)]
        num_proc += 1
        if num_proc == 4:
          ax.plot([1000, 10000, 100000], sqrt_n, color='black', label = '$1/\\sqrt{N}$', zorder=0)
        else:
          ax.plot([1000, 10000, 100000], sqrt_n, color='black', zorder=0)

    ax.loglog()
    ax.grid()
    ax.set_xlabel('Particles per Batch (-)')
    ax.set_ylabel('$L_{2}$ Error (particles-cm / eV-src)')
    ax.legend(ncol=3, loc='upper right')
    ax.set_title(f'{particle.capitalize()} Flux Error')
    fig.tight_layout()
    fig.savefig(f'./figures/spectra/{particle}_spectrum_l2_err.png')

def plot_error_linf_spectrum():
  data = {}
  for particle in ['neutron', 'photon']:
    first = ''
    sim_type = 'coupled' if particle == 'photon' else 'single'
    fig, ax = plt.subplots()
    data[particle] = {}
    num_proc = 0
    for case in CASES.keys():
      for subcase in CASES[case]:
        path = f'{case}/{subcase}'
        data[particle][case] = []
        for particles in [1000, 10000, 100000]:
          data[particle][case].append(linf_err_spectrum(particle, path, particles, 1000, 100, 'history'))
        ax.scatter([1000, 10000, 100000], data[particle][case], label=CASE_LABELS[path], zorder=3)

        # Add a line for sqrt(N) convergence.
        mid = (data[particle][case][0] / np.sqrt(10.0) +  data[particle][case][1] + data[particle][case][2] * np.sqrt(10.0)) / 3.0
        sqrt_n = [mid * np.sqrt(10.0), mid, mid / np.sqrt(10.0)]
        num_proc += 1
        if num_proc == 4:
          ax.plot([1000, 10000, 100000], sqrt_n, color='black', label = '$1/\\sqrt{N}$', zorder=0)
        else:
          ax.plot([1000, 10000, 100000], sqrt_n, color='black', zorder=0)

    ax.loglog()
    ax.grid()
    ax.set_xlabel('Particles per Batch (-)')
    ax.set_ylabel('$L_{\\infty}$ Error (particles-cm / eV-src)')
    ax.legend(ncol=3, loc='upper right')
    ax.set_title(f'{particle.capitalize()} Spectra')
    fig.tight_layout()
    fig.savefig(f'./figures/spectra/{particle}_spectrum_linf_err.png')

def main():
  plot_error_l2_spectrum()
  plot_error_linf_spectrum()

  # Plot the actual spectras
  for case in CASES.keys():
    for subcase in CASES[case]:
      path = f'{case}/{subcase}'
      for particle in ['neutron', 'photon']:
        plot_spectrum(case, particle, path, 100000, 1000, 100, 'history')


if __name__ == "__main__":
  main()
