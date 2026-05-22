#!/usr/bin/env python3

# Resolving imports for the common module
import sys
sys.path.append("../../")
import common

import os
import numpy as np
import openmc
import openmc.model

# Adapted from the OpenMC SFR core example problem.
R_FUEL  = 0.4715
IR_CLAD = 0.4865
OR_CLAD = 0.5365
HEX_PITCH = 1.24
PIN_HEIGHT = 100.0
def fresh_sfr_pincell(use_surface, particles, active, inactive, use_entropy, manual_maj) -> openmc.Model:
  pincell_model = openmc.Model()

  # Define materials.
  u235 = openmc.Material(name='U235')
  u235.add_nuclide('U235', 1.0)
  u235.set_density('g/cm3', 10.0)

  u238 = openmc.Material(name='U238')
  u238.add_nuclide('U238', 1.0)
  u238.set_density('g/cm3', 10.0)

  pu238 = openmc.Material(name='Pu238')
  pu238.add_nuclide('Pu238', 1.0)
  pu238.set_density('g/cm3', 10.0)

  pu239 = openmc.Material(name='U235')
  pu239.add_nuclide('Pu239', 1.0)
  pu239.set_density('g/cm3', 10.0)

  pu240 = openmc.Material(name='Pu240')
  pu240.add_nuclide('Pu240', 1.0)
  pu240.set_density('g/cm3', 10.0)

  pu241 = openmc.Material(name='Pu241')
  pu241.add_nuclide('Pu241', 1.0)
  pu241.set_density('g/cm3', 10.0)

  pu242 = openmc.Material(name='Pu242')
  pu242.add_nuclide('Pu242', 1.0)
  pu242.set_density('g/cm3', 10.0)

  am241 = openmc.Material(name='Am241')
  am241.add_nuclide('Am241', 1.0)
  am241.set_density('g/cm3', 10.0)

  o16 = openmc.Material(name='O16')
  o16.add_nuclide('O16', 1.0)
  o16.set_density('g/cm3', 10.0)

  sodium = openmc.Material(name='Na')
  sodium.add_nuclide('Na23', 1.0)
  sodium.set_density('g/cm3', 0.96)

  cu63 = openmc.Material(name='Cu63')
  cu63.set_density('g/cm3', 10.0)
  cu63.add_nuclide('Cu63', 1.0)

  Al2O3 = openmc.Material(name='Al2O3')
  Al2O3.set_density('g/cm3', 10.0)
  Al2O3.add_element('O', 3.0)
  Al2O3.add_element('Al', 2.0)

  fuel = openmc.Material.mix_materials(
    [u235, u238, pu238, pu239, pu240, pu241, pu242, am241, o16],
    [0.0019, 0.7509, 0.0046, 0.0612, 0.0383, 0.0106, 0.0134, 0.001, 0.1181],
    'wo')
  clad = openmc.Material.mix_materials([cu63, Al2O3], [0.997, 0.003], 'wo')
  pincell_model.materials = openmc.Materials([fuel, sodium, clad])

  # Manually compute and write the majorant cross section.
  if manual_maj:
    if os.path.isfile('./manual_majorant.csv'):
      print('Skipping generation of the majorant cross section as one already exists!')
    else:
      print('Generating majorant cross section...')
      maj_grid, maj_xs = common.compute_domain_majorant(pincell_model.materials)
      common.write_majorant_csv_file('./manual_majorant.csv', maj_grid, maj_xs)
      print('...done!')

  # Define the pin geometry.
  fuel_or = openmc.ZCylinder(r = R_FUEL)
  clad_ir = openmc.ZCylinder(r = IR_CLAD)
  clad_or = openmc.ZCylinder(r = OR_CLAD)
  outer_hex = openmc.model.HexagonalPrism(edge_length=HEX_PITCH / np.sqrt(3.0),
                                          orientation='x',
                                          boundary_type='reflective')

  top = openmc.ZPlane(z0 = PIN_HEIGHT / 2.0, boundary_type='reflective')
  bottom = openmc.ZPlane(z0 = -PIN_HEIGHT / 2.0, boundary_type='reflective')
  extents = -top & +bottom

  fuel_region = -fuel_or & extents
  gap_region  = +fuel_or & -clad_ir  & extents
  clad_region = +clad_ir & -clad_or  & extents
  moderator_region = +clad_or & -outer_hex & extents

  fuel_cell = openmc.Cell(fill=fuel, region=fuel_region)
  gap_cell = openmc.Cell(fill = fuel, region = gap_region)
  clad_cell = openmc.Cell(fill = clad, region = clad_region)
  sodium_cell = openmc.Cell(fill = sodium, region = moderator_region)
  pincell_model.geometry = openmc.Geometry([fuel_cell, gap_cell, clad_cell, sodium_cell])

  # Add tallies.
  lower_left = (-HEX_PITCH / np.sqrt(3.0), -HEX_PITCH / np.sqrt(3.0), -HEX_PITCH / np.sqrt(3.0))
  upper_right = (HEX_PITCH / np.sqrt(3.0),  HEX_PITCH / np.sqrt(3.0),  HEX_PITCH / np.sqrt(3.0))
  tals = common.tallies(energy_bin_edges = np.logspace(np.log10(1e1), np.log10(2.0e7), 101),
                        mesh_dimension = (51, 51, 1),
                        mesh_ll = lower_left,
                        mesh_ur = upper_right)
  pincell_model.tallies = tals

  # Finally, define some run settings.
  pincell_model.settings = common.settings(use_surface, particles, active, inactive)
  pincell_model.settings.run_mode = 'eigenvalue'
  uniform_dist = openmc.stats.Box(lower_left, upper_right)
  pincell_model.settings.source = openmc.IndependentSource(space = uniform_dist)
  if pincell_model.settings.delta_tracking and manual_maj:
    pincell_model.settings.delta_tracking_majorant_file = "./manual_majorant.csv"

  if use_entropy:
    entropy_mesh = openmc.RegularMesh(name = 'Entropy mesh')
    entropy_mesh.dimension = (5, 5, 11)
    entropy_mesh.lower_left = lower_left
    entropy_mesh.upper_right = upper_right
    pincell_model.settings.entropy_mesh = entropy_mesh

  return pincell_model

def main():
  parser = common.parser('LWR Fresh Pincell')
  parser.add_argument('--entropy', action = 'store_true', dest = 'entropy', default = False,
                      help = 'Whether source convergence should be assessed with Shannon entropy or not.')
  args = parser.parse_args()

  model = fresh_sfr_pincell(args.use_surface, args.particles, args.active_batches,
                            args.inactive_batches, args.entropy, args.manual)
  model.export_to_model_xml()

  if args.run:
    model.run(apply_tally_results=True, openmc_exec=f'../../{common.OPENMC_EXEC}')
    common.output_results(model, args.use_surface)

if __name__ == "__main__":
  main()
