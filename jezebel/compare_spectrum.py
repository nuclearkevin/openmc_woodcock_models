#!/usr/bin/env python3

import argparse as ap
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

def main():
  parser = ap.ArgumentParser(prog = 'Compare Spectrum', description = 'Compares the spectrum between delta tracking and surface tracking.')
  parser.add_argument('-p', type = int, dest = 'particles', default = 1000,
                      help = 'Number of particles to run per batch. Defaults to 1000.')
  parser.add_argument('--active', type = int, dest = 'active_batches', default = 1000,
                      help='Number of active batches. Defaults to 1000.')
  parser.add_argument('--inactive', type = int, dest = 'inactive_batches', default = 100,
                      help = 'Number of inactive batches. Defaults to 100.')
  args = parser.parse_args()

  delta_df   = pd.read_csv(f'./delta_spectrum_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv')
  surface_df = pd.read_csv(f'./surface_spectrum_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv')

  energy_delta  = delta_df['lower_edges'].to_numpy()
  energy_delta = np.append(energy_delta, delta_df['upper_edges'].to_numpy()[-1])
  delta_mean = delta_df['mean'].to_numpy()
  delta_three_sigma = delta_df['3_sigma'].to_numpy()

  energy_surface  = surface_df['lower_edges'].to_numpy()
  energy_surface = np.append(energy_surface, surface_df['upper_edges'].to_numpy()[-1])
  surface_mean = surface_df['mean'].to_numpy()
  surface_three_sigma = surface_df['3_sigma'].to_numpy()

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
  spec_ax.set_xlabel('Energy [eV]')
  spec_ax.set_ylabel('Flux [n-cm/eV-src]')
  spec_ax.grid()
  spec_ax.legend()
  spec_fig.savefig(f'./figures/spectrum_comp_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.png')
  plt.show()

if __name__ == "__main__":
  main()
