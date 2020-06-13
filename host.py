import os
import socket
import traceback
import select
import threading
from datetime import datetime

logdir_path = "logs"
HOST_ADDR = ("localhost", 80)


def write_msg_to_file(msg, addr, client_log_dir):
    now = datetime.now()
    
    today = now.strftime("%d-%m-%Y")
    time  = now.strftime("%H:%M:%S")

    today_logfile_path = client_log_dir + "/" + today + ".txt"

    if not os.path.exists(today_logfile_path):
        f = open(today_logfile_path, "w")
        f.close()

    with open(today_logfile_path, "a") as logfile:
        logfile.write("--------" + time + "--------\n")
        logfile.write(msg)
        logfile.close()

    return
    

def on_new_client(clientsock, addr):
    print("new thread created")
    while True:
        print("connection from", addr)
        msg = clientsock.recv(256).decode('utf-8')

        if msg:
            client_log_dir = logdir_path + "/" + addr[0]
            if not os.path.exists(client_log_dir):
                try:
                    os.mkdir(client_log_dir)
                except OSError:
                    print("Creation of directory at", client_log_dir, "failed")

            write_msg_to_file(msg, addr, client_log_dir)
            print(addr, ">>", msg)
    
def main():
    if not os.path.exists(logdir_path):
        try:
            os.mkdir(logdir_path)
        except OSError:
            print("Creation of directory at", logdir_path, "failed, terminating")
            exit()

    tcp_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("server started, waiting for clients on", HOST_ADDR)
    tcp_host.bind(HOST_ADDR)
    tcp_host.listen(5)
    print("listening...")

    threads = []

    while True:
        c, addr = tcp_host.accept()
        print("connection accepted from", addr)
        t = threading.Thread(target=on_new_client, args=(c,addr,))
        threads.append(t)
        t.start()

    
main()