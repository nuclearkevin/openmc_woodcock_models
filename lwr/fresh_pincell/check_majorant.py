import openmc
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

def main():
  uo2 = openmc.Material(name='UO2 fuel at 2.4% wt enrichment')
  uo2.set_density('g/cm3', 10.29769)
  uo2.add_element('U', 1., enrichment = 2.4)
  uo2.add_element('O', 2.)

  helium = openmc.Material(name='Helium for gap')
  helium.set_density('g/cm3', 0.001598)
  helium.add_element('He', 2.4044e-4)

  zircaloy = openmc.Material(name='Zircaloy 4')
  zircaloy.set_density('g/cm3', 6.55)
  zircaloy.add_element('Sn', 0.014  , 'wo')
  zircaloy.add_element('Fe', 0.00165, 'wo')
  zircaloy.add_element('Cr', 0.001  , 'wo')
  zircaloy.add_element('Zr', 0.98335, 'wo')

  borated_water = openmc.Material(name='Borated water')
  borated_water.set_density('g/cm3', 0.740582)
  borated_water.add_element('B', 4.0e-5)
  borated_water.add_element('H', 5.0e-2)
  borated_water.add_element('O', 2.4e-2)
  borated_water.add_s_alpha_beta('c_H_in_H2O')

  maj = pd.read_csv('./macro_majorant.txt', delimiter='	', header=None)
  openmc_maj_grid = maj[0].to_numpy()
  openmc_maj_xs = maj[1].to_numpy()

  # Compute the different total cross sections.
  fuel_grid, fuel_xs = openmc.calculate_cexs(uo2, ['total'])
  he_grid, he_xs = openmc.calculate_cexs(helium, ['total'])
  clad_grid, clad_xs = openmc.calculate_cexs(zircaloy, ['total'])
  water_grid, water_xs = openmc.calculate_cexs(borated_water, ['total'])

  # Unionize the energy grids and compute the majorant manually.
  grid_union = np.union1d(fuel_grid, clad_grid)
  grid_union = np.union1d(grid_union, he_grid)
  grid_union = np.union1d(grid_union, water_grid)
  fuel_interp = np.interp(grid_union, fuel_grid, fuel_xs[0])
  he_interp = np.interp(grid_union, he_grid, he_xs[0])
  clad_interp = np.interp(grid_union, clad_grid, clad_xs[0])
  water_interp = np.interp(grid_union, water_grid, water_xs[0])
  union_majorant = np.maximum(fuel_interp, clad_interp)
  union_majorant = np.maximum(union_majorant, he_interp)
  union_majorant = np.maximum(union_majorant, water_interp)

  # Interpolate onto OpenMC's energy grid as the size of the grids are different.
  interp_to_openmc_grid = np.interp(openmc_maj_grid, grid_union, union_majorant)
  diff = openmc_maj_xs - interp_to_openmc_grid

  print('Number of fuel grid points:', len(fuel_grid))
  print('Number of he grid points:', len(he_grid))
  print('Number of clad grid points:', len(clad_grid))
  print('Number of water grid points:', len(water_grid))
  print('Number of \'manual\' union grid points:', len(grid_union))
  print('Number of majorant grid points from OpenMC:', len(maj[0].to_numpy()))

  fig_1, ax_1 = plt.subplots()
  ax_1.plot(fuel_grid, fuel_xs[0], label = 'Fuel')
  ax_1.plot(he_grid, he_xs[0], label = 'He')
  ax_1.plot(clad_grid, clad_xs[0], label = 'Clad')
  ax_1.plot(water_grid, water_xs[0], label = 'Water')
  ax_1.plot(openmc_maj_grid, openmc_maj_xs, label = 'OpenMC Majorant', color='black', linestyle='--')
  ax_1.grid()
  ax_1.legend()
  ax_1.set_xlabel('Energy (eV)')
  ax_1.set_ylabel('Total Cross Section (cm$^{-1}$)')
  ax_1.loglog()
  fig_1.savefig('./openmc_maj_vs_total.png')
  plt.show()
  plt.close()

  fig_2, ax_2 = plt.subplots()
  #ax.plot(fuel_grid, fuel_xs[0], label = 'Fuel')
  #ax.plot(clad_grid, clad_xs[0], label = 'Clad')
  #ax.plot(na_grid, na_xs[0], label = 'Sodium')
  ax_2.plot(openmc_maj_grid, interp_to_openmc_grid, label = '\'Manual\' Majorant')
  ax_2.plot(openmc_maj_grid, openmc_maj_xs, label = 'OpenMC Majorant', color='black', linestyle='--')
  ax_2.grid()
  ax_2.legend()
  ax_2.set_xlabel('Energy (eV)')
  ax_2.set_ylabel('Cross Section (cm$^{-1}$)')
  ax_2.loglog()
  fig_2.savefig('./openmc_maj_vs_manual.png')
  plt.show()
  plt.close()

  print('Minimum difference between majorants:', np.min(diff))
  print('Maximum difference between majorants:', np.max(diff))

  if len(diff[diff < 0.0]) > 0:
    print('Energy points:', openmc_maj_grid[diff < 0.0])
    print('OpenMC - \'Manual\':', diff[diff < 0.0])

  fig_comp, ax_comp = plt.subplots()
  ax_comp.plot(openmc_maj_grid, diff, label = 'Difference')
  if len(diff[diff < 0.0]) > 0:
    ax_comp.scatter(openmc_maj_grid[diff < 0.0], diff[diff < 0.0], label = 'Negative Difference', color = 'black')
  ax_comp.grid()
  ax_comp.set_xlabel('Energy (eV)')
  ax_comp.set_ylabel('Difference in Majorant Cross Section (cm$^{-1}$)')
  ax_comp.set_xscale('log')
  if len(diff[diff < 0.0]) > 0:
    ax_comp.legend()
  fig_comp.savefig('./openmc_maj_vs_manual_diff.png')
  plt.show()
  plt.close()

if __name__ == '__main__':
  main()
