#!/usr/bin/env python3

# Resolving imports for the common module
import sys
sys.path.append("../")
import common

import argparse as ap
import openmc
import numpy as np
import pandas as pd

# Adapted from the OpenMC Jezebel example problem.
R_SPHERE = 6.3849
NUM_TALLY_MESH_ELEMS = 51
NUM_ENTROPY_MESH_ELEMS = 5

def jezebel(use_surface, particles, active, inactive, use_entropy) -> openmc.Model:
  jezebel = openmc.Model()

  # Material (only need Pu metal)
  pu = openmc.Material()
  pu.set_density('sum')
  pu.add_nuclide('Pu239', 3.7047e-02)
  pu.add_nuclide('Pu240', 1.7512e-03)
  pu.add_nuclide('Pu241', 1.1674e-04)
  pu.add_element('Ga', 1.3752e-03)
  jezebel.materials.append(pu)

  # Geometry (single cell)
  sphere = openmc.Sphere(r = R_SPHERE, boundary_type = 'vacuum')
  cell = openmc.Cell(fill = pu, region = -sphere)
  jezebel.geometry = openmc.Geometry([cell])

  # Add tallies.
  tals = common.tallies(energy_bin_edges = np.logspace(np.log10(1e2), np.log10(2.0e7), 101),
                        mesh_dimension = (NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS, NUM_TALLY_MESH_ELEMS),
                        mesh_ll = (-R_SPHERE, -R_SPHERE, -R_SPHERE),
                        mesh_ur = ( R_SPHERE,  R_SPHERE,  R_SPHERE))
  jezebel.tallies = tals

  # Finally, define some run settings.
  jezebel.settings = common.settings(use_surface, particles, active, inactive)
  jezebel.settings.run_mode = 'eigenvalue'

  if use_entropy:
    entropy_mesh = openmc.RegularMesh(name = 'Entropy mesh')
    entropy_mesh.dimension = (NUM_ENTROPY_MESH_ELEMS, NUM_ENTROPY_MESH_ELEMS, NUM_ENTROPY_MESH_ELEMS)
    entropy_mesh.lower_left = (-R_SPHERE, -R_SPHERE, -R_SPHERE)
    entropy_mesh.upper_right = (R_SPHERE, R_SPHERE, R_SPHERE)
    jezebel.settings.entropy_mesh = entropy_mesh

  return jezebel

def main():
  parser = common.parser('Jezebel')
  parser.add_argument('--entropy', action = 'store_true', dest = 'entropy', default = False,
                      help = 'Whether source convergence should be assessed with Shannon entropy or not.')
  args = parser.parse_args()

  model = jezebel(args.use_surface, args.particles, args.active_batches, args.inactive_batches, args.entropy)
  model.export_to_model_xml()

  if args.run:
    model.run(apply_tally_results=True, openmc_exec=f'../{common.OPENMC_EXEC}')
    common.output_results(model, args.use_surface)

if __name__ == "__main__":
  main()
