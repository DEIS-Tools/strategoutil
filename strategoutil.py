import re
import subprocess
import shutil
import os
import yaml 


def get_int_tuples(text):
    """
    Convert Stratego simulation output to list of tuples
    (int, int).
    """
    string_tuples = re.findall(r"\((\d+),(\d+)\)", text)
    int_tuples = [(int(t[0]), int(t[1])) for t in string_tuples]
    return int_tuples


def get_initial_states(model_config_file):
    """
    Get the names of the variables that will be replaced each
    step with updated values and their initial states from the
    supplied configuration file.
    """
    result = {}
    with open(model_config_file, "r") as yamlfile:
        cfg = yaml.safe_load(yamlfile)
        for k, v in cfg.items():
            result.update({k: v})
    return result


def get_duration_action(tuples, MAX_TIME=None):
    """
    Get tuples (duration, action) from tuples (time, variable)
    resulted from simulate query.
    """
    result = []
    if len(tuples) == 1: # Can only happen if always variable == 0.
        result.append((MAX_TIME, 0))
    elif len(tuples) == 2: # Can only happen of always variable != 0.
        action = tuples[1][1]
        result.append((MAX_TIME, action))
    else:
        for i in range(1, len(tuples)):
            duration = tuples[i][0] - tuples[i-1][0] 
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
    Convert python array string to C style array
    used in UPPAAL Stratego.
    NB, does not include ';' in the end.
    """
    arrstr = str(arr)
    arrstr = str.replace(arrstr, "[", "{", 1)
    arrstr = str.replace(arrstr, "]", "}", 1)
    return arrstr


def merge_verifyta_args(cfg_dict):
    """
    Concatenate and format a string of verifyta
    arguments given by the .yaml configuration file.
    """
    args = ""
    for k, v in cfg_dict.items():
        args += " --" + k + " " + str(v)
    return args[1:]


def run_stratego(
    modelfile, 
    queryfile="", 
    learning_args={}, 
    verifyta_path="verifyta"):
    """
    Usage: verifyta.bin [OPTION]... MODEL QUERY
    modelfile .xml
    query .q
    configfile .yaml with entries of the same format as verifyta arguments
    """
    args = {
        "verifyta": verifyta_path,
        "model": modelfile,
        "query": queryfile,
        "config": merge_verifyta_args(learning_args)
    }
    args_list = [v for v in args.values() if v != ""]
    task = " ".join(args_list)

    process = subprocess.Popen(task, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = process.communicate()
    result = [r.decode("utf-8") for r in result]
    return result


class StrategoController:
    """
    Controller class to interface with UPPAAL Stratego
    through python.
    """
    def __init__(self, modeltemplatefile, modelconfigfile, cleanup=True):
        self.templatefile = modeltemplatefile
        self.simulationfile = modeltemplatefile.replace(".xml", "_sim.xml")
        self.cleanup = cleanup
        self.states = get_initial_states(modelconfigfile)
        self.tagRule = "//TAG_{}"

    def init_simfile(self):
        """
        Make a copy of a template file where data of
        specific variables is inserted.
        """
        shutil.copyfile(self.templatefile, self.simulationfile)

    def remove_simfile(self):
        """
        Clean created temporary files after the simulation is finished.
        """
        os.remove(self.simulationfile)       

    def debug_copy(self, debug_file):
        """
        Copy UPPAAL simulationfile.xml file for manual
        debug in Stratego.
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
        Insert the current state values of the variables at the
        appropriate position in the simulation *.xml file indicated
        by the tag rule.
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

    def run(self, 
        queryfile="", 
        learning_args={}, 
        verifyta_path="verifyta"):
        """
        Runs verifyta with requested queries and parameters
        that are either part of the *.xml model file or explicitly
        specified.
        """
        output = run_stratego(self.simulationfile, queryfile,
            learning_args, verifyta_path)
        if self.cleanup:
            self.remove_simfile()
        return output[0]


if __name__ == '__main__':
    pass
