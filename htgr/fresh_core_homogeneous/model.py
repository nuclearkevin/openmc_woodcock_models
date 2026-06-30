#!/usr/bin/env python3

# Resolving imports for the common module
import sys
sys.path.append("../../")
import common

import numpy as np
import openmc

def gcmr_fresh_core(use_surface, particles, active, inactive, use_entropy, run_photon, run_event) -> openmc.Model:
  # Model is provided as a series of XML files.
  gcmr_model = openmc.Model.from_xml(geometry='./xml/geometry.xml', materials='./xml/materials.xml', settings='./xml/settings.xml')

  lower_left = (0.0, 0.0, 0.0)
  upper_right = (104.78907385791709, 240.0, 121.0)

  # Add tallies.
  tals = common.tallies(run_surface = use_surface,
                        neutron_energy_bin_edges = np.logspace(np.log10(1e-6), np.log10(2.0e7), 101),
                        photon_energy_bin_edges = np.logspace(np.log10(1e2), np.log10(2.0e7), 101),
                        mesh_dimension = (51, 1, 51),
                        mesh_ll = lower_left,
                        mesh_ur = upper_right,
                        run_photon = run_photon)
  gcmr_model.tallies = tals

  # Finally, define some run settings.
  gcmr_model.settings = common.settings(use_surface, particles, active, inactive, run_photon, run_event)
  gcmr_model.settings.run_mode = 'eigenvalue'
  uniform_dist = openmc.stats.Box(lower_left, upper_right)
  gcmr_model.settings.source = openmc.IndependentSource(space = uniform_dist)

  gcmr_model.settings.temperature = {
    'default' : 1003.4000000000001,
    'method' : 'interpolation',
    'range' : (290.0, 2501.0),
    'tolerance' : 10.0
  }

  if use_entropy:
    entropy_mesh = openmc.RegularMesh(name = 'Entropy mesh')
    entropy_mesh.dimension = (5, 11, 5)
    entropy_mesh.lower_left = lower_left
    entropy_mesh.upper_right = upper_right
    gcmr_model.settings.entropy_mesh = entropy_mesh

  return gcmr_model

def main():
  parser = common.parser('HTGR Fresh Core Based on the GCMR (Homogenized Model)')
  parser.add_argument('--entropy', action = 'store_true', dest = 'entropy', default = False,
                      help = 'Whether source convergence should be assessed with Shannon entropy or not.')
  args = parser.parse_args()

  model = gcmr_fresh_core(args.use_surface, args.particles, args.active_batches,
                          args.inactive_batches, args.entropy, args.photon, args.event)
  model.export_to_model_xml()

  if args.run:
    sp_path = model.run(apply_tally_results=True, openmc_exec=f'../../{common.OPENMC_EXEC}')
    common.output_results(model, sp_path, args.use_surface, args.photon, args.event)

  if args.output and not args.run:
    sp_path = f'./statepoint.{int(args.active_batches + args.inactive_batches)}.h5'
    model.apply_tally_results(sp_path)
    common.output_results(model, sp_path, args.use_surface, args.photon, args.event)

if __name__ == "__main__":
  main()
