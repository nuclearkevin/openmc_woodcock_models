#!/usr/bin/env python3

# Resolving imports for the common module
import sys
sys.path.append("../../")
import common

import numpy as np
import openmc

def beavrs_fresh_core(use_surface, particles, active, inactive, use_entropy, run_photon, run_event) -> openmc.Model:
  # Model is provided as a model.xml file
  beavrs_model = openmc.Model.from_model_xml('./xml/model.xml')

  lower_left = (-161.2773, -161.2773, 35.0)
  upper_right = (161.2773, 161.2773, 419.704)

  # Add tallies.
  tals = common.tallies(run_surface = use_surface,
                        neutron_energy_bin_edges = np.logspace(np.log10(1e-6), np.log10(2.0e7), 101),
                        photon_energy_bin_edges = np.logspace(np.log10(1e2), np.log10(2.0e7), 101),
                        mesh_dimension = (60, 60, 1),
                        mesh_ll = lower_left,
                        mesh_ur = upper_right,
                        run_photon = run_photon)
  beavrs_model.tallies = tals

  # Finally, define some run settings.
  beavrs_model.settings = common.settings(use_surface, particles, active, inactive, run_photon, run_event)
  beavrs_model.settings.run_mode = 'eigenvalue'
  uniform_dist = openmc.stats.Box(lower_left, upper_right)
  beavrs_model.settings.source = openmc.IndependentSource(space = uniform_dist)

  beavrs_model.settings.temperature = {
    'default' : 566.483,
    'method' : 'interpolation',
    'range' : (290.0, 2501.0),
    'tolerance' : 10.0
  }

  if use_entropy:
    entropy_mesh = openmc.RegularMesh(name = 'Entropy mesh')
    entropy_mesh.dimension = (11, 11, 11)
    entropy_mesh.lower_left = lower_left
    entropy_mesh.upper_right = upper_right
    beavrs_model.settings.entropy_mesh = entropy_mesh

  return beavrs_model

def main():
  parser = common.parser('LWR Fresh Core Based on BEAVRS ARO')
  parser.add_argument('--entropy', action = 'store_true', dest = 'entropy', default = False,
                      help = 'Whether source convergence should be assessed with Shannon entropy or not.')
  args = parser.parse_args()

  model = beavrs_fresh_core(args.use_surface, args.particles, args.active_batches,
                            args.inactive_batches, args.entropy, args.photon, args.event)
  model.export_to_model_xml()

  if args.run:
    sp_path = model.run(apply_tally_results=True, openmc_exec=f'../../{common.OPENMC_EXEC}')
    common.output_results(model, sp_path, args.use_surface, args.photon, args.event)

if __name__ == "__main__":
  main()
