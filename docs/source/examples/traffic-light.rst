..    include:: <isonum.txt>

.. _example_traffic-light:

=====================
Traffic light control
=====================

This part of the documentation demonstrates how *STOMPC* is used to perform online control
for a traffic light intersection.

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

..
    // The text below should be adjusted if there is a published model of the traffic light.
    In most cases, a UPPAAL Stratego model suitable for offline strategy synthesis is adjusted to be
    suitable for online control. That also has been the situation for this case. The model
    from `this paper <doi.org/10.1007/978-3-662-49674-9_14>`_ has been modified for this online
    model-predictive control setup.
    In this section, we do not discuss how to adjust a model suitable for offline control to one for
    online control, but we indicate what you have to do specifically for using *STOMPC* tool to
    perform this online control.

In the UPPAAL Stratego model, we need to insert placeholders at the variables that will have
different values at the start of each MPC step, for example, the traffic light phase :math:`phase`.
These placeholders are strings with the format ``//TAG_<varname>``, where ``<varname>`` is the name
of the variable. So, for the integer variable :math:`phase` representing the traffic light phase,
we will rewrite

.. code-block::

    int phase = 0; // 0 east green, 1 south green

into

.. code-block::

    int phase = //TAG_phase; // 0 east green, 1 south green

Notice that after the tag there is still the semicolon ``;``, as only the placeholder will
be replaced by the initial value of that variable. The UPPAAL Stratego GUI will now also start to
give a syntax error on the next line, as it cannot find the closing semicolon.

After inserting all the placeholders in the UPPAAL Stratego model, we have to create a model
configuration file. This file tells the *STOMPC* tool which variables it need to keep track of
during MPC, and what their initial values are for the very first step. The model configuration file
has to be a yaml file, but you can use a custom name. For this case, we have the following
``traffic-light_config.yaml`` file:

.. code-block:: yaml

    t: 0.0
    E: 0
    S: 0
    phase: 0
    Q: 0.0


Finally, we have to specify the learning and other query parameters. This is also done in a separate
yaml-file. Below you can find the content of the ``verifyta_config.yaml`` file for the traffic light
example (with some arbitrarily numbers that ensure fast calculations). In
:ref:`example_traffic-light_experiment_variables` we will indicate in python which files contain the model and
strategy configurations. This file contains pairs of the setting name and its value, where the
setting name is the one used for the command line interface of UPPAAL Stratego. In case a certain
parameter does not have a value, for example ``nosummary``, you just leave the value field empty.

.. code-block:: yaml

    learning-method: 4
    good-runs: 100
    total-runs: 100
    runs-pr-state: 100
    eval-runs: 100
    max-iterations: 30
    filter: 0
    nosummary:
    silence-progress:



---------------------------------------------
Specializing the MPCSetup class from *STOMPC*
---------------------------------------------

The *STOMPC* tool provides several classes that can be tailored for the case you want to use
it for.

* ``MPCsetup``. This class is the primarily class an end-user should specialize for his or her
  case. It implements the basic MPC scheme. It assumes that UPPAAL Stratego will always success in
  synthesizing a safe and optimal strategy.
* ``SafeMPCSetup``. This class inherits from ``MPCsetup``, yet it monitors and detects
  whether UPPAAL Stratego has successfully synthesized a strategy. If not, it will run UPPAAL
  Stratego with an alternative query, which has to be specified by the user, as it depends on the
  model what a safe query would be.

For the traffic light system, the primary goal is to synthesize a strategy that minimizes the cumulative
number of waiting cars (optimality). As there is no safety requirement, UPPAAL Stratego will always
synthesize a strategy. Therefore, the ``MPCSetup`` class should be specialized.

Below the specialized class ``MPCSetupTrafficLight`` is defined. As can be seen, we override the
``create_query_file`` method.

.. code-block:: python

    import strategoutil as stompc

    class MPCSetupTrafficLight(stompc.MPCsetup):
        # Overriding parent method.
        def create_query_file(self, horizon, period, final):
            """
            Create the query file for each step of the traffic light model. Current
            content will be overwritten.
            """
            with open(self.query_file, "w") as f:
                line1 = f"strategy opt = minE (Q) [<={horizon}*{period}]: <> (t=={final})\n"
                f.write(line1)
                f.write("\n")
                line2 = f"simulate 1 [<={period}+1] {{ " \
                        f"{self.controller.get_var_names_as_string()} }} under opt\n"
                f.write(line2)

In method ``create_query_file`` we specify the strategy synthesis query. For the traffic light case,
we have this defined with ``line1``. It states that
we want to synthesize a strategy that we call ``opt`` that minimizes the expected value of
clock variable :math:`Q` (representing the cost in the model) where all runs have a maximum duration of
the number of periods (denoted by ``horizon``) and UPPAAL Stratego time units per period
(denoted by ``period``) such that eventually the time variable :math:`t` reaches its final value.

Furthermore, we have a simulate query in this method. Only the first period is simulated to obtain
the first control action of the synthesized strategy ``opt`` and the system's state after one period.


.. _example_traffic-light_experiment_variables:

---------------------------
Define experiment variables
---------------------------

We can now define and set all the experiment variables. These include, for example, file paths to
the UPPAAL Stratego model.

.. code-block:: python

    import yaml

    if __name__ == "__main__":
        # Define location of the relevant files and commands.
        modelTemplatePath = "traffic-light_template.xml"
        queryFilePath = "traffic-light_query.q"
        outputFilePath = "results.txt"
        modelConfigPath = "traffic-light_config.yaml"
        learningConfigPath = "verifyta_config.yaml"
        verifytaCommand = "verifyta-stratego-9"

        # Define MPC model variables.
        debug = True  # Whether to run in debug mode.
        period = 60  # Period in time units (minutes).
        horizon = 1  # How many periods to compute strategy for.
        duration = 30  # Duration of experiment in periods.


After this we load the two configuration files:

.. code-block:: python

    # Get model and learning config dictionaries from files.
    with open(model_config_path, "r") as yamlfile:
        model_cfg_dict = yaml.safe_load(yamlfile)
    with open(learning_config_path, "r") as yamlfile:
        learning_cfg_dict = yaml.safe_load(yamlfile)


Finally, we can create the MPC object from our ``MPCSetupTrafficLight`` class and call ``run`` with the MPC inputs:

.. code-block:: python

    # Construct the MPC object.
    controller = MPCSetupTrafficLight(modelTemplatePath, query_file=queryFilePath,
                                      output_file_path=outputFilePath, model_cfg_dict=model_cfg_dict,
                                      learning_args=learning_cfg_dict,
                                      verifyta_command=verifytaCommand, debug=debug)

    controller.run(controller.run(period, horizon, duration)
