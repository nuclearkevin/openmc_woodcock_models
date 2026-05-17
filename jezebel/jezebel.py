#!/usr/bin/env python3

import argparse as ap
import openmc
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Adapted from the OpenMC Jezebel example problem.
R_SPHERE = 6.3849
NUM_TALLY_MESH_ELEMS = 51
NUM_ENTROPY_MESH_ELEMS = 5

def jezebel(use_surface, particles, active, inactive, use_entropy) -> openmc.Model:
  jezebel = openmc.Model()

  # Create plutonium metal material
  pu = openmc.Material()
  pu.set_density('sum')
  pu.add_nuclide('Pu239', 3.7047e-02)
  pu.add_nuclide('Pu240', 1.7512e-03)
  pu.add_nuclide('Pu241', 1.1674e-04)
  pu.add_element('Ga', 1.3752e-03)
  jezebel.materials.append(pu)

  # Create a single cell filled with the Pu metal.
  sphere = openmc.Sphere(r = R_SPHERE, boundary_type = 'vacuum')
  cell = openmc.Cell(fill = pu, region = -sphere)
  jezebel.geometry = openmc.Geometry([cell])

  # Add a tally for the spectrum.
  e_filter = openmc.EnergyFilter(np.logspace(np.log10(1e2), np.log10(20.0e6), 101))
  spectrum_tally = openmc.Tally(name = 'spectrum', tally_id = 0)
  spectrum_tally.filters = [e_filter]
  spectrum_tally.scores = ['flux']
  spectrum_tally.estimator = 'collision'
  jezebel.tallies.append(spectrum_tally)

  # Create mesh tally for the spatial flux distribution.
  tally_mesh = openmc.RegularMesh(name = 'Tally mesh')
  tally_mesh.dimension = (NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS)
  tally_mesh.lower_left = (-R_SPHERE, -R_SPHERE, -R_SPHERE)
  tally_mesh.upper_right = (R_SPHERE, R_SPHERE, R_SPHERE)
  mesh_filter = openmc.MeshFilter(tally_mesh)
  spatial_flux_tally = openmc.Tally(name = 'spatial flux', tally_id = 1)
  spatial_flux_tally.filters = [mesh_filter]
  spatial_flux_tally.scores = ['flux']
  spatial_flux_tally.estimator = 'collision'
  jezebel.tallies.append(spatial_flux_tally)

  # Finally, define some run settings.
  jezebel.settings = openmc.Settings()
  jezebel.settings.batches = active + inactive
  jezebel.settings.inactive = inactive
  jezebel.settings.particles = particles
  jezebel.settings.run_mode = 'eigenvalue'
  if use_surface:
    jezebel.settings.delta_tracking = False
  else:
    jezebel.settings.delta_tracking = True

  if use_entropy:
    entropy_mesh = openmc.RegularMesh(name = 'Entropy mesh')
    entropy_mesh.dimension = (NUM_ENTROPY_MESH_ELEMS, NUM_ENTROPY_MESH_ELEMS, NUM_ENTROPY_MESH_ELEMS)
    entropy_mesh.lower_left = (-R_SPHERE, -R_SPHERE, -R_SPHERE)
    entropy_mesh.upper_right = (R_SPHERE, R_SPHERE, R_SPHERE)
    jezebel.settings.entropy_mesh = entropy_mesh

  return jezebel

def main():
  parser = ap.ArgumentParser(prog = 'Jezebel', description = 'Builds and runs a model of Jezebel.')
  parser.add_argument('-s', '--surface', action = 'store_true', dest = 'use_surface', default=False,
                      help = 'Whether surface tracking should be used or not.')
  parser.add_argument('-r', '--run', action = 'store_true', dest = 'run', default=False,
                      help = 'Whether the model should be run or not.')
  parser.add_argument('-p', type = int, dest = 'particles', default = 1000,
                      help = 'Number of particles to run per batch. Defaults to 1000.')
  parser.add_argument('--active', type = int, dest = 'active_batches', default = 1000,
                      help='Number of active batches. Defaults to 1000.')
  parser.add_argument('--inactive', type = int, dest = 'inactive_batches', default = 100,
                      help = 'Number of inactive batches. Defaults to 100.')
  parser.add_argument('--entropy', action = 'store_true', dest = 'entropy', default = False,
                      help = 'Whether source convergence should be assessed with Shannon entropy or not.')
  args = parser.parse_args()

  model = jezebel(args.use_surface, args.particles, args.active_batches, args.inactive_batches, args.entropy)
  model.export_to_model_xml()

  if args.run:
    model.run(apply_tally_results=True)

    # Extract tally data for the spectrum.
    energy_edges = model.tallies[0].filters[0].values
    spectrum_tally_res = model.tallies[0].get_slice(scores=['flux'])
    spectrum_mean = spectrum_tally_res.mean.ravel()
    three_sigma   = 3.0 * spectrum_tally_res.std_dev.ravel()
    spectrum_results_df = pd.DataFrame({ 'lower_edges' : energy_edges[:-1], 'upper_edges' : energy_edges[1:],
                                         'mean' : spectrum_mean, '3_sigma' : three_sigma })

    # Extract tally data for spatial flux plots. Picking the centerplane to make things easier.
    spatial_tally_res = model.tallies[1].get_slice(scores=['flux'])
    spatial_tally_mean = spatial_tally_res.mean.ravel().reshape(NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS)[:,:,25]
    spatial_tally_std_dev = spatial_tally_res.std_dev.ravel().reshape(NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS)[:,:,25]
    # I cannot for the life of me get numpy to do this for me. There has to be a better way...
    single_axis = np.linspace(-R_SPHERE, R_SPHERE, NUM_TALLY_MESH_ELEMS)
    xx = np.zeros(NUM_TALLY_MESH_ELEMS ** 2)
    yy = np.zeros(NUM_TALLY_MESH_ELEMS ** 2)
    i = 0
    for x in single_axis:
      for y in single_axis:
        xx[i] = x
        yy[i] = y
        i += 1
    mesh_results_df = pd.DataFrame({ 'x' : xx.ravel(), 'y' : yy.ravel(),
                                     'mean' : spatial_tally_mean.ravel(),
                                     'sigma' : spatial_tally_std_dev.ravel() })

    if args.use_surface:
      spectrum_results_df.to_csv(f'surface_spectrum_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv', index=False)
      mesh_results_df.to_csv(f'surface_mesh_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv', index=False)
    else:
      spectrum_results_df.to_csv(f'delta_spectrum_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv', index=False)
      mesh_results_df.to_csv(f'delta_mesh_p{args.particles}_ab{args.active_batches}_ib{args.inactive_batches}.csv', index=False)

if __name__ == "__main__":
  main()
