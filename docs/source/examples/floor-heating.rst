..    include:: <isonum.txt>

.. _example_floor-heating:

=============
Floor heating
=============

This part of the documentation demonstrates how *STOMPC* is used to perform online control
for floor heating in a family house.

--------------------
Installing the tools
--------------------

For this case, we need to have two tools available:

* *strategoutil*, the tool as described in this documentation, and
* UPPAAL Stratego, the generic tool that will synthesize strategies.

Information on how to install *strategoutil* and UPPAAL Stratego can be found in the :ref:`installation`.

-----------------------------------
Preparing the UPPAAL Stratego model
-----------------------------------

In most cases, a UPPAAL Stratego model suitable for offline strategy synthesis is adjusted to be 
suitable for online control. That also has been the situation for this case. The model 
from `this paper <doi.org/10.1007/978-3-662-49674-9_14>`_ has been modified for this online
model-predictive control setup.
In this section, we do not discuss how to adjust a model suitable for offline control to one for 
online control, but we indicate what you have to do specifically for using *STOMP* tool to
perform this online control.

In the UPPAAL Stratego model, we need to insert placeholders at the variables that will have
different values at the start of each MPC step, for example, the room temperature :math:`T`.
These placeholders are strings with the format ``//TAG_<varname>``, where ``<varname>`` is the name
of the variable. So, for the clock variable :math:`T` representing the room temperature, we will rewrite

.. code-block::

    clock T = 18; // room temperature in deg. C

into

.. code-block::

    clock T = //TAG_T; // room temperature in deg. C

Notice that after the tag there is still the semicolon ``;``, as only the placeholder will
be replaced by the initial value of that variable. The UPPAAL Stratego GUI will now also start to
give a syntax error on the next line, as it cannot find the closing semicolon.

After inserting all the placeholders in the UPPAAL Stratego model, we have to create a model
configuration file. This file tells the *STOMP* tool which variables it need to keep track of
during MPC, and what their initial values are for the very first step. The model configuration file
has to be a yaml file, but you can use a custom name. For this case, we have the following
``floor-heating_config.yaml`` file:

.. code-block:: yaml

    t: 0.0
    T: 18.0
    D: 0.0
    heatLoc: 0
    winLoc: 0
    w: 0.0
    i: 0


Finally, we have to specify the learning and other query parameters. This is also done in a separate
yaml-file. Below you can find the content of the ``verifyta_config.yaml`` file for the floor heating
example (with some arbitrarily numbers that ensure fast calculations). In
:ref:`example_floor-heating_experiment_variables` we will indicate in python which files contain the model and
strategy configurations. This file contains pairs of the setting name and its value, where the
setting name is the one used for the command line interface of UPPAAL Stratego. In case a certain
parameter does not have a value, for example ``nosummary``, you just leave the value field empty.

.. code-block:: yaml

    learning-method: 4
    good-runs: 25
    total-runs: 25
    runs-pr-state: 15
    eval-runs: 25
    discretization: 1.0
    filter: 2
    nosummary:
    silence-progress:


--------------------------------------------
Specializing the MPCSetup class from *STOMP*
--------------------------------------------

The *STOMP* tool provides several classes that can be tailored for the case you want to use
it for.

* ``MPCsetup``. This class is the primarily class an end-user should specialize for his or her
  case. It implements the basic MPC scheme as explained in Section~\ref{sect:tooloverview}. It
  assumes that UPPAAL Stratego will always success in synthesizing a safe and optimal strategy.
* ``SafeMPCSetup``. This class inherits from ``MPCsetup``, yet it monitors and detects
  whether UPPAAL Stratego has successfully synthesized a strategy. If not, it will run UPPAAL
  Stratego with an alternative query, which has to be specified by the user, as it depends on the
  model what a safe query would be.

For the floor heating, the primary goal is to synthesize a strategy that minimizes the cumulative
distance between the room temperature and target temperature (optimality). As there is no safety
requirement, UPPAAL Stratego will always synthesize a strategy. Therefore, the ``MPCSetup`` class
should be specialized.

Below the specialized class ``MPCSetupFloorHeating`` is defined. As can be seen, we override the
``create_query_file`` method.

.. code-block:: python

    import strategoutil as stompc

    class MPCSetupFloorHeating(stompc.MPCSetup):
        def create_query_file(self, horizon, period, final):
            """
            Create the query file for each step of the room heating model. Current
            content will be overwritten.

            Overrides MPCsetup.create_query_file().
            """
            with open(self.query_file, "w") as f:
                line1 = f"strategy opt = minE (D) [<={horizon}*{period}]: <> (t=={final})\n"
                f.write(line1)
                f.write("\n")
                line2 = f"simulate 1 [<={period}+1] {{ " \
                    f"{self.controller.get_var_names_as_string()} }} under opt\n"
                f.write(line2)

In method ``create_query_file`` we specify the strategy synthesis query. For the floor heating case,
we have this defined with ``line1``. It states that
we want to synthesize a strategy that we call ``opt`` that minimizes the expected value of
clock variable :math:`D` (representing the cost in the model) where all runs have a maximum duration of
the number of periods (denoted by ``horizon``) and UPPAAL Stratego time units per period
(denoted by ``period``) such that eventually the time variable :math:`t` reaches its final value.

Furthermore, we have a simulate query in this method. Only the first period is simulated to obtain
the first control action of the synthesized strategy ``opt`` and the system's state after one period.


.. _example_floor-heating_experiment_variables:

---------------------------
Define experiment variables
---------------------------

We can now define and set all the experiment variables. These include, for example, file paths to
the UPPAAL Stratego model.

.. code-block:: python

    import yaml

    if __name__ == "__main__":
        # We specify the Uppaal files.
        modelTemplatePath = "floor-heating-online.xml"
        queryFilePath = "floor-heating-online_query.q"
        outputFilePath = "results.txt"
        modelConfigPath = "floor-heating_config.yaml"
        learningConfigPath = "verifyta_config.yaml"
        verifytaCommand = "verifyta-stratego-9"

        # Define MPC model variables.
        debug = True  # Whether to run in debug mode.
        period = 15  # Period in time units (minutes).
        horizon = 5  # How many periods to compute strategy for.
        duration = 96  # Duration of experiment in periods.


After this we load the two configuration files:

.. code-block:: python

    # Get model and learning config dictionaries from files.
    with open(model_config_path, "r") as yamlfile:
        model_cfg_dict = yaml.safe_load(yamlfile)
    with open(learning_config_path, "r") as yamlfile:
        learning_cfg_dict = yaml.safe_load(yamlfile)


Finally, we can create the MPC object from our ``MPCSetupPond`` class and call ``run`` with the MPC inputs:

.. code-block:: python

    # Construct the MPC object.
    controller = MPCSetupFloorHeating(modelTemplatePath, query_file=queryFilePath,
                                      output_file_path=outputFilePath, model_cfg_dict=model_cfg_dict,
                                      learning_args=learning_cfg_dict,
                                      verifyta_command=verifytaCommand, debug=debug)

    controller.run(controller.run(period, horizon, duration)
