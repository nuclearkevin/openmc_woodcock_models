#!/usr/bin/env python3

# Resolving imports for the common module
import sys
sys.path.append("../../")
import common

import argparse as ap
import openmc
import numpy as np
import pandas as pd

# Adapted from the OpenMC LWR pincell example problem.
FUEL_OR = 0.39218
CLAD_IR = 0.40005
CLAD_OR = 0.45720
PIN_PITCH = 1.25984
PIN_LENGTH  = 200.0
def fresh_lwr_pincell(use_surface, particles, active, inactive, use_entropy) -> openmc.Model:
  pincell_model = openmc.Model()

  # Materials (UO2 fuel, helium as the gas gap, Zircaloy 4 cladding, and borated water coolant).
  uo2 = openmc.Material(name='UO2 fuel at 2.4% wt enrichment')
  uo2.set_density('g/cm3', 10.29769)
  uo2.add_element('U', 1., enrichment = 2.4)
  uo2.add_element('O', 2.)
  pincell_model.materials.append(uo2)

  helium = openmc.Material(name='Helium for gap')
  helium.set_density('g/cm3', 0.001598)
  helium.add_element('He', 2.4044e-4)
  pincell_model.materials.append(helium)

  zircaloy = openmc.Material(name='Zircaloy 4')
  zircaloy.set_density('g/cm3', 6.55)
  zircaloy.add_element('Sn', 0.014  , 'wo')
  zircaloy.add_element('Fe', 0.00165, 'wo')
  zircaloy.add_element('Cr', 0.001  , 'wo')
  zircaloy.add_element('Zr', 0.98335, 'wo')
  pincell_model.materials.append(zircaloy)

  borated_water = openmc.Material(name='Borated water')
  borated_water.set_density('g/cm3', 0.740582)
  borated_water.add_element('B', 4.0e-5)
  borated_water.add_element('H', 5.0e-2)
  borated_water.add_element('O', 2.4e-2)
  borated_water.add_s_alpha_beta('c_H_in_H2O')
  pincell_model.materials.append(borated_water)

  # Geometry
  ## Radial rings
  fuel_or = openmc.ZCylinder(r = FUEL_OR, name='Fuel OR')
  clad_ir = openmc.ZCylinder(r = CLAD_IR, name='Clad IR')
  clad_or = openmc.ZCylinder(r = CLAD_OR, name='Clad OR')

  ## Axial extents
  bottom = openmc.ZPlane(z0 = -PIN_LENGTH / 2.0, boundary_type = 'vacuum')
  top    = openmc.ZPlane(z0 =  PIN_LENGTH / 2.0, boundary_type = 'vacuum')
  axial_extents = +bottom & -top

  ## Bounding water box.
  box = openmc.model.RectangularPrism(PIN_PITCH, PIN_PITCH, boundary_type = 'reflective')

  ## Create the geometry and universe.
  fuel = openmc.Cell(fill = uo2, region = -fuel_or & axial_extents)
  gap = openmc.Cell(fill = helium, region = +fuel_or & -clad_ir & axial_extents)
  clad = openmc.Cell(fill = zircaloy, region = +clad_ir & -clad_or & axial_extents)
  water = openmc.Cell(fill = borated_water, region = +clad_or & -box & axial_extents)
  pincell_model.geometry = openmc.Geometry([fuel, gap, clad, water])

  lower_left = (-PIN_PITCH / 2.0, -PIN_PITCH / 2.0, -PIN_PITCH / 2.0)
  upper_right = ( PIN_PITCH / 2.0,  PIN_PITCH / 2.0,  PIN_PITCH / 2.0)

  # Add tallies.
  tals = common.tallies(energy_bin_edges = np.logspace(np.log10(1e-6), np.log10(2.0e7), 101),
                        mesh_dimension = (11, 11, 1),
                        mesh_ll = lower_left,
                        mesh_ur = upper_right)
  pincell_model.tallies = tals

  # Finally, define some run settings.
  pincell_model.settings = common.settings(use_surface, particles, active, inactive)
  pincell_model.settings.run_mode = 'eigenvalue'
  uniform_dist = openmc.stats.Box(lower_left, upper_right)
  pincell_model.settings.source = openmc.IndependentSource(space = uniform_dist)

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

  model = fresh_lwr_pincell(args.use_surface, args.particles, args.active_batches, args.inactive_batches, args.entropy)
  model.export_to_model_xml()

  if args.run:
    model.run(apply_tally_results=True, openmc_exec=f'../../{common.OPENMC_EXEC}')
    common.output_results(model, args.use_surface)

if __name__ == "__main__":
  main()
