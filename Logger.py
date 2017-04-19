"""
Logger.py. Logs to the screen or to a file using the setted VERBOSE value

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import inspect

from MainConfig import DO_LOG_TO_FILE, LOG_FILE, DO_LOG_JSON_TO_FILE, LOG_JSON_FILE
from MainConfig import VERBOSE


def log(tag, txt, minVerbose=0):
    """
    Log the txt with a certain tag to the screen/file if the verbose is high enough
    :param tag: The tag to print before the txt. If tag is empty, no brackets/tag will be printed. If tag is "json",
    the output will be written to the json log file if enabled
    :param txt: Text to log
    :param minVerbose: Log if minVerbose >= VERBOSE.    """
    txt = str(txt)
    if tag == "json":
        # write to json, two newlines between each output
        if DO_LOG_JSON_TO_FILE:
            write_to_file(LOG_JSON_FILE, "", txt + "\n\n", 5)
    # if high enough verbose level
    elif VERBOSE >= minVerbose:
        # print to screen
        write_to_screen(tag, txt)
        # write to log file if required
        if DO_LOG_TO_FILE:
            write_to_file(LOG_FILE, tag, txt)
        # print parent caller if high enough verbose level
        if VERBOSE >= 8:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            logTxt = "Called from " + calframe[1][1] + ", in " + calframe[1][3] + ", lineno = " + str(calframe[1][2])
            # same: log to screen/file
            write_to_screen("logger", logTxt, 3)
            if DO_LOG_TO_FILE:
                write_to_file(LOG_FILE, tag, txt)


# print to screen or to file
def write_to_screen(tag, txt, tabs=1, file=None):
    txt = txt.strip()
    line = "\t" * tabs
    if len(tag) > 0:
        line += "[" + tag + "] "
    line += txt
    print(line, file=file)


# write to file
def write_to_file(filename, tag, txt, tabs=3):
    with open(filename, "a") as myfile:
        write_to_screen(tag, txt, tabs, myfile)
