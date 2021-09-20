Welcome to strategoutil's documentation!
========================================

*Strategoutil* is a collection of utility functions and classes to interface
`UPPAAL Stratego <https://people.cs.aau.dk/~marius/stratego/>`_ controllers with Python. It furthermore
provides an interface to perform model-predictive control or online-control.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   api


Getting started
---------------

1) Use pip or clone this git repo to install *strategoutil* to your environment

  .. code-block:: sh

      pip install strategoutil

  or

  .. code-block:: sh

      git clone https://github.com/mihsamusev/strategoutil.git
      cd strategoutil
      pip install -e .

2) Look how *strategoutil* is used with `example projects <https://github.com/mihsamusev/stratego_mpc_example>`_

Functionality
-------------

- Write input variables to Stratego model *\*.xml* files
- Parse outputs of *simulate* queries to get timeseries of important variables
- Run *verifyta* with chosen query *\*.q* and run parameters
- Create model predictive control (MPC) routines where plant is either defined within the same Stratego model,
  or plant is defined as external process, simulataor, etc.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
