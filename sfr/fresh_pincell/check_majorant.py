import openmc
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

def main():
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

  sodium = openmc.Material(name='Sodium')
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
  fuel.name = 'Fuel'
  clad = openmc.Material.mix_materials([cu63, Al2O3], [0.997, 0.003], 'wo')
  clad.name = 'Cladding'

  maj = pd.read_csv('./macro_majorant.txt', delimiter='	', header=None)
  openmc_maj_grid = maj[0].to_numpy()
  openmc_maj_xs = maj[1].to_numpy()

  # Compute the different total cross sections.
  fuel_grid, fuel_xs = openmc.calculate_cexs(fuel, ['total'])
  clad_grid, clad_xs = openmc.calculate_cexs(clad, ['total'])
  na_grid, na_xs = openmc.calculate_cexs(sodium, ['total'])

  # Unionize the energy grids and compute the majorant manually.
  grid_union = np.union1d(fuel_grid, clad_grid)
  grid_union = np.union1d(grid_union, na_grid)
  fuel_interp = np.interp(grid_union, fuel_grid, fuel_xs[0])
  clad_interp = np.interp(grid_union, clad_grid, clad_xs[0])
  na_interp = np.interp(grid_union, na_grid, na_xs[0])
  union_majorant = np.maximum(fuel_interp, clad_interp)
  union_majorant = np.maximum(union_majorant, na_interp)

  # Interpolate onto OpenMC's energy grid as the size of the grids are different.
  interp_to_openmc_grid = np.interp(openmc_maj_grid, grid_union, union_majorant)
  diff = openmc_maj_xs - interp_to_openmc_grid

  print('Number of fuel grid points:', len(fuel_grid))
  print('Number of clad grid points:', len(clad_grid))
  print('Number of sodium grid points:', len(na_grid))
  print('Number of \'manual\' union grid points:', len(grid_union))
  print('Number of majorant grid points from OpenMC:', len(maj[0].to_numpy()))

  fig_1, ax_1 = plt.subplots()
  ax_1.plot(fuel_grid, fuel_xs[0], label = 'Fuel')
  ax_1.plot(clad_grid, clad_xs[0], label = 'Clad')
  ax_1.plot(na_grid, na_xs[0], label = 'Sodium')
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
