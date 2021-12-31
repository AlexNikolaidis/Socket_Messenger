import socket
import struct
import threading
import os
import subprocess
import time
from datetime import datetime
from requests import get
from getmac import get_mac_address as gma
import messenger_pb2


HOST = '127.0.0.1'
PORT = 65432
ADDR = (HOST, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
print(f'[CONNECTED TO {ADDR}]')


def initialize_connection():
    # sends CONN_REQ message
    msg = messenger_pb2.project_message()
    msg.conn_req_msg.name = 'Alex'
    msg.conn_req_msg.header.type = 1
    send_msg = msg.SerializeToString()
    client.sendall(send_msg)
    print('[SENT CONN_REQ]->', end='')
    # waits to receive CONN_RESP message
    buf_data = client.recv(1500)
    msg = messenger_pb2.project_message()
    msg.ParseFromString(buf_data)
    msg_type = msg.WhichOneof('msg')
    # checks if the correct message type was received
    if msg_type == 'conn_resp_msg':
        print('[RECEIVED CONN_RESP]->', end='')
        if msg.conn_resp_msg.direction == 1:
            # saves the assigned id from received message
            user_id = msg.conn_resp_msg.assigned_id
            print('[SUCCESSFUL CONN HANDSHAKE]->', end='')
            print(f'[ID IS {user_id}]')
            return user_id
    else:
        print('[UNSUCCESSFUL CONN HANDSHAKE]->', end='')
        print('[DID\'T RECEIVE ID]')
        return -1


def discovery(user_id):
    # sends DISCOVER message
    msg = messenger_pb2.project_message()
    msg.discover_req_msg.header.type = 5
    msg.discover_req_msg.header.user_id = user_id
    send_msg = msg.SerializeToString()
    client.sendall(send_msg)
    print('[SENT DISCOVER_REQ]->', end='')
    # waits to receive DISCOVER_RESP message
    buf_data = client.recv(1500)
    msg = messenger_pb2.project_message()
    msg.ParseFromString(buf_data)
    msg_type = msg.WhichOneof('msg')
    # checks if the correct message type was received
    if msg_type == 'discover_resp_msg':
        print('[RECEIVED DISCOVER_RESP]->', end='')
        if msg.discover_resp_msg.direction == 1:
            # saves the discovered users on a list
            discovered_users = msg.discover_resp_msg.user
            print('[SUCCESSFUL DISCOVER HANDSHAKE]->', end='')
            print(f'[DISCOVERED USERS ARE {discovered_users}]')
            return discovered_users
    else:
        print('[UNSUCCESSFUL CONN HANDSHAKE]->', end='')
        print('[DID\'T RECEIVE ID]')
        return 1


# def main():
#
#     global end_conn_lock
#     # the executable in iperf command required in NEAT_MEAS
#     # {iperf_command} -c HOST -t INTERVAL -p PORT
#     iperf_command = './iperf'
#
#     send_conn()
#     # HELLO_MSG need new thread as need to be sent concurrently to other messages
#     hello_thread = threading.Thread(target=send_hello, args=(interv,))
#     hello = hello_thread.start()
#     # time.sleep(1)
#     netstat = send_netstat()
#     # time.sleep(1)
#     netmeas = send_netmeas(iperf_command)
#     # signals send_hello function to exit on next interval
#     end_conn_lock = True
#     hello_thread.join()
#     if not hello and not netstat and not netmeas:
#         print('[SUCCESSFUL EXECUTION]')
#         print('[EXITING]')
#         return 0
#     if hello:
#         print('[FAILED HELLO]')
#     if netstat:
#         print('[FAILED NETSTAT]')
#     if netmeas:
#         print('[FAILED NETMEAS]')
#     print('[EXITING]')


def main():
    initialize_connection()


if __name__ == '__main__':
    main()
