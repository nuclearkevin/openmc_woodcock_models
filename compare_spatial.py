#!/usr/bin/env python3

# Resolving imports for the common module
import common

import argparse as ap
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.colors as colors

def spatial_plot_n_sigma(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm):
  delta_points = int(np.ceil(np.sqrt(len(delta_df['x'].to_numpy()))))
  xx_delta = delta_df['x'].to_numpy().reshape(delta_points, delta_points)
  yy_delta = delta_df['y'].to_numpy().reshape(delta_points, delta_points)
  # Delta tracking results
  delta_mean = delta_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)
  delta_sigma = delta_df[f'{score}_sigma'].to_numpy().reshape(delta_points, delta_points)
  # Surface tracking results.
  surface_mean = surf_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)
  surface_sigma = surf_df[f'{score}_sigma'].to_numpy().reshape(delta_points, delta_points)

  # Compute 1, 2, and 3 sigma bounds.
  comparison = np.ones_like(delta_mean) * 4.0
  for i in range(3, 0, -1):
    delta_n_sigma_l = delta_mean - i * delta_sigma
    delta_n_sigma_u = delta_mean + i * delta_sigma
    surf_n_sigma_l = surface_mean - i * surface_sigma
    surf_n_sigma_u = surface_mean + i * surface_sigma
    delta_in_surf = (delta_mean >= surf_n_sigma_l) & (delta_mean <= surf_n_sigma_u)
    surf_in_delta = (surface_mean >= delta_n_sigma_l) & (surface_mean <= delta_n_sigma_u)
    comparison[delta_in_surf | surf_in_delta] = i

    comparison[delta_mean == 0.0] = np.inf

  cmap = plt.get_cmap('viridis', 4)

  fig_comp, ax_rel = plt.subplots()
  bar = ax_rel.pcolormesh(xx_delta, yy_delta, comparison, cmap=cmap, vmin=0.5, vmax=4.5)
  cbar = fig_comp.colorbar(bar, ax=ax_rel, label = f'$n\\sigma$ Agreement')
  cbar.ax.set_yticklabels(['', '1', '', '2', '', '3', '', '>3', ''])
  fig_comp.tight_layout()
  fig_comp.savefig(f'./{case}/figures/{algorithm}_{particle}_{score}_nsigma_agreement_p{particles}_ab{active_batches}_ib{inactive_batches}.png')
  plt.close()

def spatial_plot_mean(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm):
  delta_points = int(np.ceil(np.sqrt(len(delta_df['x'].to_numpy()))))
  xx_delta = delta_df['x'].to_numpy().reshape(delta_points, delta_points)
  yy_delta = delta_df['y'].to_numpy().reshape(delta_points, delta_points)
  delta_mean = delta_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)
  surface_mean = surf_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)

  # Compute the colour bar bounds.
  total_min = np.minimum(delta_mean.min(), surface_mean.min())
  total_max = np.maximum(delta_mean.max(), surface_mean.max())

  # Plot the score spatial distribution.
  fig_comp, [ax_delta, ax_surf] = plt.subplots(ncols=2)
  fig_comp.set_size_inches(w = 12.0, h = 5.5)
  im_1 = ax_delta.pcolormesh(xx_delta, yy_delta, delta_mean, vmin = total_min, vmax = total_max)
  ax_delta.set_title('Delta Tracking')
  im_2 = ax_surf.pcolormesh(xx_delta, yy_delta, surface_mean, vmin = total_min, vmax = total_max)
  ax_surf.set_title('Surface Tracking')
  fig_comp.colorbar(im_1, ax=ax_delta, label = f'{common.SCORE_NAMES[score]} {common.SCORE_UNITS[score]}')
  fig_comp.colorbar(im_2, ax=ax_surf, label = f'{common.SCORE_NAMES[score]} {common.SCORE_UNITS[score]}')
  fig_comp.tight_layout()
  fig_comp.savefig(f'./{case}/figures/{algorithm}_{particle}_{score}_dis_p{particles}_ab{active_batches}_ib{inactive_batches}.png')
  plt.close()

def spatial_plot_stat_rel(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm):
  delta_points = int(np.ceil(np.sqrt(len(delta_df['x'].to_numpy()))))
  xx_delta = delta_df['x'].to_numpy().reshape(delta_points, delta_points)
  yy_delta = delta_df['y'].to_numpy().reshape(delta_points, delta_points)
  # Compute statistical relative error for delta tracking.
  delta_mean = delta_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)
  delta_sigma = delta_df[f'{score}_sigma'].to_numpy().reshape(delta_points, delta_points)
  delta_rel = delta_sigma / delta_mean
  # Compute statistical relative error for surface tracking.
  surface_mean = surf_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)
  surface_sigma = surf_df[f'{score}_sigma'].to_numpy().reshape(delta_points, delta_points)
  surface_rel = surface_sigma / surface_mean

  # Compute the colour bar bounds.
  delta_rel[np.isnan(delta_rel)] = -1.0 * np.inf
  delta_rel[np.isinf(delta_rel)] = -1.0 * np.inf
  min_delta_non_neg = delta_rel[delta_rel != -1.0 * np.inf].min()
  max_delta_non_neg = delta_rel[delta_rel != -1.0 * np.inf].max()

  surface_rel[np.isnan(surface_rel)] = -1.0 * np.inf
  surface_rel[np.isinf(surface_rel)] = -1.0 * np.inf
  min_surface_non_neg = surface_rel[surface_rel != -1.0 * np.inf].min()
  max_surface_non_neg = surface_rel[surface_rel != -1.0 * np.inf].max()

  total_rel_min = np.minimum(min_delta_non_neg, min_surface_non_neg)
  total_rel_max = np.maximum(max_delta_non_neg, max_surface_non_neg)

  # Plot the statistical relative error distribution.
  fig_comp_rel, [ax_delta_rel, ax_surf_rel] = plt.subplots(ncols=2)
  fig_comp_rel.set_size_inches(w = 12.0, h = 5.5)
  im_1 = ax_delta_rel.pcolormesh(xx_delta, yy_delta, delta_rel, norm=colors.LogNorm(vmin=total_rel_min, vmax=total_rel_max))
  ax_delta_rel.set_title('Delta Tracking')
  im_2 = ax_surf_rel.pcolormesh(xx_delta, yy_delta, surface_rel, norm=colors.LogNorm(vmin=total_rel_min, vmax=total_rel_max))
  ax_surf_rel.set_title('Surface Tracking')
  fig_comp_rel.colorbar(im_1, ax=ax_delta_rel, label = f'{common.SCORE_NAMES[score]} Statistical Relative Error [-]\n Min: {min_delta_non_neg:.4e}, Max: {max_delta_non_neg:.4e}')
  fig_comp_rel.colorbar(im_2, ax=ax_surf_rel, label = f'{common.SCORE_NAMES[score]} Statistical Relative Error [-]\n Min: {min_surface_non_neg:.4e}, Max: {max_surface_non_neg:.4e}')
  fig_comp_rel.tight_layout()
  fig_comp_rel.savefig(f'./{case}/figures/{algorithm}_{particle}_{score}_rel_dis_p{particles}_ab{active_batches}_ib{inactive_batches}.png')
  plt.close()

def spatial_plot_rel_diff(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm):
  delta_points = int(np.ceil(np.sqrt(len(delta_df['x'].to_numpy()))))
  xx_delta = delta_df['x'].to_numpy().reshape(delta_points, delta_points)
  yy_delta = delta_df['y'].to_numpy().reshape(delta_points, delta_points)
  delta_mean = delta_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)
  surface_mean = surf_df[f'{score}_mean'].to_numpy().reshape(delta_points, delta_points)

  # Compute the relative difference between delta and surface tracking.
  rel_diff = np.abs(delta_mean - surface_mean) / surface_mean

  # Compute the colour bar bounds.
  rel_diff[np.isnan(rel_diff)] = -1.0 * np.inf
  rel_diff[np.isinf(rel_diff)] = -1.0 * np.inf
  rel_diff[rel_diff < 1e-10] = -1.0 * np.inf
  min_non_neg = rel_diff[rel_diff != -1.0 * np.inf].min()
  max_non_neg = rel_diff[rel_diff != -1.0 * np.inf].max()

  # Plot the spatial distribution of the relative difference.
  fig_comp, ax_rel = plt.subplots()
  im_3 = ax_rel.pcolormesh(xx_delta, yy_delta, rel_diff,
                           norm=colors.LogNorm(vmin=min_non_neg, vmax=max_non_neg))
  ax_rel.set_title(f'L2 Difference in {common.SCORE_NAMES[score]}: {np.sqrt(np.sum(np.pow(delta_mean - surface_mean, 2.0))):.4e}')
  fig_comp.colorbar(im_3, ax=ax_rel, label = f'Relative Difference in {common.SCORE_NAMES[score]} [-]\n Min: {min_non_neg:.4e}, Max: {max_non_neg:.4e}')
  fig_comp.tight_layout()
  fig_comp.savefig(f'./{case}/figures/{algorithm}_{particle}_{score}_spatial_comp_p{particles}_ab{active_batches}_ib{inactive_batches}.png')
  plt.close()

def gen_spatial_plots(dump_all, case, score, particles, active_batches, inactive_batches, particle, algorithm, sim_type):
  delta_df = pd.read_csv(f'./{case}/{sim_type}_delta_{algorithm}_{particle}_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv')
  surf_df  = pd.read_csv(f'./{case}/{sim_type}_surface_{algorithm}_{particle}_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv')

  if dump_all:
    spatial_plot_n_sigma(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm)
    spatial_plot_mean(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm)
    spatial_plot_stat_rel(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm)
  spatial_plot_rel_diff(case, delta_df, surf_df, score, particles, active_batches, inactive_batches, particle, algorithm)

def main():
  parser = ap.ArgumentParser(prog = 'Compare Spatial Distributions',
                             description = 'Compares spatial distributions between delta tracking and surface tracking.')
  parser.add_argument('--all', action = 'store_true', dest = 'dump_all', default=False,
                      help = 'Whether all plots should be generated.')
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
      gen_spatial_plots(args.dump_all, args.case, score, args.particles, args.active_batches,
                        args.inactive_batches, particle, args.algorithm, args.sim_type)

if __name__ == "__main__":
  main()
