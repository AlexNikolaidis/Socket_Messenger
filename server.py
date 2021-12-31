import messenger_pb2
import threading
import socket


HOST = '0.0.0.0'
PORT = 65432
ADDR = (HOST, PORT)


def new_user(conn, user_id):
    conn.close()
    print(f'USER WITH IS {user_id} DISCONNECTED')


def main():
    users = [[]]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print(f'[STARTED SERVER ON {ADDR}]')
    s.listen()
    assigned_user_id = 0
    while True:
        conn, addr = s.accept()
        started_thread = False
        for iter in users:
            if len(iter) != 0:
                if not iter[0].isAlive():
                    iter[0] = threading.Thread(target=new_user, args=(conn, iter[1]))
                    started_thread = True
                    assigned_user_id += 1
                    print(f'[STARTED NEW THREAD FOR USER WITH ID {iter[1]}]')
                    break
        if not started_thread:
            users.append([threading.Thread(target=new_user, args=(conn, assigned_user_id)), assigned_user_id])
            started_thread = True
            assigned_user_id += 1
            print(f'[STARTED NEW THREAD FOR USER WITH ID {assigned_user_id}]')



if __name__ ==  "__main__":
    main()