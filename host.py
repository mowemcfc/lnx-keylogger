import os
import socket
import traceback
import select
import threading
import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from datetime import datetime

logdir_path = "logs"
HOST_ADDR = ("localhost", 80)

class Packet:
    def __init__(self):
        self.type = ""
        self.time = datetime.now().strftime("%H:%M:%S")
        self.data = ""

#TODO: COMMENT EVERYTHING


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
    

def handle_key_request(clientsock):
    private_key = rsa.generate_private_key(
        public_exponent = 65537,
        key_size = 2048,
        backend = default_backend()
    )

    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    key_response_packet = Packet()
    key_response_packet.type = "PUB_KEY"
    key_response_packet.data = public_key_bytes.decode()

    print(key_response_packet.data)

    key_response_str = json.dumps(key_response_packet.__dict__)
    clientsock.sendall(key_response_str.encode("utf-8"))
    print("public key sent")

    return private_key

def on_new_client(clientsock, addr):
    print("new thread created")
    while True:
        data = clientsock.recv(256).decode('utf-8')
        data_dict = json.loads(data)

        print(addr, ">>", data)

        if data:
            client_log_dir = logdir_path + "/" + addr[0]
            if not os.path.exists(client_log_dir):
                try:
                    os.mkdir(client_log_dir)
                except OSError:
                    print("Creation of directory at", client_log_dir, "failed")
            
            if data_dict["type"] == "KEY_REQ":
                private_key = handle_key_request(clientsock)
            else:
                write_msg_to_file(data_dict["data"], addr, client_log_dir)
    
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