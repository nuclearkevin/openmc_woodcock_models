import argparse as ap
import openmc

import numpy as np
import pandas as pd

OPENMC_EXEC = 'openmc/build/bin/openmc'
SCORES = ['flux', 'total']
SCORE_NAMES = {
  'flux' : 'Flux',
  'total' : 'Total Reaction Rate'
}
SCORE_UNITS = {
  'flux' : '[n-cm/src]',
  'total' : '[rxn/src]'
}

# Add arguments for particles/batches/inactive batches.
def particle_args(parser):
  parser.add_argument('-p', type = int, dest = 'particles', default = 1000,
                      help = 'Number of particles to run per batch. Defaults to 1000.')
  parser.add_argument('--active', type = int, dest = 'active_batches', default = 1000,
                      help='Number of active batches. Defaults to 1000.')
  parser.add_argument('--inactive', type = int, dest = 'inactive_batches', default = 100,
                      help = 'Number of inactive batches. Defaults to 100.')
  return parser

# A common ArgumentParser for all models.
def parser(model_name) -> ap.ArgumentParser:
  parser = ap.ArgumentParser(prog = model_name, description = f'Builds and runs a model of {model_name}.')
  parser.add_argument('-s', '--surface', action = 'store_true', dest = 'use_surface', default=False,
                      help = 'Whether surface tracking should be used or not.')
  parser.add_argument('-r', '--run', action = 'store_true', dest = 'run', default=False,
                      help = 'Whether the model should be run or not.')
  particle_args(parser)
  return parser

# Common tallies for all models.
def tallies(energy_bin_edges, mesh_dimension, mesh_ll, mesh_ur) -> openmc.Tallies:
  tallies = openmc.Tallies()

  # Tally for the spectrum.
  e_filter = openmc.EnergyFilter(energy_bin_edges)
  spectrum_tally = openmc.Tally(name = 'Flux spectrum tally', tally_id = 0)
  spectrum_tally.filters = [e_filter]
  spectrum_tally.scores = ['flux']
  spectrum_tally.estimator = 'collision'
  tallies.append(spectrum_tally)

  # Mesh tally for the spatial flux distribution.
  tally_mesh = openmc.RegularMesh(name = 'Tally mesh')
  tally_mesh.dimension = mesh_dimension
  tally_mesh.lower_left = mesh_ll
  tally_mesh.upper_right = mesh_ur
  mesh_filter = openmc.MeshFilter(tally_mesh)
  spatial_flux_tally = openmc.Tally(name = 'Spatial flux tally', tally_id = 1)
  spatial_flux_tally.filters = [mesh_filter]
  spatial_flux_tally.scores = ['flux', 'total']
  spatial_flux_tally.estimator = 'collision'
  tallies.append(spatial_flux_tally)

  return tallies

# Common settings.
def settings(use_surface, particles, active, inactive) -> openmc.Settings:
  settings = openmc.Settings()
  settings.batches = active + inactive
  settings.inactive = inactive
  settings.particles = particles
  settings.delta_tracking = (not use_surface)

  return settings

# A function to write common results for the problem.
def output_results(model, use_surface):
  inactive_batches = model.settings.inactive
  active_batches = model.settings.batches - inactive_batches
  particles = model.settings.particles

  # Extract tally data for the spectrum.
  energy_edges = model.tallies[0].filters[0].values
  spectrum_tally_res = model.tallies[0].get_slice(scores=['flux'])
  spectrum_mean  = spectrum_tally_res.mean.ravel()
  spectrum_sigma = spectrum_tally_res.std_dev.ravel()
  spectrum_results_df = pd.DataFrame({ 'lower_edges' : energy_edges[:-1], 'upper_edges' : energy_edges[1:],
                                        'mean' : spectrum_mean, 'sigma' : spectrum_sigma })

  # Extract tally data for spatial flux plots. Picking the center-plane to make things easier.
  mesh_dim = model.tallies[1].filters[0].mesh.dimension
  mesh_ll = model.tallies[1].filters[0].mesh.lower_left
  mesh_ur = model.tallies[1].filters[0].mesh.upper_right
  z_center = int(np.floor(mesh_dim[2] / 2.0))
  spatial_tally_flux_res = model.tallies[1].get_slice(scores=['flux'])
  spatial_tally_flux_mean = spatial_tally_flux_res.mean.reshape(mesh_dim[0], mesh_dim[1], mesh_dim[2])[:,:,z_center]
  spatial_tally_flux_std_dev = spatial_tally_flux_res.std_dev.reshape(mesh_dim[0], mesh_dim[1], mesh_dim[2])[:,:,z_center]
  spatial_tally_total_res = model.tallies[1].get_slice(scores=['total'])
  spatial_tally_total_mean = spatial_tally_total_res.mean.reshape(mesh_dim[0], mesh_dim[1], mesh_dim[2])[:,:,z_center]
  spatial_tally_total_std_dev = spatial_tally_total_res.std_dev.reshape(mesh_dim[0], mesh_dim[1], mesh_dim[2])[:,:,z_center]
  # I cannot for the life of me get numpy to do this for me. There has to be a better way...
  x_axis = np.linspace(mesh_ll[0], mesh_ur[0], mesh_dim[0])
  y_axis = np.linspace(mesh_ll[1], mesh_ur[1], mesh_dim[1])
  xx = np.zeros(len(x_axis) * len(y_axis))
  yy = np.zeros(len(x_axis) * len(y_axis))
  i = 0
  for x in x_axis:
    for y in y_axis:
      xx[i] = x
      yy[i] = y
      i += 1
  mesh_results_df = pd.DataFrame({ 'x' : xx.ravel(), 'y' : yy.ravel(),
                                   'flux_mean' : spatial_tally_flux_mean.ravel(), 'flux_sigma' : spatial_tally_flux_std_dev.ravel(),
                                   'total_mean' : spatial_tally_total_mean.ravel(), 'total_sigma' : spatial_tally_total_std_dev.ravel() })

  if use_surface:
    spectrum_results_df.to_csv(f'surface_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
    mesh_results_df.to_csv(f'surface_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
  else:
    spectrum_results_df.to_csv(f'delta_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
    mesh_results_df.to_csv(f'delta_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
