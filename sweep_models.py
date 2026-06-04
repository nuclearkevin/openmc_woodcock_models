import os

# Key is the particular type of case. Value is the subcase (which contains the model file).
CASES = {
  'jezebel' : ['']#,
  #'lwr' : ['fresh_pincell'],
  #'sfr' : ['fresh_pincell'],
  #'htgr' : ['fresh_compact']
}

# Key is whether photon transport is running or not. Value is the number of particles.
PARTICLES = {
  True : [1000, 10000],
  False : [1000, 10000, 100000]
}

def run_model(run_surface, run_photon, run_event, num_particles):
  exec_str = f'./model.py -r -p {int(num_particles)}'
  if run_surface:
    exec_str += ' -s'
  if run_photon:
    exec_str += ' --photon'
  if run_event:
    exec_str += ' --event'

  print(f'Running {exec_str}')
  code = os.system(exec_str)
  if code:
    raise Exception(f'Failed to run the model with error code {code}')

def main():
  repo_root_dir = os.getcwd()
  for case in CASES.keys():
    for sub_case in CASES[case]:
      # Change to the case directory.
      dir = f'./{case}' if sub_case == '' else f'./{case}/{sub_case}'
      os.chdir(dir)
      for run_surface in [False, True]:
        for run_photon in [False, True]:
          for run_event in [False, True]:
            for num_particles in PARTICLES[run_photon]:
              run_model(run_surface, run_photon, run_event, num_particles)

      # Back out to the repo root directory.
      os.chdir(repo_root_dir)

if __name__ == '__main__':
  main()
