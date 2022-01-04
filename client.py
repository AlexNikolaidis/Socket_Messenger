import socket
import time
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
    print('[SENT CONN_REQ]')
    # waits to receive CONN_RESP message
    buf_data = client.recv(1500)
    msg = messenger_pb2.project_message()
    msg.ParseFromString(buf_data)
    msg_type = msg.WhichOneof('msg')
    # checks if the correct message type was received
    if msg_type == 'conn_resp_msg':
        print('[RECEIVED CONN_RESP]')
        if msg.conn_resp_msg.direction == 1:
            # saves the assigned id from received message
            user_id = msg.conn_resp_msg.assigned_id
            print(f'[ID IS {user_id}]')
            msg = messenger_pb2.project_message()
            msg.conn_resp_ack_msg.header.type = 3
            msg.conn_resp_ack_msg.header.id = user_id
            msg.conn_resp_ack_msg.direction = 1
            send_msg = msg.SerializeToString()
            client.sendall(send_msg)
            print('[SENT CONN_RESP_ACK]')
            print('[SUCCESSFUL CONN HANDSHAKE]')
            return user_id
    else:
        print('[UNSUCCESSFUL CONN HANDSHAKE]')
        print('[DID\'T RECEIVE ID]')
        return -1


def discovery(user_id):
    # sends DISCOVER message
    msg = messenger_pb2.project_message()
    msg.discover_req_msg.header.type = 6
    msg.discover_req_msg.header.id = user_id
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
        # saves the discovered users on a list
        discovered_users = msg.discover_resp_msg.user
        print('[SUCCESSFUL DISCOVER HANDSHAKE]->', end='')
        print(f'[DISCOVERED USERS ARE {discovered_users}]')
        return discovered_users
    else:
        print('[UNSUCCESSFUL DISCOVER HANDSHAKE]->', end='')
        print('[DID\'T RECEIVE DISCOVERED USERS]')
        return 1


def disconnect(user_id):
    msg = messenger_pb2.project_message()
    msg.exit_msg.header.type = 11
    msg.exit_msg.header.id = user_id
    send_msg = msg.SerializeToString()
    client.sendall(send_msg)
    print('[SENT EXIT]')


def main():
    id = initialize_connection()
    time.sleep(4)
    # discovery(id)
    disconnect(id)
    client.close()


if __name__ == '__main__':
    main()
