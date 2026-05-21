import openmc
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import openmc.data

def make_materials():
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

  return {'fuel' : fuel, 'clad' : clad, 'sodium' : sodium}

def max_urr_data(material):
  # We need to handle the URR as calculate_cexs cannot compute the UUR contribution.
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

def compute_maj_xs_with_urr(material):
  urr_xs = max_urr_data(material)

  nuc_fractions = material.get_nuclide_atom_densities()
  nuclides = list(nuc_fractions.keys())
  nuclide_total_micro = {}
  macro_nuclide = {}
  for nuclide in nuclides:
    nuc_grid, nuc_xs = openmc.calculate_cexs(nuclide, ['total'])
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

def main():
  materials = make_materials()

  # Compute the different total cross sections. We need to treat the fuel separately due to
  # the URR.
  per_material_maj = {}
  for name, mat in materials.items():
    grid, xs = compute_maj_xs_with_urr(mat)
    per_material_maj[name] = { 'grid' : grid, 'xs' : xs }

  grid_union = per_material_maj[list(materials.keys())[0]]['grid']
  for name in materials.keys():
    grid_union = np.union1d(grid_union, per_material_maj[name]['grid'])

  union_majorant = np.zeros_like(grid_union)
  for name in materials.keys():
    union_majorant = np.maximum(union_majorant, np.interp(grid_union, per_material_maj[name]['grid'], per_material_maj[name]['xs'], left=0.0, right=0.0))

  # Validate the majorant.
  fig, ax = plt.subplots()
  for name, mat in materials.items():
    grid, xs = openmc.calculate_cexs(mat, ['total'])
    ax.plot(grid, xs[0], label=name)
  ax.plot(grid_union, union_majorant, label='majorant')
  ax.set_ylabel('Cross Section (cm$^{-1}$)')
  ax.set_xlabel('Energy (eV)')
  ax.legend()
  ax.loglog()
  ax.grid()
  fig.tight_layout()
  fig.savefig('./new_majorant.png')
  plt.show()
  plt.close()

  df = pd.DataFrame({'energy' : grid_union, 'majorant' : union_majorant })
  df.to_csv('./manual_majorant.csv', sep=',', index=False, header=False)

if __name__ == '__main__':#
  main()
