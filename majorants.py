import numpy as np
import openmc
import openmc.data

# A function which computes the maximum URR cross section at a given energy point
# for nuclides in a given material.
def max_urr_data(material):
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

# A function which computes a majorant cross section for a material.
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

# A function which computes a whole-domain majorant cross section for a collection of materials.
def compute_domain_majorant(material_collection):
  per_material_maj = {}
  for mat in material_collection:
    grid, xs = compute_maj_xs_with_urr(mat)
    per_material_maj[mat.id] = { 'grid' : grid, 'xs' : xs }

  grid_union = per_material_maj[list(per_material_maj.keys())[0]]['grid']
  for id in per_material_maj.keys():
    grid_union = np.union1d(grid_union, per_material_maj[id]['grid'])

  union_majorant = np.zeros_like(grid_union)
  for id in per_material_maj.keys():
    union_majorant = np.maximum(union_majorant, np.interp(grid_union, per_material_maj[id]['grid'], per_material_maj[id]['xs'], left=0.0, right=0.0))

  return grid_union, union_majorant
