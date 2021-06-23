import select
import socket
import threading
import sys
import time


class Participant:
    def __init__(self, IP, PORT):
        self.IP = IP
        self.PORT = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class Client(Participant):
    def __init__(self, IP, PORT):
        Participant.__init__(self, IP, PORT)
        self.msg = ""
        self.rlist = []
        self.wlist = []
        self.xlist = []
        self.thread = threading.Thread(target=self.input)

    def socket_connector(self):
        try:
            self.socket.connect((self.IP, self.PORT))

        except(ConnectionRefusedError):
            print("there is no connection to the server")

    def input(self):
        while True:
            message = sys.stdin.readline().strip()
            sys.stdout.flush()
            self.socket.send(message.encode())

    def handel(self):
        self.thread.start()
        try:
            while True:
                self.rlist, self.wlist, self.xlist = select.select([self.socket], [], [])
                input = self.socket.recv(1024)
                print(input.decode())

        except (ConnectionRefusedError, ConnectionResetError):
            print("Connection with the server was lost")
            self.socket.close()

            self.thread.join()


class Server(Participant):
    def __init__(self, IP, PORT, listeners):
        Participant.__init__(self, IP, PORT)
        self.listeners = listeners
        self.open_client_sockets = []
        self.messages_to_send = []
        self.read_list = []
        self.write_list = []
        self.error_list = []
        self.socket_dic = {}

    def socket_connector(self):
        self.socket.bind((self.IP, self.PORT))
        self.socket.listen(self.listeners)

    def receive(self):
        while True:
            self.read_list, self.write_list, self.error_list = select.select([self.socket] + self.open_client_sockets,
                                                                             self.open_client_sockets, [])
            for current_socket in self.read_list:
                if current_socket is self.socket:

                    (new_socket, address) = self.socket.accept()
                    self.open_client_sockets.append(new_socket)
                    new_socket.send("what is your username".encode())
                    try:
                        name = new_socket.recv(1024).decode()
                        while name in self.socket_dic.values():
                            new_socket.send("name is already taken pls enter another name".encode())
                            name = new_socket.recv(1024).decode()

                        self.socket_dic[new_socket] = name
                        print(f'connected {name} : {new_socket}\n')
                        new_socket.send("connected".encode())

                    except (ConnectionResetError, ConnectionAbortedError):
                        self.open_client_sockets.remove(new_socket)
                        del self.socket_dic[new_socket]
                        print(f'closed {new_socket}\n')

                else:
                    try:
                        data = current_socket.recv(1024).decode()
                        self.messages_to_send.append((current_socket, data))
                        self.send()
                        print(data)

                    except (ConnectionResetError, ConnectionAbortedError):
                        self.open_client_sockets.remove(current_socket)
                        print(f'closed {self.socket_dic[current_socket]} : {current_socket}\n')
                        del self.socket_dic[current_socket]

    def send(self):
        for i in self.messages_to_send:
            sock, msg = i
            name = self.socket_dic[sock]
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)

            for s in self.write_list:
                if s != sock:
                    s.send(f'<{current_time}>{name}: {msg}'.encode())
            self.messages_to_send.remove(i)
