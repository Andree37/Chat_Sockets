"""
 Implements a client that communicates with a server via sockets TCP. It can be attached to an UI, making it modular.

 Daniel Afonso - 170221004
 André Ribeiro - 170221006

"""

import socket
import time
from threading import Semaphore

# Define socket host and port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000


# Client keeps control of the socket it has as well as some commands it has to send over to the server
class Client:

    def __init__(self):
        # Create socket
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sem = Semaphore()  # used to stop client from requesting clients in room whilst sending an image

    # This function connects the client to the server
    def connect_to_server(self, username):
        # Connect to server
        self.__client_socket.connect((SERVER_HOST, SERVER_PORT))

        # Get username
        self.__client_socket.send(username.encode())

    # This function is the one that reads the messages from the server
    def read_messages(self, ui_func):
        while True:
            try:
                message = self.__client_socket.recv(1024).decode()
                # ui_func is defined by the UI
                ui_func(message)
                split_message = message.split(" ")
                if split_message[0] == "Connection":
                    break

                # These two commands are for image sending between the client/UI and client/server
                if split_message[0] == "Receiving":
                    path = message.split("->")
                    self.send_messages("/sending_image->" + path[1])

                if split_message[0] == "Sending":
                    image_array = []
                    while True:
                        bit_array = self.__client_socket.recv(1024)
                        print(bit_array)
                        image_array.append(bit_array)
                        bit_array_end = bit_array.split("IEND".encode())
                        if len(bit_array_end) == 2:
                            break

                    ui_func("receive_image->", image_array)

                # Protocol if the person is kicked from a room, it joins #geral
                if split_message[0] == "/Kicked":
                    self.send_messages("/join #geral")

                # Automatic message trading between user and server
                if split_message[0] == "/returned_list":
                    self.send_messages("update_room_list->")

            except ConnectionAbortedError:
                print("Connection was broken")
                break
            except ConnectionResetError:
                ui_func("RIP")
                print("Server was lost")
                break

    # This function is the one that takes care of the messages sent to the server
    def send_messages(self, msg):
        split_msg = msg.split("->")
        # If the message is to send an image, it prepares the server to receive an image
        if split_msg[0] == "/send_image":
            try:
                file = open(split_msg[1], "r")
                file.close()
            except FileNotFoundError:
                self.__client_socket.sendall("Please select a valid file".encode())
                return
            self.__client_socket.sendall(msg.encode())

        # If the message is sending an image, it tells the server that the next message is gonna be an image
        elif split_msg[0] == "/sending_image":
            self.sem.acquire()
            file = open(split_msg[1], 'rb')
            pack = file.read(1024)
            while pack:
                self.__client_socket.send(pack)
                pack = file.read(1024)
            file.close()
            self.sem.release()

        # If the message is receive image, it tells the server that is ready to recieve an image
        elif split_msg[0] == "receive_image":
            print("Receiving an image")
            self.sem.acquire()
            image_array = []
            while True:
                bit_array = self.__client_socket.recv(1024)
                if bit_array is None:
                    break
                image_array.append(bit_array)
            self.sem.release()

        # Automatic protocol between the client and server
        elif split_msg[0] == "update_room_list":
            return
        # Exists the main loop and closes
        elif split_msg[0] == "/exit":
            self.close_client()
        else:
            # Send message
            self.__client_socket.sendall(msg.encode())

    # This function triggers the read messages function with the UI function received
    def run(self, ui_read):
        self.read_messages(ui_read)

    # This function sends the requests to the server of the list of people in the room
    def get_client_room_list(self):
        while True:
            time.sleep(2)
            try:
                self.sem.acquire()
                self.__client_socket.sendall("/return_room_list".encode())
            except OSError:
                print("Connection was lost")
                self.sem.release()
                break
            self.sem.release()

    # This function opens the client's socket
    def open_client(self):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # This function closes the client's socket
    def close_client(self):
        # Close socket
        self.__client_socket.close()
