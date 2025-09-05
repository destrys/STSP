**Overview**
- The `stsp` Python package in this repo provides a small, typed API to assemble STSP input files and run actions, producing NumPy arrays from STSP outputs.
- Examples: see `sample/run_l.py`, `sample/run_m.py`, and `sample/run_s.py` for Action-L (light curve), Action-M (unseeded MCMC), and Action-s (seeded MCMC).

**Quick Start**
- Build binary: `make` (creates `./bin/stsp`).
- Run an example: `cd sample && PATH=../bin:$PATH PYTHONPATH=.. python3 run_l.py`.
- Outputs: the runner writes a `.in` file (e.g., `pyact-l.in`) and reads the expected STSP output (e.g., `pyact-l_lcout.txt`), returning it as a NumPy array and saving a copy alongside.

**API Basics**
- Import config types: `from stsp import ActionL, ActionM, PlanetProperties, StarProperties, SpotProperties, FittingProperties`.
- Choose a runner: `from stsp.runner import ActionLRunner, ActionMRunner`.
- Assemble config, then run with a working directory containing `model_lc.dat` (or supply an absolute path). Example snippet:
  - `fit = FittingProperties(data_filename="model_lc.dat", start_time=0.0, light_curve_duration_days=12.0, light_data_max=996.942768414, light_curve_flattened=False)`
  - `cfg = ActionL(planets=[...], star_properties=..., spot_properties=..., fitting_properties=..., spot_triplets=[...])`
  - `arr = ActionLRunner(cfg).run(workdir=Path("sample"))`  # `arr` is a NumPy array of the output file

**Paths and Environment**
- `workdir` controls where files are written/read; relative data filenames resolve under `workdir`.
- Ensure `stsp` is on `PATH` (e.g., `PATH=../bin:$PATH`) and the repo root is on `PYTHONPATH` so `import stsp` works when running from `sample/`.
