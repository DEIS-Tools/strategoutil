# strategoutil
Utility functions to interface UPPAAL Stratego with python

## Repo status
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/mihsamusev/strategoutil)
[![badge](https://github.com/mihsamusev/strategoutil/workflows/build/badge.svg)](https://github.com/mihsamusev/strategoutil/actions)


### TODO:
- Travis
- Testing run on push?
- gitmodules to be able to install it with other things
- setup py installs requirements

## Getting started
 1) Clone and install `strategoutil` to your environment

```sh
git clone https://github.com/mihsamusev/strategoutil.git
cd strategoutil
pip install -e .
```

2) Run tests, successful passing of all tests does not depend on having `verifyta` installed on your machine.
```sh
python -m pytest
```

3) Import to your stratego MPC project and start hacking, see [example project](https://github.com/mihsamusev/stratego_mpc_example)
```python
import strategoutil as sutil
```

## Reference



