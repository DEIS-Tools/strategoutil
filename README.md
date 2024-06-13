# strategoutil
Collection of utility functions and classes to interface [UPPAAL Stratego](https://uppaal.org/features/#uppaal-stratego) controllers with Python.

## Repo status
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![badge](https://github.com/DEIS-Tools/strategoutil/actions/workflows/build.yml/badge.svg)](https://github.com/DEIS-Tools/strategoutil/actions)
[![Documentation Status](https://readthedocs.org/projects/strategoutil/badge/?version=latest)](https://strategoutil.readthedocs.io/en/latest/?badge=latest)

See which OS and Python versions combinations are supported [here](https://github.com/DEIS-Tools/strategoutil/actions).

## Getting started
 1) Use pip or clone this git repo to install `strategoutil` to your environment

```sh
pip install strategoutil
# OR
git clone https://github.com/DEIS-Tools/strategoutil.git
cd strategoutil
pip install -e .
```

2) Look how `strategoutil` is used with [example projects](https://github.com/mihsamusev/stratego_mpc_example)

3) Look at the [documentation](https://strategoutil.readthedocs.io/en/latest/)
## Functionality
Currently, *strategoutil* contains the tool *STOMPC* that is capable of performing the following
actions:

- Write input variables to Stratego model `*.xml` files
- Parse outputs of `simulate` queries to get timeseries of important variables
- Run `verifyta` with chosen query `*.q` and run parameters
- Create model predictive control (MPC) routines where plant is either defined within the same Stratego model, or plant is defined as external process, simulataor, etc.







