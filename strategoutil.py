import re
import subprocess
import shutil
import os


def get_int_tuples(text):
    """
    Convert Stratego simulation output to list of tuples (int, int).
    """
    string_tuples = re.findall(r"\((\d+),(\d+)\)", text)
    int_tuples = [(int(t[0]), int(t[1])) for t in string_tuples]
    return int_tuples


def get_float_tuples(text):
    """
    Convert Stratego simulation output to list of tuples (float, float).
    """
    float_re = r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
    pattern = r"\(" + float_re + "," + float_re + r"\)"
    string_tuples = re.findall(pattern, text)
    float_tuples = [(float(t[0]), float(t[4])) for t in string_tuples]
    return float_tuples


def extract_state(text, var, controlperiod):
    """
    Extract the state from the Uppaal Stratego output at the end of the simulated control period.
    """
    float_re = r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    pattern = var + r":\n\[0\]:( \(" + float_re + "," + float_re + r"\))*"
    result = re.search(pattern, text)
    float_tuples = get_float_tuples(result.group())
    x, y = 0.0, 0.0
    lastvalue = 0.0
    p = 1
    for t in float_tuples:
        while p * controlperiod < t[0]:
            lastvalue = y + (p * controlperiod - x) * (t[1] - y) / (t[0] - x)
            p += 1
        x = t[0]
        y = t[1]
    return lastvalue


def get_duration_action(tuples, max_time=None):
    """
    Get tuples (duration, action) from tuples (time, variable) resulted from simulate query.
    """
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
    """
    with open(model_file, "r+") as f:
        modeltext = f.read()
        text = modeltext.replace(tag, inserted, 1)
        f.seek(0)
        f.write(text)
        f.truncate()


def array_to_stratego(arr):
    """
    Convert python array string to C style array used in UPPAAL Stratego.
    NB, does not include ';' in the end.
    """
    arrstr = str(arr)
    arrstr = str.replace(arrstr, "[", "{", 1)
    arrstr = str.replace(arrstr, "]", "}", 1)
    return arrstr


def merge_verifyta_args(cfg_dict):
    """
    Concatenate and format a string of verifyta arguments given by the configuration dictionary.
    """
    args = ""
    for k, v in cfg_dict.items():
        if v is not None:
            args += " --" + k + " " + str(v)
        else:
            args += " --" + k
    return args[1:]


def run_stratego(modelfile, queryfile="", learning_args=None, verifyta_path="verifyta",
                 interactive_bash=True):
    """
    Usage: verifyta.bin [OPTION]... MODEL QUERY
    modelfile .xml
    query .q
    learning_args with entries of the same format as verifyta arguments
    """
    learning_args = {} if learning_args is None else learning_args
    args = {
        "verifyta": verifyta_path,
        "model": modelfile,
        "query": queryfile,
        "config": merge_verifyta_args(learning_args)
    }
    args_list = [v for v in args.values() if v != ""]
    task = " ".join(args_list)

    if interactive_bash:
        # This version of the call ensures that the bash shell is started in interactive mode,
        # thus using any aliases and path variable extensions defined in the user's .bashrc file.
        process = subprocess.Popen(['/bin/bash', '-i', '-c', task],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        # This version of the call runs Uppaal Stratego using the Popen default shell.
        process = subprocess.Popen(task, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    result = process.communicate()
    result = [r.decode("utf-8") for r in result]
    return result


def successful_result(text):
    """
    Verify whether the stratego output is based on the successful synthesis of a strategy.
    """
    result = re.search("Formula is satisfied", text)
    return result is not None


class StrategoController:
    """
    Controller class to interface with UPPAAL Stratego through python.
    """

    def __init__(self, modeltemplatefile, model_cfg_dict, cleanup=True, interactive_bash=True):
        self.templatefile = modeltemplatefile
        self.simulationfile = modeltemplatefile.replace(".xml", "_sim.xml")
        self.cleanup = cleanup
        self.states = model_cfg_dict
        self.interactive_bash = interactive_bash
        self.tagRule = "//TAG_{}"

    def init_simfile(self):
        """
        Make a copy of a template file where data of specific variables is inserted.
        """
        shutil.copyfile(self.templatefile, self.simulationfile)

    def remove_simfile(self):
        """
        Clean created temporary files after the simulation is finished.
        """
        os.remove(self.simulationfile)

    def debug_copy(self, debug_file):
        """
        Copy UPPAAL simulationfile.xml file for manual debug in Stratego.
        """
        shutil.copyfile(self.simulationfile, debug_file)

    def update_state(self, new_values):
        """
        Update the state of the MPC controller.
        """
        for name, value in new_values.items():
            self.states.update({name: value})

    def insert_state(self):
        """
        Insert the current state values of the variables at the appropriate position in the
        simulation *.xml file indicated by the tag rule.
        """
        for name, value in self.states.items():
            tag = self.tagRule.format(name)
            insert_to_modelfile(self.simulationfile, tag, str(value))

    def print_var_names(self):
        """
        Print the names of the state variables separated by a ','.
        """
        separator = ","
        return separator.join(self.states.keys())

    def print_state(self):
        """
        Print the values of the state variables separated by a ','.
        """
        separator = ","
        values_as_string = [str(val) for val in self.states.values()]
        return separator.join(values_as_string)

    def get_state(self, key):
        """
        Get the current value of the provided state.
        """
        return self.states.get(key)

    def get_states(self):
        """
        Get the state variable names.
        """
        return self.states

    def run(self, queryfile="", learning_args=None, verifyta_path="verifyta"):
        """
        Runs verifyta with requested queries and parameters that are either part of the *.xml model
        file or explicitly specified.
        """
        learning_args = {} if learning_args is None else learning_args
        output = run_stratego(self.simulationfile, queryfile,
                              learning_args, verifyta_path, self.interactive_bash)
        return output[0]


class MPCsetup:
    """
    Class that performs the basic MPC scheme for Uppaal Stratego.
    """

    def __init__(self, modeltemplatefile, queryfile="", model_cfg_dict=None, learning_args=None,
                 verifytacommand="verifyta", debug=False, interactive_bash=True):
        self.modeltemplatefile = modeltemplatefile
        self.queryfile = queryfile
        self.model_cfg_dict = {} if model_cfg_dict is None else model_cfg_dict
        self.learning_args = {} if learning_args is None else learning_args
        self.verifytacommand = verifytacommand
        self.debug = debug
        self.controller = StrategoController(self.modeltemplatefile, self.model_cfg_dict,
                                             interactive_bash=interactive_bash)

    def run(self, controlperiod, horizon, duration, **kwargs):
        """
        Run the basic MPC scheme where the controller can changes its strategy once every period,
        where the strategy synthesis looks the horizon ahead, and continues for the duration of the
        experiment.

        The control period is in Uppaal Stratego time units. Both horizon and duration have control
        period as time unit.
        """
        # Print the variable names and their initial values.
        print(self.controller.print_var_names())
        print(self.controller.print_state())

        for step in range(duration):
            # Perform some customizable preprocessing at each step.
            self.perform_at_start_iteration(controlperiod, horizon, duration, step, **kwargs)

            # At each MPC step we want a clean template copy to insert variables.
            self.controller.init_simfile()

            # Insert current state into simulation template.
            self.controller.insert_state()

            # To debug errors from verifyta one can save intermediate simulation file.
            if self.debug:
                self.controller.debug_copy(self.modeltemplatefile.replace(".xml", "_debug.xml"))

            # Create the new query file for the next step.
            final = horizon * controlperiod + self.controller.get_state("t")
            self.create_query_file(horizon, controlperiod, final)

            # Run a verifyta query to simulate optimal strategy.
            result = self.run_verifyta(horizon, controlperiod, final)

            # Extract the state from the result.
            self.extract_states_from_Stratego(result, controlperiod)

            # Print output.
            print(self.controller.print_state())

    def perform_at_start_iteration(self, *args, **kwargs):
        """
        Performs some customizable preprocessing steps at the start of each MPC iteration. This
        method can be overritten for specific models.
        """
        pass

    def create_query_file(self, horizon, period, final):
        """
        Create a basic query file for each step of the MPC scheme. Current content will be
        overwritten.

        You might want to override this method for specific models.
        """
        with open(self.queryfile, "w") as f:
            line1 = "strategy opt = minE (c) [<={}*{}]: <> (t=={})\n"
            f.write(line1.format(horizon, period, final))
            f.write("\n")
            line2 = "simulate 1 [<={}+1] {{ {} }} under opt\n"
            f.write(line2.format(period, self.controller.print_var_names()))

    def run_verifyta(self, *args, **kwargs):
        """
        Run verifyta with the current data stored in this class.
        """
        result = self.controller.run(queryfile=self.queryfile, learning_args=self.learning_args,
                                   verifyta_path=self.verifytacommand)

        if self.controller.cleanup:
            self.controller.remove_simfile()
        return result

    def extract_states_from_Stratego(self, result, controlperiod):
        """
        Extract the new state values from the simulation output of Stratego.
        """
        new_state = {}
        for var, value in self.controller.get_states().items():
            new_value = extract_state(result, var, controlperiod)
            if isinstance(value, int):
                new_value = int(new_value)
            new_state[var] = new_value
        self.controller.update_state(new_state)

class SafeMPCSetup(MPCsetup):
    def run_verifyta(self, horizon, controlperiod, final, *args, **kwargs):
        """
        Run verifyta with the current data stored in this class. It verifies whether Stratego has
        successfully synthesized a strategy. If not, it will create an alternative query file and
        run Stratego again.

        Overrides MPCsetup.run_verifyta()
        """
        result = self.controller.run(queryfile=self.queryfile, learning_args=self.learning_args,
                                     verifyta_path=self.verifytacommand)

        if not successful_result(result):
            self.create_alternative_query_file(horizon, controlperiod, final)
            result = self.controller.run(queryfile=self.queryfile, learning_args=self.learning_args,
                                verifyta_path=self.verifytacommand)

        if self.controller.cleanup:
            self.controller.remove_simfile()
        return result

    def create_alternative_query_file(self, horizon, period, final) -> str:
        """
        Create an alternative query file in case the original query could not be satisfied by
        Stratego, i.e., it could not find a strategy.
        """
        pass


if __name__ == '__main__':
    pass
