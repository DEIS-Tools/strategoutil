import re
import subprocess
import shutil
import os
import sys


def get_int_tuples(text):
    """
    Convert Stratego simulation output to list of tuples (int, int).

    :param text: The input string containing the Uppaal Stratego output.
    :type text: str
    :return: A list of tuples (int, int).
    :rtype: list
    """
    string_tuples = re.findall(r"\((\d+),(\d+)\)", text)
    if string_tuples is None:
        raise RuntimeError(
            "Output of Stratego has not the expected format of a list of tuples. Please check the "
            "output manually for error messages: \n" + text)
    int_tuples = [(int(t[0]), int(t[1])) for t in string_tuples]
    return int_tuples


def get_float_tuples(text):
    """
    Convert Stratego simulation output to list of tuples (float, float).

    :param text: The input string containing the Uppaal Stratego output.
    :type text: str
    :return: A list of tuples (float, float).
    :rtype: list
    """
    float_re = r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
    pattern = r"\(" + float_re + "," + float_re + r"\)"
    string_tuples = re.findall(pattern, text)
    if string_tuples is None:
        raise RuntimeError(
            "Output of Stratego has not the expected format of a list of tuples. Please check the "
            "output manually for error messages: \n" + text)
    float_tuples = [(float(t[0]), float(t[4])) for t in string_tuples]
    return float_tuples


def extract_state(text, var, control_period):
    """
    Extract the state from the Uppaal Stratego output at the end of the simulated control period.

    :param text: The input string containing the Uppaal Stratego output.
    :type text: str
    :param var: The variable name.
    :type var: str
    :param control_period: The interval duration after which the controller can change the control
        setting, given in Uppaal Stratego time units.
    :type control_period: int
    :return: The value of the variable at the end of *control_period*.
    :rtype: float
    """
    float_re = r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    pattern = var + r":\n\[0\]:( \(" + float_re + "," + float_re + r"\))*"
    result = re.search(pattern, text)
    if result is None:
        raise RuntimeError(
            "Output of Stratego has not the expected format. Please check the output manually for "
            "error messages: \n" + text)
    float_tuples = get_float_tuples(result.group())
    x, y = 0.0, 0.0
    last_value = 0.0
    p = 1
    for t in float_tuples:
        while p * control_period < t[0]:
            last_value = y + (p * control_period - x) * (t[1] - y) / (t[0] - x)
            p += 1
        x = t[0]
        y = t[1]
    return last_value


def get_duration_action(tuples, max_time=None):
    """
    Get tuples (duration, action) from tuples (time, variable) resulted from simulate query.
    """
    # TODO: This method is currently not used in any of the classes. Can we safely remove this?
    result = []
    if len(tuples) == 1:  # Can only happen if always variable == 0.
        result.append((max_time, 0))
    elif len(tuples) == 2:  # Can only happen of always variable != 0.
        action = tuples[1][1]
        result.append((max_time, action))
    else:
        for i in range(1, len(tuples)):
            duration = tuples[i][0] - tuples[i - 1][0]
            action = tuples[i][1]
            if duration > 0:
                result.append((duration, action))

    return result


def insert_to_modelfile(model_file, tag, inserted):
    """
    Replace tag in model file by the desired text.

    :param model_file: The file name of the model.
    :type model_file: str
    :param tag: The tag to replace.
    :type tag: str
    :param inserted: The value to replace the tag with.
    :type inserted: str
    """
    with open(model_file, "r+") as f:
        model_text = f.read()
        text = model_text.replace(tag, inserted, 1)
        f.seek(0)
        f.write(text)
        f.truncate()


def array_to_stratego(arr):
    """
    Convert python array string to C style array used in UPPAAL Stratego.
    NB, does not include ';' in the end.

    :param arr: The array string to convert.
    :type arr: str
    :return: An array string where ``"["`` and ``"]"`` are replaced by ``"{"`` and ``"}"``,
        respectively.
    :rtype: str
    """
    arrstr = str(arr)
    arrstr = str.replace(arrstr, "[", "{", 1)
    arrstr = str.replace(arrstr, "]", "}", 1)
    return arrstr


def merge_verifyta_args(cfg_dict):
    """
    Concatenate and format a string of verifyta arguments given by the configuration dictionary.

    :param cfg_dict: The configuration dictionary.
    :type cfg_dict: dict
    :return: String containing all arguments from the configuration dictionary.
    :rtype: str
    """
    args = ""
    for k, v in cfg_dict.items():
        if v is not None:
            args += " --" + k + " " + str(v)
        else:
            args += " --" + k
    return args[1:]


def check_tool_existence(name):
    """
    Check whether 'name' is on PATH and marked executable.

    From `<https://stackoverflow.com/questions/11210104/check-if-a-program-exists-from-a-python-script>`_.

    :param name: the name of the tool.
    :type name: str
    :return: True when the tool is found and executable, false otherwise.
    :rtype: bool
    """
    return shutil.which(name) is not None


def run_stratego(model_file, query_file="", learning_args=None, verifyta_command="verifyta"):
    """
    Run command line version of Uppaal Stratego.

    :param model_file: The file name of the model.
    :type model_file: str
    :param query_file: The file name of the query.
    :type query_file: str
    :param learning_args: Dictionary containing the learning parameters and their values. The
        learning parameter names should be those used in the command line interface of Uppaal
        Stratego. You can also include non-learning command line parameters in this dictionary.
        If a non-learning command line parameter does not take any value, include the empty
        string ``""`` as value.
    :type learning_args: dict
    :param verifyta_command: The command name for running Uppaal Stratego at the user's machine.
    :type verifyta_command: str
    :return: The output as produced by Uppaal Stratego.
    :rtype: str
    """
    learning_args = {} if learning_args is None else learning_args
    args = {
        "verifyta": verifyta_command,
        "model": model_file,
        "query": query_file,
        "config": merge_verifyta_args(learning_args)
    }
    args_list = [v for v in args.values() if v != ""]
    task = " ".join(args_list)

    process = subprocess.Popen(task, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = process.communicate()
    result = [r.decode("utf-8") for r in result]

    # Throw error if stderr is nonempty.
    if len(result[1]) > 0:
        raise RuntimeError("Uppaal finished with the following error message:\n" + result[1])
    return result


def successful_result(text):
    """
    Verify whether the stratego output is based on the successful synthesis of a strategy.

    :param text: The output generated by Uppaal Stratego.
    :type text: str
    :return: Whether Uppaal Stratego has successfuly ran all queries.
    :rtype: bool
    """
    result = re.search("Formula is satisfied", text)
    return result is not None


def print_progress_bar(i, max, post_text):
    """
    Print a progress bar to sys.stdout.

    Subsequent calls will override the previous progress bar (given that nothing else has been
    written to sys.stdout).

    From `<https://stackoverflow.com/a/58602365>`_.

    :param i: The number of steps already completed.
    :type i: int
    :param max: The maximum number of steps for process to be completed.
    :type max: int
    :param post_text: The text to display after the progress bar.
    :type post_text: str
    """
    n_bar = 20  # Size of progress bar.
    j = i / max
    sys.stdout.write('\r')
    sys.stdout.write(f"[{'=' * int(n_bar * j):{n_bar}s}] {int(100 * j)}%  {post_text}")
    sys.stdout.flush()


class StrategoController:
    """
    Controller class to interface with UPPAAL Stratego through python.

    :param model_template_file: The file name of the template model.
    :type model_template_file: str
    :param model_cfg_dict: Dictionary containing pairs of state variable name and its initial
        value. The state variable name should match the tag name in the template model.
    :type model_cfg_dict: dict
    :param cleanup: Whether or not to clean up the temporarily simulation file after being used.
    :type cleanup: bool
    :ivar states: Dictionary containing the current state of the system, where a state is a pair of
        variable name and value. It is initialized with the values from *model_cfg_dict*.
    :vartype states: bool
    :ivar tagRule: The rule for each tag in the template model. Currently, the rul is set to be
        ``"//TAG_{}"``. Therefore, tags in the template model should be ``"//TAG_<variable name>"``,
        where ``<variable name>`` is the global name of the variable.
    :vartype tagRule: str
    """

    def __init__(self, model_template_file, model_cfg_dict, cleanup=True):
        self.template_file = model_template_file
        self.simulation_file = model_template_file.replace(".xml", "_sim.xml")
        self.cleanup = cleanup  # TODO: this variable seems to be not used. Can it be safely removed?
        self.states = model_cfg_dict.copy()
        self.tagRule = "//TAG_{}"

    def init_simfile(self):
        """
        Make a copy of a template file where data of specific variables is inserted.
        """
        shutil.copyfile(self.template_file, self.simulation_file)

    def remove_simfile(self):
        """
        Clean created temporary files after the simulation is finished.
        """
        os.remove(self.simulation_file)

    def debug_copy(self, debug_file):
        """
        Copy UPPAAL simulationfile.xml file for manual debug in Stratego.

        :param debug_file: The file name of the debug file.
        :type debug_file: str
        """
        shutil.copyfile(self.simulation_file, debug_file)

    def update_state(self, new_values):
        """
        Update the state of the MPC controller.

        :param new_values: Dictionary containing new values for the state variables.
        :type new_values: dict
        """
        for name, value in new_values.items():
            self.states.update({name: value})

    def insert_state(self):
        """
        Insert the current state values of the variables at the appropriate position in the
        simulation \*.xml file indicated by the :py:attr:`tagRule`.
        """
        for name, value in self.states.items():
            tag = self.tagRule.format(name)
            insert_to_modelfile(self.simulation_file, tag, str(value))

    def get_var_names_as_string(self):
        """
        Print the names of the state variables separated by a ','.

        :return: All the variable names joined together with a ','.
        :rtype: str
        """
        separator = ","
        return separator.join(self.states.keys())

    def get_state_as_string(self):
        """
        Print the values of the state variables separated by a ','.

        :return: All the variable values joined together with a ','.
        :rtype: str
        """
        separator = ","
        values_as_string = [str(val) for val in self.states.values()]
        return separator.join(values_as_string)

    def get_state(self, key):
        """
        Get the current value of the provided state variable.

        :param key: The state variable name.
        :type key: str
        :return: The currently stored value of the state variable.
        :rtype: int or float
        """
        return self.states.get(key)

    def get_states(self):
        """
        Get the current states.

        :return: The current state dictionary.
        :rtype: dict
        """
        return self.states

    def run(self, query_file="", learning_args=None, verifyta_command="verifyta"):
        """
        Runs verifyta with requested queries and parameters that are either part of the \*.xml model
        file or explicitly specified.

        :param query_file: The file name of the query file where the queries are written to.
        :type query_file: str
        :param learning_args: Dictionary containing the learning parameters and their values. The
            learning parameter names should be those used in the command line interface of Uppaal
            Stratego. You can also include non-learning command line parameters in this dictionary.
            If a non-learning command line parameter does not take any value, include the empty
            string ``""`` as value.
        :type learning_args: dict
        :param verifyta_command: The command name for running Uppaal Stratego at the user's machine.
        :type verifyta_command: str
        :return: The output generated by Uppaal Stratego.
        :rtype: str
        """
        learning_args = {} if learning_args is None else learning_args
        output = run_stratego(self.simulation_file, query_file, learning_args, verifyta_command)
        return output[0]


class MPCsetup:
    """
    Class that performs the basic MPC scheme for Uppaal Stratego.

    The class parameters are also available as attributes.

    :param model_template_file: The file name of the template model.
    :type model_template_file: str
    :param output_file_path: The file name of the output file where the results are printed to.
    :type output_file_path: str
    :param query_file: The file name of the query file where the queries are written to.
    :type query_file: str
    :param model_cfg_dict: Dictionary containing pairs of state variable name and its initial
        value. The state variable name should match the tag name in the template model.
    :type model_cfg_dict: dict
    :param learning_args: Dictionary containing the learning parameters and their values. The
        learning parameter names should be those used in the command line interface of Uppaal
        Stratego. You can also include non-learning command line parameters in this dictionary. If
        a non-learning command line parameter does not take any value, include the empty string
        ``""`` as value.
    :type learning_args: dict
    :param verifyta_command: The command name for running Uppaal Stratego at the user's machine.
    :type verifyta_command: str
    :param external_simulator: Whether an external simulator is used to obtain the true state after
        applying the synthesized control strategy for a single control period.
    :type external_simulator: bool
    :param action_variable: Name of the variable in the model that captures the control actions to
        choose from. Only relevant if an external simulator is used, as we need to get the chosen
        control action from Uppaal Stratego and pass it on to the external simulator. It should be
        a variable in *model_cfg_dict*.
    :type action_variable: str
    :param debug: Whether or not to run in debug mode.
    :type debug: bool
    :ivar controller: The controller object used for interacting with Uppaal Stratego.
    :vartype controller: :class:`~StrategoController`
    """

    def __init__(self, model_template_file, output_file_path=None, query_file="",
                 model_cfg_dict=None, learning_args=None, verifyta_command="verifyta",
                 external_simulator=False, action_variable=None, debug=False):
        self.model_template_file = model_template_file
        self.output_file_path = output_file_path
        self.query_file = query_file
        self.model_cfg_dict = {} if model_cfg_dict is None else model_cfg_dict
        self.learning_args = {} if learning_args is None else learning_args
        self.verifyta_command = verifyta_command
        self.external_simulator = external_simulator
        if external_simulator and action_variable not in model_cfg_dict.keys():
            raise RuntimeError(
                f"The provided action variable {action_variable} is not defined as a model variable"
                f"in the model configuration.")
        self.action_variable = action_variable
        self.debug = debug
        self.controller = StrategoController(self.model_template_file, self.model_cfg_dict)

    def step_without_sim(self, control_period, horizon, duration, step, **kwargs):
        """
        Perform a step in the basic MPC scheme without the simulation of the synthesized strategy.

        :param control_period: The interval duration after which the controller can change the
            control setting, given in Uppaal Stratego time units.
        :type control_period: int
        :param horizon: The interval duration for which Uppaal stratego synthesizes a control strategy
            each MPC step. Is given in the number of control periods.
        :type horizon: int
        :param duration: The number of times (steps) the MPC scheme should be performed, given as
            the number of control periods. Is only forwarded to
            :meth:`~MPCsetup.perform_at_start_iteration`.
        :type duration: int
        :param step: The current iteration step in the basic MPC loop.
        :type step: int
        :param kwargs: Any additional parameters are forwarded to
            :meth:`~MPCsetup.perform_at_start_iteration`.
        :return: The output generated by Uppaal Stratego.
        :rtype: str
        """
        # Perform some customizable preprocessing at each step.
        self.perform_at_start_iteration(control_period, horizon, duration, step, **kwargs)

        # At each MPC step we want a clean template copy to insert variables.
        self.controller.init_simfile()

        # Insert current state into simulation template.
        self.controller.insert_state()

        # To debug errors from verifyta one can save intermediate simulation file.
        if self.debug:
            self.controller.debug_copy(self.model_template_file.replace(".xml", "_debug.xml"))

        # Create the new query file for the next step.
        final = horizon * control_period + self.controller.get_state("t")
        self.create_query_file(horizon, control_period, final)

        # Run a verifyta query to simulate optimal strategy.
        result = self.run_verifyta(horizon, control_period, final)

        return result

    def run_single(self, control_period, horizon, **kwargs):
        """
        Run the basic MPC scheme a single step where a single controller strategy is calculated,
        where the strategy synthesis looks the horizon ahead, and continues for the duration of the
        experiment.

        The control period is in Uppaal Stratego time units. Horizon have control period as time
        unit.

        :param control_period: The interval duration after which the controller can change the
            control setting, given in Uppaal Stratego time units.
        :type control_period: int
        :param horizon: The interval duration for which Uppaal stratego synthesizes a control strategy
            each MPC step. Is given in the number of control periods.
        :type horizon: int
        :param `**kwargs`: Any additional parameters are forwarded to
            :meth:`~MPCsetup.perform_at_start_iteration`.
        :return: The control action chosen for the first control period.
        """
        if not check_tool_existence(self.verifyta_command):
            raise RuntimeError(
                f"Cannot find the supplied verifyta command: {self.verifyta_command}")

        result = self.step_without_sim(control_period, horizon, 1, 0, **kwargs)
        chosen_action = self.extract_control_action_from_stratego(result)

        return chosen_action

    def run(self, control_period, horizon, duration, **kwargs):
        """
        Run the basic MPC scheme where the controller can changes its strategy once every period,
        where the strategy synthesis looks the horizon ahead, and continues for the duration of the
        experiment.

        The control period is in Uppaal Stratego time units. Both horizon and duration have control
        period as time unit.

        :param control_period: The interval duration after which the controller can change the
            control setting, given in Uppaal Stratego time units.
        :type control_period: int
        :param horizon: The interval duration for which Uppaal stratego synthesizes a control strategy
            each MPC step. Is given in the number of control periods.
        :type horizon: int
        :param duration: The number of times (steps) the MPC scheme should be performed, given as
            the number of control periods.
        :type duration: int
        :param `**kwargs`: Any additional parameters are forwarded to
            :meth:`~MPCsetup.perform_at_start_iteration`.
        """
        # Print the variable names and their initial values.
        self.print_state_vars()
        self.print_state()

        if not check_tool_existence(self.verifyta_command):
            raise RuntimeError(
                f"Cannot find the supplied verifyta command: {self.verifyta_command}")

        for step in range(duration):
            # Only print progress to stdout if results are printed to a file.
            if self.output_file_path:
                print_progress_bar(step, duration, "progress")

            result = self.step_without_sim(control_period, horizon, duration, step, **kwargs)

            if self.external_simulator:
                # An external simulator is used to generate the new 'true' state.
                chosen_action = self.extract_control_action_from_stratego(result)
                new_state = self.run_external_simulator(chosen_action, control_period, step,
                                                        **kwargs)
                self.controller.update_state(new_state)

            else:
                # Extract the state from Uppaal results. This requires that the query file also
                # includes a simulate query (see default query generator).
                self.extract_states_from_stratego(result, control_period)

            # Print output.
            self.print_state()
        if self.output_file_path:
            print_progress_bar(duration, duration, "finished")

    def perform_at_start_iteration(self, *args, **kwargs):
        """
        Perform some customizable preprocessing steps at the start of each MPC iteration. This
        method can be overwritten for specific models.
        """
        pass

    def create_query_file(self, horizon, period, final):
        """
        Create a basic query file for each step of the MPC scheme. Current content will be
        overwritten.

        You might want to override this method for specific models.

        :param horizon: The interval duration for which Uppaal stratego synthesizes a control strategy
            each MPC step. Is given in the number of periods.
        :type horizon: int
        :param period: The interval duration after which the controller can change the control
            setting, given in Uppaal Stratego time units.
        :type period: int
        :param final: The time that should be reached by the synthesized strategy, given in Uppaal
            Stratego time units. Most likely this will be current time + *horizon* x *period*.
        :type final: int
        """
        with open(self.query_file, "w") as f:
            line1 = "strategy opt = minE (c) [<={}*{}]: <> (t=={})\n"
            f.write(line1.format(horizon, period, final))
            f.write("\n")
            line2 = "simulate 1 [<={}+1] {{ {} }} under opt\n"
            f.write(line2.format(period, self.controller.get_var_names_as_string()))

    def run_verifyta(self, *args, **kwargs):
        """
        Run verifyta with the current data stored in this class.

        :param `*args`: Is not used in this method; it is used in the overriding method
            :meth:`~SafeMPCSetup.run_verifyta` in :class:`~SafeMPCSetup`.
        :param `**kwargs`: Is not used in this method; it is used in the overriding method
            :meth:`~SafeMPCSetup.run_verifyta` in :class:`~SafeMPCSetup`.
        :return: The output generated by Uppaal Stratego.
        :rtype: str
        """
        result = self.controller.run(query_file=self.query_file, learning_args=self.learning_args,
                                     verifyta_command=self.verifyta_command)

        if self.controller.cleanup:
            self.controller.remove_simfile()
        return result

    def extract_states_from_stratego(self, result, control_period):
        """
        Extract the new state values from the simulation output of Stratego.

        The extracted values are directly saved in the :attr:`~MPCsetup.controller`.

        :param result: The output as generated by Uppaal Stratego.
        :type result: str
        :param control_period: The interval duration after which the controller can change the
            control setting, given in Uppaal Stratego time units.
        :type control_period: int
        """
        new_state = {}
        for var, value in self.controller.get_states().items():
            new_value = extract_state(result, var, control_period)
            if isinstance(value, int):
                new_value = int(new_value)
            new_state[var] = new_value
        self.controller.update_state(new_state)

    def extract_control_action_from_stratego(self, stratego_output):
        """
        Extract the chosen control action for the first control period from the simulation output
        of Stratego.

        :param stratego_output: The output as generated by Uppaal Stratego.
        :type stratego_output: str
        :return: The control action chosen for the first control period.
        :rtype: float
        """
        float_re = r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
        pattern = self.action_variable + r":\n\[0\]:( \(" + float_re + "," + float_re + r"\))*"
        result = re.search(pattern, stratego_output)
        if result is None:
            raise RuntimeError(
                "Output of Stratego has not the expected format. Please check the output manually "
                "for error messages: \n" + stratego_output)
        float_tuples = get_float_tuples(result.group())
        last_value = 0.0

        # The last tuple at time 0 represents the chosen control action.
        for t in float_tuples:
            if t[0] == 0:
                last_value = t[1]
            else:
                break
        return last_value

    def run_external_simulator(self, chosen_action, *args, **kwargs):
        """
        Run an external simulator to obtain the 'true' state after applying the synthesized control
        action for a single control period.

        This method should be overridden by the user. The method should return the new 'true' state
        as a dictionary containing pairs where the key is a variable name and the value is its new
        value.

        :param chosen_action: The synthesized control action for the first control period.
        :type chosen_action: int or float
        :return: The 'true' state of the system after simulation a single control period. The
            dictionary containings pairs of state variable name and their values. The state variable
            name should match the tag name in the template model.
        :rtype: dict
        """
        return {}

    def print_state_vars(self):
        """
        Print the names of the state variables to output file if provided. Otherwise, it will be
        printed to the standard output.
        """
        content = self.controller.get_var_names_as_string() + "\n"
        if self.output_file_path is None:
            sys.stdout.write(content)
        else:
            with open(self.output_file_path, "w") as f:
                f.write(content)

    def print_state(self):
        """
        Print the current state to output file if provided. Otherwise, it will be printed to the
        standard output.
        """
        content = self.controller.get_state_as_string() + "\n"
        if self.output_file_path is None:
            sys.stdout.write(content)
        else:
            with open(self.output_file_path, "a") as f:
                f.write(content)


class SafeMPCSetup(MPCsetup):
    """
    Class that performs the basic MPC scheme for Uppaal Stratego.

    The class monitors and detects whether Uppaal Stratego has sucessfully synthesized a strategy.
    If not, it will run Uppaal Stratego with an alternative query, which has to be specified by
    the user, as it depends on the model what a safe query would be.
    """

    def run_verifyta(self, horizon, control_period, final, *args, **kwargs):
        """
        Run verifyta with the current data stored in this class.

        It verifies whether Stratego has successfully synthesized a strategy. If not, it will create
        an alternative query file and run Stratego again.

        Overrides :meth:`~MPCsetup.run_verifyta()` in :class:`~MPCsetup`.

        :param horizon: The interval duration for which Uppaal stratego synthesizes a control strategy
            each MPC step. Is given in the number of periods.
        :type horizon: int
        :param control_period: The interval duration after which the controller can change the
            control setting, given in Uppaal Stratego time units.
        :type control_period: int
        :param final: The time that should be reached by the synthesized strategy, given in Uppaal
            Stratego time units. Most likely this will be current time + *horizon* x *period*.
        :type final: int
        :param `*args`: Is not used in this method; it is included here to safely override the
            original method.
        :param `**kwargs`: Is not used in this method; it is included here to safely override the
            original method.
        """
        result = self.controller.run(query_file=self.query_file, learning_args=self.learning_args,
                                     verifyta_command=self.verifyta_command)

        if not successful_result(result):
            self.create_alternative_query_file(horizon, control_period, final)
            result = self.controller.run(query_file=self.query_file, learning_args=self.learning_args,
                                         verifyta_command=self.verifyta_command)

        if self.controller.cleanup:
            self.controller.remove_simfile()
        return result

    def create_alternative_query_file(self, horizon, period, final):
        """
        Create an alternative query file in case the original query could not be satisfied by
        Stratego, i.e., it could not find a strategy.

        :param horizon: The interval duration for which Uppaal stratego synthesizes a control strategy
            each MPC step. Is given in the number of periods.
        :type horizon: int
        :param period: The interval duration after which the controller can change the control
            setting, given in Uppaal Stratego time units.
        :type period: int
        :param final: The time that should be reached by the synthesized strategy, given in Uppaal
            Stratego time units. Most likely this will be current time + *horizon* x *period*.
        :type final: int
        """
        pass
