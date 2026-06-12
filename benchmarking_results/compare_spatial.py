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

def l2_err_spatial(particle, path, particles, active, inactive, algorithm):
  if particle == 'photon':
    delta_df   = pd.read_csv(f'./{path}/coupled_delta_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/coupled_surface_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')
  else:
    delta_df   = pd.read_csv(f'./{path}/single_delta_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/single_surface_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')

  return np.sqrt(np.sum(np.pow(delta_df['total_mean'].to_numpy() - surface_df['total_mean'].to_numpy(), 2.0)))

def linf_err_spatial(particle, path, particles, active, inactive, algorithm):
  if particle == 'photon':
    delta_df   = pd.read_csv(f'./{path}/coupled_delta_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/coupled_surface_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')
  else:
    delta_df   = pd.read_csv(f'./{path}/single_delta_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')
    surface_df = pd.read_csv(f'./{path}/single_surface_{algorithm}_{particle}_mesh_p{particles}_ab{active}_ib{inactive}.csv')

  return np.max(np.abs(delta_df['total_mean'].to_numpy() - surface_df['total_mean'].to_numpy()))

def plot_error_l2_spatial():
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
          data[particle][case].append(l2_err_spatial(particle, path, particles, 1000, 100, 'history'))
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
    ax.set_ylabel('$L_{2}$ Error (total reactions / src)')
    ax.legend(ncol=3, loc='upper right')
    ax.set_title(f'{particle.capitalize()} Spatial Total Reaction Rates')
    fig.tight_layout()
    fig.savefig(f'./figures/spatial/{particle}_spatial_l2_err.png')

def plot_error_linf_spatial():
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
          data[particle][case].append(linf_err_spatial(particle, path, particles, 1000, 100, 'history'))
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
    ax.set_ylabel('$L_{\\infty}$ Error (total reactions / src)')
    ax.legend(ncol=3, loc='upper right')
    fig.tight_layout()
    fig.savefig(f'./figures/spatial/{particle}_spatial_linf_err.png')

def main():
  plot_error_l2_spatial()
  plot_error_linf_spatial()

if __name__ == "__main__":
  main()
