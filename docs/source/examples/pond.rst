..    include:: <isonum.txt>

.. _example_pond:

==========================
Storm water detention pond
==========================

This part of the documentation demonstrates how *strategoutil* is used to perform online control
for storm water detention ponds.

--------------------
Installing the tools
--------------------

For this case, we need to have three tools available:

* *strategoutil*, the tool as described in this documentation,
* UPPAAL Stratego, the generic tool that will synthesize strategies, and
* pySWMM the Python API for SWMM, the domain-specific tool that will perform detailed simulations of the pond.

Information on how to install *strategoutil* and UPPAAL Stratego can be found in the :ref:`installation`.

pySWMM is available though pip:

.. code-block:: sh
    
    pip install pyswmm


-----------------------------------
Preparing the UPPAAL Stratego model
-----------------------------------

In most cases, a UPPAAL Stratego model suitable for offline strategy synthesis is adjusted to be 
suitable for online control. That also has been the situation for this case. The model 
from `this paper <doi.org/10.1016/j.ifacol.2021.08.467>`_ has been modified for this online
model-predictive control setup.
In this section, we do not discuss how to adjust a model suitable for offline control to one for 
online control, but we indicate what you have to do specifically for using *strategoutil* tool to 
perform this online control.

In the UPPAAL Stratego model, we need to insert placeholders at the variables that will have
different values at the start of each MPC step, for example, the water level :math:`w`. These placeholders
are strings with the format ``//TAG_<varname>``, where ``<varname>`` is the name
of the variable. So, for the clock variable :math:`w` representing the water level, we will rewrite

.. code-block::

    clock w = 100; // water level in pond [cm]

into

.. code-block::

    clock w = //TAG_w; // water level in pond [cm]

Notice that after the tag there is still the semicolon ``;``, as only the placeholder will
be replaced by the initial value of that variable. The UPPAAL Stratego GUI will now also start to
give a syntax error on the next line, as it cannot find the closing semicolon.

After inserting all the placeholders in the UPPAAL Stratego model, we have to create a model
configuration file. This file tells the *strategoutil* tool which variables it need to keep track of
during MPC, and what their initial values are for the very first step. The model configuration file
has to be a yaml file, but you can use a custom name. For this case, we have the following
``pond_experiment_config.yaml`` file:

.. code-block:: yaml

    w: 0.0


Finally, we have to specify the learning and other query parameters. This is also done in a separate
yaml-file. Below you can find the content of the ``verifyta_config.yaml`` file for the storm water
pond (with some arbitrarily numbers that ensure fast calculations). In
:ref:`example_pond_experiment_variables` we will indicate in python which files contain the model and
strategy configurations. This file contains pairs of the setting name and its value, where the
setting name is the one used for the command line interface of UPPAAL Stratego. In case a certain
parameter does not have a value, for example ``nosummary``, you just leave the value field empty.

.. code-block:: yaml

    learning-method: 4
    good-runs: 10
    total-runs: 20
    runs-pr-state: 5
    eval-runs: 5
    discretization: 0.5
    filter: 2
    nosummary:
    silence-progress:


-------------------------------------------------------
Specializing the SafeMPCSetup class from *strategoutil*
-------------------------------------------------------

The *strategoutil* tool provides several classes that can be tailored for the case you want to use
it for.

* ``MPCsetup``. This class is the primarily class an end-user should specialize for his or her
  case. It implements the basic MPC scheme as explained in Section~\ref{sect:tooloverview}. It
  assumes that UPPAAL Stratego will always success in synthesizing a safe and optimal strategy.
* ``SafeMPCSetup``. This class inherits from ``MPCsetup``, yet it monitors and detects
  whether UPPAAL Stratego has successfully synthesized a strategy. If not, it will run UPPAAL
  Stratego with an alternative query, which has to be specified by the user, as it depends on the
  model what a safe query would be.

For the storm water detention pond, the primary goal is to synthesize a strategy that ensures no
overflow (safety) while maximizing particle sedimentation (optimality). Nonetheless, it might be
the case that overflow cannot be prevented by any strategy, thus UPPAAL Stratego will fail.
Therefore, the ``SafeMPCSetup`` class should be specialized.

Below the specialized class ``MPCSetupPond`` is defined. As can be seen, we override three
methods for the pond case: ``create_query_file``, ``create_alternative_query_file``,
and ``perform_at_start_iteration``.

.. code-block:: python

    import strategoutil as stompc
    import weather_forecast_generation as weather
    import datetime

    class MPCSetupPond(stompc.SafeMPCSetup):
        def create_query_file(self, horizon, period, final):
            """
            Create the query file for each step of the pond model.
            Current content will be overwritten.

            Overrides SafeMPCsetup.create_query_file().
            """
            with open(self.queryfile, "w") as f:
                line1 = "strategy opt = minE (c) [<={}*{}]: <> (t=={} && o <= 0)\n"
                f.write(line1.format(horizon, period, final))
                f.write("\n")
                line2 = "simulate 1 [<={}+1] {{ {} }} under opt\n"
                f.write(line2.format(period,self.controller.get_var_names_as_string()))

        def create_alternative_query_file(self, horizon, period, final):
            """
            Create an alternative query file in case the original
            query could not be satisfied by Stratego, i.e., it could
            not find a strategy. Current content will be overwritten.

            Overrides SafeMPCsetup.create_alternative_query_file().
            """
            with open(self.queryfile, "w") as f:
                line1 = "strategy opt = minE (w) [<={}*{}]: <> (t=={})\n"
                f.write(line1.format(horizon, period, final))
                f.write("\n")
                line2 = "simulate 1 [<={}+1] {{ {} }} under opt\n"
                f.write(line2.format(period, self.controller.get_var_names_as_string()))

        def perform_at_start_iteration(self, controlperiod, horizon, duration, step, **kwargs):
            """
            Performs some customizable preprocessing steps at the
            start of each MPC iteration.

            Overrides SafeMPCsetup.perform_at_start_iteration().
            """
            current_date = kwargs["start_date"] + datetime.timedelta(hours=step)
            weather.create_weather_forecast(kwargs["historical_rain_data_path"],
                                            kwargs["weather_forecast_path"],
                                            current_date,
                                            horizon * controlperiod,
                                            kwargs["uncertainty"])


In method ``create_query_file`` we specify the strategy synthesis query. For the pond case,
we have this defined with ``line1``. Observe that the python place holders ``{}`` are replaced
by the variables ``horizon``, ``period``, and ``final`` at the next line. It states that
we want to synthesize a strategy that we call ``opt`` that minimizes the expected value of
clock variable :math:`c` (representing the cost in the model) where all runs have a maximum duration of
the number of periods (denoted by ``horizon``) and UPPAAL Stratego time units per period
(denoted by ``period``) such that eventually the time variable :math:`t` reaches its final value and
accumulated overflow duration :math:`o` is zero or less.

Furthermore, we have a simulate query in this method. Only the first period is simulated to obtain
the first control action of the synthesized strategy ``opt``.

The second method ``create_alternative_query_file`` specifies the query in case there is
overflow and UPPAAL Stratego fails to synthesize a safe strategy. We have almost the same strategy
synthesis query, except we removed the requirement that no overflow can occur (:math:`o \leq 0`) and we
want to minimize the water level :math:`w` instead of the cost :math:`c`.

Finally, at the start of each MPC iteration, we need to create a weather forecast. These are
generated from historical rain data and, similarly to real weather forecasts, these change over
time. Therefore, we create new ones each iteration. A separate custom library contains methods to
generate weather forecasts.


.. _example_pond_experiment_variables:

---------------------------
Define experiment variables
---------------------------

We can now define and set all the experiment variables. These include, for example, file paths to
the UPPAAL Stratego and SWMM models.

.. code-block:: python

    import yaml

    if __name__ == "__main__":
        # SWMM files.
        swmm_inputfile = "swmm_simulation.inp"
        rain_data_file = "swmm_5061.dat"

        # Other variables of swimm.
        orifice_id = "OR1"
        basin_id = "SU1"
        time_step = 60 * 60 # duration of SWMM simulation step in seconds.
        swmm_results = "swmm_results_online.csv"

        # Now we specify the Uppaal files.
        model_template_path = "pond_experiment.xml"
        query_file_path = "pond_experiment_query.q"
        model_config_path = "pond_experiment_config.yaml"
        learning_config_path = "verifyta_config.yaml"
        weather_forecast_path = "weather_forecast.csv"
        output_file_path = "stratego_result.txt"
        verifyta_command = "verifyta-stratego-8-7"

        # Define MPC model variables.
        action_variable = "Open"  # Name of the control variable.
        debug = True  # Whether to run in debug mode.
        period = 60  # Control period in Stratego time units (minutes).
        horizon = 12  # How many periods to compute strategy for.
        uncertainty = 0.1  # The uncertainty in the weather forecast generation.


After this we load the two configuration files:

.. code-block:: python

    # Get model and learning config dictionaries from files.
    with open(model_config_path, "r") as yamlfile:
        model_cfg_dict = yaml.safe_load(yamlfile)
    with open(learning_config_path, "r") as yamlfile:
        learning_cfg_dict = yaml.safe_load(yamlfile)


Finally, we can create the MPC object from our ``MPCSetupPond`` class:

.. code-block:: python

    # Construct the MPC object.
    controller = MPCSetupPond(model_template_path, output_file_path, queryfile=query_file_path,
                              model_cfg_dict=model_cfg_dict, learning_args=learning_cfg_dict,
                              verifyta_command=verifyta_command, external_simulator=False,
                              action_variable=action_variable, debug=debug)


-------------------------------------------
Combining strategy synthesis and simulation
-------------------------------------------

Finally, we need to actually define how *strategoutil* should combine UPPAAL Stratego and SWMM
together. Because SWMM is a stateful simulator from which we cannot extract the full state through
the pySWMM API, we cannot use the default ``SafeMPCSetup.run`` method to perform MPC.
Therefore, we will 'pause' the SWMM simulator after each step and let ``SafeMPCSetup`` perform
a single MPC step instead.

The method below will start and run the SWMM simulation, and after each step ask for the next
control setting.

.. code-block:: python

    from pyswmm import Simulation, Nodes, Links
    import csv

    def swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, swmm_results,
                     controller, period, horizon, rain_data_file, weather_forecast_path,
                     uncertainty):
        # Arrays for storing simulation results before writing it to file.
        time_series = []
        water_depth = []
        orifice_settings = []

        with Simulation(swmm_inputfile) as sim:
            # Get the pond and orifice objects from the simulation.
            pond = Nodes(sim)[basin_id]
            orifice = Links(sim)[orifice_id]

            sim.step_advance(time_step)
            current_time = sim.start_time

            # Ask for the first control setting.
            orifice.target_setting = get_control_strategy(pond.depth, current_time, controller,
                                                          period, horizon, rain_data_file,
                                                          weather_forecast_path, uncertainty)

            # Get the initial data points.
            orifice_settings.append(orifice.target_setting)
            time_series.append(sim.start_time)
            water_depth.append(pond.depth)

            for step in sim:
                current_time = sim.current_time
                time_series.append(current_time)
                water_depth.append(pond.depth)

                # Get and set the control parameter for the next period.
                orifice.target_setting = get_control_strategy(pond.depth, current_time,
                                                              controller, period, horizon,
                                                              rain_data_file,
                                                              weather_forecast_path, uncertainty)
                orifice_settings.append(orifice.target_setting)

        # Write results to file.
        with open(swmm_results, "w") as f:
            writer = csv.writer(f)
            for i, j, k in zip(time_series, water_depth, orifice_settings):
                i = i.strftime('%Y-%m-%d %H:%M')
                writer.writerow([i, j, k])

The method ``get_control_strategy`` that gets the next control setting is defined below.
It first updates the state of the controller by updating the value of the water level :math:`w` as
obtained by the SWMM simulation. Subsequently, it performs the ``run_single`` method that
performs a single MPC step. This method returns the control setting for the next period.

.. code-block:: python

    def get_control_strategy(current_water_level, current_time, controller, period, horizon,
                             rain_data_file, weather_forecast_path, uncertainty):
        # The 100 is due to conversion from m to cm.
        controller.controller.update_state({'w':current_water_level * 100})
        control_setting = controller.run_single(period, horizon, start_date=current_time,
                                                historical_rain_data_path=rain_data_file,
                                                weather_forecast_path=weather_forecast_path,
                                                uncertainty=uncertainty)

        return control_setting

Finally, we have to start everything in our ``main`` block. We do this by simply calling
``swmm_control`` with the necessary inputs.

.. code-block:: python

    swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, swmm_results, controller,
                 period, horizon, rain_data_file, weather_forecast_path, uncertainty)


