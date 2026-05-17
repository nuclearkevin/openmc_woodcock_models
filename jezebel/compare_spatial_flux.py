#!/usr/bin/env python3

import argparse as ap
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.colors as colors

def main():
  parser = ap.ArgumentParser(prog = 'Compare Fluxes',
                             description = 'Compares the flux distribution between delta tracking and surface tracking.')
  parser.add_argument('-p', type = int, dest = 'particles', default = 1000,
                      help = 'Number of particles to run per batch. Defaults to 1000.')
  parser.add_argument('--active', type = int, dest = 'active_batches', default = 1000,
                      help='Number of active batches. Defaults to 1000.')
  parser.add_argument('--inactive', type = int, dest = 'inactive_batches', default = 100,
                      help = 'Number of inactive batches. Defaults to 100.')
  args = parser.parse_args()

  delta_df   = pd.read_csv(f'./delta_mesh_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv')
  surface_df = pd.read_csv(f'./surface_mesh_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv')

  delta_points = int(np.ceil(np.sqrt(len(delta_df['x'].to_numpy()))))
  xx_delta = delta_df['x'].to_numpy().reshape(delta_points, delta_points)
  yy_delta = delta_df['y'].to_numpy().reshape(delta_points, delta_points)
  delta_mean = delta_df['mean'].to_numpy().reshape(delta_points, delta_points)
  delta_sigma = delta_df['sigma'].to_numpy().reshape(delta_points, delta_points)
  delta_rel = delta_sigma / delta_mean

  surface_mean = surface_df['mean'].to_numpy().reshape(delta_points, delta_points)
  surface_sigma = surface_df['sigma'].to_numpy().reshape(delta_points, delta_points)
  surface_rel = surface_sigma / surface_mean

  total_min = np.minimum(delta_mean.min(), surface_mean.min())
  total_max = np.maximum(delta_mean.max(), surface_mean.max())

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

  fig_comp, [ax_delta, ax_surf] = plt.subplots(ncols=2)
  fig_comp.set_size_inches(w = 12.0, h = 5.5)
  im_1 = ax_delta.pcolormesh(xx_delta, yy_delta, delta_mean, vmin = total_min, vmax = total_max)
  ax_delta.set_title('Delta Tracking')
  im_2 = ax_surf.pcolormesh(xx_delta, yy_delta, surface_mean, vmin = total_min, vmax = total_max)
  ax_surf.set_title('Surface Tracking')
  fig_comp.colorbar(im_1, ax=ax_delta, label = f'Flux [n-cm/src]')
  fig_comp.colorbar(im_2, ax=ax_surf, label = f'Flux [n-cm/src]')
  fig_comp.tight_layout()
  fig_comp.savefig(f'./figures/flux_dis_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.png')
  plt.close()

  fig_comp_rel, [ax_delta_rel, ax_surf_rel] = plt.subplots(ncols=2)
  fig_comp_rel.set_size_inches(w = 12.0, h = 5.5)
  im_1 = ax_delta_rel.pcolormesh(xx_delta, yy_delta, delta_rel, norm=colors.LogNorm(vmin=total_rel_min, vmax=total_rel_max))
  ax_delta_rel.set_title('Delta Tracking')
  im_2 = ax_surf_rel.pcolormesh(xx_delta, yy_delta, surface_rel, norm=colors.LogNorm(vmin=total_rel_min, vmax=total_rel_max))
  ax_surf_rel.set_title('Surface Tracking')
  fig_comp_rel.colorbar(im_1, ax=ax_delta_rel, label = f'Flux Statistical Relative Error [-]\n Min: {min_delta_non_neg:.4e}, Max: {max_delta_non_neg:.4e}')
  fig_comp_rel.colorbar(im_2, ax=ax_surf_rel, label = f'Flux Statistical Relative Error [-]\n Min: {min_surface_non_neg:.4e}, Max: {max_surface_non_neg:.4e}')
  fig_comp_rel.tight_layout()
  fig_comp_rel.savefig(f'./figures/flux_rel_dis_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.png')
  plt.close()

  rel_diff = np.abs(delta_mean - surface_mean) / surface_mean
  rel_diff[np.isnan(rel_diff)] = -1.0 * np.inf
  rel_diff[np.isinf(rel_diff)] = -1.0 * np.inf
  min_non_neg = rel_diff[rel_diff != -1.0 * np.inf].min()
  max_non_neg = rel_diff[rel_diff != -1.0 * np.inf].max()

  fig_comp, ax_rel = plt.subplots()
  im_3 = ax_rel.pcolormesh(xx_delta, yy_delta, rel_diff,
                           norm=colors.LogNorm(vmin=min_non_neg, vmax=max_non_neg))
  ax_rel.set_title(f'L2 Difference in Mean Values: {np.sqrt(np.sum(np.pow(delta_mean - surface_mean, 2.0))):.4e}')
  fig_comp.colorbar(im_3, ax=ax_rel, label = f'Relative Difference in Mean Value [-]\n Min: {min_non_neg:.4e}, Max: {max_non_neg:.4e}')
  fig_comp.tight_layout()
  fig_comp.savefig(f'./figures/spatial_comp_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.png')
  plt.close()

if __name__ == "__main__":
  main()
