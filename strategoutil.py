import re
import subprocess
import yaml 

def get_int_tuples(text):
    """converts stratego simulation output to list of tuples
    (int, int)
    """
    string_tuples = re.findall(r"\((\d+),(\d+)\)", text)
    int_tuples = [(int(t[0]), int(t[1])) for t in string_tuples]
    return int_tuples

def get_duration_action(tuples, MAX_TIME=None):
    """get tuples (duration, action) from tuples (time, variable) 
    resulted from simulate quiery 
    """
    result = []
    if len(tuples) == 1: # can only happen if always variable == 0
        result.append((MAX_TIME, 0))
    elif len(tuples) == 2: # can only hapen of always variable != 0
        action = tuples[1][1]
        result.append((MAX_TIME, action))
    else:
        for i in range(1, len(tuples)):
            duration = tuples[i][0] - tuples[i-1][0] 
            action = tuples[i][1]
            if duration > 0:
                result.append((duration, action))

    return result

def insert_to_modelfile(path, tag, inserted):
    """Replaces tag in modelfile by the desired text"""
    with open(path, "r+") as f:
        modeltext = f.read()
        text = modeltext.replace(tag, inserted, 1)
        f.seek(0)
        f.write(text)
        f.truncate()

def array_to_stratego(arr):
    """converts python array string to C style array
    used in UPPAAL Stratego, 
    NB, does not include ';' in the end!
    """
    arrstr = str(arr)
    arrstr = str.replace(arrstr, "[", "{", 1)
    arrstr = str.replace(arrstr, "]", "}", 1)
    return arrstr

def merge_verifyta_args(cfg_dict):
    """Concatenates and formats a string of verifyta
    arguments given by the .yaml configuration file"""
    args = ""
    for k, v in cfg_dict.items():
        args += " --" + k + " " + str(v)
    return args[1:]

def run_stratego(modelfile, queryfile="", learning_args={}, verifyta_path="verifyta"):
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

if __name__ == '__main__':
    pass