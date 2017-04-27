"""
Logger.py. Logs to the screen or to a file using the given VERBOSE value

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import inspect

from MainConfig import DO_LOG_TO_FILE, LOG_FILE, DO_LOG_JSON_TO_FILE, LOG_JSON_FILE
from MainConfig import VERBOSE


def log(tag, txt, min_verbose=0):
    """
    Log the txt with a certain tag to the screen/file if the verbose is high enough
    :param tag: The tag to print before the txt. If tag is empty, no brackets/tag will be printed. If tag is "json",
    the output will be written to the json log file if enabled
    :param txt: Text to log
    :param min_verbose: Log if min_verbose >= VERBOSE.    """
    txt = str(txt)
    if tag == "json":
        # write to json, two newlines between each output
        if DO_LOG_JSON_TO_FILE:
            write_to_file(LOG_JSON_FILE, "", txt + "\n\n", 5)
    # if high enough verbose level
    elif VERBOSE >= min_verbose:
        # print to screen
        write_to_screen(tag, txt)
        # write to log file if required
        if DO_LOG_TO_FILE:
            write_to_file(LOG_FILE, tag, txt)
        # print parent caller if high enough verbose level
        if VERBOSE >= 8:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            log_txt = "Called from " + calframe[1][1] + ", in " + calframe[1][3] + ", lineno = " + str(calframe[1][2])
            # same: log to screen/file
            write_to_screen("logger", log_txt, 3)
            if DO_LOG_TO_FILE:
                write_to_file(LOG_FILE, tag, txt)


def write_to_screen(tag, txt, tabs=1, file=None):
    """
    print to screen or to file
    :param tag: The tag to print before the txt
    :param txt: The txt to print
    :param tabs: amount of tabs to print before the tag
    :param file: file to write to or none to print to screen
    """
    txt = txt.strip()
    line = "\t" * tabs
    if len(tag) > 0:
        line += "[" + tag + "] "
    line += txt
    print(line, file=file)


def write_to_file(filename, tag, txt, tabs=3):
    """
    write to file
    :param filename: file path to write to 
    :param tag: The tag to print before the txt
    :param txt: The txt to print
    :param tabs: amount of tabs to print before the tag
    """
    with open(filename, "a") as myfile:
        write_to_screen(tag, txt, tabs, myfile)
