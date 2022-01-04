import messenger_pb2
import threading
import socket

HOST = '0.0.0.0'
PORT = 65432
ADDR = (HOST, PORT)

# clients list -> list of client objects
# client status -> 0 active / 1 away / 2 do not disturb

class Client:
    def __init__(self, conn, user_id, status):
        self.thread = 0
        self.conn = conn
        self.id = user_id
        self.status = status
        self.name = 'NOT_SET'

    def conn_handshake(self):
        # waits to receive CONN_REQ message
        buf_data = self.conn.recv(1500)
        msg = messenger_pb2.project_message()
        msg.ParseFromString(buf_data)
        msg_type = msg.WhichOneof('msg')
        # checks if the correct message type was received
        if msg_type == 'conn_req_msg':
            name = msg.conn_req_msg.name
            # sends CONN_RESP message
            msg = messenger_pb2.project_message()
            msg.conn_resp_msg.direction = 1
            msg.conn_resp_msg.assigned_id = self.id
            msg.conn_resp_msg.header.id = 0
            msg.conn_resp_msg.header.type = 2
            send_msg = msg.SerializeToString()
            self.conn.sendall(send_msg)
            buf_data = self.conn.recv(1500)
            msg = messenger_pb2.project_message()
            msg.ParseFromString(buf_data)
            msg_type = msg.WhichOneof('msg')
            if msg_type == 'conn_resp_ack_msg':
                if msg.conn_resp_ack_msg.direction == 1:
                    print(f'[USER {self.id}: SUCCESSFUL CONN HANDSHAKE]')
                    return name
                else:
                    return -1
            else:
                return -1
        else:
            return -1


class Messenger:
    def __init__(self, addr):
        self.addr = addr
        self.clients = []

    def run_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(self.addr)
        print(f'[STARTED SERVER ON {self.addr}]')
        s.listen()
        assigned_user_id = 1
        while True:
            conn, addr = s.accept()
            started_thread = False
            for iter in self.clients:
                if not iter.thread.is_alive():
                    client = Client(conn, iter.id, 0)
                    client.thread = threading.Thread(target=self.new_client, args=(client,))
                    self.clients.remove(iter)
                    self.clients.append(client)
                    self.clients[len(self.clients) - 1].thread.start()
                    started_thread = True
                    print(f'[STARTED NEW THREAD FOR USER WITH ID {iter.id}]')
            if not started_thread:
                client = Client(conn, assigned_user_id, 0)
                client.thread = threading.Thread(target=self.new_client, args=(client,))
                self.clients.append(client)
                self.clients[len(self.clients) - 1].thread.start()
                print(f'[STARTED NEW THREAD FOR USER WITH ID {assigned_user_id}]')
                assigned_user_id += 1
            print(f'connected clients: {threading.active_count() - 1}')
            for i in self.clients:
                print(f'client {i.id} thread running -> {i.thread}')

    def run_discovery(self, client):
        discovered_users = self.clients.copy()
        discovered_users.remove(client)
        return discovered_users

    def new_client(self, client):
        # saves client's name
        client.name = client.conn_handshake()
        if client.name == -1:
            print(f'[USER {client.id}: SOME ERROR OCCURRED]')
            return -1
        disconnect = False
        while not disconnect:
            # receive message
            buf_data = client.conn.recv(1500)
            msg = messenger_pb2.project_message()
            msg.ParseFromString(buf_data)
            msg_type = msg.WhichOneof('msg')
            if msg_type == 'discover_req_msg':
                disc = self.run_discovery(client)
                if disc:
                    msg = messenger_pb2.project_message()
                    msg.discover_resp_msg.header.id = 0
                    msg.discover_resp_msg.header.type = 7
                    for element in disc:
                        user = msg.discover_resp_msg.user.add()
                        user.id = element[2]
                        user.name = element[3]
                    send_msg = msg.SerializeToString()
                    client.conn.sendall(send_msg)
                    # waits for ack
                    buf_data = client.conn.recv(1500)
                    msg = messenger_pb2.project_message()
                    msg.ParseFromString(buf_data)
                    msg_type = msg.WhichOneof('msg')
                    if msg_type == "discovery_resp_ack_msg":
                        if msg.direction == 2:
                            disconnect = True
                            print(f'[USER {client.id}: SOME ERROR OCCURRED]')
                    else:
                        disconnect = True
                        print(f'[USER {client.id}: SOME ERROR OCCURRED]')
                else:
                    msg = messenger_pb2.project_message()
                    msg.discover_resp_msg.header.id = 0
                    msg.discover_resp_msg.header.type = 7
                    send_msg = msg.SerializeToString()
                    client.conn.sendall(send_msg)
                    # waits for ack
                    buf_data = client.conn.recv(1500)
                    msg = messenger_pb2.project_message()
                    msg.ParseFromString(buf_data)
                    msg_type = msg.WhichOneof('msg')
                    if msg_type == "discovery_resp_ack_msg":
                        if msg.direction == 2:
                            disconnect = True
                            print(f'[USER {client.id}: SOME ERROR OCCURRED]')
            elif msg_type == 'exit_msg':
                disconnect = True
            elif msg_type == 'status_msg':
                # changes client's status to whatever was requested and sents back ack
                client.status = msg.status_msg.status
                msg = messenger_pb2.project_message()
                msg.status_ack_msg.header.id = 0
                msg.status_ack_msg.header.type = 10
                msg.status_ack_msg.direction = 1
                send_msg = msg.SerializeToString()
                client.conn.sendall(send_msg)
            elif msg_type == 'data_msg':
                pass
        client.conn.close()
        print(f'[USER {client.id}: DISCONNECTED]')


def main():
    server = Messenger(ADDR)
    server.run_server()


if __name__ == "__main__":
    main()
