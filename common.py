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
  parser.add_argument('--photon', action = 'store_true', dest = 'photon', default=False,
                      help = 'Whether the model should run photon transport or not.')
  parser.add_argument('--event', action = 'store_true', dest = 'event', default=False,
                      help = 'Whether the model should run in event-based mode or not.')
  particle_args(parser)
  return parser

# Common tallies for all models.
def tallies(neutron_energy_bin_edges, photon_energy_bin_edges, mesh_dimension, mesh_ll, mesh_ur, run_photon) -> openmc.Tallies:
  tallies = openmc.Tallies()

  # Tally for the neutron spectrum.
  n_filter = openmc.ParticleFilter(bins = 'neutron')
  e_filter_n = openmc.EnergyFilter(neutron_energy_bin_edges)
  n_spectrum_tally = openmc.Tally(name = 'Neutron flux spectrum tally', tally_id = 0)
  n_spectrum_tally.filters = [n_filter, e_filter_n]
  n_spectrum_tally.scores = ['flux']
  n_spectrum_tally.estimator = 'collision'
  tallies.append(n_spectrum_tally)

  # Mesh tally for the neutron flux spatial distribution.
  tally_mesh = openmc.RegularMesh(name = 'Tally mesh')
  tally_mesh.dimension = mesh_dimension
  tally_mesh.lower_left = mesh_ll
  tally_mesh.upper_right = mesh_ur
  mesh_filter = openmc.MeshFilter(tally_mesh)
  n_spatial_flux_tally = openmc.Tally(name = 'Neutron spatial flux tally', tally_id = 1)
  n_spatial_flux_tally.filters = [n_filter, mesh_filter]
  n_spatial_flux_tally.scores = ['flux', 'total']
  n_spatial_flux_tally.estimator = 'collision'
  tallies.append(n_spatial_flux_tally)

  if run_photon:
    # Tally for the photon spectrum.
    p_filter = openmc.ParticleFilter(bins = 'photon')
    e_filter_p = openmc.EnergyFilter(photon_energy_bin_edges)
    p_spectrum_tally = openmc.Tally(name = 'Photon spectrum tally', tally_id = 2)
    p_spectrum_tally.filters = [p_filter, e_filter_p]
    p_spectrum_tally.scores = ['flux']
    p_spectrum_tally.estimator = 'collision'
    tallies.append(p_spectrum_tally)

    # Mesh tally for the photon flux spatial distribution.
    p_spatial_flux_tally = openmc.Tally(name = 'Photon spatial flux tally', tally_id = 3)
    p_spatial_flux_tally.filters = [p_filter, mesh_filter]
    p_spatial_flux_tally.scores = ['flux', 'total']
    p_spatial_flux_tally.estimator = 'collision'
    tallies.append(p_spatial_flux_tally)

  return tallies

# Common settings.
def settings(use_surface, particles, active, inactive, run_photon, run_event) -> openmc.Settings:
  settings = openmc.Settings()
  settings.batches = active + inactive
  settings.inactive = inactive
  settings.particles = particles
  settings.delta_tracking = (not use_surface)
  settings.photon_transport = run_photon
  settings.event_based = run_event

  return settings

def _mesh_tally_output_df(tally):
  mesh_dim = tally.filters[1].mesh.dimension
  mesh_ll = tally.filters[1].mesh.lower_left
  mesh_ur = tally.filters[1].mesh.upper_right
  z_center = int(np.floor(mesh_dim[2] / 2.0))
  spatial_tally_flux_res = tally.get_slice(scores=['flux'])
  spatial_tally_flux_mean = spatial_tally_flux_res.mean.reshape(mesh_dim[0], mesh_dim[1], mesh_dim[2])[:,:,z_center]
  spatial_tally_flux_std_dev = spatial_tally_flux_res.std_dev.reshape(mesh_dim[0], mesh_dim[1], mesh_dim[2])[:,:,z_center]
  spatial_tally_total_res = tally.get_slice(scores=['total'])
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
                                   'flux_mean' : spatial_tally_flux_mean.ravel(),
                                   'flux_sigma' : spatial_tally_flux_std_dev.ravel(),
                                   'total_mean' : spatial_tally_total_mean.ravel(),
                                   'total_sigma' : spatial_tally_total_std_dev.ravel() })
  return mesh_results_df

def _spectrum_tally_output_df(tally):
  energy_edges = tally.filters[1].values
  spectrum_tally_res = tally.get_slice(scores=['flux'], squeeze=True)
  spectrum_mean  = spectrum_tally_res.mean.ravel()
  spectrum_sigma = spectrum_tally_res.std_dev.ravel()
  spectrum_results_df = pd.DataFrame({ 'lower_edges' : energy_edges[:-1],
                                       'upper_edges' : energy_edges[1:],
                                       'mean' : spectrum_mean,
                                       'sigma' : spectrum_sigma })
  return spectrum_results_df

# A function to write common results for the problem.
def output_results(model, sp_path, use_surface, run_photon, run_event):
  inactive_batches = model.settings.inactive
  active_batches = model.settings.batches - inactive_batches
  particles = model.settings.particles

  tr_type = "surface" if use_surface else "delta"
  alg = "event" if run_event else "history"
  integral_name = "coupled" if run_photon else "single"

  # Load the statepoint.
  sp = openmc.StatePoint(sp_path)
  # Performance data.
  inactive_rate = np.float64(particles * inactive_batches) / sp.runtime['inactive batches']
  active_rate = np.float64(particles * active_batches) / sp.runtime['active batches']

  # Build and output a dataframe with all of the integral/performance data.
  integral_results_df = pd.DataFrame({ 'inactive_rate' : [inactive_rate],
                                       'active_rate' : [active_rate],
                                       'k_coll_mean' : [sp.global_tallies[0][3]],
                                       'k_coll_std_dev' : [sp.global_tallies[0][4]],
                                       'k_combined_mean' : [sp.keff.nominal_value],
                                       'k_combined_std_dev' : [sp.keff.std_dev],
                                       'leakage_mean' : [sp.global_tallies[3][3]],
                                       'leakage_std_dev' : [sp.global_tallies[3][4]] })

  # Extract tally data for the neutron spectrum.
  neutron_spectrum_results_df = _spectrum_tally_output_df(model.tallies[0])

  # Extract mesh tally results for neutrons.
  neutron_mesh_results_df = _mesh_tally_output_df(model.tallies[1])

  integral_results_df.to_csv(f'{integral_name}_{tr_type}_{alg}_integral_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
  neutron_spectrum_results_df.to_csv(f'{tr_type}_{alg}_neutron_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
  neutron_mesh_results_df.to_csv(f'{tr_type}_{alg}_neutron_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)

  # Photon tallies if requested.
  if run_photon:
    # Extract tally data for the photon spectrum.
    photon_spectrum_results_df = _spectrum_tally_output_df(model.tallies[2])

    # Extract mesh tally results for photons.
    photon_mesh_results_df = _mesh_tally_output_df(model.tallies[3])

    # Write the photon tally results.
    photon_spectrum_results_df.to_csv(f'{tr_type}_{alg}_photon_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
    photon_mesh_results_df.to_csv(f'{tr_type}_{alg}_photon_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
