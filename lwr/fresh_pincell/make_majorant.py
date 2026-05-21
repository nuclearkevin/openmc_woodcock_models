import openmc
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import openmc.data

def make_materials():
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

  return {'fuel' : uo2,  'helium' : helium,  'clad' : zircaloy, 'water' : borated_water}

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
  library = openmc.data.DataLibrary.from_xml()
  urr_xs = max_urr_data(material)

  nuc_fractions = material.get_nuclide_atom_densities()
  nuclides = list(nuc_fractions.keys())

  # Find SAB data.
  sabs = {}
  for nuclide in nuclides:
      sabs[nuclide] = None
  for sab_name, _ in material._sab:
    sab = openmc.data.ThermalScattering.from_hdf5(
        library.get_by_material(sab_name, data_type='thermal')['path'])
    for nuc in sab.nuclides:
        sabs[nuc] = sab_name

  nuclide_total_micro = {}
  macro_nuclide = {}
  for nuclide in nuclides:
    nuc_grid, nuc_xs = openmc.calculate_cexs(nuclide, ['total'], sab_name=sabs[nuclide])
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
