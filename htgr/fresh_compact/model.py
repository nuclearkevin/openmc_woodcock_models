#!/usr/bin/env python3

# Resolving imports for the common module
import sys
sys.path.append("../../")
import common

import os
import argparse as ap
import numpy as np
import pandas as pd
import openmc
import openmc.model

# Adapted from the Cardinal TRISO compact tutorial.
COMPACT_D = 1.27
HEIGHT = 160.0
def fresh_htgr_compact(use_surface, particles, active, inactive, use_entropy, run_photon, run_event) -> openmc.Model:
  compact_model = openmc.Model()
  # superimposed search lattice
  triso_lattice_shape = (4, 4, int(HEIGHT / 0.125))
  lattice_orientation = 'x'
  cell_edge_length = 1.628

  enrichment_234     = 2e-3
  enrichment_uranium = 0.155
  mass_234 = openmc.data.atomic_mass('U234')
  mass_235 = openmc.data.atomic_mass('U235')
  mass_238 = openmc.data.atomic_mass('U238')
  n_234 = enrichment_234 / mass_234
  n_235 = enrichment_uranium / mass_235
  n_238 = (1.0 - enrichment_uranium - enrichment_234) / mass_238
  total_n = n_234 + n_235 + n_238
  fuel = openmc.Material(name='fuel')
  fuel.add_nuclide('U234', n_234 / total_n)
  fuel.add_nuclide('U235', n_235 / total_n)
  fuel.add_nuclide('U238', n_238 / total_n)
  fuel.add_element('C'   , 1.50)
  fuel.add_element('O'   , 0.50)
  fuel.set_density('kg/m3', 10820)

  graphite_c_buffer = openmc.Material(name='buffer')
  graphite_c_buffer.add_element('C', 1.0)
  graphite_c_buffer.add_s_alpha_beta('c_Graphite')
  graphite_c_buffer.set_density('kg/m3', 1050)

  graphite_pyc = openmc.Material(name='pyc')
  graphite_pyc.add_element('C', 1.0)
  graphite_pyc.add_s_alpha_beta('c_Graphite')
  graphite_pyc.set_density('kg/m3', 1900)

  sic = openmc.Material(name='sic')
  sic.add_element('C' , 1.0)
  sic.add_element('Si', 1.0)
  sic.set_density('kg/m3', 3203)

  graphite_matrix = openmc.Material(name='graphite moderator')
  graphite_matrix.add_element('C', 1.0)
  graphite_matrix.add_s_alpha_beta('c_Graphite')
  graphite_matrix.set_density('kg/m3', 1700)

  coolant = openmc.Material(name='Helium coolant')
  coolant.add_element('He', 1.0, 'ao')
  coolant.set_density('g/cm3', 0.125)
  compact_model.materials = openmc.Materials([fuel, graphite_c_buffer, graphite_pyc, sic, graphite_matrix, coolant])

  # TRISO particle
  radius_pyc_outer   = 429.85e-4
  s_fuel             = openmc.Sphere(r=214.85e-4)
  s_c_buffer         = openmc.Sphere(r=314.85e-4)
  s_pyc_inner        = openmc.Sphere(r=354.85e-4)
  s_sic              = openmc.Sphere(r=389.85e-4)
  s_pyc_outer        = openmc.Sphere(r=radius_pyc_outer)
  c_triso_fuel       = openmc.Cell(name='c_triso_fuel'     , fill=fuel,              region=-s_fuel)
  c_triso_c_buffer   = openmc.Cell(name='c_triso_c_buffer' , fill=graphite_c_buffer, region=+s_fuel      & -s_c_buffer)
  c_triso_pyc_inner  = openmc.Cell(name='c_triso_pyc_inner', fill=graphite_pyc,      region=+s_c_buffer  & -s_pyc_inner)
  c_triso_sic        = openmc.Cell(name='c_triso_sic'      , fill=sic,               region=+s_pyc_inner & -s_sic)
  c_triso_pyc_outer  = openmc.Cell(name='c_triso_pyc_outer', fill=graphite_pyc,      region=+s_sic       & -s_pyc_outer)
  c_triso_matrix     = openmc.Cell(name='c_triso_matrix'   , fill=graphite_matrix,   region=+s_pyc_outer)
  u_triso            = openmc.Universe(cells=[c_triso_fuel, c_triso_c_buffer, c_triso_pyc_inner, c_triso_sic, c_triso_pyc_outer, c_triso_matrix])

  # Channel surfaces
  fuel_cyl = openmc.ZCylinder(r=0.635)
  coolant_cyl = openmc.ZCylinder(r=0.8)

  # create a TRISO lattice for one axial section (to be used in the rest of the axial zones)
  # center the TRISO region on the origin so it fills lattice cells appropriately
  min_z = openmc.ZPlane(z0=-HEIGHT / 2.0, boundary_type='vacuum')
  max_z = openmc.ZPlane(z0=HEIGHT / 2.0, boundary_type='vacuum')
  axial_extents = +min_z & -max_z

  # region in which TRISOs are generated
  r_triso = -fuel_cyl & axial_extents

  rand_spheres = openmc.model.pack_spheres(radius=radius_pyc_outer, region=r_triso, pf=0.15, seed=1.0)
  random_trisos = [openmc.model.TRISO(radius_pyc_outer, u_triso, i) for i in rand_spheres]

  llc, urc = r_triso.bounding_box
  pitch = (urc - llc) / triso_lattice_shape
  # insert TRISOs into a lattice to accelerate point location queries
  triso_lattice = openmc.model.create_triso_lattice(random_trisos, llc, pitch, triso_lattice_shape, graphite_matrix)

  coolant_cell = openmc.Cell(region=-coolant_cyl, fill=coolant)
  graphite_cell = openmc.Cell(region=+coolant_cyl, fill=graphite_matrix)
  fuel_ch_cell = openmc.Cell(region=-fuel_cyl, fill=triso_lattice)
  fuel_ch_matrix_cell = openmc.Cell(region=+fuel_cyl, fill=graphite_matrix)

  fuel_u = openmc.Universe(cells=[fuel_ch_cell, fuel_ch_matrix_cell])
  coolant_u = openmc.Universe(cells=[coolant_cell, graphite_cell])
  lattice_univs = [[[fuel_u] * 6, [coolant_u]]]

  hex_lattice = openmc.HexLattice(name="Unit cell lattice")
  hex_lattice.orientation = lattice_orientation
  hex_lattice.center = (0.0, 0.0, 0.0)
  hex_lattice.pitch = (1.628, HEIGHT)
  hex_lattice.universes = lattice_univs
  hex_lattice.outer = openmc.Universe(cells=[openmc.Cell(fill=graphite_matrix)])
  hex_bb = openmc.model.HexagonalPrism(cell_edge_length, lattice_orientation, boundary_type='reflective')
  hex_cell = openmc.Cell(region=-hex_bb & axial_extents, fill=hex_lattice)
  compact_model.geometry = openmc.Geometry([hex_cell])

  hexagon_half_flat = np.sqrt(3.0) / 2.0 * cell_edge_length
  lower_left = (-cell_edge_length, -hexagon_half_flat, -HEIGHT / 2.0)
  upper_right = (cell_edge_length, hexagon_half_flat, HEIGHT / 2.0)

  # Add tallies.
  tals = common.tallies(run_surface = use_surface,
                        neutron_energy_bin_edges = np.logspace(np.log10(1e-6), np.log10(2.0e7), 101),
                        photon_energy_bin_edges = np.logspace(np.log10(1e2), np.log10(2.0e7), 101),
                        mesh_dimension = (51, 51, 1),
                        mesh_ll = lower_left,
                        mesh_ur = upper_right,
                        run_photon = run_photon)
  compact_model.tallies = tals

  # Finally, define some run settings.
  compact_model.settings = common.settings(use_surface, particles, active, inactive, run_photon, run_event)
  compact_model.settings.run_mode = 'eigenvalue'
  uniform_dist = openmc.stats.Box(lower_left, upper_right)
  compact_model.settings.source = openmc.IndependentSource(space = uniform_dist)

  compact_model.settings.temperature['method'] = 'nearest'
  compact_model.settings.temperature['range'] = (294.0, 500.0)
  compact_model.settings.temperature['tolerance'] = 200.0

  if use_entropy:
    entropy_mesh = openmc.RegularMesh(name = 'Entropy mesh')
    entropy_mesh.dimension = (5, 5, 11)
    entropy_mesh.lower_left = lower_left
    entropy_mesh.upper_right = upper_right
    compact_model.settings.entropy_mesh = entropy_mesh

  return compact_model

def main():
  parser = common.parser('HTGR Fresh Compact')
  parser.add_argument('--entropy', action = 'store_true', dest = 'entropy', default = False,
                      help = 'Whether source convergence should be assessed with Shannon entropy or not.')
  args = parser.parse_args()

  model = fresh_htgr_compact(args.use_surface, args.particles, args.active_batches,
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
