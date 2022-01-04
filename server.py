import messenger_pb2
import threading
import socket

HOST = '0.0.0.0'
PORT = 65432
ADDR = (HOST, PORT)

# clients list -> for each client -> [client thread, conn, user id, name]
# client status -> 0 active / 1 away / 2 do not disturb
#
#
#
#

test_array = [[1, 2, 3, 'test1'], [4, 5, 6, 'test2'], [7, 8, 9, 'test3']]


class Client:
    def __init__(self, conn, user_id, status):
        self.conn = conn
        self.user_id = user_id
        self.status = status

    def conn_handshake(self):
        # waits to receive CONN_REQ message
        buf_data = self.conn.recv(1500)
        msg = messenger_pb2.project_message()
        msg.ParseFromString(buf_data)
        msg_type = msg.WhichOneof('msg')
        # checks if the correct message type was received
        if msg_type == 'conn_req_msg':
            name = msg.conn_req_msg.name
            # print(f'[RECEIVED CONN_REQ: NAME IS {name}]')
            # sends CONN_RESP message
            msg = messenger_pb2.project_message()
            msg.conn_resp_msg.direction = 1
            msg.conn_resp_msg.assigned_id = self.user_id
            msg.conn_resp_msg.header.id = 0
            msg.conn_resp_msg.header.type = 2
            send_msg = msg.SerializeToString()
            self.conn.sendall(send_msg)
            # print('[SENT CONN_RESP] ')
            buf_data = self.conn.recv(1500)
            msg = messenger_pb2.project_message()
            msg.ParseFromString(buf_data)
            msg_type = msg.WhichOneof('msg')
            if msg_type == 'conn_resp_ack_msg':
                if msg.conn_resp_ack_msg.direction == 1:
                    print(f'[USER {self.user_id}: SUCCESSFUL CONN HANDSHAKE]')
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
        self.clients = [[]]
        self.ids = [[]]

    def run_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(self.addr)
        print(f'[STARTED SERVER ON {self.addr}]')
        s.listen()
        self.clients.pop(0)
        assigned_user_id = 1
        while True:
            conn, addr = s.accept()
            started_thread = False
            for iter in self.clients:
                if len(iter) != 0:
                    if not iter[0].is_alive():
                        iter[0] = threading.Thread(target=self.new_client, args=(conn, iter[2]))
                        iter[0].start()
                        started_thread = True
                        print(f'[STARTED NEW THREAD FOR USER WITH ID {iter[2]}]')
                        break
            if not started_thread:
                self.clients.append([threading.Thread(target=self.new_client, args=(conn, assigned_user_id)),
                                     conn, assigned_user_id])
                self.clients[len(self.clients) - 1][0].start()
                print(f'[STARTED NEW THREAD FOR USER WITH ID {assigned_user_id}]')
                assigned_user_id += 1
            print(f'connected clients: {threading.active_count() - 1}')

    def run_discovery(self, user_id):
        discovered_users = self.clients
        # print(discovered_users)
        for enum, element in enumerate(discovered_users):
            if user_id == element[2]:
                break
        discovered_users.pop(enum)
        return discovered_users

    def new_client(self, conn, user_id):
        client = Client(conn, user_id, 0)
        # print(self.clients)
        for x, element in enumerate(self.clients):
            if user_id == element[2]:
                break

        # saves client's name
        self.clients[x].append(client.conn_handshake())
        name = self.clients[x][3]
        if name == -1:
            print(f'[USER {user_id}: SOME ERROR OCCURRED]')
            return -1
        disconnect = False

        while not disconnect:
            # receive message
            buf_data = conn.recv(1500)
            msg = messenger_pb2.project_message()
            msg.ParseFromString(buf_data)
            msg_type = msg.WhichOneof('msg')
            if msg_type == 'discover_req_msg':
                disc = self.run_discovery(user_id)
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
                    buf_data = conn.recv(1500)
                    msg = messenger_pb2.project_message()
                    msg.ParseFromString(buf_data)
                    msg_type = msg.WhichOneof('msg')
                    if msg_type == "discovery_resp_ack_msg":
                        if msg.direction == 2:
                            disconnect = True
                            print(f'[USER {user_id}: SOME ERROR OCCURRED]')
                    else:
                        disconnect = True
                        print(f'[USER {user_id}: SOME ERROR OCCURRED]')
                else:
                    msg = messenger_pb2.project_message()
                    msg.discover_resp_msg.header.id = 0
                    msg.discover_resp_msg.header.type = 7
                    send_msg = msg.SerializeToString()
                    client.conn.sendall(send_msg)
                    # waits for ack
                    buf_data = conn.recv(1500)
                    msg = messenger_pb2.project_message()
                    msg.ParseFromString(buf_data)
                    msg_type = msg.WhichOneof('msg')
                    if msg_type == "discovery_resp_ack_msg":
                        if msg.direction == 2:
                            disconnect = True
                            print(f'[USER {user_id}: SOME ERROR OCCURRED]')

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


        # time.sleep(15)
        # i = self.ids.index((user_id, True))
        # self.ids[i] = (user_id, False)
        client.conn.close()
        print(f'[USER {user_id}: DISCONNECTED]')


def main():
    server = Messenger(ADDR)
    server.run_server()


if __name__ == "__main__":
    main()
