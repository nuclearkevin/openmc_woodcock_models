#!/usr/bin/env python3

import numpy as np
import pandas as pd
import argparse as ap
from matplotlib import pyplot as plt

def main():
  parser = ap.ArgumentParser(prog = 'Plot Majorant',
                             description = 'Plots the majorant cross section from an CSV file.')
  parser.add_argument(type = str, dest = 'file',
                      help = 'The majorant file to  plot')

  args = parser.parse_args()

  df = pd.read_csv(f'{args.file}', header=None)
  energy = df[0].to_numpy()
  xs = df[1].to_numpy()

  if "photon" in args.file:
    energy = np.exp(energy)
    xs = np.exp(xs)

  plt.plot(energy, xs)
  plt.loglog()
  plt.xlabel('Energy eV]')
  plt.ylabel('Majorant Cross Section  [cm^-1]')
  plt.show()

if __name__ == '__main__':
  main()
