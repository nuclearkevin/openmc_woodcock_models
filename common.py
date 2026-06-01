import argparse as ap
import openmc
import openmc.data

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
def settings(use_surface, particles, active, inactive, run_photon) -> openmc.Settings:
  settings = openmc.Settings()
  settings.batches = active + inactive
  settings.inactive = inactive
  settings.particles = particles
  settings.delta_tracking = (not use_surface)
  settings.photon_transport = run_photon

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
                                   'flux_mean' : spatial_tally_flux_mean.ravel(), 'flux_sigma' : spatial_tally_flux_std_dev.ravel(),
                                   'total_mean' : spatial_tally_total_mean.ravel(), 'total_sigma' : spatial_tally_total_std_dev.ravel() })
  return mesh_results_df


# A function to write common results for the problem.
def output_results(model, use_surface, run_photon):
  inactive_batches = model.settings.inactive
  active_batches = model.settings.batches - inactive_batches
  particles = model.settings.particles

  # Extract tally data for the neutron spectrum.
  neutron_energy_edges = model.tallies[0].filters[1].values
  neutron_spectrum_tally_res = model.tallies[0].get_slice(scores=['flux'], squeeze=True)
  neutron_spectrum_mean  = neutron_spectrum_tally_res.mean.ravel()
  neutron_spectrum_sigma = neutron_spectrum_tally_res.std_dev.ravel()
  neutron_spectrum_results_df = pd.DataFrame({ 'lower_edges' : neutron_energy_edges[:-1], 'upper_edges' : neutron_energy_edges[1:],
                                               'mean' : neutron_spectrum_mean, 'sigma' : neutron_spectrum_sigma })

  # Mesh tally results for neutrons.
  neutron_mesh_results_df = _mesh_tally_output_df(model.tallies[1])

  # Write the neutron tally results.
  if use_surface:
    neutron_spectrum_results_df.to_csv(f'surface_neutron_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
    neutron_mesh_results_df.to_csv(f'surface_neutron_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
  else:
    neutron_spectrum_results_df.to_csv(f'delta_neutron_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
    neutron_mesh_results_df.to_csv(f'delta_neutron_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)

  # Photon tallies if requested.
  if run_photon:
    # Extract tally data for the photon spectrum.
    photon_energy_edges = model.tallies[2].filters[1].values
    photon_spectrum_tally_res = model.tallies[2].get_slice(scores=['flux'], squeeze=True)
    photon_spectrum_mean  = photon_spectrum_tally_res.mean.ravel()
    photon_spectrum_sigma = photon_spectrum_tally_res.std_dev.ravel()
    photon_spectrum_results_df = pd.DataFrame({ 'lower_edges' : photon_energy_edges[:-1], 'upper_edges' : photon_energy_edges[1:],
                                                'mean' : photon_spectrum_mean, 'sigma' : photon_spectrum_sigma })

    # Mesh tally results for photons.
    photon_mesh_results_df = _mesh_tally_output_df(model.tallies[3])

    # Write the photon tally results.
    if use_surface:
      photon_spectrum_results_df.to_csv(f'surface_photon_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
      photon_mesh_results_df.to_csv(f'surface_photon_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
    else:
      photon_spectrum_results_df.to_csv(f'delta_photon_spectrum_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)
      photon_mesh_results_df.to_csv(f'delta_photon_mesh_p{particles}_ab{active_batches}_ib{inactive_batches}.csv', index=False)

# A function which computes the maximum URR cross section at a given energy point
# for nuclides in a given material.
def max_urr_data(material):
  library = openmc.data.DataLibrary.from_xml()
  nuc_fractions = material.get_nuclide_atom_densities()
  nuclides = list(nuc_fractions.keys())
  urr_data = {}
  urr_temps = {}
  collapsed_urr = {}
  for nuclide in nuclides:
    lib = library.get_by_material(nuclide)
    nuclide_data = openmc.data.IncidentNeutron.from_hdf5(lib['path'])
    if len(nuclide_data.urr.keys()) > 0:
      urr_temps[nuclide] = []
      urr_data[nuclide] = []
      for temp, temp_urr_data in nuclide_data.urr.items():
        urr_temps[nuclide].append(temp)
        urr_data[nuclide].append({
          'energy' : temp_urr_data.energy,
          'xs' : np.zeros_like(temp_urr_data.energy),
          'mult_smooth' : temp_urr_data.multiply_smooth
        })
        for e_idx in range(len(temp_urr_data.energy)):
          # Maximum value from the nuclide's ptable at a given temperature and energy.
          urr_data[nuclide][-1]['xs'][e_idx] = temp_urr_data.table[e_idx,1,:].max()

      # Take the max across temperature. Crude, but works for the majorant.
      collapsed_urr[nuclide] = {
        'energy' : urr_data[nuclide][0]['energy'],
        'mult_smooth' : urr_data[nuclide][0]['mult_smooth'],
        'xs' : urr_data[nuclide][0]['xs']
      }
      for data in urr_data[nuclide]:
        collapsed_urr[nuclide]['xs'] = np.maximum(collapsed_urr[nuclide]['xs'], data['xs'])

  return collapsed_urr

# A function which computes a majorant cross section for a material.
def compute_maj_xs_with_urr(material):
  library = openmc.data.DataLibrary.from_xml()
  urr_xs = max_urr_data(material)

  nuc_fractions = material.get_nuclide_atom_densities()
  nuclides = list(nuc_fractions.keys())

  # Find SAB data.
  sabs = {}
  for nuclide in nuclides:
      sabs[nuclide] = None
  for sab_name, _ in material._sab:
    sab = openmc.data.ThermalScattering.from_hdf5(
        library.get_by_material(sab_name, data_type='thermal')['path'])
    for nuc in sab.nuclides:
        sabs[nuc] = sab_name

  nuclide_total_micro = {}
  macro_nuclide = {}
  for nuclide in nuclides:
    nuc_grid, nuc_xs = openmc.calculate_cexs(nuclide, ['total'], sab_name=sabs[nuclide])
    nuclide_total_micro[nuclide] = {'energy' : nuc_grid, 'xs' : nuc_xs[0]}
    macro_nuclide[nuclide] = {}

  # Unionize against the URR grid and deal with those cross sections
  for nuclide in nuclides:
    if nuclide in urr_xs:
      union_urr = np.union1d(urr_xs[nuclide]['energy'], nuclide_total_micro[nuclide]['energy'])
      macro_nuclide[nuclide]['energy'] = union_urr
      urr_interp = np.interp(union_urr, urr_xs[nuclide]['energy'], urr_xs[nuclide]['xs'], left=0.0, right=0.0)
      smooth_interp = np.interp(union_urr, nuclide_total_micro[nuclide]['energy'], nuclide_total_micro[nuclide]['xs'], left=0.0, right=0.0)
      if urr_xs[nuclide]['mult_smooth']:
        urr_interp *= smooth_interp
      macro_nuclide[nuclide]['xs'] = nuc_fractions[nuclide] * np.maximum(urr_interp, smooth_interp)
    else:
      macro_nuclide[nuclide]['energy'] = nuclide_total_micro[nuclide]['energy']
      macro_nuclide[nuclide]['xs'] = nuc_fractions[nuclide] * nuclide_total_micro[nuclide]['xs']

  # Unionize the per-nuclide energy grids
  nuclide_grid_union = macro_nuclide[nuclides[0]]['energy']
  for nuclide in nuclides:
    nuclide_grid_union = np.union1d(nuclide_grid_union, macro_nuclide[nuclide]['energy'])

  # Interpolate cross sections onto the grid while accumulating the total cross section
  majorant_cross_section = np.zeros_like(nuclide_grid_union)
  for nuclide in nuclides:
    majorant_cross_section += np.interp(nuclide_grid_union, macro_nuclide[nuclide]['energy'], macro_nuclide[nuclide]['xs'])

  return nuclide_grid_union, majorant_cross_section

# A function which computes a whole-domain majorant cross section for a collection of materials.
def compute_domain_majorant(material_collection):
  per_material_maj = {}
  for mat in material_collection:
    grid, xs = compute_maj_xs_with_urr(mat)
    per_material_maj[mat.id] = { 'grid' : grid, 'xs' : xs }

  grid_union = per_material_maj[list(per_material_maj.keys())[0]]['grid']
  for id in per_material_maj.keys():
    grid_union = np.union1d(grid_union, per_material_maj[id]['grid'])

  union_majorant = np.zeros_like(grid_union)
  for id in per_material_maj.keys():
    union_majorant = np.maximum(union_majorant, np.interp(grid_union, per_material_maj[id]['grid'], per_material_maj[id]['xs'], left=0.0, right=0.0))

  return grid_union, union_majorant
