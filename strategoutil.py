import re

def get_int_tuples(text):
    """converts stratego simulation output to list of tuples
    (int, int)
    """
    string_tuples = re.findall(r"\((\d+),(\d+)\)", text)
    int_tuples = [(int(t[0]), int(t[1])) for t in string_tuples]
    return int_tuples

def get_duration_action(tpls, MAX_TIME=None):
    """get tuples (duration, action) from tuples (time, variable) 
    resulted from simulate quiery 
    """
    result = []
    if len(tpls) == 1: # can only happen if always variable == 0
        result.append((MAX_TIME, 0))
    elif len(tpls) == 2: # can only hapen of always variable != 0
        action = tpls[1][1]
        result.append((MAX_TIME, action))
    else:
        for i in range(1, len(tpls)):
            duration = tpls[i][0] - tpls[i-1][0] 
            action = tpls[i][1]
            if duration > 0:
                result.append((duration, action))

            
    return result