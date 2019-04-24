"""
 Implements a server that communicates with a client via sockets TCP. It is used to create a chat for multiple users.
 It has a console which is used to evoke commands from the server itself

 Daniel Afonso - 170221004
 André Ribeiro - 170221006

"""

import socket
from threading import Thread
import time
import re

# Define socket host and port


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000


# This function sends a string to all connections in said room
def echo_all_clients(room, message):
    room_list = room.get_clients()
    for connection in room_list:
        echo_client(connection, message)


# This function sends a message to a connection
def echo_client(connection, message):
    try:
        connection.sendall(message.encode())
    except ConnectionResetError:
        print("The user has disconnected and the message wasn't sent")


# This function sends an array of bytes to all clients in said room(used for images)
def echo_bytes_all_clients(room, message):
    room_list = room.get_clients()
    for connection in room_list:
        connection.sendall(message)


# This function returns if this username is an admin of a room
def is_admin(room, name):
    for username in room.admin_clients:
        if username == name:
            return True
    for username in server.super_admins:
        if username == name:
            return True
    return False


# Class server is the Server of the project, it has a socket, list of rooms, connections and admins for a chat
class Server:

    def __init__(self):
        # Create socket
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.__server_socket.listen(1)

        # Create common room, list of rooms and list of connections connected to the server
        self.__common_room = Room(name="#geral")
        self.__list_of_rooms = [self.__common_room]
        # Relation between a connection and an username
        self.__conns_to_username = {}
        # This variable is to make sure the client's username is always unique
        self.__last_number_logged = 0
        self.super_admins = []
        print('Listening on port %s ...' % SERVER_PORT)

    # This function starts the server
    def start_server(self):
        console_thread = Thread(target=self.console_handler, args=[])
        console_thread.start()
        while True:
            # Wait for client connections
            client_connection, client_address = self.__server_socket.accept()

            # A thread is created to take care of the user's requests
            thread = Thread(target=self.__start_client, args=[client_connection])
            thread.start()

    # This function is for the console part of the server, where it handles it's commands
    def console_handler(self):
        while True:
            command = input("> ")
            split_command = command.split(" ")
            if split_command[0] == "/superadmin":
                # Check if the protocol is being followed, if not, skip
                if len(split_command) != 2:
                    print("please use this format: /superadmin {name}")
                    continue
                # Make username super admin
                username = split_command[1]
                if self.find_conn_by_name(username) is not None:
                    self.super_admins.append(username)
                    print(f"Username added as superadmin: {username}")
                else:
                    print("Username doesnt exist in this server")

    # This function closes the server
    def close_server(self):
        # Close socket
        self.__server_socket.close()

    # This function is used to find a room by name on the server
    def find_room_by_name(self, name):
        found_room = None
        if name[0] == "#":
            name = name[1::]
        for room in self.__list_of_rooms:
            # Check if room exists, if so, doesn't create it
            if name == room.name[1::]:
                found_room = room
        return found_room

    # This function is to find a connection of an user, given it's name
    def find_conn_by_name(self, name):
        for k, v in self.__conns_to_username.items():
            if name.upper() == v.upper():
                return k

    # This function finds the name of an user, given it's connection
    def find_name_by_conn(self, conn):
        for k, v in self.__conns_to_username.items():
            if k == conn:
                return v

    # This function is the main loop to where the client will go to and will get it's requests
    def __start_client(self, conn):
        # When accepted, its requested it's username so it can start
        name = conn.recv(1024).decode()
        # Make sure the name is unique
        logged = str(self.__last_number_logged)
        logged = logged.zfill(4)
        name = logged + name
        self.__last_number_logged += 1
        name = name.replace(" ", "")
        # Feedback to the user what the final username is
        message = f"You are now connected, {name}"
        echo_client(conn, message)
        time.sleep(0.5)

        # Add the connection to the dictionary of connected clients with its name
        self.__conns_to_username[conn] = name

        # He goes directly to the common room and its broadcasted his connection to all users in it
        self.__common_room.add_client(conn)
        message = "%s has joined the chat!" % name
        echo_all_clients(self.__common_room, message)

        # Initial room of the connection
        client_room = self.__common_room

        # Main Loop of the client's choices and messages
        while True:
            # Print message from client
            try:
                # Treatment for command of image type
                msg = conn.recv(1024).decode()
                msg_split = msg.split("->")
                if msg_split[0] == "/send_image":
                    # It sends a feedback to the client that is receiving said image
                    echo_client(conn, "Receiving image->" + msg_split[1])
                    image_array = []
                    # Since images are long arrays of bits, and we can only pass 1024 bits per message on the socket
                    # We need a while loop to send all the bites
                    while True:
                        bit_array = conn.recv(1024)
                        print(bit_array)
                        image_array.append(bit_array)
                        # To know if the binary code of the image file is complete
                        bit_array_end = bit_array.split("IEND".encode())
                        if len(bit_array_end) == 2:
                            break
                    # Sends all clients in the room the image
                    echo_all_clients(client_room, "Sending image...")
                    for i in image_array:
                        echo_bytes_all_clients(client_room, i)
                    continue

                # This message treatment is for a normal command, not image
                msg = msg.strip()
                msg_split = msg.split(" ")
            except ConnectionResetError:
                # Error occurs if the client leaves the server without properly disconnecting
                print(f"Something went bad and client {name} disconnected abruptly")
                client_room.remove_client(conn)
                message = ("an error as occurred to %s and he has disconnected" % name)
                echo_all_clients(client_room, message)
                return

            # Check for exit
            if msg_split[0] == '/exit' and len(msg_split) == 1:
                conn.sendall(("Goodbye, %s" % name).encode())
                break

            # Check if client wants to whisper to someone (private message)
            if msg_split[0] == "/whisper":
                # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 3:
                    echo_client(conn, "please use this format: /whisper {name} {message}")
                    continue
                other_name = msg_split[1]
                send_message = " ".join(msg_split[2::])
                other_conn = self.find_conn_by_name(other_name)

                if other_conn is not None:
                    # Message to whisper
                    message = f"{name} has whispered you: " + send_message
                    echo_client(other_conn, message)
                    echo_client(conn, f"You whispered to {other_name}: {send_message}")
                else:
                    echo_client(conn, f"There is no client with this name: {other_name}")
                continue

            # Check if client wants to open a new room
            if msg_split[0] == '/create':
                # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 2:
                    echo_client(conn, "please use this format: /create {room_name} limit({max_limit}) password({"
                                      "password}) ")
                    continue
                room_name = msg_split[1]
                found_room = self.find_room_by_name(room_name)

                # Check if user wants password or max limit of people in room
                limit = -1
                password = ""
                if len(msg_split) > 2:
                    first_request = re.split("\(|\)", msg_split[2])
                    if len(first_request) < 2:
                        echo_client(conn, "please use this format on the parameters: limit(number) and password(pass)")
                        continue
                    if first_request[0] == "limit":
                        try:
                            limit = int(first_request[1])
                        except ValueError:
                            echo_client(conn, "please use a number to refer to the limit")
                            continue
                    elif first_request[0] == "password":
                        password = str(first_request[1])
                    # This is in case the user has given two parameters, and we have to take care of both
                    # Since we give the option of putting password or limit in whatever place the user wants,
                    # We have to check for both again
                    if len(msg_split) > 3:
                        second_request = re.split("\(|\)", msg_split[3])
                        if len(second_request) < 2:
                            echo_client(conn,
                                        "please use this format on the parameters: limit(number) and password(pass)")
                            continue
                        if limit == -1:
                            try:
                                limit = int(second_request[1])
                            except ValueError:
                                echo_client(conn, "please use a number to refer to the limit")
                                continue
                        else:
                            password = str(second_request[1])
                    # Check if the parameters are being used correctly
                    if limit == 0:
                        echo_client(conn, "please use a number higher than 0")
                        continue
                # If there is't a room with that name, the Client creates a new room with said name
                if found_room is None:
                    # Removes client from previous room
                    client_room.remove_client(conn)
                    # Creates new room and adds him to it
                    new_room = Room(name=room_name, size=limit, password=password)
                    new_room.add_client(conn, password=password)
                    new_room.add_admin(name)
                    self.__list_of_rooms.append(new_room)
                    client_room = new_room
                    message = "You are now connected to the room %s" % room_name
                    echo_client(conn, message)
                else:
                    echo_client(conn, "this room already exists")
                continue

            # Check if client wants to join a room
            if msg_split[0] == '/join':
                password = ""
                # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 2:
                    echo_client(conn, "please use this format: /join #{room_name} {password}")
                    continue
                if len(msg_split) == 3:
                    password = str(msg_split[2])
                # If everything checks, the user joins the chat
                room_name = msg_split[1]
                found_room = self.find_room_by_name(room_name)
                # Client only joins a room, if this one is found
                if found_room is not None:
                    # Check if username has been banned from the server
                    banned = False
                    for client in found_room.banned_clients:
                        if client == name:
                            banned = True
                    if banned:
                        echo_client(conn, "this username has been banned from this chat")
                        continue

                    # Check if the user needs to enter a password to join the room, and if he has entered one.
                    # It checks if it's correct
                    try:
                        found_room.add_client(conn, password)
                    except ValueError as error:
                        echo_client(conn, "Error: " + repr(error))
                        continue
                    client_room.remove_client(conn)
                    client_room = found_room
                    message = "You are now connected to the room %s" % found_room.name
                    echo_client(conn, message)
                    # Echo to all other clients on this room, that an user has joined
                    echo_all_clients(client_room, f"User {name} has connected room {found_room.name}")
                else:
                    echo_client(conn, "this room doesn't exist")
                continue

            # Check if client wants to list all rooms of the server
            if msg_split[0] == "/list":
                # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 1:
                    echo_client(conn, "please use this format: /list")
                    continue
                # Lists all the rooms in the server, and the number of people in said room
                for room in self.__list_of_rooms:
                    echo_client(conn, f"{room.name} ({len(room.get_clients())})")
                continue

            # Check if the user wants to kick another user
            if msg_split[0] == "/kick":
                admin = is_admin(client_room, name)
                if not admin:
                    echo_client(conn, "You must be an admin of this room to use this command")
                    continue
                # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 2:
                    echo_client(conn, "please use this format: /kick {name}")
                    continue
                kicked_name = msg_split[1]
                kicked_conn = self.find_conn_by_name(kicked_name)
                if kicked_conn is None:
                    echo_client(conn, f"Name not found: {kicked_name}")
                else:
                    # The client joins the other room, leaving the room that he is, by himself
                    # Echos for both clients saying they got kicked, and kicked the other
                    echo_client(conn, f"You have kicked: {kicked_name}")
                    echo_client(kicked_conn, f"/Kicked from {client_room.name}...")
                continue

            # Checks if the user wants to permaban another user
            if msg_split[0] == "/permaban":
                admin = is_admin(client_room, name)
                if not admin:
                    echo_client(conn, "You must be an admin of this room to use this command")
                    continue
                    # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 2:
                    echo_client(conn, "please use this format: /permaban {name}")
                    continue
                banned_name = msg_split[1]
                banned_conn = self.find_conn_by_name(banned_name)
                if banned_conn is None:
                    echo_client(conn, f"Name not found: {banned_conn}")
                else:
                    client_room.ban_clients(banned_name)
                    echo_client(conn, f"You have banned: {banned_name}")
                    echo_client(banned_conn, f"/Kicked from {client_room.name} FOREVER")
                continue

            # Checks if the user wants to unban another user
            if msg_split[0] == "/unban":
                admin = is_admin(client_room, name)
                if not admin:
                    echo_client(conn, "You must be an admin of this room to use this command")
                    continue
                    # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 2:
                    echo_client(conn, "please use this format: /unban {name}")
                    continue
                unban_name = msg_split[1]
                unban_conn = self.find_conn_by_name(unban_name)
                if unban_conn is None:
                    echo_client(conn, f"Name not found: {unban_name}")
                else:
                    client_room.banned_clients.remove(unban_name)
                    echo_client(conn, f"You have unbanned: {banned_name}")
                    echo_client(unban_conn, f"Unbanned from {client_room.name}")
                continue

            # Checks if the user wants to broadcast to all users
            if msg_split[0] == "/broadcast":
                # Check if the protocol is being followed, if not, skip
                if len(msg_split) < 2:
                    echo_client(conn, "please use this format: /broadcast {message}")
                    continue
                if name not in self.super_admins:
                    echo_client(conn, "You are not allowed to use this command")
                    continue
                broadcast_message = " ".join(msg_split[1::])
                for r in self.__list_of_rooms:
                    echo_all_clients(r, f"Broadcasted message: {broadcast_message}")
                continue

            # Checks if the user sent a forbidden command(used to take of people kicked in server/user interactions)
            if msg_split[0] == "/Kicked":
                echo_client(conn, "You can not send this command")
                continue
            # Checks if the user has requested for the list of people in room(this is automatic in the UI)
            if msg_split[0] == "/return_room_list":
                conn_list = client_room.get_clients()
                name_list = []
                for connection in conn_list:
                    client_name = self.find_name_by_conn(connection)
                    name_list.append(client_name)
                echo_client(conn, "update_room_list->" + client_room.name + "->" + '\n'.join(name_list))
                continue

            # Return the message to the server console
            print('Received: (%s)' % name, msg)
            # Return message to all clients in the client's room
            message_time = time.ctime()
            message = f"@{message_time}- [{client_room.name}] {name}: {msg}"
            echo_all_clients(client_room, message)

        # Close client connection
        print('Client disconnected...')
        conn.close()
        client_room.remove_client(conn)
        message = ("%s has left the server..." % name)
        echo_all_clients(client_room, message)


# Class Room takes care of a room, has it's admins as well as the size and password and banned clients
class Room:
    def __init__(self, name, size=-1, password=""):
        if name[0] != "#":
            name = "#" + name
        self.name = name
        self.__list_connections = []
        self.size = size
        self.password = password
        self.admin_clients = []
        self.banned_clients = []

    # This function adds a client to the room. It pays attention if the room has password and compares to the one given
    # As well as if the size of the room can support a new addition
    def add_client(self, conn, password=""):
        if len(self.__list_connections) < self.size or self.size == -1:
            if self.password == password:
                self.__list_connections.append(conn)
            else:
                raise ValueError("The passwords dont match")
        else:
            raise ValueError("This room can not carry another person")

    # This function returns a copy of the clients on the room
    def get_clients(self):
        copy_list = self.__list_connections.copy()
        return copy_list

    # This function removes a client from a room
    def remove_client(self, conn):
        self.__list_connections.remove(conn)

    # This function makes a certain username an admin of the room
    def add_admin(self, username):
        self.admin_clients.append(username)

    # This function bans an username
    def ban_clients(self, username):
        self.banned_clients.append(username)


# These lines of code is that it needs to run this server. This is used on the project to demonstrate the server.
server = Server()
server.start_server()
