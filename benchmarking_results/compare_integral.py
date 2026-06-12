#!/usr/bin/env python3

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

CASES = {
  'jezebel' : [''],
  'lwr' : ['fresh_pincell'],
  'sfr' : ['fresh_pincell'],
  'htgr' : ['fresh_compact']
}

CASE_LABELS = {
  'jezebel/' : 'Jezebel',
  'lwr/fresh_pincell' : 'LWR Pincell',
  'sfr/fresh_pincell' : 'SFR Pincell',
  'htgr/fresh_compact' : 'HTGR Compact ($15\\%$ PF)'
}

TRACK_LABEL = {
  'surface' : 'Surface Tracking',
  'delta' : 'Delta Tracking'
}

def plot_speedups(integral_data):
  # Collapse to speedup data
  speedup = {}
  for num_particles in [1000, 10000, 100000]:
    speedup[num_particles] = {}
    for case in CASES.keys():
      for subcase in CASES[case]:
        path = f'{case}/{subcase}'
        speedup[num_particles][path] = []
        for run_photon in [False, True]:
          sim_type = "coupled" if run_photon else "single"
          algorithm = "history"

          datapoint_d = f"{sim_type}_delta_{algorithm}_integral_p{num_particles}"
          datapoint_s = f"{sim_type}_surface_{algorithm}_integral_p{num_particles}"
          speedup[num_particles][path].append(
            float(f'{(integral_data[path][datapoint_d]['active_rate'].to_numpy() / integral_data[path][datapoint_s]['active_rate'].to_numpy())[0]:.2f}')
          )

  # Plot the speedup data
  sim_labels = ['Neutron', 'Photon + Neutron']

  for num_particles in [1000, 10000, 100000]:
    x = np.arange(2)  # the label locations
    width = 0.225  # the width of the bars
    multiplier = 0
    fig, ax = plt.subplots(layout='constrained')

    for case, data in speedup[num_particles].items():
      offset = width * multiplier
      rects = ax.bar(x + offset, tuple(data), width, label=CASE_LABELS[case], zorder=3)
      ax.bar_label(rects, padding=10)
      multiplier += 1

    ax.set_ylabel('Active Rate Speedup (-)')
    ax.set_xticks(x + width * (1.5), sim_labels)
    ax.legend(loc='upper left', ncols=2)
    ax.set_ylim(0, 6)
    ax.set_title(f'{num_particles} Particles per Batch')
    ax.grid(zorder=0)
    fig.savefig(f'./figures/performance/active_speedup_p{num_particles}.png')
    plt.close()

def plot_leakage(integral_data):
  algorithm = "history"

  # Collapse to leakage fraction data.
  leakage = {}
  leakage_std = {}
  for track_type in ['surface', 'delta']:
    leakage[track_type] = {}
    leakage_std[track_type] = {}
    for case in CASES.keys():
      for subcase in CASES[case]:
        path = f'{case}/{subcase}'
        leakage[track_type][path] = {}
        leakage_std[track_type][path] = {}
        for run_photon in [False, True]:
          sim_type = "coupled" if run_photon else "single"
          leakage[track_type][path][sim_type] = []
          leakage_std[track_type][path][sim_type] = []
          for num_particles in [1000, 10000, 100000]:
            datapoint = f"{sim_type}_{track_type}_{algorithm}_integral_p{num_particles}"
            leakage[track_type][path][sim_type].append(integral_data[path][datapoint]['leakage_mean'].to_numpy()[0])
            leakage_std[track_type][path][sim_type].append(integral_data[path][datapoint]['leakage_std_dev'].to_numpy()[0])

  # Plot the leakage fraction data.
  particles = [1000, 10000, 100000]
  for case in CASES.keys():
    for subcase in CASES[case]:
      path = f'{case}/{subcase}'
      fig, ax = plt.subplots()
      for track_type in ['surface', 'delta']:
        sim_type = 'single'
        mean = leakage[track_type][path][sim_type]
        std_dev = 3.0*np.array(leakage_std[track_type][path][sim_type])
        ax.errorbar(particles, mean, yerr=std_dev, capsize=4, fmt='o', label=TRACK_LABEL[track_type])
      ax.set_title(CASE_LABELS[path])
      ax.set_xscale('log')
      ax.legend()
      ax.set_ylabel('Leakage Fraction $\\pm 3\\sigma$ (-)')
      ax.set_xlabel('Particles per Batch (-)')
      ax.grid()
      fig.tight_layout()
      if subcase:
        fig.savefig(f'./figures/integral/{case}_{subcase}_leakage.png')
      else:
        fig.savefig(f'./figures/integral/{case}_leakage.png')
      plt.close()

def plot_keff(integral_data):
  algorithm = "history"

  # Collapse to k-collision data.
  k_collision = {}
  k_collision_std = {}
  for track_type in ['surface', 'delta']:
    k_collision[track_type] = {}
    k_collision_std[track_type] = {}
    for case in CASES.keys():
      for subcase in CASES[case]:
        path = f'{case}/{subcase}'
        k_collision[track_type][path] = {}
        k_collision_std[track_type][path] = {}
        for run_photon in [False, True]:
          sim_type = "coupled" if run_photon else "single"
          k_collision[track_type][path][sim_type] = []
          k_collision_std[track_type][path][sim_type] = []
          for num_particles in [1000, 10000, 100000]:
            datapoint = f"{sim_type}_{track_type}_{algorithm}_integral_p{num_particles}"
            k_collision[track_type][path][sim_type].append(integral_data[path][datapoint]['k_coll_mean'].to_numpy()[0])
            k_collision_std[track_type][path][sim_type].append(integral_data[path][datapoint]['k_coll_std_dev'].to_numpy()[0])

  # Plot the k-collision data
  particles = [1000, 10000, 100000]
  for case in CASES.keys():
    for subcase in CASES[case]:
      path = f'{case}/{subcase}'
      fig, ax = plt.subplots()
      for track_type in ['surface', 'delta']:
        sim_type = 'single'
        mean = k_collision[track_type][path][sim_type]
        std_dev = 3.0*np.array(k_collision_std[track_type][path][sim_type])
        ax.errorbar(particles, mean, yerr=std_dev, capsize=4, fmt='o', label=TRACK_LABEL[track_type])
      ax.set_title(CASE_LABELS[path])
      ax.set_xscale('log')
      ax.legend()
      ax.set_ylabel('$k_{eff} \\pm 3\\sigma$, Collision Estimator (-)')
      ax.set_xlabel('Particles per Batch (-)')
      ax.grid()
      fig.tight_layout()
      if subcase:
        fig.savefig(f'./figures/integral/{case}_{subcase}_keff.png')
      else:
        fig.savefig(f'./figures/integral/{case}_keff.png')
      plt.close()

def main():
  integral_data = {}
  for case in CASES.keys():
    for subcase in CASES[case]:
      path = f'{case}/{subcase}'
      integral_data[path] = {}
      for run_surface in [False, True]:
        track_type = "surface" if run_surface else "delta"
        for run_photon in [False, True]:
          sim_type = "coupled" if run_photon else "single"
          for run_event in [False]:
            algorithm = "event" if run_event else "history"
            for num_particles in [1000, 10000, 100000]:
              datapoint = f"{sim_type}_{track_type}_{algorithm}_integral_p{num_particles}"
              integral_data[path][datapoint] = pd.read_csv(f"./{path}/{datapoint}_ab1000_ib100.csv")

  plot_speedups(integral_data)
  plot_keff(integral_data)
  plot_leakage(integral_data)

if __name__ == '__main__':
  main()
