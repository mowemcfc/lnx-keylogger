# **Introduction**
A simple keylogger program written in python (minus infection method) created to demonstrate Unix OS IO functionalities, file IO and socket programming.

## Setup
In a real-world scenario, the host script should be frozen into an .exe so that infected hosts will not require python to be installed. However, for demonstration purposes, you can simply run the scripts using Python 3.7.

Both the server.py and host.py files require the remote server address to be configured to match the IP and port you want to host the server on. This is all that is required to run the client/server on a LAN. You can additionally configure the location that log files will be saved to.


To run the hostfile on a remote network, you will require special network configurations (such as port-forwarding) in order for an outside address to initiate the TCP connection with server. You could also run server.py on a web server.

## To run
You will first require a running server for the host to send keystroke data back to.

`sudo python3 server.py`

From here, you can run the host script.

`sudo python3 host.py`



Written by mowemcfc.
