#!/usr/bin/env python3

# Resolving imports for the common module
import common

import argparse as ap
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

def plot_spectrum(particle, case, particles, active, inactive, algorithm, sim_type):
  delta_df   = pd.read_csv(f'./{case}/{sim_type}_delta_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')
  surface_df = pd.read_csv(f'./{case}/{sim_type}_surface_{algorithm}_{particle}_spectrum_p{particles}_ab{active}_ib{inactive}.csv')

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
  spec_ax.set_xlabel('Energy [eV]')
  spec_ax.set_ylabel(f'{particle} flux [n-cm/eV-src]')
  spec_ax.grid()
  spec_ax.legend()
  spec_fig.suptitle(algorithm)
  spec_fig.savefig(f'./{case}/figures/{algorithm}_{particle}_spectrum_comp_p{particles}_ab{active}_ib{inactive}.png')
  plt.close()

def main():
  parser = ap.ArgumentParser(prog = 'Compare Spectrum',
                             description = 'Compares the spectrum between delta tracking and surface tracking.')
  parser.add_argument('--type', type = str, dest = 'sim_type', default="single",
                      help = 'The type of simulation. Options are \'single\' and \'coupled\'.')
  parser.add_argument('--alg', type = str, dest = 'algorithm', default="history",
                      help = 'The Monte Carlo algorithm. Options are \'history\' and \'event\'.')
  parser.add_argument(type = str, dest = 'case',
                      help = 'Results to post-process in the format \'model\'/\'case\'. As an example, for a fresh LWR pincell this would be lwr/fresh_pincell')
  parser = common.particle_args(parser)
  args = parser.parse_args()

  particles = []
  if args.sim_type == "single":
    particles = ['neutron']
  elif args.sim_type == "coupled":
    particles = ['neutron', 'photon']

  if args.algorithm not in ['history', 'event']:
    raise Exception('Incorrect algorithm! Options are \'history\' or \'event\'')

  for particle in particles:
    for score in common.SCORES:
      plot_spectrum(particle, args.case, args.particles, args.active_batches,
                    args.inactive_batches, args.algorithm, args.sim_type)


if __name__ == "__main__":
  main()
